# Watcher: role / run

- Author (role / model / unique session):
- Created (ISO 8601 with timezone):
- Last modified (ISO 8601 with timezone):
- Human authorization / active task (or prepare-only, not started):
- State: not armed / armed / paused / stopped / error:
- Peer directory and role-owned cursor / handled baseline:
- Local detector and event filter (peer paths/content hashes/completion/ack; no idle model calls):
- Wakeup bridge: verified background completion / reviewed CLI relay / explicitly chosen fallback:
- Fallback limitation and human selection of recurring AI usage, if applicable:
- AI-timer fallback only: first-operation scan and authorized compact chat/session arrangement:
- Actual task ID or process and last heartbeat/verification:
- Poll interval (default 60 seconds):
- Idle-check evidence: local script only / observed no model dispatch / unverified:
- Event wakeup evidence: script exit only / actual intended client resumed / unverified:
- Substantive model/strength and verification source (preserve authorized settings):
- Model-call/usage behavior while idle; unavailable measurements:
- Peer monitor evidence or unknown:
- Latest scan diagnostic / unmarked-file warning / separate warning acknowledgement:
- Stop reason / pending human decision / outstanding work:
- Resume command or supported client action:

## Update history

| Timestamp with timezone | Author | Change |
| --- | --- | --- |

This mutable role-owned status record uses the shared writer lock and update log when stored in the coordination root. A claimed PID alone is not proof of autonomous model wakeup.

## Existing-chat queue (only if selected)

- Authorized target chat UUID and explicit model/effort: <record source>
- Trusted queue config/runtime/pinned hashes: <paths>
- Local detector PID and last verified queue-to-chat evidence: <evidence; unknown is not verified>
- Queue-process / review-ack watchdogs: <human choices>
- Outstanding event/message ID, bound review and reviewer acknowledgement: <identities or none>
- Retained recovery state and restart procedure: <no automatic resend>
- Idle/busy/archive/sleep/reboot verification limits: <observed vs untested>
- While queue adapter owns cursor, verify its existing process; do not start another watcher/AI timer.
