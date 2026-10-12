#!/usr/bin/env python3
"""Local fake queue CLI; never imports or invokes a model/client."""
import json
from pathlib import Path
import sys
import time

area = Path(__file__).resolve().parent
args = sys.argv[1:]
with (area / 'calls.jsonl').open('a') as out:
    out.write(json.dumps(args) + '\n')
mode = (area / 'mode').read_text().strip()
if mode == 'hang':
    time.sleep(120)
if mode == 'fail':
    print('synthetic refusal or capacity error', file=sys.stderr)
    sys.exit(7)
if mode == 'bad':
    print('unrecognized response')
elif mode == 'wrong-thread':
    print('Queued message 00000000-0000-4000-8000-000000000001 for thread 00000000-0000-4000-8000-000000000002.')
else:
    assert args[0] == 'queue'
    print('Queued message 00000000-0000-4000-8000-000000000001 for thread ' + args[args.index('--thread')+1] + '.')
