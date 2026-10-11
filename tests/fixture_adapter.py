"""Synthetic worker for relay tests only. Does not invoke an AI provider."""
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    mode, job_file, result_file = sys.argv[1:]
    job = json.loads(Path(job_file).read_text())
    root = Path(job["project_root"])
    counter = root / "adapter-invocations.txt"
    with counter.open("a") as stream:
        stream.write(job["role"] + "\n")
    if mode == "fail":
        return 7
    if mode == "sleep":
        time.sleep(30)
    if mode == "delay":
        time.sleep(1.5)
    kind = {"task": "candidate", "candidate": "review_approved",
            "review_approved": "build_accepted", "changes_requested": "candidate"}[job["message"]["kind"]]
    sha = job["message"]["sha"] or subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if job["role"] == "review":
        subprocess.run(["git", "-C", job["settings"]["workdir"], "checkout", "--detach", sha], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report = "docs/forgeduet/{}-{}.md".format(kind, job["message"]["id"])
    (root / report).write_text("# Synthetic result\n\nTransport fixture only, not model evidence.\n")
    result = {"kind": kind, "sha": sha, "report": report,
              "summary": "Synthetic worker completed", "execution": {k: job["settings"][k] for k in ("provider", "model", "effort")},
              "usage": {"tokens": 0, "usd": 0, "source": "Synthetic worker, no model call"},
              "required_gates_passed": True, "blocking_issue_ids": []}
    Path(result_file).write_text(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
