# Current review state — project-owned template

Author: <role / session>
Updated: <ISO-8601 timestamp with timezone>
State schema: 1

This is compact **data**, not additional authority. Replace placeholders from original records; use `unknown` when unsupported. Do not insert remembered project facts or benchmark answers. Keep each project's filled copy in its own coordination root, separate from this generic template.

## Freshness and identity

- Project / coordination root: <absolute paths>
- Current task and scope source: <task path, SHA-256, section>
- Product source at last verification: <full commit SHA; not a branch tip>
- Record revision at last verification: <full existing commit or uncommitted file manifest SHA-256>
- Evidence checked at: <timestamp with timezone>
- Supersedes state revision: <digest / record reference>

A record cannot contain its own future commit hash. After committing records, add a separate revision receipt or bind the next state to that existing commit. A stale/mismatched source SHA must be reconciled against delivery, Git objects and original records before a verdict. A branch label is not a freshness guarantee.

## Current handoff

| Kind | Path | Exact SHA-256 | Candidate full SHA | Status / source |
| --- | --- | --- | --- | --- |
| Latest delivery | <path> | <digest> | <SHA> | <completed / incomplete> |
| Latest review | <path> | <digest> | <SHA> | <findings / approval> |
| Builder acceptance | <path or absent> | <digest or unknown> | <SHA or unknown> | <explicit / absent> |

- Open issues: <stable IDs, severity, trigger/impact, original finding path/section>
- Closed issues: <ID, fixing full SHA, independent evidence reference>
- Required gates: <passed / failed / not run, evidence path and hash>
- Remaining limitations: <what is untested; why it can/cannot be deferred>
- Next action / owner: <review, repair, acceptance, human gate or closure>

## Human decisions and permissions — cite every entry

| Decision | Exact source (user/date or immutable record/section/hash) | Scope / still applicable? |
| --- | --- | --- |
| <requirement / deferral / chosen model and strength> | <verified source> | <current scope> |

- Authorized read/write roots and restrictions: <source reference>
- Devices / network / external actions: <source reference; absence is not authorization>
- Detector / dispatcher / cursor: <paths and actual verified state>
- Poll interval: <human choice and source>
- Stop / resume conditions: <current-run bilateral same-SHA closure or explicit gate/cancellation>
- Actual cumulative usage: <verified counts or unknown; no guessed quota/cost>

## Update history

| Timestamp with timezone | Author | Source revision | Change |
| --- | --- | --- | --- |
| <timestamp> | <role/session> | <existing full SHA or manifest> | <summary> |

Assign exactly one state owner. Before the builder publishes a delivery, that owner updates this state under the coordination writer lock from durable original records, logs its hash, then the builder publishes the completed delivery referring to the prepared state path/hash. Freeze this state from delivery publication until the corresponding review or explicit transport/cancellation gate is durably recorded; do not patch it while the reviewer is running. Once the review is published and the active call has ended, the owner may update state from that review before the next delivery. The reviewer writes its own report, not this frozen state. If an urgent state correction is required, explicitly stop/reconcile the active call first; preserve the input and disclose already spent usage. Never hold the writer lock across this waiting period. Preserve original reports and append corrections; never silently rewrite another role's state. New sessions read this summary, current task and newest relevant reports first, then retrieve original evidence when needed. This reduces unnecessary history reading but does not prove lower token cost or unchanged review quality.

For a blind quality benchmark, generate a separate sanitized packet and new neutral session. Exclude this operational state if it contains known bugs, later fixes/reviews or revealing history. A fresh chat alone does not prevent filesystem or project-memory answer leakage.
