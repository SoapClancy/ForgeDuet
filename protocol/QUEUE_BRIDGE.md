# Candidate Markdown → existing Codex chat queue adapter

Status: **queue adapter candidate 0.1; fake-CLI tests and one real synthetic write/ack smoke passed; installed for user-authorized project trials, no project monitor enabled by installation**. The 2026-10-12 write smoke verified one idle disposable Codex App chat running two Python tests, publishing a bound report/log and exact-hash acknowledging within its existing writable workspace, without child permission escalation or parent rescue. See `docs/deliveries/2026-10-12-queue-write-smoke.md`; Claude independently accepted that limited result. This is not evidence of semantic review quality, arbitrary project write permissions, busy/archived chats, sleep/reboot or unattended production readiness. The canonical implementation is `scripts/queue_bridge.py`, bundled with both role skills. It supports the **reviewer** only. Claude's build watcher uses its separately verified client background-completion facility; no Codex queue support for Claude sessions is implied.

## Mechanism and ownership

One foreground local process calls `handoff.Cursor.check`, comparing peer Markdown path + SHA-256 + completion marker against durable acknowledgements. Idle checks do not invoke a CLI, network or model, basic or advanced. Default example interval is 60 seconds, overridden by the human. Reports/logs/status in the role's own output do not trigger a wakeup. Changed bytes are not completed/correct work; the reviewer still checks the exact source, scope, tests and evidence.

Only a complete pending input invokes the pinned CLI once:

```text
codex queue --thread <exact UUID> --message <literal event envelope>
  --model <human choice> -c model_reasoning_effort="<human choice>"
  --sandbox workspace-write
```

No shell interpolation, remote endpoint, CLI profile, sandbox bypass, provider fallback, new chat, `codex exec` fallback or recurring AI heartbeat is started. The message includes trusted skill path/hash, project/mailbox/cursor, event ID and input path/hash/kind, never the peer's report body or commands. Model/effort flags express the requested values, not independent remote attestation. A queue receipt is not usage telemetry; token/cost totals remain unknown here.

The **existing target chat** must already be explicitly assigned by the human to this project/run, use trusted instructions, and possess the right read/write/test grants. Its existing context/client configuration and permissions still apply; queue flags do not prove stronger isolation or disable already-loaded hooks/MCP/instructions. The adapter cannot grant rights or retrofit a contaminated chat. Prefer one dedicated project review chat. Do not create or retarget a chat automatically. A long chat can cost more on each wake; this adapter makes idle detection model-free, not substantive review free.

The queue CLI needs local access to Codex's state databases. Run the detector in a human-authorized local environment with that access; starting it inside a restricted Codex tool sandbox may fail, as the smoke demonstrated. Never silently escalate, weaken the review sandbox or claim that changing JSON grants OS permissions. The trusted control cwd, config, executable, instructions and private runtime are separate from the candidate. Review tests still use authorized fixed-SHA copies and project-appropriate tools. No particular programming language is required.

## Explicit setup — no deployment by installing skills

Use `queue.example.json` as a placeholder, not runnable project settings. Required fields:

- `thread`: exact lowercase UUID of the already-authorized review chat; no fuzzy title lookup.
- `cli`, `instructions`: existing absolute real files; CLI executable. Pin their bytes. Config and instructions stay outside project/control trees.
- `project_dir`: existing real project root; the existing reviewer cursor's coordination root must be inside it, with `deliveries/` and `reviews/` ready.
- `control_dir`: trusted disposable working directory for the local queue command, outside project/runtime. Its ancestry must not automatically select candidate client configuration.
- `runtime_dir`: initially empty private directory outside project/control. One journal per cursor/target. Keep it across restarts, with logs private/untracked. Missing/corrupt state is not a fresh start.
- `cursor`: existing `handoff.py` review cursor, preserving hashes, warning acknowledgements and pause. Initialize a genuinely new cursor separately; no automatic `baseline-existing`.
- Explicit `owner`, `model`, `effort`, positive finite `interval`, `queue_timeout_seconds`, `ack_timeout_seconds`, boolean `desktop_notifications`. The example's 30-second queue-process and 3600-second handling watchdogs are placeholders to choose before activation, not token/currency limits or guarantees of completion. No budget is guessed/enforced.

