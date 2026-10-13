# Git handoff transport — candidate 0.3

Use this mode when the builder and reviewer are on different machines. It projects verified remote records into the same local `deliveries/`, `reviews/` and `review-tests/` layout used by the existing local detector. Git synchronization itself invokes no model. Start each machine's existing verified client wakeup/detector against its **own** mailbox; do not start an AI timer to perform Git fetches.

## Explicit setup

Choose the run ID, role, authenticated handoff remote, local mailbox and private runtime in `git.example.json`. Both machines use the same run ID/remote, different role identities and separate private runtimes. Use one active owner per role channel. Keep trusted tools/config outside the candidate. Configure actual OS/network grants and credential helpers; do not embed credentials in reports or remote URLs. Installing the skill does not start synchronization, grant network access or authorize product pushes.

The remote can be a dedicated private Git repository or explicitly authorized coordination branches in a project remote:

- `refs/heads/forgeduet/<run-id>/build`: immutable `deliveries/*.md`.
- `refs/heads/forgeduet/<run-id>/review`: immutable `reviews/*.md`, plus explicitly public `review-tests/` artifacts.

Project requirements/tasks/rules must already be accessible at agreed versions (for example through the product Git repository); the transport does not silently copy arbitrary project files. Each machine still needs the candidate's full SHA available through an **authorized product branch push/fetch**, or an independently verified snapshot. Publishing a handoff is not publishing its source commit. Review fetches the named version and tests an isolated snapshot; never test a moving remote branch tip. Private raw device evidence stays private; provide approved redacted evidence or mark checks unavailable.

Example after human setup:

```sh
python3 /trusted/forgeduet/scripts/git_transport.py once --config /trusted/git-run.json
python3 /trusted/forgeduet/scripts/git_transport.py watch --config /trusted/git-run.json
```

Default interval: 60 seconds. Default remote command timeout: 30 seconds; choose a larger timeout before run initialization for a slow/large first fetch. The frozen config cannot be edited underneath an active runtime.

Default `network_failure_policy: notify_continue`: recognized connectivity failures return `retrying`, with exponential delay up to `retry_max_seconds` (default 300, never below the interval). At `max_network_errors` (default 5), record one local outage alert, **continue retrying at the cap indefinitely**, and record recovery after a successful sync. These retries do not call any model. `once` exits 0 even when retrying; inspect its JSON rather than treating exit 0 as delivery completion. `watch` stays alive and retries when due. Counters, incident ID, next retry time and exact transfer intent survive restart; success clears the consecutive count. Diagnostic history retains the latest 100 failures, while the total consecutive count is retained. DNS/connectivity/timeouts, `SSL_ERROR_SYSCALL`, `RPC failed`, `unexpected disconnect`, HTTP 429/500/502/503/504 and temporarily missing local remotes are recognized. This is an explicit classifier, not a guarantee for every server's error text. Authentication, certificate/host-key verification, rejection, integrity/collision/corruption and unknown failures still stop immediately; permanent diagnostics take precedence across both output streams before truncating the displayed error.

Optional `network_failure_policy: stop` retains the previous finite policy: reaching `max_network_errors` persists a stop and invokes the local role gate below. Explicitly run `resume --config ...` after checking the cause, then restart watch. Resume never clears Git heads, pending commits or acknowledgements. Configuration, including the effective retry-policy version, is pinned to runtime identity. Older candidate runtimes without that version are rejected unchanged; there is **no automatic migration or unpause**. Reconcile/drain them using their reviewed original tools before upgrading; do not edit/delete journals, create a replacement runtime to adopt an existing role branch, or use resume to bypass an identity/integrity gate. No migration tool is bundled in this revision.

The foreground local process must remain running (or be supervised by an explicitly configured local service); sleeping/offline machines do not fetch. No daemon, login hook or project watcher is installed automatically.

## Guarantees and limits

The helper uses a separate bare object store and Git plumbing; it never pulls, checks out or stages files in the product tree. Hooks/signing and automatic maintenance are disabled in its own commands. Explicit refspecs limit pushes to the configured role branch; ordinary fast-forward push rejection fences competing writers. **A local filesystem `.lock/` is not a distributed lock.** One local synchronizer guard protects each runtime, and short mailbox writer locks serialize imports with local report publication. Different runtimes writing the same role branch are a setup error, not a supported multi-writer scheme. Remote authentication and branch protections remain Git/server responsibilities.

