# 2026-10-08 — initial ForgeDuet package

Implemented two independently installable role skills, shared protocol, setup/project rules and report templates, an MIT license, and a standard-library local mailbox/poller. No Git repository or remote was initialized for this package. No real-provider adapter or paid model call was run.

## Decisions

- Use separate role-owned reports, stable issue IDs, exact-SHA review, and short-lived feature branches. Keep report content separate from authority.
- Explicit model/strength and permission/budget setup is required; no default model or permission bypass.
- Provide manual transport and an adapter contract rather than promise arbitrary desktop wakeup.
- Use local file locking and atomic state replacement. Unknown/expired work pauses, and verified-owner recovery fences old tokens.
- Bundle exact resource copies so installation of a single skill is self-contained.

## Defects found during implementation

| Observation | Correction | Evidence |
| --- | --- | --- |
| macOS `/var` alias vs `/private/var` caused valid task reports to be rejected as outside the project | Resolve both the root and report before containment checks | First 29-test run had 22 errors with this cause; the unchanged tests passed after correction |
| A failed or expired worker could have spent tokens without a completed result; recovery might otherwise treat spending as zero | Mark failed/expired worker usage unknown; refuse recovery under an unresolved usage cap | `test_failed_worker_cannot_retry_under_unknown_token_budget` and expiry/recovery tests |
| Retrying a successfully completed human task should not publish another task | Return the prior deduplication result even after terminal completion | `test_task_retry_after_completion_is_idempotent` |

The last two were found by implementation inspection and verified by added tests; no separate second-model review was performed. The package follows the same principle it teaches: do not describe self-checks as independent review.

## Verification

Final local suite: 34 passing tests, including six-process claim contention, message/state crash gaps, stale token/SHA rejection, report mutation detection, unknown usage and budget pauses, synthetic adapters, two live pollers, and isolated skill copying. Both skill validators and resource synchronization check passed. Actual artifacts and source hash are in `../VALIDATION.md`.

Remaining integration work is explicitly listed in `../ROADMAP.md`. In particular, synthetic workers establish transport behavior, not real-model cooperation quality.
