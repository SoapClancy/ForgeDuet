# Candidate Markdown → Codex CLI bridge (step 1)

Status: candidate bridge 0.2, **fake-CLI tested only**. This is a separate runtime from typed `relay.py` 0.3.0; it does not change `handoff.py`. It supports the **reviewer** receiving Markdown in `deliveries/`. Claude's client-managed build watcher is separate. Do not run this bridge together with a native AI heartbeat, standalone watcher or typed dispatcher on the same review cursor/work.

Installation, documentation and fake tests do not start a project. Step 1 authorizes no real model call. Keep existing project monitors paused. Before any real smoke test, obtain the human's separate authorization, pin their actual CLI model/effort IDs, and use a small synthetic task. A successful real smoke test is required before project adoption.

## Local detector and dispatch

The persistent Python process uses the existing `handoff.Cursor.check`: filenames, SHA-256, completion markers, durable `seen` and unmarked diagnostics. Default example interval is 60 seconds; a human override wins. No model, CLI subprocess, network request or AI timer runs during idle detection. This proves zero **model calls for idle checks**, not zero OS work or zero overall review cost.

Only a complete pending event starts `codex exec`, serially and one event at a time. A completion marker is a transport claim; the reviewer must still validate full candidate SHA, task scope, self-tests, unresolved work and evidence. A changed previously handled file is explicitly labelled `mutated_record`; it is not automatic approval. Incomplete-file notices return `attention` without starting a model or acknowledging the file. Handle them durably with the existing transport notice / `ack-warning` procedure, then explicitly re-arm. Repeated scan failures retain diagnostics and pause after three checks. Invalid cursor/config state fails immediately; never reset it to empty.

The bridge owns both private bridge and watcher locks for its whole lifetime, including model work, preventing a second watcher on that cursor. The **shared writer lock is only taken for publication**, not while waiting, reviewing or testing. Private cursor/journal writes retain their own atomic/locking rules.

## Human-controlled setup — not a runnable project configuration

Use `bridge.example.json` as a placeholder reference. Every field is explicit; the bridge never selects a model or downgrades effort. `timeout_seconds` must be a finite positive number: null, zero, booleans, infinity and missing values fail before dispatch. The placeholder example uses 3600 seconds; choose and record an appropriate watchdog before any real run. This is a single-process watchdog, not a token/currency budget, and does not silently change any existing project configuration. Fake tests also use a positive timeout. `desktop_notifications` defaults to true when omitted; explicitly set false to disable best-effort local OS alerts while retaining peer-file notices. The script does not enforce a token or currency budget.

- `project_dir`: actual project; mailbox must be inside it, with existing `deliveries/` and `reviews/`.
- `cursor`: existing reviewer cursor. Initialize only a new run; preserve existing handled hashes and pauses. Do not automatically baseline historical files.
- `state_file`: that project's compact state inside the mailbox, filled from the bundled `REVIEW_STATE.md` template (canonical source: `templates/REVIEW_STATE.md`) with original-source citations. State is data and may be stale. The bridge does not fabricate or silently edit project decisions/state.
- `instructions`: trusted role skill outside project and control workspace. Candidate task/config/hooks/MCP/plugins are never startup authority.
- `control_dir`: dedicated trusted review workspace, outside project and runtime; the CLI starts here, not in the candidate. Keep project configuration/answer keys out of its ancestry.
- `runtime_dir`: existing private directory outside project and control trees. Retains per-attempt schema, answer, raw JSONL, stderr and `attempt.json`, plus `bridge.json`. Restrict OS permissions and keep these files untracked; raw logs can contain source/data. Use one runtime per cursor.
- Config itself lives outside both project and control trees and is supplied by the human. No config discovery from reports. Paths are absolute and existing, without symlink indirection. Filesystem grants still come from the platform; JSON is not a permission grant.

Illustrative commands, run only after the corresponding authorization:

```sh
python3 /trusted/forgeduet/scripts/markdown_bridge.py watch --config /trusted/private/review-bridge.json
# One local scan / at most one authorized dispatch, not a free dry-run:
python3 /trusted/forgeduet/scripts/markdown_bridge.py watch --config /trusted/private/review-bridge.json --once
```

**`watch --once` can invoke the configured real CLI if a completed event exists.** There is no fake-mode switch that makes an arbitrary CLI safe. Step-1 tests supply an explicit local fake executable in a temporary directory; never test against the user's real CLI accidentally.

## Fresh context and completion

