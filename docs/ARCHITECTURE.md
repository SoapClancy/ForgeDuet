# ForgeDuet v0.3.0 architecture

The two skills define role decisions; the relay carries typed work and records workflow state. Neither substitutes for human authority or independent evidence.

## Local transport

One mailbox has one frozen configuration, one run ID, and one conversation. The human task goes to build, a candidate to review, feedback to build, and explicit same-SHA approvals close the loop. Separate mailboxes support separate tasks; budgets are per mailbox, not an account-wide spending monitor.

`state.json` indexes jobs, claim tokens, usage, round counts, and approvals. Immutable messages point to Markdown reports with SHA-256 hashes. Short `flock` critical sections protect state changes; each replacement writes and fsyncs a temporary file, replaces the destination, and fsyncs the directory. Publication writes the message before the state, so interrupted publication cannot produce an indexed job with no payload. Unindexed orphans remain evidence and are never dispatch sources.

One active lease per role prevents accidental duplicate work. A new lease uses a new token; old completions are fenced. A stopped/expired job requires verified-owner recovery, rather than assuming the prior process died. Completion records deduplicate finish retries and usage accounting. The implementation is not an exactly-once transaction around arbitrary product edits; adapters and builders must inspect partial work before retrying.

## Execution boundary

The optional poller invokes only argv from the frozen human-configured adapter. It appends two local JSON paths, heartbeats without calling a model, and validates the typed result. No lock is held while an adapter runs. A peer can supply report content, not a new executable. The adapter is trusted local code and must enforce actual model selection and normal client permissions. File access controls and sandbox grants remain the platform's job.

Automatic two-way Markdown handoff is the default for active local paired runs, without requiring relay configuration. Native client scheduling or verified background completion bridges the file event to the agent. `handoff.py` supplies cooperative `.lock/` ownership, atomic immutable publication, append-only update logging and role-private durable polling/acknowledgement at 60 seconds. It never launches a model. A wakeup is not an acknowledgement; unhandled events survive restarts. The mailbox relay is an alternative dispatcher. Manual/browser handoff is an explicit fallback. Preparing/installing skills does not start a project.

Optional Codex/Claude example adapters are included but real-provider integration is untested. Fake CLI tests exercise flag/output plumbing only; they do not establish authentication, real permission handling, or remote model identity. Native AI timer wakeups can consume model usage; local idle polling does not. Neither cooperative lock is a security boundary. Short shared-write locks and Git serialization supplement the mailbox's internal flock; no shared lock spans AI execution. Publication and update-log append are separate operations, so a crash gap is retained and reconciled rather than claimed transactional.

Each run pins the relay byte hash/version and rules content. Changes to live rules hold new dispatch while existing work uses its pinned copy. Human adoption after work drains changes the rules revision and invalidates prior approvals. Explicit pause remains the immediate-stop action. Schema-1 state is retained rather than silently migrated. Human redispatch preserves original inputs, the immutable reply chain, and hashed separate decisions without impersonating a model. Adoption while separately paused records history without dispatch; resume issues one task. Claimed context validates original reports and adoption records.

## Packaging and traceability

Canonical protocol, templates, license, and relay are copied into each installable skill by `sync_bundle.py`. No symlinks or imports outside a skill folder are needed. A check detects drift. The public root README is packaging documentation; role instructions remain in exactly two `SKILL.md` files.

Project records are split by writer and round. Review evidence names the exact source SHA; raw private evidence stays outside Git with redacted summaries and archive references. The skills require risk-matched validation, unchanged regression assertions, and honest claims. Machine declaration checks do not prove reports are true or that two roles used different reasoning.

Example CLI isolation: Claude safe mode plus user-only settings and empty strict MCP configuration; Codex review launches from a trusted external control directory with project-document loading disabled. Review instructions come from a trusted external installed copy. These are documented/fake-client-tested boundaries, not demonstrated real-client enforcement.
