# ForgeDuet

**Two AI roles, one auditable engineering loop.** One implements and tests; the other reviews the exact commit and tests independently. Humans set scope, choose the models, and resolve decisions that need human judgment.

ForgeDuet packages a workflow learned from repeated development, independent review, and real-device testing. It works with different model providers; the roles are deliberately separate even when both use the same provider. Two agreeing models are not proof of correctness. Reproducible evidence is the acceptance criterion.

[简体中文](README.zh-CN.md) · **[Start the paired loop](protocol/MANUAL.md)** · [Automatic handoff](protocol/AUTO_HANDOFF.md) · [Protocol](protocol/PROTOCOL.md)

## Included

- [Build + test skill](skills/forgeduet-build/SKILL.md): implementation, focused self-tests, preserved regression tests, and evidence-based handoffs.
- [Review + test skill](skills/forgeduet-review/SKILL.md): pinned-commit review, independent reproduction, regression tests, and explicit acceptance gates.
- [Project rules](templates/PROJECT_RULES.md), [setup checklist](templates/SETUP.md), and report templates.
- Automatic two-way handoff instructions, a 60-second local Markdown watcher, shared writer lock, atomic complete reports, durable acknowledgements and update log.
- Local checks before model invocation: neither a basic nor an advanced model is needed while idle. A standard-library CLI mailbox is also available, with deduplication, leases and recovery. Native AI timers are an explicitly chosen recurring-cost fallback.

The skills include identical protocol and helper copies so either skill directory can be installed on its own. Edit the canonical `protocol/`, `templates/`, and `scripts/` resources, then run `python3 scripts/sync_bundle.py`. `--check` detects stale copies.

## Start with the skills

Start each role once with its skill and authorized task. **Active local runs require automatic two-way handoff by default**: build watches `reviews/`, review watches `deliveries/`, every 60 seconds. The default order is **local hash/completion/ack check → pending input → verified client wakeup or CLI dispatch → selected build/review model**. Use verified client background completion or a configured CLI relay; do not wake an AI chat every minute just to perform the check. If neither is available, disclose the missing bridge and resolve the fallback with the human. Native AI timers require explicit, cost-informed selection; the relay itself is optional. Both roles publish complete records under the shared lock and re-arm after each turn. No human message courier should be needed. Editing/installing skills alone does not start a project monitor. See [AUTO_HANDOFF.md](protocol/AUTO_HANDOFF.md).

An [uploaded snapshot](protocol/SNAPSHOTS.md) supports explicit browser/manual fallback without local Git. Disclose missing automatic wakeup early; do not silently downgrade an automatic run to manual.

Copy the two skill directories to your agent's supported skill location. For Codex use project `.agents/skills/`; for Claude Code use project `.claude/skills/` or personal `~/.claude/skills/`. Copy each complete `forgeduet-build` / `forgeduet-review` directory beneath that location, inspecting existing destinations first. Codex can invoke `$forgeduet-build` / `$forgeduet-review`; Claude Code can invoke `/forgeduet-build` / `/forgeduet-review`. Project-local installation can serve the builder. Automated review must use a trusted installed review skill outside both the builder project and candidate, such as a personal skill directory or separate trusted tools folder. Or give the role trusted `SKILL.md` and references directly in a chat. `agents/openai.yaml` is optional Codex UI metadata; Claude uses the same SKILL frontmatter. [Codex discovery docs](https://learn.chatgpt.com/docs/build-skills), [Claude skill discovery docs](https://code.claude.com/docs/en/skills).

1. Complete the relevant choices in [SETUP.md](templates/SETUP.md): **both requested models/strengths**, verification level/source, report language, access, and optional budgets. `verified`, `self_reported`, and `unavailable` are honest distinctions; unavailable verification does not itself forbid work. Reuse standing authorization.
2. Fill [PROJECT_RULES.md](templates/PROJECT_RULES.md). Use a short-lived feature branch and a separate review worktree **or a verified snapshot**. Branch creation, merge, push, release, and installation stay within recorded authorization.
3. Start build with `$forgeduet-build` and review with `$forgeduet-review`, both pointing to the task/rules and peer folder. Each must arm and verify its own monitor, record its real ID/PID/cursor and limits, and publish/re-arm without asking you to forward reports. Commit reports, issue records, and synthetic regression tests; keep private raw evidence outside version control.
4. Iterate until the reviewer approves the **same full commit SHA** that the builder accepts, all required gates pass, and no current-scope P1/P2 remains. P3 deferral must follow the project's agreed policy.

Use a new short session per handoff when your client supports it. Load the rules, current task, latest report, and relevant issue records instead of the whole conversation history.