The config, skill and CLI bytes remain pinned across restarts. Changing interval/target/policy requires explicit reconciliation and migration of the retained evidence; do not delete a journal or create a fresh runtime to bypass an unresolved dispatch. Retire an old runtime only after checking its queue, report, cursor and child process. New snapshots/tasks do not automatically authorize monitor activation.

Illustrative commands only after the appropriate authorization:

```sh
python3 /trusted/forgeduet/scripts/queue_bridge.py watch --config /trusted/private/review-queue.json
# One local check / at most one queue attempt. NOT a free dry-run:
python3 /trusted/forgeduet/scripts/queue_bridge.py watch --config /trusted/private/review-queue.json --once
```

**`watch --once` may wake a real model**. Synthetic tests use a separately named local fake executable; the adapter has no switch that makes an arbitrary real CLI harmless. It installs no daemon/service/startup task and does not resume a paused project. Explicitly retire any native AI heartbeat, exec bridge, relay or standalone watcher targeting the same work before adoption. The adapter takes the cursor's `.queue` and existing `.watcher` lifetime locks; a second dispatcher fails without pausing or alarming on behalf of the first. Distinct cursors targeting the same work are a configuration error these locks cannot prevent.

## Queue acceptance, processing, acknowledgement

1. Save/fsync dispatch **intent** in private `queue.json` before invoking the CLI. Record run path, hashes, requested thread/model/effort; retain per-dispatch literal message, argv, stdout/stderr and own child PID. The shared writer lock is never held during queue/model work or waiting.
2. Accept only successful exit plus the currently verified CLI receipt `Queued message <UUID> for thread <exact UUID>.`. Persist `submitted` with message ID and wall-clock timestamp. A different output format is an uncertain dispatch, not proof nothing was sent.
3. Wait locally, **serially**. Do not queue a second input while this one is unhandled. Repeated scans/restarts do not resend this path/hash. Changes to a queued report stop for reconciliation; they do not replace already queued bytes. Previously acknowledged reports with changed bytes are labelled `mutated_record` for reviewer investigation.
4. The review chat checks the named event against actual bytes, task/rules and exact source SHA. It performs independent review/tests within standing grants. In its published complete review/gate report, preserve these three separate literal lines from the wake message:

```text
Queue-Event-ID: <event ID>
Input-Path: deliveries/<report>.md
Input-SHA256: <observed SHA-256>
```

5. The chat atomically publishes under the normal coordination `.lock/`, logs the update and releases the lock. **Only then the chat itself** calls trusted `handoff.py ack` for the original path/hash. The adapter never acknowledges a delivery or warning. It corroborates that ack with exactly one complete review containing all three matching lines, stores that report's path/hash, then waits for the next input. These lines establish transport association, not review quality or substantive approval. An unrelated review, duplicate bound reports or an ack without a report stops for reconciliation. The chat must still satisfy the review gates.

Every dispatched input needs its own bound durable response, **including a builder acceptance record**. For acceptance, verify the exact candidate and current-round conclusion, then publish a short closure/gate record with that event's three identity lines before ack; do not rerun unrelated tests or treat acceptance as a new code candidate. A prior approval cannot serve as the response to a different input/event. A normal cursor pause is not evidence that the adapter corroborated the ack: if stop happened before its next check, the journal may still show submitted. Check/reconcile that retained entry before claiming transport closure or starting a new run.

The chat should not start another watcher or queue itself; this process remains armed while it reviews. Approval alone normally keeps waiting for explicit builder acceptance of the same candidate. Current-run bilateral closure, user cancellation or a human-only gate requires the role to record the reason, acknowledge only durably handled input and `handoff.py stop` the cursor. A stopped cursor ends the adapter on the next local check. Old closure is not grounds for stopping a reopened run. Review state must still be updated from source-cited records, before the builder's next delivery; no automatic fabricated memory.

