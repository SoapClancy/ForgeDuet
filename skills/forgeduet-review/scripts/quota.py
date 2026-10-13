#!/usr/bin/env python3
"""Provider-neutral, model-free quota receipt validation. No prose guessing.

Trusted client adapters emit these receipts ONLY after their worker has ended.
Missing reset time is a gate, not permission to probe with model requests.
"""
import math
import hashlib
import json
import re
import time


class QuotaError(ValueError):
    pass


class QuotaDeferred(Exception):
    def __init__(self, value):
        self.receipt = value
        super().__init__('Provider quota exhausted; awaiting reset')


def before_work_jsonl(path, event_id, model):
    """A narrow pre-work CLI case. Any tool/item/unknown output forbids replay.

Plain error prose, 429 alone, capacity errors and billing exhaustion are not
typed renewable quota evidence. Client versions lacking metadata stay gated.
"""
    try:
        data = path.read_bytes()
        events = [json.loads(row) for row in data.splitlines() if row.strip()]
    except (OSError, ValueError):
        return None
    allowed = {'thread.started', 'turn.started', 'turn.failed', 'error'}
    if not events or any(not isinstance(e, dict) or e.get('type') not in allowed for e in events):
        return None
    failures = [e.get('error') for e in events if e.get('type') == 'turn.failed']
    if len(failures) != 1 or not isinstance(failures[0], dict):
        return None
    error = failures[0]
    if error.get('code') != 'usage_limit_reached':
        return None
    q = dict(schema=1, status='quota_exhausted', event_id=event_id, model=model,
             receipt_id=hashlib.sha256(data).hexdigest(), observed_at=time.time(),
             resets_at=error.get('resets_at'), terminal=True, resume_safe=True,
             source='trusted CLI typed turn.failed before any item/tool output')
    return receipt(q, event_id, model)


def receipt(value, event_id, model=None, now=None):
    if not isinstance(value, dict) or value.get('schema') != 1 or value.get('status') != 'quota_exhausted':
        raise QuotaError('Expected structured quota_exhausted receipt from trusted client adapter')
    if value.get('event_id') != event_id or (model is not None and value.get('model') != model):
        raise QuotaError('Quota receipt identifies another task/model')
    if not isinstance(value.get('receipt_id'), str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', value['receipt_id']):
        raise QuotaError('Missing unique quota receipt ID')
    if value.get('terminal') is not True or value.get('resume_safe') is not True:
        raise QuotaError('Worker not demonstrably stopped or continuation not safe; reconcile first')
    observed = value.get('observed_at')
    reset = value.get('resets_at')
    for name, number in [('observed_at', observed), ('resets_at', reset)]:
        if type(number) not in (int, float) or not math.isfinite(number) or number <= 0:
            raise QuotaError('Quota '+name+' unavailable; wait for reliable client telemetry, no model probes')
    clock = time.time() if now is None else now
    if observed > clock + 5 or reset < observed:
        raise QuotaError('Invalid quota clock/reset; reconcile')
    if not isinstance(value.get('source'), str) or not value['source'].strip():
        raise QuotaError('Record the provider/client receipt source')
    return dict(value)


def ready(value, now=None, cushion=2):
    clock = time.time() if now is None else now
    if clock + 5 < value['observed_at']:
        raise QuotaError('Clock moved backwards during quota wait')
    return clock >= value['resets_at'] + cushion
