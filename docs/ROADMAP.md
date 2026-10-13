# Roadmap and initial limits

No feature below is a promise of automatic implementation. Add future changes through an authorized task and normal paired review.

Current candidate workflow instructions and relay runtime: **v0.4.0**. This feature branch adds Git handoff and structured quota continuation; old byte-pinned runs are not migrated.

| Item | Current behavior | Possible follow-up |
| --- | --- | --- |
| Real-provider adapters | Included examples pass fake CLI plumbing checks; no real/paid invocation tested | Authorized smoke tests, version-specific metadata/usage parsing and scoped permission integration |
| Windows | Not supported; local Unix file locks required | Separate lock/process backend and real Windows tests |
| Network filesystems | Not supported | Define and test filesystem durability/locking semantics before enabling |
| Account/project-wide budgets | Per-run counters and between-job checks only | Verified aggregation and provider-side hard-cap integration where available |
| Long runs | State and immutable handoffs retained for diagnosis; no auto-GC | Explicit archival/export after completion, preserving report references and private evidence boundaries |
| Model identity | Verified/self-reported/unavailable levels retained; unknown observations are not fabricated | Client-specific metadata verification; never claim remote attestation from a prompt |
| Semantic progress | Stable blocking-issue transitions plus human review | Better progress summaries only if real usage demonstrates need |
| Behavior validation of skills | v0.3.2 independently reviewed by Claude at `d2321e1`; reviewer reported 95/95 and no P1/P2. Follow-up documentation has local structural checks, not a new independent approval | Exercise an authorized actual full client-to-client loop; helper/source tests do not prove client wakeup |
| Native-client lifecycle | Local checks precede model invocation. Claude reported actual background-completion wakeup in a disposable mailbox, scoped to that client/session. Codex desktop wakeup is unverified; CLI/App Server routes and timer limits are documented | Authorized real Codex idle/event/restart and isolation smoke tests. A bundled CLI was found, but help/version and a missing default daemon socket do not prove an operational loop. Preserve prepare-only/paused state |
| Rules adoption during pending repair (P3, accepted policy) | New rules invalidate pending feedback/approval and return the current candidate to review; this can add a round before build resumes | Keep this conservative routing for v0.2.1; optimize only if real use justifies it, preserving original inputs and new-rule review |

Claude’s v0.2 review found two P2s: human redispatch lost original inputs and the example reviewer could auto-load candidate client configuration. Its subsequent v0.2.1 review independently confirmed the original-input repair and checked the example Claude isolation parameters against documentation; it found no new P1/P2 and approved the relay, snapshot tooling and reviewed documentation within that scope. **Real-client isolation is still unverified.** Local tests and this bounded review are not a guarantee that no defects remain.

The remaining v0.2.1 P3s about local-commit permissions, explicit approved build conventions, and workspace/report ownership have documentation fixes in the [follow-up record](deliveries/2026-10-11-v021-review-followup.md). Runtime code is unchanged; the extra review round above is an explicit deferral rather than an unimplemented blocker.

Optional snapshot follow-up: include the raw commit object and reconstruct the Git tree so an expected commit ID can directly verify the exported source without Git. Keep the current independently supplied ZIP SHA-256 check until a separately tested/reviewed format supports this. Do not replace it with trusting the ZIP comment or manifest.

Queue adapter 0.1 candidate: local detector → existing Codex reviewer chat; fake integration tests only. Underlying idle-chat queue smoke passed, but busy/archive/sleep/reboot and real adapter deployment require separate authorization/validation. Keep exec alternative and installed/project pauses unchanged.


## v0.4 candidate scope

Git synchronization now supports two role-owned remote branches, complete immutable reports, public regressions, manifest/hash/ancestry checks and recoverable transfer intents; private runtime remains local. Provider quota defaults to local wait/same-task continuation for validated terminal/reset receipts in both relay roles, queue and the pre-work exec path. 202 synthetic tests passed; independent review and real SSH/HTTPS/client quota-telemetry trials remain pending. No universal Codex/Claude telemetry observer is shipped; unsupported reset/terminal metadata is a gate. See [Git mode](../protocol/GIT_TRANSPORT.md) and [quota mode](../protocol/QUOTA_RESUME.md).


## Open desktop quota integration (required original goal, not completed)

- **FD-QUOTA-DESKTOP-001 — Codex App/queue:** investigate and implement a trusted observer associating actual terminal quota failure, matching queued message/turn, reliable reset time and partial-work checkpoint; only then validate one safe same-chat continuation. No real observer is bundled yet.
- **FD-QUOTA-DESKTOP-002 — Claude Code desktop:** investigate reliable ended-session/quota/reset telemetry and a verified local reset-to-session-wakeup path; `handoff.py watch` observes reviews, not account limits. No automatic quota continuation currently exists for this mode.

Both are explicit remaining parts of the user's requested desktop goal, not claimed as P3-complete or covered by fake-client tests. Investigations and real-client experiments must preserve project/model/budget/permission authorization and report unsupported client capabilities honestly.


## Git round-3 follow-up (approved in synthetic scope)

The round-2 approved candidate 8096fd2 is accepted only in its recorded synthetic scope. This follow-up changes the default to notify-and-continue through long outages; the explicit stop policy remains optional. Outage/recovery receipts stay private and do not wake either model. Common HTTPS transient signatures were added with fatal authentication/certificate/integrity precedence. Old runtime retry identities are not silently migrated. Real SSH/HTTPS, two-host lifecycle and the desktop quota tasks above remain open; source tests do not close them.


Author: ChatGPT. Recorded: 2026-10-13T23:00:40+01:00

Round-3 closure: Claude approved full candidate 85a655fe73d9370535f14b94986d082b66ec8af7 after reporting 232/232 independent tests, and build accepts the same SHA and archive in [the acceptance record](deliveries/2026-10-13-git-round-03-accepted.md). No runtime/test changes follow that candidate.

**FD-GIT-P3-003 (deferred, nonblocking):** the broad permanent-error substring `corrupt` can conservatively stop synchronization for an unrelated temporary server/proxy error page containing that word. Keep the safe stop; reconsider only with an observed redacted diagnostic and a regression preserving genuine integrity failure precedence. Real GitHub/two-host/lifecycle validation and FD-QUOTA-DESKTOP-001/002 remain open. This closes the reviewed Git synthetic round, not those integration tasks; no push, merge, installation or project activation follows from acceptance.
