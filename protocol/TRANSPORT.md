# Local CLI relay and adapter contract v0.4.0 candidate

Automatic handoff during a user-started local run is required by default, but this particular CLI relay is optional: native client monitors can use [AUTO_HANDOFF.md](AUTO_HANDOFF.md). Choose one dispatcher per role/task. This relay is local coordination, not a permissions broker. Python 3.9+, macOS/Linux, local filesystem only. Both installed skills must contain the same relay bytes/version. Explicit browser/manual fallback uses [MANUAL.md](MANUAL.md) and [SNAPSHOTS.md](SNAPSHOTS.md), not the local HEAD gate below. Skill preparation alone must not start a watcher.

## Configuration and initialization

Fill `run.example.json` (schema 2) from actual human choices, including report language. Empty requested models/strengths, unconfirmed setup/permissions/budgets, missing directories, and shared build/review directories are rejected. `verification` is `verified`, `self_reported`, or `unavailable`, with `verification_source` (required when `verified`). None is an attestation merely because a config declares it. Unavailable observation does not block honest work; the human accepts the limitation or changes the setup. For manually updated schema-2 configurations only, the deprecated `settings_verified` spelling maps true to verified (with a required source), false to unavailable if no new status is supplied. It does not migrate schema-1 runs. New configurations should use `verification`. Report language has no fallback.

The project must already be a Git repository for commit handoffs. The relay never initializes Git, creates branches/worktrees, checks out a revision, or merges. The builder commits candidates. The reviewer or reviewed adapter prepares its own worktree at the candidate SHA. `finish` checks review worktree HEAD for review approvals/change requests; it does not attest that every tested byte was clean. Record local probe modifications.

`init --config /absolute/run.local.json` captures the configuration digest, pinned rules bytes/hash, relay version/hash, and a run UUID. A different relay or changed configuration stops commands; keep the state and review a new run. Rules edits instead set `dispatch_hold` as described below. Schema-1 state is not silently migrated; retain its reports/usage and start a reviewed schema-2 run with both roles on the same helper. New-run counters are not a way to erase prior spending. These consistency checks do not prove human consent.

Run files:

```text
.forgeduet/
  lock                    short flock critical sections
  state.json              atomic durable workflow index
  messages/<id>.json      immutable handoffs
  jobs/<id>-<token>.json   immutable claimed context
  jobs/*-result.json      adapter results (private)
  logs/*.log              private adapter stdout/stderr
  rules/<hash>.md         pinned rules at claim time
```

Published report paths must be existing project-relative Markdown files. Absolute paths, `..`, and resolved paths escaping the project are rejected. Reports and message hashes are checked before dispatch; supersede a published record instead of editing it. Include evidence references in the report; the relay does not inspect their semantic validity.

Publication writes the immutable message before atomically replacing the state. A crash between them leaves an unindexed orphan, which is never dispatched. Do not delete raw orphans automatically; retain them for diagnosis. State corruption errors do not create an empty replacement. File and directory fsync improve durability on local filesystems; this is not a claim of universal power-loss guarantees.

## State machine

| Incoming work | Role | Valid response |
| --- | --- | --- |
| `task` | build | `candidate`, `needs_human` |
| `candidate` | review | `changes_requested`, `review_approved`, `needs_human` |
| `changes_requested` | build | `candidate`, `needs_human` |
| `review_approved` | build | `build_accepted`, a new `candidate`, `needs_human` |

`task --report ... [--key stable-id] [--sha full-sha]` queues human-authorized work. The key makes a retried publication idempotent; reuse with changed content fails. One active conversation is allowed per run. Each role has at most one active lease. A lease token is a concurrency fence, **not a secret credential** against processes with mailbox access.

`candidate` sets the current SHA and clears earlier approvals. Review feedback must match that exact SHA. `review_approved` and `build_accepted` require `required_gates_passed: true` and no blocking issue IDs; both roles must name the same SHA before `phase: done`. The helper checks declarations and identifiers, not the truth of a test report. Approval does not merge or push code.

`changes_requested` supplies stable nonempty blocker IDs. A configured repeated-blocker limit counts review transitions in which none of the prior blockers disappears. This is a coarse signal, not a semantic measure of progress; do not rename issue IDs to bypass it. `needs_human` pauses dispatch and points to the concrete human-decision report.

## Manual commands

