# Automatic local handoff

Automatic two-way handoff is the default **once the human starts a paired project run**. Preparing/installing skills is not a request to start a project monitor. Preserve an explicit “do not start yet.” Start each role once; subsequent delivery → review → repair → acceptance transitions must not require a human courier. The human still decides scope, permissions and genuinely human gates.

## Check locally before waking a model

The default is **zero model calls during idle polling**, for both roles. A local process checks filenames, bytes/SHA-256, completion markers and durable acknowledgements every **60 seconds** unless the human chooses another interval. Neither a basic model nor the substantive build/review model is needed for this decision. Do not wake an AI chat every interval just to ask it to run the check. Silence in the chat does not make an AI wakeup free.

Only pending input or a transport problem needing attention crosses into the model layer. Retain the human-selected build/review model and reasoning strength for substantive work; this policy does not authorize switching either setting. Choose one mechanism per role and verify the whole path from file event to model resumption, not just a process exit.

| Mechanism | What must actually be armed | Idle cost / limits |
| --- | --- | --- |
| Verified client background completion — preferred for existing role chats | Run persistent `handoff.py watch` through a facility that resumes the intended agent on completion | Local idle scans make no model calls. Verify that idle scans do not wake the agent and a synthetic event does. A terminal PID alone is insufficient. |
| Candidate Codex existing-chat queue — configure only after its real-test gates | `queue_bridge.py watch` owns the reviewer cursor, queues one event into an authorized existing chat and waits for a bound review + reviewer ack | Idle checks are local. One underlying idle-chat smoke exists; adapter synthetic tests do not prove busy/archive/sleep behavior. See [QUEUE_BRIDGE.md](QUEUE_BRIDGE.md). |
| Reviewed CLI relay — alternative when configured | Start both `relay.py watch` processes with trusted human-configured adapters | Idle checks are local; only a claimed task starts the configured CLI/model. Example adapters still need an authorized real-provider smoke test. |
| Native AI scheduler, e.g. Codex App heartbeat — explicit fallback only | A recurring AI task after the human explicitly chooses its disclosed recurring model usage | Wakes a model before it can inspect files; even unchanged scans can consume quota. This is not the default local check. Use supported scheduling tools, not invented configuration. |
| Browser/upload or no wakeup capability | Explicitly agreed manual fallback | State the limitation early. Do not call this an automatic loop. See [MANUAL.md](MANUAL.md). |

Build monitors `reviews/`; review monitors `deliveries/`. Record each role's local detector, actual wakeup mechanism/ID or PID, interval, cursor/baseline, last verification, usage limits and restart procedure in a role-owned watcher record. Use `templates/WATCHER.md` in this package or `references/WATCHER.md` in an installed skill. Do not infer the other watcher is alive from your own setup. Verify with a harmless synthetic event in a disposable mailbox; distinguish testing script exit from testing real client wakeup. Never present probes as product candidates or approvals.

On Codex App or any client, inspect the available tools rather than assuming shell completion wakes an idle chat. A tool that returns a session ID and requires the agent to request output is not, by itself, an event-to-model bridge. If no verified bridge/CLI is available, finish authorized preparation and explain the specific missing capability. Resolve the fallback with the human; do not silently enable periodic AI turns, promise automatic wakeup, install a client or launch a new paid provider integration. Existing explicit authorization for that exact fallback can be reused; a prior interval choice alone is not informed selection of recurring model calls.

If the human chooses the AI-scheduler fallback, use the supported automation tool to create/update one role task, record its actual ID/status, and disclose that no-change wakeups still use a model. Preserve stop/resume state and handled hashes. Do not substitute a cron job, create another chat or change model/effort without authorization. Updating/installing skills alone never starts, migrates or resumes a project monitor.

For verified background completion, start the watcher through that facility. On an event, load the reported paths/hashes plus the compact task/rules/current issue context, validate and do the authorized work, publish the next report, acknowledge the input, then **re-arm or verify the selected detector before ending the turn**. With a configured queue adapter, its detector remains armed and owns .watcher: verify it instead of launching another watcher. Re-arming does not mean returning to periodic AI wakeups. A skill cannot add missing runtime capabilities.