## Failure, notices and recovery

CLI refusal/capacity, unknown receipt, timeout or interruption is **uncertain**, even if exit is nonzero: a message might already be queued. Process death between intent/CLI/receipt leaves `dispatching`; restart refuses automatic retry. `queue.json` retains every attempted path/hash, including handled/reconciled entries; rewinding the cursor cannot resend them. Recovery never erases this dedup ledger. Filesystem atomic replacement and subprocess submission are separate operations, not an exactly-once distributed transaction. This adapter favors **no automatic duplicate dispatch**; ambiguous outcomes may need manual handling.

If no bound review + matching ack arrives within the selected deadline, stop/pause and notify; do not automatically resend, fall back to `exec` or choose a cheaper model. A report already acknowledged by the time of the next check can be corroborated even after elapsed watchdog time. The wall-clock deadline spans sleep/downtime; a backwards clock requires reconciliation. No guarantee of timely checks while asleep/offline. A hung queue subprocess is terminated only as this adapter's own child process group; that does not cancel an already queued/model-running turn. Pause during submission has the same limitation. Hard kill can leave its child behind: verify identity/termination before recovery, never kill an unrelated PID.

Settled unmarked files stop with a transport warning and **no model queue**; a human/role handles the transport record and separate `ack-warning` if warranted, without calling the candidate finished. Temporary scan errors retry locally; the third consecutive error stops. Corrupt or mismatched runtime/config/cursor stops immediately without resetting history.

Stops publish deterministic, deduplicated complete `reviews/queue-transport-<ID>.md` records under the shared writer lock, plus best-effort OS notifications. `record_type: transport_notice`, `review_verdict: null`: these are not product findings, source approvals or completed-review proof. Normal user pause says “监听已暂停”; faults/deadlines say “交接需核对”. A peer lock is preserved; failed file notices retain private diagnostics and try OS fallback. Repeated stops retain the original cause and do not repeat an already attempted desktop notice. OS submission is not proof of display. A peer agent handling the notice may itself consume model tokens; notice generation does not. Inspect stdout/stderr/private receipts when any channel fails. SIGKILL/power loss cannot reliably generate a notice; no external liveness supervisor is supplied.

After explicit human reconciliation of original chat queue, existing reports, input bytes/cursor and own child:

```sh
python3 /trusted/forgeduet/scripts/queue_bridge.py recover --config /trusted/private/review-queue.json --reason 'Human reconciled original queue/report/child and retained evidence'
# Does NOT ack, resume, requeue, delete state or cancel a model turn.
python3 /trusted/forgeduet/scripts/handoff.py resume --cursor /project/handoff/.runtime/review.json --reason 'Human authorized resumption'
```

`recover` marks the unresolved active attempt reconciled, not successfully reviewed. Handle any original input durably and ack it through the ordinary role workflow before continuing. The same attempted path/hash remains barred from automatic resend. If another real attempt is necessary, the human must reconcile it explicitly outside this adapter; it has no unattended retry override. A local restart cannot undo an existing chat message. Startup/config failures attempt only OS notification because a trustworthy mailbox may not be available; stderr remains essential. Exit 0: one-shot waiting/retrying/submitted/awaiting_ack/handled/reconciled; 2: fault/attention/needs_recovery; 3: normal paused; 130: interrupted. Always inspect JSON as well.

## Proof limits and next gate

The fake suite covers idle scans, literal argv/model/thread, one outstanding input, durable intent, restart/hard-kill dedup, deadlines, input mutation, bound report+reviewer ack, warning/error handling, peer locks/notices and pause. It does not run a real model or prove queue-to-App behavior. The earlier CLI smoke only establishes one **idle** test chat on that local CLI version. Busy/archived chats, sleep/reboot and production permissions remain separately authorized real-test gates. The fresh-session [MARKDOWN_BRIDGE.md](MARKDOWN_BRIDGE.md) candidate remains a manually selected alternative, never automatic fallback.

## FD-QA-001 — first real adapter smoke: unattended write permission

