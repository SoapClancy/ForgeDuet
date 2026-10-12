#!/usr/bin/env python3
"""Synthetic CLI only. Never imports a provider SDK or invokes a model."""
import json
import os
from pathlib import Path
import sys
import time

args = sys.argv[1:]
prompt = sys.stdin.read()
context = json.loads(prompt.split('\n', 1)[1])
work = Path.cwd()
with (work / 'calls.jsonl').open('a') as out:
    out.write(json.dumps({'args': args, 'context': context}) + '\n')
mode_file = work / 'mode'
mode = mode_file.read_text().strip() if mode_file.exists() else 'ok'
(work / 'started').write_text('yes')
if mode == 'fail':
    print('fake failure', file=sys.stderr)
    sys.exit(7)
if mode == 'sleep':
    time.sleep(60)
if mode == 'mutate':
    path = Path(context['mailbox']) / context['event']['path']
    path.write_text(path.read_text() + '\nchanged\n交付完成\n')
if mode == 'state_change':
    path = Path(context['state_file'])
    path.write_text('changed state')
answer = Path(args[args.index('--output-last-message') + 1])
if mode != 'no_answer':
    answer.write_text(json.dumps({
        'input_path': 'deliveries/wrong.md' if mode == 'wrong' else context['event']['path'],
        'input_sha256': context['event']['sha256'],
        'review_markdown': '' if mode == 'empty' else '# Synthetic review\nNo actual code review or model call.\n',
        'action': 'stop' if mode == 'stop' else 'continue'}))
if mode == 'bad_jsonl':
    print('not json')
elif mode == 'turn_failed':
    print(json.dumps({'type': 'turn.failed'}))
else:
    print(json.dumps({'type': 'turn.completed', **({} if mode == 'no_usage' else {
        'usage': {'input_tokens': 10, 'cached_input_tokens': 2,
                  'output_tokens': 4, 'reasoning_output_tokens': 1}})}))
