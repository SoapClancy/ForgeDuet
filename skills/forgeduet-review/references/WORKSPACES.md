# Workspace and record ownership

Use this local layout when both roles have filesystem access. It separates source from current coordination records without requiring a new repository or a custom scheduler. Paths are examples, not permission grants or instructions to create/move the user's checkouts.

## Recommended: three linked checkouts

```text
/work/myapp/                         project_root: primary Git checkout
  docs/forgeduet/PROJECT_RULES.md    current rules
  docs/forgeduet/tasks/             human-authorized tasks
  docs/forgeduet/deliveries/        build-authored reports
  docs/forgeduet/reviews/           review-authored reports
  docs/forgeduet/review-tests/      original review regressions
  docs/devlog/                     build-authored round records
  .forgeduet/                      ignored mailbox / private transport output
/work/myapp-build/                   build.workdir: short-lived feature branch
/work/myapp-review/                  review.workdir: detached candidate SHA
/trusted/forgeduet-build/            installed build skill
/trusted/forgeduet-review/           installed review skill
/trusted/review-control/             optional Codex review startup directory
```

The three checkouts are linked worktrees of the same repository, so `project_root` can resolve candidate commits created in the build worktree. A plain records folder with no Git object access does not meet the local relay's commit check. Choose branches with the human; do not rename existing branches or move existing files merely to match this example. Only update the review worktree between jobs, after its prior worker has stopped, within the recorded authorization.

Map these paths to `project_root`, `roles.build.workdir`, `roles.review.workdir`, `rules_file`, and `mailbox` in the run configuration. Report paths returned to the relay are relative to `project_root`; for example `docs/forgeduet/reviews/round-01.md` means the file under `/work/myapp/`, not a copy under `/work/myapp-review/`. Both roles read current tasks/reports there. During a dispatched job the saved `rules_snapshot` is authoritative for that job, even if the live rules file has changed.

The reviewer writes/tests only in its own authorized worktree, scratch area, and shared report/probe paths. Keep the worktree at the reported commit, and disclose any test-only modifications. It does not alter build source or the build checkout's Git index. Linked worktrees share Git metadata: record required access to the common Git directory separately. Worktrees and permission lists are not an OS security boundary. The trusted skill and optional control directory stay outside both the coordination checkout and candidate; the Codex control directory is explicitly disposable/writable.

## Who writes and commits records

| Location | Author / writer |
| --- | --- |
| Build worktree product code and adopted tests | Build role |
| Coordination deliveries and devlog | Build role |
| Coordination reviews and original regression artifacts | Review role |
| Shared requirements, architecture, roadmap | One assigned writer; the other proposes changes |
| Coordination Git staging/commits | One designated records committer, within standing authorization |
| Mailbox | Relay helpers; do not hand-edit state |

Commit durable Markdown records and small synthetic regressions. The human can be the records committer, or authorize one role to do it after the record is published and immutable. Record the choice in project rules. All shared record writes and authorized coordination Git staging/commits take the same coordination-root `.lock/`, append `updates.log`, and release promptly; never hold it during tests or AI work. If product and records share an index, its authorized writers must use that same lock for index operations too. A report author does not gain Git rights from lock ownership. See [AUTO_HANDOFF.md](AUTO_HANDOFF.md). Copy reviewer regressions into the build worktree for adoption, preserving their assertions and original provenance.

Add `.lock/` and `.runtime/` to the coordination directory's ignore rules. Each role owns a private runtime cursor and a separate watcher status record; readers can inspect status without writing it. Reports/logs use author and timezone timestamps; mutable shared rules/tasks/issues retain update-history tables. Do not rewrite immutable reports or old log entries.

A delivery names the product candidate's full SHA. A later records-only commit preserves that evidence; it does not turn the earlier test or approval into a pass for the newer commit. Keep candidate identity and records-commit identity distinct. Final merges, pushes and releases follow existing authorization and the applicable validation gates. Keep private raw logs/screenshots/ZIPs ignored and retain their hashes plus accessible evidence locations in the committed summary.

## If `project_root` is also the build checkout

This is supported, but the reviewer still needs its own worktree or snapshot. Explicitly grant review-owned subdirectories such as `docs/forgeduet/reviews/` and `docs/forgeduet/review-tests/` in the shared root. That narrow report exception does not authorize reviewer edits to product files, staging, commits, branch operations or client configuration there. Build stages its intended paths explicitly so it does not accidentally include unfinished review artifacts. Apply real client/OS grants in addition to writing down the boundary.

Browser/snapshot handoff does not require these three live directories. Use [SNAPSHOTS.md](SNAPSHOTS.md) and disclose available verification tools.

## Project conventions with isolated clients

For the builder, put concise human-approved conventions in the pinned rules, or record the approved `CLAUDE.md` / `AGENTS.md` paths and baseline revision/hash there. The builder reads that baseline explicitly as scoped guidance: test framework, style, directory conventions. If the file has changed, use the pinned excerpt/baseline or the normal rules-adoption process; do not silently adopt new authority. This does not enable its hooks, plugins or MCP, grant extra commands, or override human instructions.

The reviewer reads candidate convention/configuration changes as source evidence, using its trusted installed skill and human rules as authority. The examples keep Claude safe mode for both roles; explicit convention reading supplies the missing project context without restoring automatic configuration execution.
