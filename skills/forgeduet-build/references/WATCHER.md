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
