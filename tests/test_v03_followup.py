"""Regressions derived from Claude's v0.3 review; all data is synthetic."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_handoff as base
import handoff


class V03FollowupTests(unittest.TestCase):
    def setUp(self):
        self.case = base.HandoffTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def test_completion_accepts_sentence_punctuation_but_not_questions(self):
        for tail in ("交付完成", "交付完成。", "交付完成.", "交付完成！", " 交付完成。  "):
            with self.subTest(tail=tail):
                self.assertTrue(handoff.complete(("# Report\n" + tail + "\n\n").encode()))
        for tail in ("交付完成？", "尚未交付完成。", "交付完成。还有工作", "交付完成\n# Still writing"):
            with self.subTest(tail=tail):
                self.assertFalse(handoff.complete(("# Report\n" + tail).encode()))
        self.assertTrue(handoff.complete(("# Report\n" + handoff.COMPLETE).encode()))

    def test_unmarked_stable_report_notifies_without_dispatching_or_ack(self):
        c = self.case
        (c.root / "deliveries/missing.md").write_text("# Done-looking report, no marker\n")
        with patch.object(handoff.time, "time", return_value=1000):
            self.assertFalse(c.cursor.check(60).get("notices"))
        with patch.object(handoff.time, "time", return_value=1119):
            self.assertFalse(c.cursor.check(60).get("notices"))
        with patch.object(handoff.time, "time", return_value=1120):
            result = c.cursor.check(60)
        self.assertEqual(result["status"], "attention")
        self.assertEqual(result["events"], [])
        self.assertEqual(result["notices"][0]["kind"], "unmarked_record")
        self.assertEqual(c.cursor.load()["seen"], {})

    def test_one_read_failure_retries_then_delivers_the_same_report(self):
        c = self.case
        event = c.publish()
        target = c.root / event["path"]
        original = Path.read_bytes
        failures = []
        sleeps = []

        def read(path):
            if path == target and not failures:
                failures.append(True)
                raise PermissionError("temporary read denial")
            return original(path)

        def sleep(seconds):
            sleeps.append(seconds)
            state = c.cursor.load()
            self.assertEqual(state["last_check"]["status"], "retrying")
            self.assertIn("temporary read denial", state["last_check"]["error"])
            self.assertEqual(state["seen"], {})

        with patch.object(Path, "read_bytes", new=read), patch.object(handoff.time, "sleep", side_effect=sleep):
            result = c.cursor.watch(interval=60)
        self.assertEqual(sleeps, [60])
        self.assertEqual(result["events"][0]["sha256"], event["sha256"])
        self.assertEqual(c.cursor.load()["scan_errors"], 0)

    def test_persistent_bad_encoding_stops_after_three_checks_with_diagnostics(self):
        c = self.case
        (c.root / "deliveries/broken.md").write_bytes(b"\xff\xfe")
        sleeps = []
        with patch.object(handoff.time, "sleep", side_effect=sleeps.append):
            result = c.cursor.watch(interval=60)
        self.assertEqual(sleeps, [60, 60])
        self.assertEqual(result["status"], "error")
        self.assertIn("broken.md", result["error"])
        self.assertEqual(result["consecutive_errors"], 3)
        state = c.cursor.load()
        self.assertEqual(state["last_check"]["status"], "error")
        self.assertEqual(state["seen"], {})
        self.assertIsNone(state["watcher"])

    def test_warning_ack_is_separate_hash_bound_and_completion_still_dispatches(self):
        c = self.case
        target = c.root / "deliveries/missing.md"
        target.write_text("# Report without final marker")
        with patch.object(handoff.time, "time", return_value=1000):
            c.cursor.check(60)
        with patch.object(handoff.time, "time", return_value=1120):
            notice = c.cursor.check(60)["notices"][0]
        with self.assertRaises(handoff.HandoffError):
            c.cursor.ack(notice["path"], notice["sha256"])
        with self.assertRaises(handoff.HandoffError):
            c.cursor.ack_warning(notice["path"], "0" * 64)
        c.cursor.ack_warning(notice["path"], notice["sha256"])
        restarted = handoff.Cursor(c.cursor.path)
        with patch.object(handoff.time, "time", return_value=1180):
            self.assertEqual(restarted.check(60)["notices"], [])
        self.assertEqual(restarted.load()["seen"], {})
        target.write_text("# Report now complete\n交付完成。\n")
        result = restarted.check(60)
        self.assertEqual(result["events"][0]["path"], notice["path"])
        self.assertNotEqual(result["events"][0]["sha256"], notice["sha256"])

    def test_changing_draft_restarts_warning_settle_period(self):
        c = self.case
        target = c.root / "deliveries/draft.md"
        target.write_text("# First draft")
        with patch.object(handoff.time, "time", return_value=1000):
            c.cursor.check(60)
        target.write_text("# Changed draft")
        with patch.object(handoff.time, "time", return_value=1110):
            self.assertFalse(c.cursor.check(60)["notices"])
        with patch.object(handoff.time, "time", return_value=1120):
            self.assertFalse(c.cursor.check(60)["notices"])
        with patch.object(handoff.time, "time", return_value=1230):
            self.assertEqual(c.cursor.check(60)["notices"][0]["kind"], "unmarked_record")

    def test_status_exposes_latest_unmarked_warning(self):
        c = self.case
        (c.root / "deliveries/missing.md").write_text("# No marker")
        with patch.object(handoff.time, "time", return_value=1000):
            c.cursor.check(60)
        with patch.object(handoff.time, "time", return_value=1120):
            c.cursor.check(60)
        process = subprocess.run([sys.executable, str(base.ROOT / "scripts/handoff.py"),
                                  "status", "--cursor", str(c.cursor.path)],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        state = json.loads(process.stdout)
        self.assertEqual(state["last_check"]["notices"][0]["kind"], "unmarked_record")

    def test_old_cursor_fields_upgrade_without_losing_seen_hashes(self):
        c = self.case
        event = c.publish()
        c.cursor.ack(event["path"], event["sha256"])
        state = c.cursor.load()
        for key in ("unmarked", "warning_seen", "scan_errors", "last_check"):
            state.pop(key, None)
        c.cursor.path.write_text(json.dumps(state))
        self.assertEqual(c.cursor.watch(once=True)["events"], [])
        self.assertEqual(c.cursor.load()["seen"][event["path"]], event["sha256"])

    def test_change_during_read_retries_without_dispatching_old_bytes(self):
        c = self.case
        event = c.publish()
        target = c.root / event["path"]
        original = Path.read_bytes
        changed = []

        def read(path):
            data = original(path)
            if path == target and not changed:
                changed.append(True)
                target.write_bytes(b"# New version, deliberately longer\n" + handoff.COMPLETE.encode())
            return data

        with patch.object(Path, "read_bytes", new=read), patch.object(handoff.time, "sleep") as sleep:
            result = c.cursor.watch(interval=60)
        sleep.assert_called_once_with(60)
        self.assertNotEqual(result["events"][0]["sha256"], event["sha256"])
        self.assertEqual(c.cursor.load()["seen"], {})

    def test_path_violation_is_not_treated_as_transient_io(self):
        c = self.case
        (c.root / "deliveries/escape.md").symlink_to(c.area / "outside.md")
        with patch.object(handoff.time, "sleep") as sleep:
            with self.assertRaises(handoff.HandoffError):
                c.cursor.watch(interval=60)
        sleep.assert_not_called()

    def test_cli_warning_ack_deduplicates_without_consuming_delivery(self):
        c = self.case
        target = c.root / "deliveries/missing.md"
        target.write_text("# Unmarked report")
        with patch.object(handoff.time, "time", return_value=1000):
            c.cursor.check(60)
        with patch.object(handoff.time, "time", return_value=1120):
            notice = c.cursor.check(60)["notices"][0]
        process = subprocess.run([sys.executable, str(base.ROOT / "scripts/handoff.py"),
                                  "ack-warning", "--cursor", str(c.cursor.path),
                                  "--path", notice["path"], "--sha256", notice["sha256"]],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse(json.loads(process.stdout)["delivery_acknowledged"])
        self.assertEqual(c.cursor.load()["seen"], {})


if __name__ == "__main__":
    unittest.main()
