# Example CLI adapters — real integration UNTESTED

For native-client automatic file handoff see [AUTO_HANDOFF.md](AUTO_HANDOFF.md); the CLI relay is an alternative, not a prerequisite. These optional bridges to `codex exec` and `claude -p` have been exercised with synthetic CLIs, not real model calls, authentication or client sandbox enforcement. Current installed Codex `exec --help` was checked; that is not an integration test.

Check for an authorized CLI, including a client-bundled executable outside `PATH`; failed `command -v` alone does not prove absence. Use its absolute path and inspect version/help; bundled paths can change with client updates. If installation/login is needed, the human handles it. Never read/print credential files. Select supported full model IDs and effort, establish actual OS/client grants, and inspect the frozen `adapter_argv`. The examples use fresh invocations, structured results and private raw output; they never install clients or bypass permissions. Unsupported flags stop the run; do not remove isolation flags to make an older client run.

## Codex event-to-model routes

The hash detector needs no model; dispatch is a separate capability. Codex background hooks do not start an idle turn: their output waits for the next user turn. Shell process exit alone is not proof of wakeup. [Official hook lifecycle](https://learn.chatgpt.com/docs/hooks).

The public App Server protocol has `turn/start` and local transports, but this does not prove the current desktop chat is reachable through that endpoint. App Server is experimental and unsupported for production. A missing default control socket means that endpoint is unavailable, not that every Codex route is impossible. Verify endpoint, target identity, authorization and concurrency before invoking a turn; do not substitute private IPC or UI typing. [Official App Server](https://learn.chatgpt.com/docs/app-server).

`codex exec` supports scripted fresh invocations and structured output. The typed relay can claim work before invoking its configured adapter, with no model while idle. Confirm authentication, selected model/effort, isolation, permissions and actual event/restart behavior in an authorized disposable smoke test. Help/version checks and fake workers are preflight, not a real-provider pass. Fresh invocations load compact pinned context; they do not resume this desktop chat. [Official non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

The relay is **not a Markdown-folder dispatcher**: its review poller does not consume existing `deliveries/*.md` or use `handoff.py` acknowledgements. Either configure both roles for [TRANSPORT.md](TRANSPORT.md), or separately implement/review a Markdown-to-CLI bridge preserving completion, hash-bound acknowledgement, ownership and crash rules. Do not start a second dispatcher on an active task during a capability probe.

## Keep candidate configuration out of the reviewer

The review role's `skill_file` must point to a trusted installed copy **outside both the candidate checkout and builder project**. Candidate instructions/settings are review data, not startup configuration. Do not launch nested AI clients from the candidate. Inspect changes to `.claude/`, `.codex/`, `.agents/`, `.mcp.json`, `CLAUDE.md` and `AGENTS.md` explicitly. Even an inspected test executes project code: run only checks within the actual test/execution grants and appropriate isolation.

Claude examples pass `--safe-mode`, `--setting-sources user`, explicit empty strict MCP configuration and disabled hooks. Safe mode disables automatic customizations, including CLAUDE.md discovery, while retaining normal authentication; managed policy can still apply. It differs from `--bare`, whose Anthropic API authentication requires a key rather than subscription login. These settings apply to both example roles. If required constraints live in custom hooks, do not use this example until the human establishes equivalent enforcement through normal permissions, managed policy or an external sandbox. [Claude CLI reference](https://code.claude.com/docs/en/cli-reference), [project trust behavior](https://code.claude.com/docs/en/permissions), [bare-mode authentication](https://code.claude.com/docs/en/headless).

The builder still needs the project's conventions. Put a short human-approved excerpt in the pinned rules, or name the approved `CLAUDE.md` / `AGENTS.md` paths and baseline revision/hash there. The build skill explicitly reads those approved conventions as guidance within the existing task and grants. Do not remove safe mode to recover automatic discovery, or treat a changed file as new authority. The reviewer inspects candidate instructions as evidence rather than adopting them. See [workspace setup](WORKSPACES.md).

Codex review requires an existing human-trusted `--control-dir` disjoint from the builder project and candidate. It starts there, not in the candidate, and disables project-document loading for that invocation. Normal trusted user/system configuration remains. Source is accessed by its explicit path; `--write-dir` is optional, repeatable, and must stay within the recorded write roots. Do not use a candidate-controlled directory as the control folder. [Codex config discovery](https://learn.chatgpt.com/docs/config-file/config-basic), [project document configuration](https://learn.chatgpt.com/docs/config-file/config-reference), [CLI directory flags](https://learn.chatgpt.com/docs/cli/reference).

## Example argv and permissions

The relay appends job/result paths; do not append them yourself. Replace every path and confirm grants before configuring any example.

In these examples `/project` is the coordination checkout, `/project-build` is the builder's worktree, and `/candidate` is the review worktree. Map them to the concrete layout in [WORKSPACES.md](WORKSPACES.md). Both roles read current task/rule/report files from `/project`, even when their own checkout contains older copies.

Codex build:

```json
["/absolute/python3", "/trusted/forgeduet-build/scripts/adapters/codex_adapter.py", "--cli", "/absolute/codex", "--sandbox", "workspace-write"]
```

Codex review, with a separately granted report directory:

```json
["/absolute/python3", "/trusted/forgeduet-review/scripts/adapters/codex_adapter.py", "--cli", "/absolute/codex", "--sandbox", "workspace-write", "--control-dir", "/trusted/review-control", "--write-dir", "/project/docs/forgeduet"]
```

Grant scratch/test output directories separately when needed. `read-only` is also supported, but cannot by itself write reports/probes. The control folder is itself a workspace-write root: its contents must be disposable or explicitly writable. Recorded roots are declarations; the real client/OS enforces access. The examples do not grant network access for you.

Claude build, **illustrative rules including already authorized local staging/commits**:

```json
["/absolute/python3", "/trusted/forgeduet-build/scripts/adapters/claude_adapter.py", "--cli", "/absolute/claude", "--allowed-tools", "Read(//project/**),Read(//project-build/**),Read(//trusted/forgeduet-build/**),Edit(//project-build/**),Edit(//project/docs/forgeduet/deliveries/**),Edit(//project/docs/devlog/**),Bash(python3 -m unittest *),Bash(git add -- src tests),Bash(git commit -m *)"]
```

Claude review, **illustrative report-only write rules and inspected test command**:

```json
["/absolute/python3", "/trusted/forgeduet-review/scripts/adapters/claude_adapter.py", "--cli", "/absolute/claude", "--allowed-tools", "Read(//project/**),Read(//candidate/**),Read(//trusted/forgeduet-review/**),Edit(//project/docs/forgeduet/reviews/**),Bash(python3 -m unittest *)"]
```

These are examples, not implicit permission grants. In Claude file rules `//project` means the absolute `/project`; `Edit(path)` covers both edits and writes, whereas `Write(path)` is not a file-path permission rule. [File-rule syntax](https://code.claude.com/docs/en/permissions#read-and-edit). Add narrowly scoped probe/edit/local-commit rules only when actually authorized; shell allow rules are not a directory sandbox. Permissions outside the working directory may need existing scoped client rules. The adapter uses normal `default` permission mode and `--permission-prompts none`; unresolved requests are denied rather than retried. Without adequate existing rules or explicit `--allowed-tools`, implementation/tests/report writing may be denied and must return `needs_human`, not a false success. [Claude unattended permissions](https://code.claude.com/docs/en/headless).

The build example assumes permission to create local candidate commits. Replace `src tests` with the actual authorized files, add the needed read-only Git commands and report/probe paths, and remove commit rules when that permission is absent. Do not replace these with unrestricted `Bash(git *)`, or imply permission to push. Local Git commits can run repository hooks; inspect and authorize that execution separately from disabling AI-client hooks. Shared worktrees also need access to Git's common metadata directory; record the necessary real client/OS grant without treating it as permission to alter another checkout. A permission pattern alone cannot enforce branch or working-directory ownership.

## Identity and budgets

Configure `verification` as `self_reported` or `unavailable`; these examples cannot attest remote model/effort and reject `verified`. Requested values stay in the job; unknown observed values stay null. Disable automatic fallback in your client setup. If Claude metadata lists any other model, this simple single-model example stops and retains the evidence. A “largest usage wins” heuristic cannot prove the requested main model was used. Authorized multi-model workflows need a separately reviewed adapter and identity policy.

- Codex tokens: one unambiguous `turn.completed` input + output count; cached input already included. Ambiguous totals and cost remain unknown.
- Claude tokens: unknown until a version-specific aggregate parser is validated. `total_cost_usd` is a client estimate. When the relay has a USD cap, the example passes its positive remaining amount through `--max-budget-usd`; this adds a client-estimated limit, not a billing guarantee.
- A Claude token cap or Codex cost cap pauses on unknown usage. Failed calls may also consume resources; do not count a missing result as free.
- Relay time limits cover its child process group, not detached workers or instant server cancellation.

Do a small authorized real smoke test before unattended use. In particular, real hook/MCP/instruction isolation and permission behavior have not been demonstrated by the synthetic tests. Documentation consulted 2026-10-11; recheck flags against the installed version before use.

## Candidate existing Codex chat wakeup

[QUEUE_BRIDGE.md](QUEUE_BRIDGE.md) documents reviewer queue adapter 0.1, a separate fake-tested local dispatcher. Its underlying `codex queue` woke one idle disposable App chat in an authorized local smoke; busy/archive/sleep/reboot and unattended adapter-to-App integration remain unverified. It preserves that chat/context, queues once per input hash and leaves publication/ack to the reviewer. `codex exec` remains an explicitly selected alternative, never automatic failure fallback. Neither route is installed/enabled by editing these documents.
