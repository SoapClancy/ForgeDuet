# Delivery: run / round

- Author (role / model / unique session); created timestamp with timezone:
- Full candidate SHA, base SHA, branch, clean/dirty status:
- Requested build provider/model/strength; observed values or unknown; verification level/source:
- Report language; active rules revision/hash:
- Snapshot archive SHA-256 / manifest and separately forwarded expected values, if used:
- Authorized task and rules paths:
- Changed behavior and user impact:
- Relevant design/architecture decisions:

## Findings addressed

| Issue ID | Fix | Preserved regression | Negative control result or limitation |
| --- | --- | --- | --- |

## Verification

| Check | Exact source SHA / environment | Result | Evidence path + hash |
| --- | --- | --- | --- |

Distinguish passed, failed, not run, and explicitly deferred. Note inherited checks and why source behavior is unchanged. Record interface adaptations without weakening assertions. Do not claim true power-loss testing from a graceful exit or simulated exception.

## Remaining work

- Current-scope P1/P2:
- Agreed P3 / roadmap links:
- Human/device evidence still needed:
- Budget usage source and known/unknown usage:
- Next review focus:
- Monitor: reviews/ mechanism, actual ID/PID, interval, cursor; armed/verified or explicit limitation:

Publish atomically under the shared `.lock/`, append `updates.log`, then verify/re-arm the monitor. The publisher appends the final completion marker only after this report is finished.