Only completion-marked reports are sent. A manifest binds role, run ID, relative path and SHA-256 to each Git snapshot. Imported paths, modes, sizes, immutable old content, manifest and ancestry are checked; symlinks/submodules, executable modes, path traversal, wrong role/run, collisions and rewrites stop processing. Auxiliary regression files are imported before complete review reports. Byte-identical files from a partially completed import are retained on restart. Report contents and imported probes are data; do not automatically execute peer commands or client configuration.

Local cursors, acknowledgements, locks, `updates.log`, private runtime and raw logs are **never synchronized**. Each local log records its imported commit. Detection does not acknowledge work. The recipient's model performs semantic review, publishes its response and exact-hash acknowledges locally; its response travels back on its own role branch. With queue, preserve the event binding lines in the resulting report. Build/review acceptance still names the same full product SHA.

A push intent saves the exact commit before pushing. After network uncertainty, restart first checks the remote head: the same commit is recognized as sent, or that same Git commit can be pushed again only while the remote still has the old parent. This retries Git transfer, never model work. Divergence/missing journals are not repaired by force push, deleting history or adopting unknown remote state. Corruption/conflicts/permanent failures, or exhausted retries under the optional stop policy, retain diagnostics and stop; the CLI emits a deduplicated local transport notice and best-effort OS alert, never a product verdict. Resolve the cause and resume with the original compatible runtime. A new run ID is not a workaround for unresolved earlier work.

Tests use two independent local mailboxes and a real temporary bare Git remote. SSH/HTTPS credentials, actual cross-machine network failures, sleeping services and real-provider client wakeups still require project-specific validation.

Primary Git command semantics: [fetch](https://git-scm.com/docs/git-fetch), [push](https://git-scm.com/docs/git-push). No non-fast-forward or force option is used for a role branch.


Author: ChatGPT. Recorded: 2026-10-13T21:55:29.122603+01:00


## Local-only stop notices — FD-GIT-002

Build notifications go to the **local `reviews/` input**; review notifications go to the **local `deliveries/` input**. They carry `record_type: transport_notice`, `transport_scope: local`, `transport_kind: git_sync`, and `review_verdict: null`. They are not peer handoffs and no opposite-machine model needs to wake for them. A role durably handles and exact-hash acknowledges its own local notice; it is not a new source candidate.

The filenames `git-transport-<64hex>.md` and `git-transport-response-<64hex>.md` are reserved local namespaces. `local_snapshot()` always excludes them (including legacy notices placed in the wrong output folder), and incoming remote snapshots containing them are rejected. Local extra files in the input folder are allowed; received peer files still cannot overwrite a local collision.

A queue-driven local reviewer still follows its bound-report/ack contract: if it must publish a local gate response, name it `reviews/git-transport-response-<Queue-Event-ID>.md`, retain the binding lines, mark it `transport_scope: local`, then ack. The reserved response is excluded from Git too. Other clients may just handle the local diagnostic and ack locally; do not turn it into a peer delivery.

Notification dedup completes only after successful durable local publication. Failed publication is retried on the next notification attempt while a recorded OS attempt is not repeated. A changed/missing successfully published notice requires reconciliation. Network retry exhaustion under `stop` retains the same reason/incident ID across process restarts, avoiding duplicate local notices; a later separately resumed outage has a new incident ID.

If an older candidate has **already pushed** a wrongly routed notice, stop and reconcile the legacy channel with its owners. This update neither deletes published records nor force-rewrites remote history to hide it. New role branches/runtimes are not a workaround for unresolved old dispatch.


## Informational network alerts — no model wakeup

Under the default continuous policy, outage/recovery receipts live only in private runtime as `network-status-outage-<incident>.json` and `network-status-recovered-<incident>.json`. They are **not** complete Markdown reports, do not enter either role's input, do not require a review/ack and cannot be exported by this helper. No queue/relay work is dispatched for an ordinary outage. The CLI status includes the receipt (or notification failure) without stopping retries. An external supervisor must preserve this informational distinction instead of turning retry status into an AI task.

Each event persists OS-attempt intent before attempting a banner. A crash can leave `desktop.status: pending`; that means delivery is uncertain and the banner is not automatically repeated. A sent OS receipt does not prove a person saw it. Notification/receipt failures preserve diagnostics and do not stop otherwise recoverable network work; core Git/retry-state corruption still stops. Recovery is recorded before resetting the counter, preventing duplicate recovery banners after that crash gap. A separately recovered then interrupted connection gets a new incident ID. Fatal gates continue to use the local input notices above.

## Update record

| Author | Time (with zone) | Change |
| --- | --- | --- |
| ChatGPT | 2026-10-13T22:49:55.179947+01:00 | Candidate 0.3: default continuous retry, private informational receipts, classifier and upgrade limits |