Each CLI invocation is a fresh ephemeral session, with a compact envelope: input path/hash/kind, trusted instruction path/hash, project state path/hash and project/mailbox paths. No old chat transcript or bulk historical report is injected. The model reads the current task/newest relevant records and retrieves evidence as needed; it must reconcile stale state and verify actual Git objects. Product tests use fixed isolated snapshots under the trusted control workspace with synthetic data. Candidate active source/index/.build remain untouched. Persist review evidence there and reference absolute paths/hashes in the report. Fresh context is not a quality guarantee or a blind benchmark by itself.

`codex exec` runs with `--ephemeral`, `--json`, `--output-schema`, explicit model/effort, `project_doc_max_bytes=0` and `workspace-write` in the control workspace, with no extra candidate write roots or sandbox bypass. Normal trusted user/system configuration and policy remain applicable. Candidate project config is not selected by cwd. Workspace separation and prompt rules are cooperative workflow controls, not a hostile-code security boundary; use stronger OS isolation for untrusted execution.

The worker returns structured Chinese review Markdown, exact input identity and `action: continue|stop`; it does not directly write shared reports or acknowledge input. The bridge checks successful CLI completion, response structure, unchanged input/state/settings, then publishes a fresh immutable `reviews/YYYY-MM-DD-run-<unique ID>.md` under the existing `.lock/`, with author, timezone, input hash and completion marker. Publication appends `updates.log`; the lock is released before exact-hash acknowledgement. A durable review/gate is required before consumption. Worker judgement still controls substantive correctness; schema validity does not prove good review.

After successful handling, the process waits locally again. `stop` is only for a documented human gate/cancellation or **current-run** full-SHA approval plus explicit builder acceptance and required gates. Approval alone normally returns `continue`. A prior run's closure cannot terminate new work. The state file is not auto-updated. Its single assigned owner must prepare and log the state before the builder publishes a completed delivery. Freeze those bytes until the corresponding review or explicit transport/cancellation gate is durably recorded and any active call has ended. Then update from durable handoffs before the next delivery. A shared writer lock is held only for short writes, never throughout that freeze. See the state template for the sequence; urgent mid-review changes require explicit stop/reconciliation, not silent edits. New workers also inspect the newest actual reports; they cannot treat a stale summary as authoritative.

## Failures, shutdown and restart

Child failure, malformed/mismatched response, changed input/state, timeout, publication/ack failure or interrupted CLI work retains private evidence, pauses the cursor and marks the attempt unresolved. A restart returns `needs_recovery` rather than charging for repeated retries. A hard process kill can leave an orphan CLI; the journal includes the child PID for diagnosis. PID alone does not authorize killing another process. Check that the original child is stopped before retrying. On a requested cursor pause during child work, the bridge terminates its own child process group and preserves evidence; idle pause is observed at the next interval.

Publication/log/ack/journal are separate durable operations, **not one transaction**. A crash can leave a published report without ack or even without its log line. Inspect the deterministic dated report name derived from `run_dir` and original input hash. Reconcile missing logs under the writer lock. If the completed report genuinely handled the exact input, use ordinary exact-hash `handoff.py ack` after inspection; do not rerun that model call just because the journal says failed. A report may still require a human gate.

Only after that inspection:

```sh
python3 /trusted/forgeduet/scripts/markdown_bridge.py recover --config /trusted/private/review-bridge.json --reason 'Human reconciled retained report/log/cursor and verified child ended'
# recover preserves diagnostics and does NOT ack, resume, invoke a model or delete evidence.
python3 /trusted/forgeduet/scripts/handoff.py resume --cursor /project/coordination/.runtime/review.json --reason 'Human authorized resumption after reconciliation'
# Re-arm exactly one bridge when appropriate.
```

`recover` records a human decision, not automatic proof of safety. Never run it from an unattended retry loop. Exit codes: 0 waiting/handled/reconciled, 3 paused, 2 error/attention/needs_recovery, 130 interruption. Inspect JSON as well. Runtime state corrupt/missing while prior work may be active requires manual diagnosis, not recreation. The process is foreground; use an actually authorized local service/supervisor later. No daemon, startup registration or desktop AI heartbeat is installed here. Closing the process/session, sleep and unavailable credentials/network can delay work.

## Usage and outstanding proof

Raw CLI JSONL is retained. Exactly one successful `turn.completed` may report input, cached-input, output and reasoning-output counts; missing, negative, boolean, inconsistent or ambiguous counts are `unknown`, never zero. Cached/reasoning counts overlap the corresponding input/output totals: do not add them again. No quota conversion, dollar estimate or account-limit inference. Unknown usage does not undo a valid transported review, but it blocks a measured token/cost comparison until another trustworthy measurement exists.

