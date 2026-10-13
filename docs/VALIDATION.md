# Validation

## Current follow-up — 2026-10-12, v0.3.2 independent review

- Author: ChatGPT, ForgeDuet skill maintainer; recorded 2026-10-12T08:22:34+01:00.
- Claude reviewed `d2321e1f983531e4e20ed19d2a97b1f85a35ebee` and reported **95/95 passed, 22.3 seconds**, no P1/P2 and matching installed Claude copies. Its unchanged feedback SHA-256 is `a9f01f2d97146da6954d2f9f57fd0a45c74be4ed7c39ee44414e2e76f017572e`. Accepted within that scope; this documentation follow-up has not had another independent review.
- Its disposable Claude Code probe reported about eight idle scans, then actual background-completion notification, with no automatic acknowledgement. Report-to-detection was 7 seconds, detection-to-wakeup 5 seconds: **12 seconds total**, not within the 10-second scan interval. Some waiting overlapped its active reply. This is reviewer-reported evidence for that client/session, not Codex or sleep/restart proof.
- Workflow instructions are explicitly v0.3.2; relay runtime stays 0.3.0. Timer fallback now specifies first-operation local scanning, immediate quiet exit when unchanged, human-selected cadence and authorized compact context. Setup assigns installed-copy synchronization ownership. No Python, tests, schema or model settings changed.
- Local Codex preflight found the existing bundled executable `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`, version `0.162.0-alpha.17.2`. Help exposes non-interactive exec and App Server controls. The documented daemon version probe failed because its default control socket was absent. No daemon was started or model turn invoked; availability/help is not an integration pass. [Hook lifecycle](https://learn.chatgpt.com/docs/hooks) does not wake idle turns; [App Server](https://learn.chatgpt.com/docs/app-server) and [CLI](https://learn.chatgpt.com/docs/non-interactive-mode) are documented routes with gates explained in [ADAPTERS](../protocol/ADAPTERS.md).
- Checks passed: source bundles; six source/installed skill validators; 164 relative Markdown targets; four installed copies byte-matching source; unchanged runtime hashes below; Git whitespace check. Existing behavior tests were not rerun for documentation alone; creator 95/95 and independent 95/95 remain separately scoped evidence.

The synchronizer was ChatGPT. Human authorization is the user's request to update ForgeDuet's polling instructions and latest continuation; a current-turn system grant covered the repository and all four installed roots. Exact destinations: `/Users/soapclancy/.codex/skills/forgeduet-build`, `/Users/soapclancy/.codex/skills/forgeduet-review`, `/Users/soapclancy/.claude/skills/forgeduet-build`, `/Users/soapclancy/.claude/skills/forgeduet-review`. The previous 28 updates were seven relative files per root: `SKILL.md` and `references/{AUTO_HANDOFF,MANUAL,PROJECT_RULES,PROTOCOL,SETUP,WATCHER}.md`. This follow-up compared 108 package files and wrote 20: per root, `SKILL.md` plus `references/{ADAPTERS,AUTO_HANDOFF,SETUP,WATCHER}.md`. Existing bytes matched the reviewed source before copying; extras were preserved. Exact paths, before/after hashes, author, grant source and synchronization time are retained privately in `evidence/raw/v032/installed-followup.json`.

**Still unverified:** a real Codex provider invocation, permission/config isolation, actual event-to-model dispatch/restart, and a complete two-client loop. Typed relay does not consume the Markdown watcher's reports without a separately reviewed bridge or explicit workflow migration. No WristFiles operation, monitor resume, extra CLI/model session, commit or push occurred. This chat itself still uses model resources; its cumulative token/cost is unavailable. See the [follow-up record](deliveries/2026-10-12-v032-review-followup.md).

## Original validation snapshot — 2026-10-12, v0.3.2 instruction update

- Author: ChatGPT, ForgeDuet skill maintainer; settings not independently attested.
- Recorded: 2026-10-12T07:41:52+01:00.
- Scope: make local checks **before** model invocation the default for both roles. No basic or advanced model is needed for idle hash/completion/ack checks. Periodic AI wakeups are now an explicitly chosen, cost-disclosed fallback, not an equivalent default.
- This changes both SKILL entrypoints, canonical handoff/setup guides, bilingual start instructions and bundled references. It does **not** change Python runtime/tests, cursor schemas, model settings, or restart any project monitor. Runtime behavior was already local; the earlier native-timer choice caused the model to wake before the local check.

| Check | Observed result | Scope |
| --- | --- | --- |
| Full existing package suite | **95/95 passed, 22.296 seconds** | Synthetic temporary mailboxes/workers; no real provider invocation |
| Idle detector/dispatch regressions in that suite | Passed | Persistent Markdown watcher remains waiting until delivery; relay starts no idle worker; two live role pollers dispatch only when work arrives |
| Crash/ack and completion regressions | Passed | Process exit does not consume input; exact-hash acknowledgement survives restart; mutations surface; unmarked notices are separate from deliveries |
| Source bundle equality and both source skill validators | Passed | Instructions/resources synchronized; not actual client-wakeup proof |
| Four installed packages | **108 files compared; 28 instruction/reference files updated; all matched source** | Codex and Claude build/review copies; existing copies matched the pre-edit source, unknown extra files preserved; all four validators passed |
| Relative Markdown targets and whitespace | Passed | Public guides/templates/bundles and Git diff checks |
| WristFiles pause | Read-only verified | Native heartbeat PAUSED; review cursor paused, no watcher, 7 handled reports and 2 handled warnings retained |

The existing tests `test_background_process_is_quiet_then_exits_on_delivery`, `test_idle_watch_does_not_start_worker`, `test_two_live_pollers_wake_on_new_work_and_exit_when_done` and `test_exit_does_not_consume_and_hash_bound_ack_survives_restart` exercise the relevant local behavior. Their fixture workers are not real model calls. No new runtime tests were needed for this instruction-only change; no assertion was weakened. Raw test output is retained privately/ignored at `evidence/raw/v032/full-suite.log`.

Unchanged runtime hashes:

| File | SHA-256 |
| --- | --- |
| `scripts/handoff.py` | `9fe5a0fa7b70bfca8e88b1bb1dda446eaf02b6c01c9e976eb8aa6ebedc675e6c` |
| `scripts/relay.py` | `b519024f736e4eef2dc9b5892b74bdd2066e6ece700e629a36d3c17bad43fd4f` |

**Remaining integration limit at this snapshot:** this update does not establish a zero-idle-model loop in the current Codex desktop chat. Its available shell tool exposes a session to poll; no automatic process-exit-to-chat wakeup was verified. A real client background-completion bridge or reviewed CLI setup still needs an authorized live smoke test. The package does not provide a generic desktop-chat wakeup API; the example real-provider adapters remain untested. A previous Claude-reported background notification is not independent proof for Codex or every client session. Skill installation does not hot-reload another agent's already-read instructions or restart its watcher. Both configured substantive models are preserved; no basic model was added to polling, no CLI installed, no paid provider invoked, and no product code or project coordination file written. Independent review was pending then; its later result is recorded above.

## Historical validation — 2026-10-11, v0.3.1

- Author: ChatGPT, ForgeDuet skill maintainer; user-configured settings, not independently attested.
- Recorded: 2026-10-11T21:00:11+01:00.
- Input: Claude independently reviewed v0.3.1 and reported 95/95 tests passing in 22.3 seconds, matching helper hashes and no new issues. The creating-agent results below and the bounded independent follow-up are separate evidence.

| Check | Observed result | Scope |
| --- | --- | --- |
| Three unchanged regressions against old installed v0.3 helper | All three failed as expected | Punctuation; settled unmarked report; transient read failure |
| Same three against v0.3.1 helper | All three passed | Same fixtures/assertions, disposable copies; no product repository used |
| Full package suite | **95/95 passed, 22.022 seconds** | Previous 84 plus 11 new tests; one older test adapted to the intentional scan-retry policy |
| New transport scenarios | Passed | Warning age reset, hash-bound separate warning ack, status diagnostics, old-cursor compatibility, read interleaving, immediate path-boundary rejection, CLI warning acknowledgement |
| Bundles and both source skill validators | Passed | Canonical resources and skill structure; not client wakeup proof |

The older adapted test still requires corrupt cursor bytes to fail without reset. For a missing peer directory it now expects two `retrying` checks, then `error`, instead of an immediate exception. Its state-retention assertion remains. The new warning acknowledgement never sets delivery `seen`; ordinary delivery acknowledgement still rejects unmarked content. A completed report is subsequently found normally.

Raw logs are private/ignored in `evidence/raw/v031/`: `baseline-v030.log`, `fixed-v031.log`, `full-suite.log`. No provider/CLI model call or real project monitor was started. The previously paused WristFiles monitor was read-only checked and remains PAUSED. Claude's live process/installed copies were not modified or restarted by this change.

| File | SHA-256 |
| --- | --- |
| `scripts/handoff.py` | `9fe5a0fa7b70bfca8e88b1bb1dda446eaf02b6c01c9e976eb8aa6ebedc675e6c` |
| `tests/test_v03_followup.py` | `fb21b417cf7b747b061a59dbc00bfd0565c58772b6a921d42eee0f2823447af8` |
| `scripts/relay.py` (unchanged runtime 0.3.0) | `b519024f736e4eef2dc9b5892b74bdd2066e6ece700e629a36d3c17bad43fd4f` |

Remaining limits from v0.3 still apply. Warning age uses successful hash observations and wall time, not proof of writer completion. It produces a transport notice, not a technical candidate/approval. Local scan failures retry at the configured interval up to three consecutive failures by default; corrupt cursor state/path violations remain fatal. The readable owner token is explicitly not an identity credential. Use the same reviewed helper on both sides; do not mix a token-unaware shell unlocker with it. Updating a script file does not hot-update an already running Python watcher; use the documented owner-controlled stop/re-arm process.

### Independent follow-up and closure

Claude's separate v0.3.1 feedback, forwarded by the human and read from the ignored local feedback file, reports **95/95 passed in 22.3 seconds**, passing bundle synchronization and matching helper hashes. It also exercised punctuation completion, settled-unmarked notices with separate warning acknowledgement and later completion, and read-failure retries/recovery in disposable directories. Its warning-age probe used a 2-second override, not an observation of the default 120-second interval.

At closure the creating agent rechecked the three canonical hashes above and the unchanged original delivery hash. This closing step changes only documentation and the append-only update log; the test suite was not rerun for those documentation changes. The creating agent accepts the independent review within its stated scope. See the [v0.3.1 closing record](deliveries/2026-10-11-v031-acceptance.md).

Six historical WristFiles deliveries require reconciliation against their existing reviews/acceptances when the human next starts that project workflow. No product delivery scan, cursor acknowledgement, or monitor restart was performed for closure. A separately running Claude watcher does not authorize restarting the paused review watcher. Real-provider invocation and a complete real client-to-client wakeup/review loop remain unverified.

## Historical validation — 2026-10-11, v0.3.0

- Author: ChatGPT, ForgeDuet skill maintainer; user-configured model/strength, not independently attested.
- Recorded: 2026-10-11T20:42:53+01:00.
- Scope: repair the missing default two-way automatic handoff, update both source/installed skills, and validate local helper behavior. The creating-agent results are below; Claude subsequently independently reported 84/84 in 22.3 seconds, source/bundle review and no P1/P2, with the follow-ups addressed in v0.3.1 above. Its synthetic client-wakeup check does not establish a full real client-to-client loop.

| Check | Observed result | Scope |
| --- | --- | --- |
| Complete package suite | **84/84 passed, 21.751 seconds** | Previous 69 plus 15 local handoff tests; synthetic fixtures, no provider invocation |
| Shared lock contention | Six real processes, exactly one writer | No-holder/wrong-token actions refused; legacy mkdir locks respected; no automatic stale-lock removal |
| Local background watcher | Stayed alive while idle, then emitted a complete delivery event and exited | Actual Python process behavior; **not** proof a particular client resumes its AI |
| Durable acknowledgements | Unacknowledged work returned after restart; wrong hashes refused | Explicit acknowledgement only; mutation of an acknowledged complete record surfaced |
| Complete publication | Hidden/unmarked drafts ignored; final report immutable and hash logged | Fault before atomic publication left no final file/log; path/symlink escapes refused |
| Two-role synthetic Markdown loop | Delivery → review → acceptance → explicit stop | Real helper functions; synthetic substantive decisions, no claim of actual AI review |
| Both skill validators | Passed | Frontmatter/scaffold checks, not semantic certification |
| Canonical/bundled/installed resources | Passed | Both standalone bundles synchronized; 27 files per installed Codex skill matched source bytes |
| Local Markdown links | No broken relative targets found | Public package and both installed skills, excluding ignored private feedback |

The helper `handoff.py` executes no peer commands and never starts a model. Native AI scheduler wakeups may consume quota; a local process alone is not AI wakeup. Both entrypoints require actual client monitor evidence, re-arming after handoff and explicit fallback when capability is unavailable. Preparation/installation alone must not start a project monitor.

Canonical runtime SHA-256:

| File | SHA-256 |
| --- | --- |
| `scripts/handoff.py` | `a3af77c16d26b739e8eb347f6db06d28f421808b7ac787366fdf033b56e4fc09` |
| `scripts/relay.py` | `b519024f736e4eef2dc9b5892b74bdd2066e6ece700e629a36d3c17bad43fd4f` |

Relay runtime is now 0.3.0, schema remains 2. Existing runs pin their original bytes: preserve them, do not rewrite their runtime hash/config to force an upgrade. Finish with the matching helper or configure a reviewed new run carrying prior spending forward.

Remaining limits: real-provider CLI adapters and their actual client isolation/permissions are still untested; no real client-to-client smoke test was performed for this revision. Script-process exit and fixture adapters are not evidence of GUI wakeup. No Windows/network-filesystem/power-loss test. The cooperative writer lock is not authentication. Publication and log append have a documented crash gap. Skills cannot guarantee persistence through closed clients, quota exhaustion or machine sleep. Local filesystem grants still apply.

Only ForgeDuet source and its two installed Codex skill copies were updated for this skill repair. No product code, devices, real notes, merges or pushes were touched. An existing product monitor was prematurely reopened before the human clarified “skills only”; it was then explicitly paused and remains stopped. This package revision does not start any product watcher merely because it is installed.

## Historical validation — 2026-10-11, v0.2.1

Claude independently reviewed v0.2, ran its 51 tests and withheld approval for two P2s. After the repairs, its separate v0.2.1 review ran **69/69 tests in 22.3 seconds**, confirmed the relay input repair, checked the example Claude isolation parameters against official documentation, and found no new P1/P2. It approved the reviewed relay, snapshot tooling and documentation within those stated limits. It did not test real Claude/Codex invocation or independently check Codex CLI flags. The earlier creating-agent validation and source hashes are retained below.

| Check | Observed result | Scope |
| --- | --- | --- |
| Five regressions added before changing v0.2 production code | 5/5 failed | Four real relay cases (adopt/resume, build/review); one synthetic CLI startup-hook case |
| Full local suite after repairs | **69/69 passed, 21.936 seconds** | Previous 51 unchanged test cases plus 18 new cases |
| Bundle equality and both skill validators | Passed | Current helper/reference bytes and SKILL structure |
| Installed Codex `exec --help` | Listed the relevant CLI flags | Help only, no model invocation or permission/isolation verification |
| Current official Claude/Codex documentation | Reviewed | Startup discovery/isolation and argv design; not a substitute for real client tests |
| Claude's independent v0.2.1 review | 69/69; bundles and recorded hashes matched | Reviewer-reported results in its separate feedback; real-provider calls not tested |

The five baseline tests were derived here from Claude's review, not supplied by Claude as test files. Their assertions were not relaxed after the failing baseline. Four directly exercise production relay state. The fifth deliberately models documented client startup discovery in a fake CLI; it establishes adapter plumbing, **not real Claude hook suppression**.

New checks also cover paused adoption without double dispatch, hashed decision immutability, original-input mutation, adoption before any task exists, repeated adoption context, a complete new review/acceptance, required verified-setting evidence, trusted review SKILL location, external Codex startup, write-root bounds, explicit Claude allow rules, remaining estimated USD budget, and rejecting unauthorized extra models.

All product repositories are disposable temporary fixtures. This turn did not read or export WristFiles, access devices/notes, initialize the ForgeDuet output as Git, install a client/skill, or invoke a paid model. Claude's private source feedback remains unchanged and ignored for publication.

### Documentation-only follow-up after independent approval

The subsequent [follow-up](deliveries/2026-10-11-v021-review-followup.md) adds conditional local-commit permission examples, explicit approved convention reading, workspace/report ownership and a documented P3 deferral for the extra rules-adoption review round. Both skill entrypoints and their bundled references changed; relay, snapshot, adapter and test code did not. This follow-up has not had a separate independent skill-use evaluation.

Validation for this follow-up: both skill validators, bundle equality and local Markdown links were checked; helper hashes, test bytes, existing immutable delivery/devlog records and all private feedback were checked unchanged. The 69-test behavior evidence is carried forward at the exact helper hashes below; the suite was not rerun solely for documentation changes. These checks do not demonstrate real-client permission behavior or validate live worktree setup.

Claude subsequently approved this documentation follow-up in the final review message forwarded by the human on 2026-10-11. It reported another **69/69 pass on the current files**, passing bundle synchronization, unchanged Python bytes and agreement with all four P3 dispositions. This is reviewer-reported evidence; the creating agent did not rerun that suite or obtain a new raw test log in this closing step. This additional source/documentation review is not a live skill-use evaluation or real-client smoke test. The creating agent accepts that bounded approval; see the [closing record](deliveries/2026-10-11-v021-acceptance.md).

### Remaining limits

Neither real Claude startup isolation nor a real Codex review invocation was exercised. Installed Codex help was checked; Claude CLI is unavailable here. Safe-mode/settings behavior, authentication, actual sandbox permissions, hooks/MCP loading and cost limits need an authorized real smoke test. User/managed configuration and inspected test execution are separate trust boundaries; the examples are not a hostile-code container.

Snapshot code is unchanged. Direct commit-object/tree reconstruction is deferred; full commit SHA **and separately supplied ZIP SHA-256** remain required by the current workflow. No SHA-only proof is claimed.

Relay 0.2.1 retains schema 2 but pins different runtime bytes. Do not reuse an older active run with the new runtime or edit its recorded hash to force compatibility. Preserve its artifacts/spending and configure a reviewed new run, or finish it with the matching old runtime.

### Current source SHA-256

| File | SHA-256 |
| --- | --- |
| `scripts/relay.py` | `57c8c33fed62bd978ddeedce027b11b374c6a6550672798a6d4b2406deb4b6f3` |
| `scripts/snapshot.py` | `9863186ae59728f70fb769e9bdb862e36a55dab679b177efcf4f40ab3101e34d` |
| `scripts/adapters/common.py` | `c24983601ca381f2856510f60cb753761e9bc185d92bb8789872558c1674ea84` |
| `scripts/adapters/codex_adapter.py` | `dd4a9cc8dd7378e07394a1c52b0664dbd44c93a38499537b8b62e3f94ff36f3b` |
| `scripts/adapters/claude_adapter.py` | `c4a686266504ee4e791087a40448d6518a4e553d22f67b9a6321a2b6138633ba` |

The following records describe earlier artifacts, not current code or approval status.

## Historical validation — 2026-10-11, v0.2

Environment: macOS, Python 3.9.6, local filesystem. The output folder is still not a Git repository, as the human requested. Temporary Git fixtures are isolated and disposable. No real model/client invocation, authentication change, global installation, or publication was performed.

### Results

| Check | Observed result | Scope |
| --- | --- | --- |
| Three new regression scenarios against unchanged v0.1 | All three reproduced: two failed assertions and one initialization error | Self-reported settings, runtime mismatch, rules edit killing an actual running synthetic adapter |
| `python3 -m unittest discover -s tests -v` after repairs | 51/51 passed, 19.629 seconds | 34 earlier tests plus 17 new tests; one earlier rules-mutation expectation adapted to the intentionally changed policy |
| `python3 scripts/sync_bundle.py --check` | Passed | Protocol/templates/helpers match both standalone skill copies |
| Skill-creator `quick_validate.py` for each skill | Both passed | Frontmatter/scaffold only, not behavior certification |
| Example Codex/Claude bridges | Fake CLI tests passed | Selected argv, structured output, model mismatch/error rejection, conservative usage extraction; **real integration untested** |
| Snapshot export/verify/extract | Six tests passed | Committed bytes only, no-Git review, separately supplied hash, unsafe archives, export attributes, existing-target refusal |

The three baseline regressions were derived here from Claude's feedback, not supplied as test files by Claude. The baseline run is a before/after control for those three scenarios. No claim is made that all 17 added tests were also run against v0.1.

### New invariants exercised

- Honest self-reported or unavailable settings can use the mailbox. A result cannot promote its verification level. Requested settings are distinct from observed metadata.
- A rules edit holds new dispatch and preserves the active task's pinned rules; the synthetic child finishes. Adoption is hash-bound, forbidden while a worker is active, and invalidates old approval. Explicit pause/recovery with a rules hold does not deadlock.
- A different recorded relay hash is rejected. Schema-1 state is deliberately not silently migrated; preserved evidence and carried-forward spending are required for a new run.
- Snapshots exclude dirty/untracked files and are checked against the committed Git tree at export. Review verification/extraction do not require Git. Traversal, symlinks/special files and ambiguous duplicate paths are rejected.
- Adapter tests do not invoke real providers. Cached Codex input is counted once; ambiguous totals remain unknown. Claude token usage remains unknown in this example; its cost is a client estimate.

### Review status and limits

Claude performed an independent read-only review of v0.1 and ran its 34 tests; the resulting feedback prompted these repairs. The **v0.2 repairs and added tests are this creating agent's self-validation**, awaiting independent follow-up. Neither side has tested these examples against real Codex/Claude clients. No Linux, Windows, network-filesystem, actual power-loss, or full real-project paired run was validated here.

Browser/snapshot review uses the documented manual workflow. It is not a snapshot mode inside the local relay: that relay retains its local Git HEAD check. A text-only reviewer must disclose unavailable hash/test tools. ZIP metadata/hash consistency is not a signed Git commit-graph proof.

### v0.2 source SHA-256

No package commit is available until the human initializes Git. These hashes identify the checked canonical helpers; synchronized copies are verified separately. They are integrity records, not signatures.

| File | SHA-256 |
| --- | --- |
| `scripts/relay.py` | `3f80bdedaabe5a8101ff0df6c4beb3a88619a763d46812524b414fa379fe72b6` |
| `scripts/snapshot.py` | `9863186ae59728f70fb769e9bdb862e36a55dab679b177efcf4f40ab3101e34d` |
| `scripts/adapters/common.py` | `df0423856b5725ed72c6526932ca3d1dd2b6149bea75bed678501b6ea5f1097c` |
| `scripts/adapters/codex_adapter.py` | `dd4a9cc8dd7378e07394a1c52b0664dbd44c93a38499537b8b62e3f94ff36f3b` |
| `scripts/adapters/claude_adapter.py` | `c4a686266504ee4e791087a40448d6518a4e553d22f67b9a6321a2b6138633ba` |

The following v0.1 record is retained as history.

## Historical validation — 2026-10-08, v0.1

Environment: macOS, Python 3.9.6, local filesystem. All product fixtures use disposable temporary Git repositories/worktrees. The ForgeDuet output directory itself was not initialized as a Git repository.

### Observed results

| Check | Result | Scope |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -v` | 34/34 passed | Local transport, process interface, isolated fixtures |
| `python3 scripts/sync_bundle.py --check` | Passed | Canonical resources match both installed skill copies |
| Codex `skill-creator/scripts/quick_validate.py` on both skills | Passed | Frontmatter/name/scaffold validation; not behavior certification |
| Single copied skill outside this package | Bundled relay help and protocol available | No external package imports required |
| Two real local poller processes with synthetic adapters | Idle without adapter calls; build → review → build; both exited with `done` | Exactly three synthetic invocations; no real provider calls |

### Covered invariants

- One claim across six competing processes; heartbeat extension; explicit expired-owner recovery; late-result fencing.
- Immutable report/message detection, path traversal and symlink escape rejection, corrupt/incomplete state preservation, frozen config/rules checks.
- Interrupted message publication and interrupted completion before the state commit do not dispatch orphans or double-count completed usage.
- Exact-SHA approval, separate pinned review worktree, invalid response/model fallback rejection, required-gate/blocker checks, new-candidate approval invalidation.
- Unknown usage pauses an active usage-capped run; overrun is surfaced; failed workers cannot recover around unknown spending; repeated blockers and candidate-round caps stop further work.
- Wall-time termination of the poller's own synthetic child, failed-adapter retention, idempotent task/completion retries, human pause/resume without fake approval.

### Historical limits

Tests are authored and run by the creating agent. No independent second-model review or forward-use study of the skills was performed. Real Codex/Claude adapters, remote usage metadata, GUI wakeups, user-product integration, Windows, network filesystems, and actual power-loss durability were not tested. Crash-gap tests inject write failure; they do not cut power.

The checked-in tests and fixture adapter reproduce these checks without network or paid models. The source SHA-256 is recorded below because the user requested an output folder without Git initialization. This record covers the canonical relay; bundle equality is checked separately.

Canonical `scripts/relay.py` SHA-256: `2f3a54fd421e0c4a3378521bd5f8a434675a843c7818ec4505038d51a44900e4`


## 2026-10-12 — Markdown CLI reviewer bridge, step 1 candidate

Author: ChatGPT / ForgeDuet step-1 build
Recorded: 2026-10-12T19:50:54+01:00

- Added generic source-cited `templates/REVIEW_STATE.md`, explicit placeholder config, and separate `scripts/markdown_bridge.py` reviewer runtime.
- Focused bridge suite: 21/21 passed (3.397 s); complete synthetic suite: 116/116 passed (25.530 s). Commands: `python3 -m unittest discover -s tests -p test_markdown_bridge.py -v` and `python3 -m unittest discover -s tests -v`.
- Real local fake-CLI processes verified idle zero invocation, one dispatch on complete input, dedup/restart, incomplete warnings, mutated-input identity, successful publication/log before ack, missing usage, failure/pause/recovery, timeout, active-child cancellation and cross-process lock exclusion. Publication/log and ack crash gaps retain the report and block automatic paid retries.
- `handoff.py` and `relay.py` unchanged; source bundles synchronized separately. No extra real model calls, installed-skill update, project monitoring, WristFiles access/export, device action or repository commit/push.
- Transport tests are not evidence of real-provider auth/model availability, actual usage fields, desktop sidebar behavior, review quality or comparative token cost. A separately authorized tiny real smoke test is still required.
- Raw logs and immutable source snapshot/manifest: `evidence/raw/2026-10-12-markdown-bridge-step1/`; exact hashes are in this step's delivery record. Existing earlier uncommitted documentation retained.


## 2026-10-12 — Bridge step-1 review follow-up (candidate 0.2)

Author: ChatGPT / ForgeDuet bridge follow-up
Recorded: 2026-10-12T20:10:36+01:00

- Addresses Claude's FD-BR-001: owning bridge publishes typed transport-only stop notice, with exact-hash dedup, durable receipt, peer build-watcher discovery and best-effort local OS fallback. No delivery is acknowledged by the notice and no model is invoked to generate it.
- Positive finite CLI watchdog is now required; placeholder config uses 3600 seconds, not a project budget change. Source state must be prepared before delivery, frozen through the active review, then updated from its durable result. Later real smoke must execute a synthetic test command and retain sandbox/usage evidence; still not authorized or run.
- Original errors survive pause/cleanup/notification failures. Review filenames now have date prefixes. Rejected concurrent launchers do not falsely announce the running owner stopped.
- Focused bridge suite: 35/35 passed (4.445 s). Full synthetic suite: 130/130 passed (26.428 s). OS notifications stubbed; no actual provider call or OS banner claimed.
- FD-BR-001 unfixed/fixed control uses the same fake CLI failure against the prior fixed archive versus this candidate: old emits 0 peer notices, fixed emits 1; both retain pending input and call only the fake CLI once.
- Original 21 bridge tests retain assertions; only fixture config now uses a positive timeout/disabled desktop notifications, and review-file counts match dated substantive run files instead of counting the new distinct transport notices. 14 new regressions added; original handoff/relay test assertions untouched.
- Fixed source snapshot, manifest, raw logs and negative-control harness are in `evidence/raw/2026-10-12-markdown-bridge-step1-followup/`; hashes are in the immutable follow-up delivery.
- No installed-skill rollout, daemon/project monitor, WristFiles access/export, real device action, real model invocation, repository commit or push. Both prior delivery and peer feedback remain immutable. Notification receipt/stderr cannot guarantee delivery when all channels fail or the process is killed before cleanup; this limitation is documented.

Queue adapter 0.1 candidate validation uses `python3 -m unittest discover -s tests -p test_queue_bridge.py -v`, with a local `tests/fixture_queue.py` executable only. It tests idle no-call, durable dispatch dedup, hard-kill recovery, bound review+reviewer ack, errors/notices/pause. Fake responses are not real queue/App/capacity/sleep evidence. Underlying CLI smoke is in `docs/deliveries/2026-10-12-queue-sandbox-smoke.md`; no new provider call or project activation is authorized by these tests.


## 2026-10-12 — User-authorized latest skill installation

Author: ChatGPT. User explicitly requested installing the latest local skills, committing local updates to a feature branch and pushing it, then resetting local main to origin/main.

- Updated all four personal role installations (Codex and Claude build/review): 136 package files compared, 44 updated; every package file now matches source bytes and modes. No extra installed files were present. Existing copies and the complete pre-install workspace/Git history were backed up outside the repository before overwriting.
- Both source bundles synchronized; six source/installed skill validators passed. Full local synthetic suite: 167/167 passed in 30.658 seconds. No new real model/provider call, device action or project monitor.
- Queue adapter remains candidate 0.1: one idle synthetic workspace write/ack smoke and independent peer review passed; busy/archived chats, sleep/reboot, semantic review quality and other project paths remain outside that evidence. Installation does not enable a project. Adoption notes now reflect the completed limited smoke; runtime scripts were not changed in this installation step.
- Exact installation destinations, before/after hashes, author, timestamp and authorization are retained in ignored `evidence/raw/2026-10-12-installed-latest/installation.json`; all 136 installed paths are listed in `installed-manifest.json`. Its SHA-256 is `6a4cbe5fe237ed572243b6ced1b6616fc94e1339bc2f538c09757c25d6a78fa1`. Full test output is beside it.
- Private raw evidence and peer feedback remain local under existing ignore rules and are included in the external backup. Public source, tests, documentation and delivery records are prepared for the authorized feature branch; this record is written before Git publication and does not itself claim a successful push.


## 2026-10-13 — Git sync and quota resume candidate

Author: ChatGPT. Human request: a new feature branch supporting cross-machine Git collaboration and default waiting/continuation after renewable token-limit reset. Base: b044e2c73ed904de6188ef23e88db9651214b073; branch feature/git-sync-quota-resume.

- Full synthetic suite: **202/202 passed, 42.201 seconds** (167 original tests plus 35 new behavioral/integration tests). Real temporary bare Git remote and two independent mailbox/runtime roots exercise bidirectional transport, immutable records, history rewind, collision, interruption, push uncertainty and deduplicated stop notices. No model/provider/network-service/device was called by the suite.
- Quota tests cover both relay roles, an actual exited fake adapter returning a typed quota receipt then completing the same task, default-on wait across restart, unchanged model/identity, no early calls, exactly one queue continuation per terminal receipt, final report/ack precedence, unknown reset, partial work, changed input/state, budgets and manual pause. Fake reset time and fake clients are explicitly not proof of real Codex/Claude reset telemetry integration.
- Two bundles synchronized, both skill validators and git diff --check passed. Runtime changed to candidate 0.4.0; old relay byte/version-pinned runs stay protected. New source entrypoints route to Git and quota references. Installed copies and all project monitoring were left unchanged.
- Early focused attempts are retained: a Unicode bytes literal and wrong fixture method call prevented one Git test from running; a queue restart assertion initially expected a new recovery status despite the already persisted error/pause. Fixtures/assertions were corrected to verify the actual paused uncertain state and no resend. Production safety assertions from previous tests were not weakened. Final original-plus-new suite is green.
- Raw logs and tested script/test hashes: ignored evidence/raw/2026-10-13-git-sync-quota-resume/. A source archive and exact candidate SHA are recorded in the delivery.
- Deferred: independent Claude review, real SSH/HTTPS/authentication, real cross-host service lifecycle, real-provider reset/terminal telemetry and quota continuation. The provider-neutral receipt contract is implemented; no unsupported universal observer, powered-off-machine wakeup, account-billing purchase or production readiness is claimed.


## 2026-10-13 — Git candidate round-2 review repairs

Author: ChatGPT. Addresses independent Claude findings FD-GIT-001/002 against ac11a4f, without changing the original delivery/report.

- **FD-GIT-001:** recognized transient remote connectivity/timeouts retry locally with persistent exponential backoff (default 60s base, 300s cap, five consecutive failed attempts). Success resets the consecutive count; restart does not reset it. Explicit stop reason/incident is retained after exhaustion, with operator resume required. Auth/integrity/collision/corruption and unknown errors still stop immediately. No model request is used for retry. Actual temporary bare-remote disappearance/reappearance was tested in a running watch subprocess; a single once scan now reports retrying rather than generating a stop.
- **FD-GIT-002:** stop notices enter the local role input (build reviews/, review deliveries/). Reserved local notice/response names are excluded from export and rejected in peer snapshots; local extra input files are permitted, not overwritten. A combined fake-queue/Git test binds/acks a local notice response and verifies neither record reaches the remote side. Failure to publish a local notice does not complete dedup; subsequent publication can succeed without repeating its recorded banner.
- **Scope correction:** current Claude Code desktop build + Codex App/queue review cannot automatically continue after quota reset. No real observer/reset-wakeup integration is delivered. README, both skill entrypoints, quota mode table, requirement and FD-QUOTA-DESKTOP-001/002 roadmap tasks now say so explicitly. Conditional typed-adapter policy and pre-work exec tests remain bounded; no quota runtime code was changed in this repair.
- Fixed-SHA negative control: the same three regression methods against exported ac11 fail (2 failed assertions + the old fatal offline exception); selected method ASTs match the fixed tests. The accepted control is not the earlier preliminary mutable-worktree run, which is retained and labelled separately.
- **218/218 full synthetic tests passed in 47.126 seconds** (202 original + 16 new). Previous stop-notice dedup assertions were preserved; only their route expectation changed to the correct local input directory. Both skill validators, source bundles, relative links and git diff --check passed. No real clients/models, remote service, installed-skill changes, project activation, push or merge.
- Raw logs, exact tested code hashes, reviewer feedback hash and controls: ignored evidence/raw/2026-10-13-git-sync-quota-round-02/. A fixed candidate/source archive is named in the new delivery. Independent rereview remains pending; no self-approval is implied.
