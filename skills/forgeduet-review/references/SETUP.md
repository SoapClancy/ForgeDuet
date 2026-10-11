# ForgeDuet setup — human choices

Complete before starting the loop. Ask missing questions together, early. Existing explicit authorization is enough; link it rather than re-asking. Never imply a SKILL grants sandbox access.

| Choice | Recorded value |
| --- | --- |
| Authorized task and acceptance criteria | |
| Build provider, exact model, reasoning strength | |
| Review provider, exact model, reasoning strength | |
| Settings verification: verified / self_reported / unavailable; source for each | |
| Report and handoff language | |
| Project absolute directory | |
| Build checkout, base branch, short-lived feature branch | |
| Review mode: local worktree or uploaded snapshot; directory/export identity | |
| Shared reports and mailbox directories | |
| Workspace layout, role-owned report paths, records committer | |
| Approved build conventions: excerpt or paths plus baseline revision/hash | |
| Read roots / write roots / allowed tools and execution | |
| Network access / external integrations | |
| Standing authorization for local commits and merges | |
| Push, publication, deployment, device installation authorization | |
| Token limit: total, per role, or explicitly none | |
| Cost limit and whether usage is available, or none | |
| Wall time, maximum rounds, repeated-blocker limit, or none | |
| Budget action: stop and retain artifacts | |
| Test tiers and required human/device gates | |
| P3 deferral policy | |
| Active run or preparation only (do not start monitors during preparation) | |
| Both monitors: native scheduler / background completion / reviewed CLI relay; explicit manual fallback if unavailable | |
| Each role's actual task ID/PID, wakeup evidence, private cursor and handled baseline | |
| Poll interval (default 60 seconds), idle usage and client/sleep limitations | |
| Shared coordination .lock/ root, unique owners, append-only updates.log and records writer | |
| Stop conditions and authorized restart procedure | |
| Who resolves disagreement and resumes stopped work | |

Always record the requested model/strength. Record observed settings as `verified` (checked against client evidence), `self_reported` (asserted by operator/client), or `unavailable` (cannot check). Unavailable verification does not prohibit work; disclose it and let the human accept or change the setup. Inability to set the requested model is a separate constraint to resolve; never silently choose another model. No status is remote attestation merely because the config says so.

Record each grant's source (human message/date or prior standing instructions). State the exact permission request and path if blocked. Continue independent authorized preparation while waiting. Never use broad executable/permission bypass to avoid a narrow request.

For automation, record the reviewed adapter path and argv, and then fill `run.example.json`. The boolean confirmations in that JSON are workflow declarations, not proof of consent and not OS access controls. The agent must have real human authorization for the recorded choices.

An active local paired run defaults to automatic two-way handoff. Follow `AUTO_HANDOFF.md` to arm and verify **both** sides without a human courier. If a real wakeup mechanism is unavailable, disclose it early and agree a fallback; never silently downgrade to manual. Skill editing/installation is preparation, not a request to start monitoring another project.

Choose the workspace layout before grants: coordination records, build source, and review source have different owners. See `protocol/WORKSPACES.md` in the package, or `references/WORKSPACES.md` in an installed skill. Commit durable Markdown and synthetic regressions through the designated records/product writer; do not let both roles stage the same checkout concurrently. With safe-mode Claude examples, explicitly supply approved build conventions in the pinned rules; automatic `CLAUDE.md` discovery is disabled.
