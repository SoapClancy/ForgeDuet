# Project rules

Status: awaiting human configuration. Do not treat this template as authority.

## Scope and acceptance

- Authorized objective:
- Current requirements: `docs/requirements/`
- Out of scope:
- Product owner / escalation contact:
- Evidence required for acceptance:
- Human decisions and their authorization source:

## Roles, settings, access

- Build: requested provider/model/strength; verification level and source:
- Review: requested provider/model/strength; verification level and source:
- Reports and handoffs language:
- Approved build conventions: short excerpt or absolute file paths with approved revision/hash; scope remains subject to human task/grants:
- Build checkout and writable paths:
- Review worktree and writable paths:
- Shared read paths:
- Network / tool / executable boundaries:
- User data / devices / production boundaries:
- Budget choices and actual enforcement limitations:

## Git and records

- Coordination checkout (`project_root`), build worktree, review worktree, and trusted review control/skill directories:
- Base branch and feature branch:
- Local commits / merge authorization:
- Push / release / install authorization:
- Reviewer pins an exact full SHA in an independent worktree, or an exported snapshot's SHA plus archive SHA-256. Record which mode and which checks are available.
- Build owns `docs/forgeduet/deliveries/`, `docs/devlog/`, product code, adopted tests.
- Review owns `docs/forgeduet/reviews/`, `docs/forgeduet/review-tests/`, review issue records.
- Records committer, authorization, and serialization: role authors its own reports; only the designated writer stages/commits coordination records. Source approval stays bound to the candidate SHA, not a later records commit.
- If coordination and build share a checkout: explicitly granted reviewer report/test-artifact subdirectories; product files and that checkout's Git index are excluded from reviewer writes:
- Each role owns its own files in `docs/decisions/`, `docs/issues/`, `docs/forgeduet/human/`. Refer to counterpart records; do not rewrite them.
- Requirements, architecture, and roadmap changes: owner and authorized update process:
- One record per round, immutable after publication. Supersede with a new file.
- Raw evidence retention, redaction, private archive locations:

## Automatic handoff

- Active run authorization (skill preparation alone does not start a monitor):
- Build monitors reviews/; review monitors deliveries/; interval defaults to 60 seconds:
- Local detector before model invocation; no model, including a basic one, for idle checks:
- Verified event-to-model bridge and actual ID/PID/idle and wakeup evidence for each role:
- Missing bridge / explicitly chosen fallback; recurring AI-timer cost consent if applicable:
- Role-private cursors / acknowledged report path+hash baseline / watcher status records; never consume at detection:
- Idle model usage and runtime/sleep limits; unavailable measurements:
- Shared coordination .lock/ root and unique owner IDs; updates.log writer:
- Atomic completed reports; immutable records corrected by supersession:
- Stop on same-SHA closure, required human gate, agreed budget or user stop; resume procedure:
- Explicit manual/browser fallback, only if chosen or automatic capability is unavailable:

## Verification and convergence

- Required checks by risk tier:
- Required human or device gates:
- Definition of P1/P2/P3 for this project:
- P1/P2 in current scope block acceptance. Agreed P3 deferral policy:
- Regression assertions remain unchanged unless the reviewer accepts a documented test defect or minimal interface adaptation.
- Negative control method or reason impractical:
- Escalation limit for unresolved disagreements / repeated blockers:
- Success means both roles accept the same SHA and all required gates are met.

## Autonomous decisions

Within the authorized scope, either role may propose a small fix, missing test, or design clarification. Implement it autonomously when both agree, it does not change the product contract materially, and existing grants cover the actions. Record the decision and verify it.

New major functionality, changed privacy/data behavior, breaking compatibility, expanded permissions/cost, missing required human evidence, or unresolved disagreement goes to `docs/forgeduet/human/`. Two AI votes cannot create human authorization. Existing broad human authorization may already cover a decision; do not invent another approval step.

## Update history

| Timestamp with timezone | Author | Change |
| --- | --- | --- |
