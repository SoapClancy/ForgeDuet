#!/usr/bin/env python3
"""Local fake queue CLI; never imports or invokes a model/client.

Argument handling mirrors `codex queue` in codex-cli 0.171.0-alpha.13: unknown
flags such as --model/--sandbox are rejected with exit 2, like the real parser.
"""
import json
from pathlib import Path
import sys
import time

VALUED = {'--thread', '--message', '--enable', '--disable', '--remote', '--remote-auth-token-env',
          '-p', '--profile', '-c', '--config'}
SWITCHES = {'--resume', '--strict-config'}
HELP = """Queue a message for an existing session

Usage: codex queue [OPTIONS] --thread <THREAD> --message <TEXT>

Options:
      --thread <THREAD>
          Session UUID or exact session name
      --message <TEXT>
          Message text to queue
      --resume
          After queueing, try to resume the thread
  -c, --config <key=value>
          Override a startup configuration value (key=value). Queued messages use the thread's model.
  -h, --help
          Print help
"""

area = Path(__file__).resolve().parent
args = sys.argv[1:]
mode_file = area / 'mode'
mode = mode_file.read_text().strip() if mode_file.exists() else 'ok'

if args[:1] == ['queue'] and ('--help' in args or '-h' in args):
    with (area / 'help_calls.jsonl').open('a') as out:
        out.write(json.dumps(args) + '\n')
    if mode == 'help-fail':
        sys.exit(1)
    print(HELP.replace('--message', '--text') if mode == 'help-old' else HELP)
    sys.exit(0)

with (area / 'calls.jsonl').open('a') as out:
    out.write(json.dumps(args) + '\n')
if args[:1] != ['queue']:
    print("error: unrecognized subcommand", file=sys.stderr)
    sys.exit(2)
seen, i = {}, 1
while i < len(args):
    flag = args[i]
    if flag in VALUED and i + 1 < len(args):
        seen[flag] = args[i + 1]
        i += 2
    elif flag in SWITCHES:
        seen[flag] = True
        i += 1
    else:
        print("error: unexpected argument '" + flag + "' found", file=sys.stderr)
        sys.exit(2)
if '--thread' not in seen or '--message' not in seen:
    print("error: the following required arguments were not provided", file=sys.stderr)
    sys.exit(2)
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
    print('Queued message 00000000-0000-4000-8000-000000000001 for thread ' + seen['--thread'] + '.')