Official CLI documentation describes [ephemeral mode, JSONL and structured output](https://learn.chatgpt.com/docs/non-interactive-mode). `--ephemeral` means rollout files are not persisted; this step has **not** proved desktop sidebar behavior, actual CLI usage fields, authentication, sandbox grants, model availability or real-provider startup. Those require the separately authorized tiny real smoke test. Fake tests prove transport behavior only. Review-quality and context-cost comparisons are a separate later blind experiment; no historical WristFiles data is used in step 1.


## Stop notifications — FD-BR-001

A bridge that owns the running watcher emits a local transport stop notification on `attention` (settled incomplete file), repeated scan error, `needs_recovery`, CLI failure/timeout, interruption, explicit pause, or a successfully recorded stop. A rejected concurrent launcher does not announce that the actual owner stopped. Normal idle `waiting`, first scan retries and successfully re-armed `handled` work do not notify. A one-shot successful diagnostic is not an unexpected failure.

Primary channel: publish an immutable completed `reviews/YYYY-MM-DD-bridge-stopped-<notice-ID>.md` under the same writer lock and append `updates.log`. The body explicitly says **transport notice, not a review**, with `record_type: transport_notice`, `event: bridge_stopped`, `review_verdict: null`, reason, input references/hashes, run/receipt paths and recovery guidance. The notice neither acknowledges the source delivery nor `ack-warning`s an incomplete input, and it never resumes a paused cursor or invokes a model. A substantive review can separately have acknowledged its input before returning stop; the notice does not undo that acknowledgement.

The builder monitors `reviews/` and can detect this file through its usual local watcher. It must classify the record as a transport gate, preserve product state, inspect retained evidence and notify the human when needed. Do not treat it as approval, a product defect report, a new coding task or bilateral closure. After durable handling, the builder may acknowledge **only the notice's own path/hash** on its build cursor. Never use it to consume the original review-side delivery or to auto-retry a paid call/change models. The bridge does not prove the peer watcher is armed.

Secondary channel: when enabled, attempt a local macOS notification via fixed `/usr/bin/osascript` with literal argv and a five-second notification-process timeout. This is OS code, not a model call. A successful return only means submitted: notification permissions, Focus mode and session conditions may suppress display. Tests stub this OS channel; no real banner is claimed. A blocked shared writer lock or missing mailbox does not prevent this fallback; never break the other writer's lock. If initial configuration cannot be validated, only a best-effort generic desktop alert and stderr are possible, because no peer root is yet trusted.

The private `runtime_dir/stop-notice.json` receipt records both channels' results and any errors; stderr reports its path. Same reason/input identity is deduplicated across restarts (volatile scan age is excluded). A failed peer publication can be explicitly retried later without re-submitting a prior desktop alert. If publication succeeded but its log/receipt write failed, reconcile the retained exact notice under the writer lock rather than overwrite it. Notice delivery failures do not replace the original CLI/cursor error. Even if cursor pause/cleanup itself fails, retain the first error in the attempt journal where possible.

No notification generation calls a model. **If Claude's watcher wakes Claude to read the notice, that handling can consume Claude tokens.** This is an exceptional actionable event, not idle polling. If both peer writes and OS alerts fail, delivery cannot be guaranteed: the retained receipt/stderr is the only remaining channel. Process hard-kill, power loss or sleep can prevent any cleanup/notification from executing; a separately authorized service supervisor would be needed for stronger liveness guarantees. This candidate does not install one or claim unattended deployment is verified.

## Second-stage real smoke gate — still not authorized

The later separately authorized tiny real Codex call must execute at least one actual test command inside a fixed synthetic snapshot, not merely produce review prose. Prefer a minimal local Swift package for a Swift project, with scratch/build/cache paths contained in the control workspace and no dependency downloads. Retain command, exit status, stdout/stderr, sandbox permission/network limitations and JSONL usage. A denied or unavailable test is a failed/limited gate, never a passed test; do not bypass the sandbox or touch devices to make it pass. Confirm any required extra paths/network permissions with the human before use. Successful synthetic Swift execution would not by itself prove the full WristFiles toolchain, simulators or Release build will work. Do not start a historical quality benchmark until actual testing ability and trustworthy usage measurement are established.


## Candidate pre-work quota wait

See [QUOTA_RESUME.md](QUOTA_RESUME.md). Default-on continuation is restricted to typed quota failure before any item/tool output; partial work, unknown reset or changed state stays gated. Historical v0.2 evidence does not validate this new path.
