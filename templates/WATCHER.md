# Watcher: role / run

- Author (role / model / unique session):
- Created (ISO 8601 with timezone):
- Last modified (ISO 8601 with timezone):
- Human authorization / active task (or prepare-only, not started):
- State: not armed / armed / paused / stopped / error:
- Peer directory and role-owned cursor / handled baseline:
- Mechanism: native scheduler / background completion / CLI relay / explicit manual fallback:
- Actual task ID or process and last heartbeat/verification:
- Poll interval (default 60 seconds):
- Wakeup evidence: script only / actual client resumed / unverified:
- Model-call/usage behavior while idle; unavailable measurements:
- Peer monitor evidence or unknown:
- Latest scan diagnostic / unmarked-file warning / separate warning acknowledgement:
- Stop reason / pending human decision / outstanding work:
- Resume command or supported client action:

## Update history

| Timestamp with timezone | Author | Change |
| --- | --- | --- |

This mutable role-owned status record uses the shared writer lock and update log when stored in the coordination root. A claimed PID alone is not proof of autonomous model wakeup.
