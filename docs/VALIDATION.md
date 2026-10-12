# Validation

## Current validation — 2026-10-12, v0.3.2 instruction update

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

**Remaining integration limit:** this update does not establish a zero-idle-model loop in the current Codex desktop chat. Its available shell tool exposes a session to poll; no automatic process-exit-to-chat wakeup was verified. A real client background-completion bridge or reviewed CLI setup still needs an authorized live smoke test. The package does not provide a generic desktop-chat wakeup API; the example real-provider adapters remain untested. A previous Claude-reported background notification is not independent proof for Codex or every client session. Skill installation does not hot-reload another agent's already-read instructions or restart its watcher. Both configured substantive models are preserved; no basic model was added to polling, no CLI installed, no paid provider invoked, and no product code or project coordination file written. This instruction update has not yet received independent peer review.

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
