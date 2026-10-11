# Review: run / round

- Author (role / model / unique session); created timestamp with timezone:
- Reviewed full SHA; worktree or snapshot mode, archive SHA-256 and verification:
- Requested review provider/model/strength; observed values or unknown; verification level/source:
- Report language; active rules revision/hash:
- Rules and delivery paths:
- Conclusion: changes requested / approved / needs human:

## Findings

| ID | Priority | Trigger and impact | Source file / line | Reproduction / regression artifact | Suggested correction |
| --- | --- | --- | --- | --- | --- |

Each finding needs code evidence or a reproducible observation. Separate demonstrated defects from hypotheses. Match severity to actual impact. A disagreement about a valid test belongs in the issue record, not a silently changed assertion.

## Independent verification

| Check | Exact source SHA / environment | Observed result | Evidence path + hash |
| --- | --- | --- | --- |

- Claims checked against source:
- Negative control results or limitations:
- Unexamined areas and missing human/device checks:
- P3 deferrals under the recorded policy:
- Required gates met / unmet:
- Budget usage source and known/unknown usage:

Approval covers this exact SHA and named gates. A limited successful scenario does not establish every edge case.

- Monitor: deliveries/ mechanism, actual ID/PID, interval, cursor; armed/verified or explicit limitation:

Publish atomically under the shared `.lock/`, append `updates.log`, then verify/re-arm monitoring for repair or same-SHA acceptance. Append the final completion marker only when finished.