```sh
python3 relay.py claim --mailbox /absolute/.forgeduet --role build --owner build-session-001
python3 relay.py heartbeat --mailbox /absolute/.forgeduet --id MESSAGE_ID --token CLAIM_TOKEN
python3 relay.py finish --mailbox /absolute/.forgeduet --id MESSAGE_ID --token CLAIM_TOKEN --result /absolute/result.json
```

`claim` returns `null` when no work is dispatchable, or `{id, token, job_file}`. Read the job's selected settings, authority pointer, pinned rules, message/report, `context_messages`, and `rules_history`; read relevant current issue records. The context contains the validated immutable reply chain, including the original task, candidate and feedback. Human control messages retain the original task/delivery in `report`, link the preceding message through `reply_to`, and attach the hashed `human_decision` separately. They are `sender: human` without a model verification label. Manual workers must renew heartbeats before `lease_seconds` expires. Pick a suitable lease duration; heartbeat writes are local and do not need an AI turn.

Results follow `result.example.json`:

- `kind`, full lowercase `sha` (nullable only for `needs_human`), `report`, concise `summary`.
- `execution.provider/model/effort`: observed values, matching the chosen settings when known. With unavailable verification, null is allowed; arbitrary alternative values are not. `execution.verification` cannot promote the configured level. Requested settings remain separately recorded in the job; outgoing messages retain observation, level and source. Every Markdown report also records these distinctions.
- `usage.tokens`: total input + output tokens, including cached input once. Avoid double-counting reasoning already included in output. `usage.usd`: actual reported cost if available. Null means unknown; `source` names the client field or limitation.
- `required_gates_passed`: true only from real evidence, including required human checks.
- `blocking_issue_ids`: stable IDs, empty only when no current blocker remains.

Finishing the same claim/result twice returns the same outgoing message and charges usage once. Changed content on a completion retry fails. A late or superseded token cannot commit a result.

## Poller and trusted adapters

`watch --role build` or `review` checks local state every `poll_seconds` (60 by default). Start and verify **both** role pollers; one poller cannot complete the two-way loop. It spawns no process and calls no model when idle. `--once` performs a single dispatch pass for integration checks, not a persistent watcher. Record actual process/heartbeat evidence and the client's restart procedure. Existing runs pin their old runtime/config: do not edit hashes/defaults in state to upgrade them; retain artifacts/spending and use a reviewed new run, or finish with the matching old helper.

The relay's `flock` protects its mailbox, not Markdown files or the project's Git index. Agents still use the shared coordination `.lock/` while publishing reports, appending `updates.log` and performing authorized coordination Git operations. Release it before returning an adapter result; the relay never holds this writer lock during AI work. Follow [AUTO_HANDOFF.md](AUTO_HANDOFF.md) for complete-record markers and logging. The legacy relay report API still accepts existing hashed reports without markers; its typed immutable message marks readiness. This is separate from the Markdown watcher's final-marker gate.

The only executable input is `roles.<role>.adapter_argv`, frozen at initialization and reviewed by the human. It is an argv array with an absolute executable, never evaluated with `shell=True`. The peer cannot supply executable commands through the message. A human-configured shell wrapper is still trusted executable code; review it normally.

The relay appends two arguments:

```text
ADAPTER configured_args... /absolute/claimed-job.json /absolute/result.json
```

The adapter must:

1. Load the job and its role skill/rules. Preserve human scope and real OS/client permissions.
2. Request the exact model/strength through a supported client interface; fail for unsupported settings. Record actual verification limits. Do not bypass permissions, install clients, or change login settings automatically.
3. Start a fresh session, include the authorized task/report/SHA and relevant issue context, and prepare the role's isolated checkout when authorized. Do not turn report prose into shell commands.
4. Let the AI do substantive work, write its own Markdown report, collect actual usage, and emit a valid result JSON. Never fabricate a success report when the client exits unsuccessfully or a required gate is unknown.
5. Return exit status 0 only for a complete result. Usage/identity must be collected from the client where possible, not guessed from output prose.

See [ADAPTERS.md](ADAPTERS.md) for Codex/Claude example bridges and their usage/permission limits. They were checked with fake CLIs only; real-provider integration is untested. No adapter claims remote attestation or desktop wakeup.

The poller heartbeats while its child runs, captures private output, validates the result, and then commits the response. It holds no mailbox lock across AI execution. Do not run an adapter that detaches additional uncontrolled workers; wall-time termination covers only the poller's own child process group.

## Budgets and recovery