The earlier real idle-chat smoke only returned a marker. It did **not** prove that a queued turn can acquire the shared writer lock, publish a review, append updates.log and exact-hash ack the cursor without a human approving a tool request. Successful wakeup is not this gate passing.

After separate human authorization, create one disposable test chat and put a **synthetic** project/mailbox inside the actual workspace returned for that chat. Record the real cwd, sandbox/write roots and approval behavior; placement alone is not proof of permission. Keep detector config/control/private runtime outside the synthetic project. Select the already agreed model/effort explicitly. Supply a short trusted smoke-only instruction file rather than unrelated product history or the full skill reference set. A tiny approved local test command and a transport-only probe report are sufficient; this is not a product review/quality benchmark.

Measure in order: local idle checks cause no queue call; a single completed fake delivery queues exactly once; the queued turn executes the small synthetic test and itself takes the lock, publishes a bound report, logs, releases and acknowledges the exact input; the adapter records handled with that report hash and waits again. Save observed permissions, approval requests (including none), logs, report/hash, cursor/journal ordering and per-turn usage when available. Count bootstrap and queued model turns separately. One expected bootstrap plus one queue turn is **two real model turns**, not a free test. Do not auto-retry on capacity, permission, timeout or uncertain dispatch.

If the model cannot perform any required write without a human click, FD-QA-001 is **not passed**, even if the parent can write the report afterwards. Preserve the blocked result rather than laundering it through parent publication/ack. Do not silently add --add-dir, change -C/cwd, broaden permissions or disable the sandbox. Those are possible separately authorized designs, not verified behaviors or implemented adapter options. Production coordination permissions need their own evidence; a same-workspace synthetic pass alone does not authorize writing the real project. Only after this gate should separately authorized busy/archived/sleep tests follow. No actual sleep/reboot is induced by preparation.

## Expected pause after App / CLI / skill updates

The executable bytes, trusted instructions and config are pinned, not merely their paths. An App update can change the bundled CLI and trigger Trusted settings changed on the next local check; if the file disappears temporarily, an I/O failure can be the first symptom. A restarted process can instead report changed queue identity because the retained journal binds the old bytes. This is an expected transport safeguard, not a new product defect. Installation of updated skill bytes has the same migration concern. The adapter does not auto-trust replacements or resend queued work.

1. Preserve the old runtime, journal, cursor, raw queue output and reports. Confirm the old detector is stopped and identify any original CLI child / queued or running chat turn. Stopping a local process is not cancellation of a queued turn.
2. Reconcile every outstanding attempted input in the original chat and against published reports. A legitimately handled input needs its complete bound report and ordinary exact-hash ack. Do not ack unfinished input just to unblock migration. If any attempt remains unresolved, keep monitoring paused; a new empty runtime must not bypass its no-resend ledger.
3. Inspect the new local CLI version/help and the intended argv, selected model/effort and permissions. Recheck trusted skill compatibility; changes in supported behavior need a separate authorized smoke. These help/hash checks themselves do not call a model. Do not retain an obsolete App binary merely to evade pinning.
4. Once **all old attempted inputs are durably reconciled and handled**, no old child/turn is active, and the human authorizes migration, retain the old ledger as immutable evidence. Prepare a new private runtime/config for the reviewed new identities, using the **same preserved cursor/ack history**, record old/new hashes and evidence paths, then explicitly resume one detector. The code has no automatic pin-migration command. recover with a changed identity is not expected to override the old pins; do not hand-edit queue.json or delete old state. If unfinished/abandoned attempted inputs must carry across, a separately reviewed migration policy/tool is needed first, rather than this all-handled procedure.

Before real use, synchronize the compatible source bundles to the actual role skill installations under authorization and verify hashes/links. The reviewer must verify the queue detector already owning .watcher instead of launching a second watcher. Builder installations also need to recognize transport notices. Updating installed skills does not resume project monitoring. For a disposable smoke, the explicitly configured trusted smoke guide can establish these rules without changing global installed skills; record that distinction honestly.
