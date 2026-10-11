# Roadmap and initial limits

No feature below is a promise of automatic implementation. Add future changes through an authorized task and normal paired review.

| Item | Current behavior | Possible follow-up |
| --- | --- | --- |
| Real-provider adapters | Included examples pass fake CLI plumbing checks; no real/paid invocation tested | Authorized smoke tests, version-specific metadata/usage parsing and scoped permission integration |
| Windows | Not supported; local Unix file locks required | Separate lock/process backend and real Windows tests |
| Network filesystems | Not supported | Define and test filesystem durability/locking semantics before enabling |
| Account/project-wide budgets | Per-run counters and between-job checks only | Verified aggregation and provider-side hard-cap integration where available |
| Long runs | State and immutable handoffs retained for diagnosis; no auto-GC | Explicit archival/export after completion, preserving report references and private evidence boundaries |
| Model identity | Verified/self-reported/unavailable levels retained; unknown observations are not fabricated | Client-specific metadata verification; never claim remote attestation from a prompt |
| Semantic progress | Stable blocking-issue transitions plus human review | Better progress summaries only if real usage demonstrates need |
| Behavior validation of skills | WristFiles exposed missing mandatory two-way monitoring; v0.3.1 now has independent source review and a reviewer-reported 95/95 pass, including completion notices and scan retries | Exercise an authorized actual full client-to-client loop; helper-process tests and source approval do not prove client wakeup |
| Native-client lifecycle | Instructions require real monitor IDs, 60-second checks, re-arming, stop/resume and an explicit prepare-only boundary | Client-specific actual wakeup/restart smoke tests; no claim of automatic recovery after app closure or computer sleep |
| Rules adoption during pending repair (P3, accepted policy) | New rules invalidate pending feedback/approval and return the current candidate to review; this can add a round before build resumes | Keep this conservative routing for v0.2.1; optimize only if real use justifies it, preserving original inputs and new-rule review |

Claude’s v0.2 review found two P2s: human redispatch lost original inputs and the example reviewer could auto-load candidate client configuration. Its subsequent v0.2.1 review independently confirmed the original-input repair and checked the example Claude isolation parameters against documentation; it found no new P1/P2 and approved the relay, snapshot tooling and reviewed documentation within that scope. **Real-client isolation is still unverified.** Local tests and this bounded review are not a guarantee that no defects remain.

The remaining v0.2.1 P3s about local-commit permissions, explicit approved build conventions, and workspace/report ownership have documentation fixes in the [follow-up record](deliveries/2026-10-11-v021-review-followup.md). Runtime code is unchanged; the extra review round above is an explicit deferral rather than an unimplemented blocker.

Optional snapshot follow-up: include the raw commit object and reconstruct the Git tree so an expected commit ID can directly verify the exported source without Git. Keep the current independently supplied ZIP SHA-256 check until a separately tested/reviewed format supports this. Do not replace it with trusting the ZIP comment or manifest.