## Optional local relay

Requires **Python 3.9+ and macOS/Linux** (`fcntl.flock`). No third-party Python packages. Windows and network-shared mailboxes are not supported in this version.

If you want local dispatch, copy `templates/run.example.json` to `run.local.json`, replace empty settings, and record the user's choices. This template is intentionally not runnable: no default model or implied approval. `permissions` documents access; the OS/client actually enforces it. The local relay still requires local worktrees; snapshot/browser review uses the complete manual workflow above.

```sh
python3 /path/to/ForgeDuet/scripts/relay.py init --config /path/to/project/run.json
python3 /path/to/ForgeDuet/scripts/relay.py task --mailbox /path/to/project/.forgeduet --report docs/forgeduet/tasks/task-001.md
python3 /path/to/ForgeDuet/scripts/relay.py status --mailbox /path/to/project/.forgeduet
```

For manual use, `claim` returns a job file and a fencing token. Work on that task, write a JSON result using [result.example.json](templates/result.example.json), and call `finish` with the token. For automatic dispatch, configure a **trusted local adapter** and run one poller for each role:

```sh
python3 /path/to/ForgeDuet/scripts/relay.py watch --mailbox /path/to/project/.forgeduet --role build
python3 /path/to/ForgeDuet/scripts/relay.py watch --mailbox /path/to/project/.forgeduet --role review
```

The poller starts the adapter only for a claimed task. The adapter receives a job JSON path and result JSON path as its final two arguments. It must launch the human-selected model/effort, load the skill and pinned context, write a report, and return the documented result. It must use normal client permissions; never enable permission bypass just to make automation run. See [TRANSPORT.md](protocol/TRANSPORT.md) for the exact contract and recovery commands.

Two [example CLI adapters](protocol/ADAPTERS.md) are included. **Real-provider CLI integration is untested**; fake CLI tests cover argument/output plumbing only. A skill alone cannot wake an idle GUI conversation: actual background completion or CLI dispatch must be armed and verified. A shell process that the agent must poll is not proof of such a bridge. Native AI timers wake before checking and can consume usage even when no report changes; do not enable them as a silent fallback. The local watcher reads reports and maintains its private cursor without calling a model. Example review adapters keep candidate configuration out of startup; Codex review additionally requires a trusted external control folder. See the adapter guide for Claude permission rules. The relay records settings verification honestly and cannot attest to the remote model. Unsupported settings must fail instead of silently falling back.

Both roles must install the same relay bytes/version; each run records and checks them. A changed rules file holds new dispatch without killing the current task, which retains a pinned rules snapshot. Human-confirmed `adopt-rules` after the task finishes can continue the same run and invalidates old approvals. Adoption/resume keeps the original task/delivery and attaches the decision separately; adoption while paused waits for resume. Explicit `pause` still terminates the poller's child. Configuration/model/permission/budget changes require a reviewed new run. See the [transport reference](protocol/TRANSPORT.md).

Budgets are checked between jobs. The poller enforces configured wall time for its own child process; token/cost limits need accurate adapter usage and may overshoot by one running job. Unknown usage with an active limit pauses the run. This is not a provider-side hard spending cap.

## Records and boundaries

Each role writes its own Markdown reports and issue/decision files. Shared writes and authorized coordination Git operations use one short `.lock/`; `updates.log` is append-only under that lock. Reports carry author/timezone timestamps and final completion markers. Mutable shared documents retain update history. Product changes are made on feature branches; independent review tests are adopted without weakening assertions. These cooperative locks reduce accidental races; they are **not an authentication boundary** between mutually untrusted local processes. Never expire someone else's lock automatically.

See [workspace ownership](protocol/WORKSPACES.md) for concrete coordination/build/review paths, report-write permissions and a single records committer. Isolated builders read human-approved project conventions explicitly; the example Claude adapter does not automatically discover `CLAUDE.md`.

Do not publish device logs, personal files, secrets, or private screenshots just because a report references them. Keep a redacted summary, artifact hash, and an accessible private archive reference. Required evidence that the reviewer cannot access remains unverified.

## Verify this package

```sh
python3 -m unittest discover -s tests -v
python3 scripts/sync_bundle.py --check
```

See [docs/VALIDATION.md](docs/VALIDATION.md) for the actual validation performed. Unit tests exercise the local relay with synthetic workers; they do not establish real-provider integration or product correctness.

MIT licensed. The package does not initialize your Git repository, configure a remote or start project monitors merely because you install it. The example adapters invoke your chosen CLI only when configured and started within your authorization. See the dated validation records for checks actually performed and remaining limits.
