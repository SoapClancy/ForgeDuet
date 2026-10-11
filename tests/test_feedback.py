"""Regression scenarios derived from Claude's 2026-10-11 feedback."""
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

import test_relay as base
import relay


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.case = base.RelayTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def test_honest_self_reported_settings_can_use_mailbox(self):
        c = self.case
        for role in relay.ROLES:
            c.cfg["roles"][role].update(settings_verified=False, verification="self_reported",
                                       verification_source="Human-selected client UI; no remote attestation")
        c.init()
        c.task()
        self.assertIsNotNone(c.box.claim("build", "honest-manual-user"))

    def test_different_relay_hash_cannot_share_run(self):
        c = self.case
        c.init()
        path = c.box.path / "state.json"
        state = json.loads(path.read_text())
        state["relay_sha256"] = "0" * 64
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(relay.RelayError, "relay|Relay"):
            c.box.status()

    def test_rules_typo_does_not_kill_active_adapter(self):
        c = self.case
        c.configure_adapter("delay")
        c.init()
        c.task()
        process = subprocess.Popen([sys.executable, str(base.ROOT / "scripts/relay.py"),
                                    "watch", "--mailbox", str(c.box.path), "--role", "build", "--once"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not (c.root / "adapter-invocations.txt").exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue((c.root / "adapter-invocations.txt").exists())
            c.report("rules", "# Same scope, corrected spelling\n")
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
            state = json.loads((c.box.path / "state.json").read_text())
            self.assertTrue(state["dispatch_hold"])
            self.assertEqual(state["current_sha"], c.sha)
            self.assertEqual(state["usage"]["tokens"], 0)
            self.assertIsNone(c.box.claim("review", "reviewer"))
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=5)

    def test_unavailable_identity_is_explicit_and_not_promoted(self):
        c = self.case
        c.cfg["roles"]["build"].update(verification="unavailable", settings_verified=False)
        c.init()
        c.task()
        claim = c.box.claim("build", "builder")
        result = c.result("candidate", "build")
        result["execution"].update(provider=None, model=None, effort=None, verification="verified")
        with self.assertRaisesRegex(relay.RelayError, "promote"):
            c.finish(claim, result)
        result["execution"]["verification"] = "unavailable"
        ident = c.finish(claim, result)
        message = json.loads((c.box.path / "messages" / (ident + ".json")).read_text())
        self.assertEqual(message["settings_verification"], "unavailable")

    def test_rules_adoption_is_hash_bound_and_invalidates_old_approval(self):
        c = self.case
        c.init()
        c.candidate()
        claim = c.box.claim("review", "reviewer")
        c.finish(claim, c.result("review_approved", "review"))
        c.report("rules", "# New required acceptance check\n")
        report = c.report("human-adoption", "# Human approved changed checks; original task unchanged\n")
        current = c.box.status()["dispatch_hold"]["observed_hash"]
        with self.assertRaisesRegex(relay.RelayError, "changed again"):
            c.box.adopt_rules("0" * 64, report, "Synthetic human decision")
        c.box.adopt_rules(current, report, "Synthetic human decision")
        state = c.box.status()
        self.assertIsNone(state["dispatch_hold"])
        self.assertIsNone(state["review_approved_sha"])
        self.assertIsNone(c.box.claim("build", "cannot-accept-old-approval"))
        self.assertIsNotNone(c.box.claim("review", "recheck-new-rules"))

    def test_cannot_adopt_rules_while_worker_is_active(self):
        c = self.case
        c.init()
        c.task()
        claim = c.box.claim("build", "builder")
        payload = json.loads(Path(claim["job_file"]).read_text())
        original_rules = Path(payload["rules_snapshot"]).read_bytes()
        c.report("rules", "# Future rules\n")
        new_hash = c.box.status()["dispatch_hold"]["observed_hash"]
        self.assertEqual(Path(payload["rules_snapshot"]).read_bytes(), original_rules)
        with self.assertRaisesRegex(relay.RelayError, "current worker"):
            c.box.adopt_rules(new_hash, c.report("adoption"), "Human reviewed")
        c.box.heartbeat(claim["id"], claim["token"])
        c.finish(claim, c.result("candidate", "build"))
        self.assertTrue(c.box.status()["dispatch_hold"])

    def test_pause_and_recovery_with_changed_rules_do_not_deadlock(self):
        c = self.case
        c.init()
        c.task()
        claim = c.box.claim("build", "builder")
        c.report("rules", "# New rules\n")
        c.box.pause("Human explicitly stopped old job")
        c.box.recover(claim["id"], "Human verified old owner stopped, no AI call was made", True)
        self.assertIsNone(c.box.claim("build", "new-worker"))
        new_hash = c.box.status()["dispatch_hold"]["observed_hash"]
        c.box.adopt_rules(new_hash, c.report("human-adoption"), "Human confirmed new rules")
        self.assertIsNotNone(c.box.claim("build", "new-worker"))


if __name__ == "__main__":
    unittest.main()
