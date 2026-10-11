"""Fake provider CLI. The test prepends the current Python shebang."""
import json
from pathlib import Path
import sys

args = sys.argv[1:]
# Model only the documented startup configuration discovery. This is not a real CLI.
settings = Path('.claude/settings.json')
if 'exec' not in args and '--safe-mode' not in args and settings.is_file():
    marker = json.loads(settings.read_text()).get('synthetic_hook_marker')
    if marker:
        Path(marker).write_text('Synthetic startup hook ran')
prompt = sys.stdin.read()
job = json.loads(prompt.split("\n", 1)[1])
Path("cli-args.json").write_text(json.dumps(args))
report = Path(job["project_root"]) / "docs/forgeduet/fake-provider.md"
report.write_text("# Synthetic provider fixture only\n")
result = {"kind": "needs_human", "sha": None, "report": "docs/forgeduet/fake-provider.md", "summary": "Synthetic pause",
          "required_gates_passed": False, "blocking_issue_ids": []}
if "exec" in args:
    Path(args[args.index("--output-last-message") + 1]).write_text(json.dumps(result))
    print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 8, "output_tokens": 2}}))
else:
    print(json.dumps({"is_error": False, "structured_output": result, "total_cost_usd": 0.02,
                      "modelUsage": {job["settings"]["model"]: {}}}))
