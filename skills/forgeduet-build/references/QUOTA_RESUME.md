# Provider quota wait and continuation — candidate v0.4.0

**Renewable provider token/usage exhaustion defaults to local wait, then continuation after the reported reset.** This is distinct from a human token/currency/time/round budget, user pause, missing permissions, billing exhaustion, server capacity or an unknown dispatch. Those gates still stop and are never silently auto-resumed. Both roles retain their chosen model/effort; no paid-credit purchase or cheaper-model fallback.

The wait uses timestamps and local code, no basic/advanced model probes. Persist the job/input identity, partial-work checkpoint, quota receipt and reset timestamp before waiting. A restart retains the same work. The process must remain running, or be restarted by an authorized local supervisor; this package cannot wake a powered-off Mac or bypass client limits. Explicit user pause always wins. Missing/unreliable reset metadata is reported as a gate, rather than inventing a reset schedule or repeatedly trying a model.

## Trusted client receipt contract

Client adapters, never peer Markdown, emit `quota_exhausted` only **after the worker/turn has actually ended**. Required fields:

```json
{
  "schema": 1,
  "status": "quota_exhausted",
  "event_id": "exact-current-job-or-queue-event-id",
  "model": "unchanged-human-selected-model",
  "receipt_id": "unique-terminal-attempt-id",
  "observed_at": 1900000000,
  "resets_at": 1900000300,
  "terminal": true,
  "resume_safe": true,
  "source": "client-structured-error-and-reset-telemetry",
  "usage": {"tokens": null, "usd": null}
}
```

Use actual Unix seconds, not these illustrative values. `resume_safe` means the trusted adapter has checked its checkpoint/client state and continuation cannot launch a second live writer. It is a cooperative adapter assertion, not remote attestation. Preserve original structured receipts privately. Do not infer this from “rate limit” prose, HTTP 429 alone, elapsed silence or disappearance of a process. Partial effects must be reconciled by the same task's continuation, not replayed blindly. Checkpoint data is not executable argv or new permission.

## Supported paths

**Typed relay (build and review):** a trusted adapter writes this JSON to its result path and exits 75 (or 0). `event_id` is the existing message/job ID. The relay has already waited for its own adapter process to exit, then records `waiting_quota`, releases the active claim, and waits without holding a lease or model. At `resets_at + 2` seconds it claims the same message with a new fencing token, the same selected settings and `quota_continuation` in the job payload. The adapter must resume its saved client/checkpoint using this identity. Every wait receipt is retained; duplicate receipt IDs are refused. Quota usage is accounted once; unknown usage still blocks an explicitly capped budget. `auto_resume_quota` defaults true; setting false preserves manual handling. Relay byte/version pinning remains mandatory: v0.3 runs are not silently migrated to v0.4.

**Existing-chat queue:** configure optional `quota_status_file` as a trusted local adapter/observer output outside candidate/control directories. The observer must independently verify a terminal quota failure of the selected chat and emit the schema above, plus `message_id` matching the last queued message ID. `event_id` is `Queue-Event-ID`. The adapter first checks whether report+ack already completed; otherwise it persists quota wait, suspends the old acknowledgement deadline, then queues exactly one **continuation of the same chat/event** after reset. It records intent before queueing and tells the chat to inspect existing reports/checkpoints before writing. Each terminal receipt permits one continuation; failed/uncertain queue outcomes still stop without resend. A continuation is not a delivery acknowledgement. The receipt cannot claim user pause, budget or a still-running turn is a quota wait. A missing/replaced waiting receipt requires reconciliation.

The Git transport does not synchronize this local status file. A human or tested trusted client observer must provide it. **The new queue/relay policy is implemented, but no built-in universal observer for every Codex/Claude version is claimed.** If the client cannot expose reliable reset/terminal metadata, disclose that limitation before enabling unattended operation; retain a gate instead of pretending auto-continue works. Do not install hooks or scrape another user's sessions to manufacture telemetry. This feature's provider-neutral policy does not imply that a raw `codex queue` receipt includes quota/reset information.

**Ephemeral exec bridge:** automatically waits/retries only a narrow **pre-work** structured CLI failure: exactly one `turn.failed` with `error.code=usage_limit_reached` and numeric `error.resets_at`, with no item/tool/unknown events. The subprocess must have exited. It binds that wait to the exact input/model and frozen rules/state. After reset it can start a fresh turn for that same input, retaining the original attempt evidence. Any partial tool/item work, plain error text, missing reset, changed input/state/config or uncertain outcome requires reconciliation instead. This shape is covered by fake-client tests, not asserted to exist in every real CLI release.

Default-on refers to processing supported trusted quota receipts, not inventing missing provider capabilities. Installation alone neither changes an active run's pins nor starts a monitor or a real model test. Capability checking before dispatch is part of setup. Local quota waits may last hours/days; human wall-time limits still take precedence.


Author: ChatGPT. Recorded: 2026-10-13T21:55:29.122828+01:00