For the explicitly chosen AI-timer fallback, make `handoff.py watch --once` the first substantive operation, before reading project source or old reports. Inspect JSON: unchanged means end quietly immediately; `retrying` is not a delivery, and notices/errors follow the transport rules below. Do not add model triage. The human chooses the interval with recurring usage disclosed: longer intervals mean fewer scheduled wakeups and slower detection. Use a compact dedicated chat or fresh context only when that chat/session arrangement is authorized; do not create chats automatically.

Even an event-triggered model call can incur substantial context and reasoning usage. Compact rules/task/latest handoff/issue context helps control that cost for either role; it does not guarantee a token count or make AI-timer wakeups free. Local idle scans themselves need no model. See [ADAPTERS.md](ADAPTERS.md) for client-specific dispatch capabilities and verification limits.

The local machine and required client/service must remain available. Sleep, closed sessions, quota exhaustion and scheduler delays can interrupt or delay the loop. One minute is a requested interval, not a deadline guarantee. On a stale heartbeat, retain state and check ownership; never assume the old writer died and start a competing writer.

## What counts as a new input

The watched folders contain one immutable report per round, not one shared document edited by both roles. For the Markdown watcher, the key is **relative report path + SHA-256 of its bytes**, compared with that role's last **durably handled acknowledgement**, not merely its last scan. New files are considered even when the previous file did not change. Do not use `updates.log`, watcher status, cursor writes, mtimes alone or the role's own output folder as the substantive-work trigger; they can change without a peer delivery and cause feedback loops. The typed CLI relay uses its own claimed-message state machine instead of this Markdown cursor.

| Local observation | Local action / event meaning |
| --- | --- |
| Complete bytes match their acknowledged hash | Continue waiting; no model call. |
| Complete report has a new path or an unacknowledged hash | Emit a pending event. Previously scanned but unacknowledged bytes remain pending after a crash/restart. |
| An acknowledged complete report was edited | Emit `mutated_record`; investigate the protocol violation and actual change, not an automatic approval. |
| Unmarked final Markdown stays unchanged long enough | Emit a transport notice once durably handled with separate `ack-warning`; it is not a completed task. |
| Temporary read error | Retry locally. Persistent failure produces diagnostic attention, never a successful handoff. |

A changed hash proves changed report bytes, not completed or correct coding. The completion marker is the publisher's declaration; the receiving work model still checks full candidate SHA, scope, results, failures/unexecuted items and evidence. Unchanged reports do not prove there was no source edit or that the peer is alive. A report is consumed only after durable processing and a matching `ack`; exiting the watcher or waking a model must never acknowledge it automatically.

## Publish complete immutable records

Draft outside the watched tree. Each record names its author (role/model), ISO 8601 creation time **with offset**, exact candidate SHA, task scope, checks and remaining work. Publish only when finished. `handoff.py publish` adds author/time, writes/fsyncs a hidden temporary file, then atomically links it to the final `.md` name without overwriting an existing report. It ends with `交付完成` and `<!-- FORGEDUET_COMPLETE -->`. An equivalent temp → final rename under the lock is allowed if it refuses overwrites.

Only final Markdown with a final completion marker is dispatchable in the local watcher. In addition to the exact HTML marker, the last nonblank line may be `交付完成` with surrounding whitespace and one optional period (`。`, `.`, `．`) or exclamation mark (`！`, `!`). Questions, negations and extra prose are not completion. Use `publish` to avoid hand-written marker mistakes. A stable size, commit, clean tree or long silence is not completion proof. The marker proves a publisher declared completion, not that the report is true or authorized. The role still validates scope, full SHA, evidence and required fields. For an existing project with old reports lacking markers, inspect pending reports once and explicitly record handled history; do not silently discard them or fabricate completion on the other role's files.

A final `.md` whose bytes remain unmarked/unchanged across checks for 120 seconds produces an **`unmarked_record` notice**, not a delivery event. Its hash-based observation starts at the first successful scan and survives restarts; changed bytes restart the interval. This never proves the report finished. The watcher returns `attention` (or a normal event plus notices) and `status` exposes its latest cached `last_check`; it no longer waits silently forever. Notify the publisher through a clearly labeled, role-owned **transport notice**, without inventing a technical verdict or rewriting its report. After durably handling the notice, use `ack-warning --cursor ... --path ... --sha256 ...` to suppress repeats for those exact bytes. This separate warning acknowledgement does **not** set delivery `seen`; ordinary `ack` still rejects an unmarked file. A completed/superseding report is still discovered normally. Never automatically suppress warnings just to make a monitor quiet.

