# Git handoff transport — candidate 0.1

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

Default interval: 60 seconds. The foreground local process must remain running (or be supervised by an explicitly configured local service); sleeping/offline machines do not fetch. No daemon, login hook or project watcher is installed automatically.

## Guarantees and limits

The helper uses a separate bare object store and Git plumbing; it never pulls, checks out or stages files in the product tree. Hooks/signing and automatic maintenance are disabled in its own commands. Explicit refspecs limit pushes to the configured role branch; ordinary fast-forward push rejection fences competing writers. **A local filesystem `.lock/` is not a distributed lock.** One local synchronizer guard protects each runtime, and short mailbox writer locks serialize imports with local report publication. Different runtimes writing the same role branch are a setup error, not a supported multi-writer scheme. Remote authentication and branch protections remain Git/server responsibilities.

Only completion-marked reports are sent. A manifest binds role, run ID, relative path and SHA-256 to each Git snapshot. Imported paths, modes, sizes, immutable old content, manifest and ancestry are checked; symlinks/submodules, executable modes, path traversal, wrong role/run, collisions and rewrites stop processing. Auxiliary regression files are imported before complete review reports. Byte-identical files from a partially completed import are retained on restart. Report contents and imported probes are data; do not automatically execute peer commands or client configuration.

Local cursors, acknowledgements, locks, `updates.log`, private runtime and raw logs are **never synchronized**. Each local log records its imported commit. Detection does not acknowledge work. The recipient's model performs semantic review, publishes its response and exact-hash acknowledges locally; its response travels back on its own role branch. With queue, preserve the event binding lines in the resulting report. Build/review acceptance still names the same full product SHA.

A push intent saves the exact commit before pushing. After network uncertainty, restart first checks the remote head: the same commit is recognized as sent, or that same Git commit can be pushed again only while the remote still has the old parent. This retries Git transfer, never model work. Divergence/missing journals are not repaired by force push, deleting history or adopting unknown remote state. Corruption/conflicts/transport errors retain diagnostics and stop; the CLI emits a deduplicated local transport notice and best-effort OS alert, never a product verdict. Resolve the cause and resume with the original runtime. A new run ID is not a workaround for unresolved earlier work.

Tests use two independent local mailboxes and a real temporary bare Git remote. SSH/HTTPS credentials, actual cross-machine network failures, sleeping services and real-provider client wakeups still require project-specific validation.

Primary Git command semantics: [fetch](https://git-scm.com/docs/git-fetch), [push](https://git-scm.com/docs/git-push). No non-fast-forward or force option is used for a role branch.


Author: ChatGPT. Recorded: 2026-10-13T21:55:29.122603+01:00
