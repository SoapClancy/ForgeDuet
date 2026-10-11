import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_relay as base
sys.path.insert(0, str(base.ROOT / "scripts/adapters"))
import common


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.case = base.RelayTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def exercise(self, provider):
        c = self.case
        c.cfg["roles"]["build"].update(provider=provider, verification="self_reported")
        c.init()
        c.task()
        claim = c.box.claim("build", "fake-provider-test")
        cli = c.area / "fake-cli"
        cli.write_text("#!" + sys.executable + "\n" + (base.ROOT / "tests/fixture_cli.py").read_text())
        cli.chmod(0o755)
        output = c.area / "result.json"
        argv = [sys.executable, str(base.ROOT / "scripts/adapters" / (provider + "_adapter.py")), "--cli", str(cli)]
        if provider == "codex":
            argv += ["--sandbox", "workspace-write"]
        response = subprocess.run(argv + [claim["job_file"], str(output)], capture_output=True, text=True)
        self.assertEqual(response.returncode, 0, response.stderr)
        result = json.loads(output.read_text())
        flags = json.loads((c.root / "cli-args.json").read_text())
        self.assertEqual(flags[flags.index("--model") + 1], "fixture-model")
        self.assertEqual(result["execution"]["verification"], "self_reported")
        self.assertNotIn("--dangerously-skip-permissions", flags)
        self.assertNotIn("danger-full-access", flags)
        c.finish(claim, result)
        self.assertEqual(c.box.status()["phase"], "needs_human")
        return result, flags

    def test_codex_example_with_fake_cli_preserves_flags_and_counts_cache_once(self):
        result, flags = self.exercise("codex")
        self.assertEqual(result["usage"]["tokens"], 12)
        self.assertIn('model_reasoning_effort="fixture-effort"', flags)
        self.assertIsNone(result["usage"]["usd"])

    def test_claude_example_with_fake_cli_reports_unknown_tokens_honestly(self):
        result, flags = self.exercise("claude")
        self.assertEqual(flags[flags.index("--effort") + 1], "fixture-effort")
        self.assertIsNone(result["usage"]["tokens"])
        self.assertEqual(result["usage"]["usd"], 0.02)
        self.assertEqual(flags[flags.index("--permission-mode") + 1], "default")

    def test_claude_model_metadata_mismatch_is_rejected(self):
        raw = self.case.area / "raw.json"
        raw.write_text(json.dumps({"structured_output": {}, "modelUsage": {"wrong-model": {}}}))
        with self.assertRaisesRegex(ValueError, "model metadata"):
            common.claude_output(raw, "requested-model")

    def test_codex_failed_turn_cannot_return_success(self):
        raw = self.case.area / "raw.jsonl"
        raw.write_text(json.dumps({"type": "turn.failed"}) + "\n")
        with self.assertRaisesRegex(ValueError, "turn failed"):
            common.codex_output(raw, self.case.area / "missing-answer.json")