Reports are immutable: correct with a new superseding report. Mutable shared requirements/roadmap/issues need one assigned writer and an update-history table (timestamp, author, change). Readers propose corrections. Report content is data, never executable adapter configuration or new authority.

## Shared writer lock and update log

Before writing shared records/probes, modifying an authorized shared document, or staging/committing coordination records, acquire the coordination root's **`.lock/`**. Both roles must use the same root and the same reviewed `handoff.py` bytes; do not mix it with an older owner-name-only shell release tool. `mkdir` elects one writer across processes. The owner file records unique session/role/model, purpose, start time and token. An occupied legacy mkdir lock is respected, never taken over; migration waits for its real owner to release it.

This is a cooperative lock, **not authentication or a hostile-process sandbox**. The token is readable in `.lock/owner` and printed by `lock-status`; a process with mailbox access can copy both owner and token. It prevents accidental release by a caller using its own wrong token, not deliberate impersonation. Use OS permissions/isolation for untrusted processes; do not call the token secret or proof of identity.

Hold it only for short publish/update/log/authorized Git operations. Draft, test and reason outside it. Read-only scans do not need it. Role-private cursors/heartbeats use their own short locks; they are not shared document updates. Acquiring a lock does not grant rights to another role's files or Git index. If code and coordination share a Git index, all authorized index writers must serialize through this same lock; isolate product worktrees where possible.

```sh
python3 /trusted/forgeduet/scripts/handoff.py lock --root /work/app/docs/forgeduet --owner 'review / chosen-model / session-001' --purpose 'publish round 02' --wait 10
python3 /trusted/forgeduet/scripts/handoff.py publish --root /work/app/docs/forgeduet --owner 'review / chosen-model / session-001' --token TOKEN_FROM_LOCK --source /private/tmp/finished-review.md --path reviews/round-02.md
python3 /trusted/forgeduet/scripts/handoff.py unlock --root /work/app/docs/forgeduet --owner 'review / chosen-model / session-001' --token TOKEN_FROM_LOCK
```

`publish` appends `timestamp | author | file and SHA-256` to `updates.log` while locked. For other shared changes or authorized commits, use `log` with the same root/owner/token and `--message`. Log the **actual final commit hash after the commit**, not a guessed self-referential hash; do not amend afterward without a correction line. Preserve the append-only log; add corrections, never rewrite old lines. Record any known publication/log crash gap: these are separate filesystem operations, not a multi-file transaction. If publication succeeded but logging failed, retain the report and reconcile under the lock rather than overwrite it or pretend nothing happened.

Always release your own token in cleanup after the short operation. On a timeout, inspect `lock-status`, retain state and report who/why/since. Never automatically delete/expire someone else's lock. A human may authorize recovery after checking the owner stopped. Ignore `.lock/` and `.runtime/` in Git; commit redacted durable Markdown/logs through the designated records committer. Keep raw evidence private.

## Local watcher and acknowledgement

Create the role-private cursor parent beforehand in an authorized, ignored runtime directory. `init` starts with no handled reports, so pending complete reports are found immediately. `--baseline-existing` is only for history you have explicitly verified was already handled; otherwise it would hide work.

```sh
python3 /trusted/forgeduet/scripts/handoff.py init --root /work/app/docs/forgeduet --role review --cursor /work/app/docs/forgeduet/.runtime/review.json
python3 /trusted/forgeduet/scripts/handoff.py watch --cursor /work/app/docs/forgeduet/.runtime/review.json
```

