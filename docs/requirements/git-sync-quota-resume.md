# Git collaboration and quota continuation — authorized scope

Author: ChatGPT
Recorded: 2026-10-13T22:00:42.986312+01:00

Source: user's 2026-10-13 request in this chat to create another feature branch, support Git collaboration across computers as well as same-host file exchange, and add default token-limit wait/reset/continue when missing.

Decisions: retain the latest b044e2c work as base; use separate role-owned remote handoff branches, immutable completed records and a private bare object store; leave actual product branch push/fetch authority in project setup. Default renewable quota continuation requires trusted structured terminal/reset/checkpoint receipts, preserves exact task/model/settings and survives local restart. Human budget limits, pause, permissions and ambiguous live workers remain gates.

Acceptance: real temporary bare remote/two mailboxes; interruption/uncertain-transfer/hash/role/history/collision checks; both-role quota continuation with no early model attempts and durable no-duplicate intent. Fake clients and synthetic data only in this development step. Real provider/remote and lifecycle trials need separately scoped setup; no automatic project enablement or installed-skill replacement.


Current implementation boundary after round-1 review: Git transport and conditional typed-receipt quota policy are candidate implementations. The user's actual Claude Code desktop build + Codex App/queue review combination does not auto-continue after quota reset. FD-QUOTA-DESKTOP-001/002 remain open implementation/integration work; current fake-adapter tests do not fulfill that desktop goal.