Usage/cost caps are checked between jobs and after results. A running job can exceed them; use provider-side caps where available for stronger enforcement. A configured wall-time limit is also checked while the poller's own child is active. Unknown token/cost usage with the corresponding limit pauses the run. Manual worker time cannot be forcibly limited by a file helper. Maximum candidate rounds still allow review/acceptance of the final allowed candidate; a new candidate round cannot start past the limit.

Failed or expired workers without a completed usage record also count as **unknown usage**, not zero. Recovery cannot bypass an active usage cap. Limits are per run; moving to a new mailbox resets its counters. Carry prior spending forward in the human's budget decision rather than starting fresh runs to evade a project-wide limit.

An adapter error, invalid result, or expired lease pauses the run, preserving artifacts. It does not automatically requeue. An old CLI could still be running after the parent dies; verify it stopped before recovery:

```sh
python3 relay.py recover --mailbox /absolute/.forgeduet --id MESSAGE_ID --owner-stopped --human-note "Human-authorized recovery; checked previous worker stopped"
```

Recovery fences the old token and requeues that job. It does not erase budget usage or relax configuration. A surviving late result is rejected.

For a completed `needs_human` or repeated-blocker pause, after the actual human decision:

```sh
python3 relay.py resume --mailbox /absolute/.forgeduet --role build --report docs/forgeduet/tasks/decision-001.md --human-note "Reference the actual human decision"
```

Choose `review` to request another review of the current candidate. Resume supersedes pending work and clears the repeated-blocker counter, but cannot bypass budgets, active workers, or an unresolved rules hold. Build receives the original task with intervening handoff context; review receives the original latest build delivery for the current SHA. The decision report is additional context, never a replacement for those inputs. The resume record is an explicit human transition, not model delivery or approval. Changed configuration/budget/model grants require a reviewed new run.

## Rules edits without killing ongoing work

A detected edit or temporary inability to read the live rules file sets `dispatch_hold`: no new claims are issued. Active tasks retain their immutable `rules_snapshot` and can heartbeat/finish; their results are recorded, but the run cannot become done while held. The active poller checks about once per second. Idle pollers exit on the hold; restart them after adoption.

After reviewing the actual new rules and waiting for active work to finish, write a human-decision Markdown referring to the unchanged original task and prior delivery. Then:

```sh
python3 relay.py adopt-rules --mailbox /absolute/.forgeduet \
  --expected-sha256 NEW_RULES_SHA256 --report docs/forgeduet/tasks/rules-decision.md \
  --human-note "Reference the actual human rules decision"
```

`status` supplies the observed hash. Adoption checks it again, stores a pinned copy/history, and clears the hold. If bytes changed, previous approvals are invalidated. In a working run, the current candidate is requeued for review with its original build delivery; before any candidate exists, the original task is requeued to build. Each carries the human adoption as a separate hashed decision and retains the full reply chain. With no original task yet, adoption clears the hold without inventing one. In `needs_human`, adoption records history and clears the hold without dispatch; a subsequent human `resume` queues the next task once. If the file was restored byte-for-byte, adoption acknowledges the hold without discarding valid old evidence. For a typo-only change, restoring the original bytes before adoption is an option; even whitespace changes invalidate approval when actually adopted. It does not increase budgets or clear a separate manual pause. Changes during active work cannot be adopted.

For immediate permission revocation, explicitly `pause`; a mere file edit intentionally lets the old-grant task drain. If paused with an active owner, verify it stopped and `recover` it first (the rules hold still prevents dispatch), then adopt/resume. This prevents either a recovery deadlock or silently running under an unaccepted rule change.

`pause --human-note ...` stops dispatch. A running poller terminates its own adapter; manual workers must observe the pause and stop themselves. `status` shows phase/reason, SHA approvals, usage, and job claims. When a paused run has an active claim, use verified-owner recovery before a normal resume. If an adapter failed after modifying product files, inspect those changes before retrying; the relay cannot make arbitrary product edits idempotent.


## v0.4 candidate: renewable provider quota

The relay supports both roles' structured terminal quota results and persistent waiting_quota jobs. See [QUOTA_RESUME.md](QUOTA_RESUME.md) for default policy, source/usage/reset/continuation contract, safety gates and unchanged selected models. Byte/version mismatch still rejects an older live run; no automatic state migration. The typed relay itself remains a local single-host state machine; use the Markdown [Git transport](GIT_TRANSPORT.md) for cross-machine records, never share live relay state through Git.