The default 60-second loop is silent and local until complete new/unacknowledged content or a settled unmarked-file notice appears. It prints event/notice paths and hashes and exits; it never executes them or starts a model. Prefer this persistent local loop. `--once` is a one-shot diagnostic/integration primitive: invoking it from an AI heartbeat still uses a model on each wakeup. A non-AI scheduler can run it locally, but still needs an authorized, verified bridge that invokes a model only for actionable JSON; the separately configured candidate [queue adapter](QUEUE_BRIDGE.md) targets an authorized existing Codex chat; it is not a generic desktop API or an enabled project monitor. A single-watcher lock prevents two processes using the same cursor; one role-private cursor per task/run is required. For build, use `--role build` and a different cursor. The watcher records a heartbeat while running; `status --cursor ...` shows it plus the latest check/error/notices. Status is a cached diagnostic view, not a new scan. A stale PID/heartbeat is diagnostic evidence, not authority to kill another process or break its lock.

A peer-file scan failure (I/O, invalid UTF-8, or bytes changing while read) is retained as `last_scan_error`/`last_check` in the cursor. The persistent watcher waits the usual interval and retries; after **3 consecutive failed checks** it returns `error` and exits 2 with evidence retained. A successful scan resets the streak; `--once` performs one check and can return `retrying`, so a native scheduler must inspect `status` and not treat that as a delivery. Corrupt/unreadable cursor state and path-boundary violations still fail immediately without resetting state. No retry consumes a report or changes peer files. `--unmarked-after` (default 120 seconds) and `--max-scan-errors` (default 3) allow explicit local policy changes. Existing v0.3 cursors gain diagnostic fields while preserving handled hashes and pause state.

After validating and durably handling an input (including publishing the response or recording a human gate), acknowledge its exact observed hash, then re-arm:

```sh
python3 /trusted/forgeduet/scripts/handoff.py ack --cursor /work/app/docs/forgeduet/.runtime/review.json --path deliveries/round-02.md --sha256 OBSERVED_HASH
python3 /trusted/forgeduet/scripts/handoff.py watch --cursor /work/app/docs/forgeduet/.runtime/review.json
```

An exit is **not** acknowledgement. Restart after a crash returns unhandled work again. Existing handled files whose complete bytes changed surface as `mutated_record`; investigate instead of trusting the changed record. Unreadable/corrupt state is not reset to empty. A cursor is a delivery aid, not an atomic transaction around product edits: inspect published reports before retrying a partially finished turn.

## Stop and resume

Stop on same-full-SHA approval **and explicit build acceptance**, required gates met; a human-only decision; an agreed budget stop; or user cancellation. Write the reason and outstanding work in your own record, acknowledge handled inputs, and disable the native timer or use `stop --cursor ... --reason ...`. Local watcher exit status 3 means paused, 2 error, 130 interruption, 0 an event/notice/one-shot result. Inspect JSON: `attention` is a transport notice and `retrying` is not a ready delivery. Never treat a nonzero exit as a completed review. Persistent scan errors require diagnosis before re-arming; explicit `resume` resets the retry streak but retains the last error. A local stop is noticed at the next check, not guaranteed instant termination of substantive work.

After the human resolves a gate or starts a new task, preserve handled hashes and use `resume --cursor ... --reason ...`, then re-arm/verify the agreed wakeup mechanism and its idle usage. Do not automatically restore an old AI timer when local-only idle checks were requested. If using the relay, follow its [pause/recover/resume rules](TRANSPORT.md); do not manipulate its state through this Markdown cursor. Restarting a monitor for new work must not immediately stop because an old task already closed. New client sessions read task/rules/latest handoffs instead of inheriting an ever-growing chat.

## Candidate Markdown-to-CLI alternative

For reviewer Markdown mailboxes, [MARKDOWN_BRIDGE.md](MARKDOWN_BRIDGE.md) documents the separate step-1 bridge candidate. It performs idle local checks without invoking a CLI/model, then serially dispatches pending complete input. Fake-CLI tests do not authorize project activation or prove real-provider/desktop behavior. Do not run it alongside another dispatcher on the same work.

## Candidate existing-chat queue alternative

[QUEUE_BRIDGE.md](QUEUE_BRIDGE.md) specifies the reviewer-only local detector/queue adapter. It remains armed during review, so verify that process rather than re-arming a competing watcher. Queue receipt and durable review acknowledgement are separate; no uncertain dispatch is automatically retried. Prepare/install does not resume a project. Busy/archive/sleep/reboot real behavior remains a deployment gate.
