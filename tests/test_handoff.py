"""Real local processes and synthetic Markdown only; no model/client invocation."""
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import handoff


def contender(root, ready, queue, release):
    ready.wait(10)
    writer = handoff.Writer(root)
    try:
        token = writer.acquire("worker-" + str(os.getpid()), "race")
    except handoff.HandoffError:
        queue.put(False)
        return
    queue.put(True)
    release.wait(10)
    writer.release("worker-" + str(os.getpid()), token)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="forgeduet-handoff-")
        self.addCleanup(self.temp.cleanup)
        self.area = Path(self.temp.name).resolve()
        self.root = self.area / "records"
        self.root.mkdir()
        for name in ("deliveries", "reviews"):
            (self.root / name).mkdir()
        self.writer = handoff.Writer(self.root)
        self.cursor = handoff.Cursor(self.area / "review.json")
        self.cursor.init(self.root, "review")

    def publish(self, path="deliveries/one.md", body="# Full synthetic delivery\n", owner="fixture build"):
        token = self.writer.acquire(owner, "publish fixture")
        try:
            return self.writer.publish(owner, token, path, body)
        finally:
            self.writer.release(owner, token)

    def test_nonholder_cannot_log_publish_or_release(self):
        token = self.writer.acquire("owner", "test")
        for owner, supplied in (("other", token), ("owner", "wrong")):
            for action in (lambda: self.writer.log(owner, supplied, "no"),
                           lambda: self.writer.publish(owner, supplied, "reviews/no.md", "no"),
                           lambda: self.writer.release(owner, supplied)):
                with self.assertRaises(handoff.HandoffError):
                    action()
        self.assertTrue(self.writer.lock.exists())
        self.assertFalse((self.root / "updates.log").exists())
        self.writer.release("owner", token)

    def test_six_processes_have_one_writer(self):
        ctx = multiprocessing.get_context("fork")
        ready, release, queue = ctx.Event(), ctx.Event(), ctx.Queue()
        processes = [ctx.Process(target=contender, args=(self.root, ready, queue, release)) for _ in range(6)]
        for process in processes:
            process.start()
        try:
            ready.set()
            self.assertEqual(sum(queue.get(timeout=10) for _ in processes), 1)
        finally:
            release.set()
            for process in processes:
                process.join(10)
                self.assertEqual(process.exitcode, 0)

    def test_legacy_lock_and_missing_owner_are_never_broken(self):
        self.writer.lock.mkdir()
        with self.assertRaisesRegex(handoff.HandoffError, "never breaking"):
            self.writer.acquire("review", "publish")
        (self.writer.lock / "owner").write_text("who: Claude\npurpose: records\nsince: old\n")
        with self.assertRaisesRegex(handoff.HandoffError, "Claude"):
            self.writer.acquire("review", "publish")
        with self.assertRaises(handoff.HandoffError):
            self.writer.release("Claude", "invented")
        self.assertTrue(self.writer.lock.is_dir())

    def test_legacy_mkdir_cannot_take_python_lock(self):
        token = self.writer.acquire("review session unique", "publish")
        result = subprocess.run(["mkdir", str(self.writer.lock)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("who: review session unique", self.writer.status())
        self.writer.release("review session unique", token)

    def test_publish_is_complete_immutable_and_logged_with_hash(self):
        event = self.publish()
        data = (self.root / event["path"]).read_bytes()
        self.assertTrue(handoff.complete(data))
        self.assertEqual(hashlib.sha256(data).hexdigest(), event["sha256"])
        self.assertIn(b"Author: fixture build", data)
        self.assertIn("sha256=" + event["sha256"], (self.root / "updates.log").read_text())
        with self.assertRaises(FileExistsError):
            self.publish(body="different")
        self.assertEqual((self.root / event["path"]).read_bytes(), data)

    def test_partial_hidden_and_unmarked_files_do_not_wake(self):
        (self.root / "deliveries/.one.tmp").write_text("half")
        (self.root / "deliveries/partial.md").write_text("# Looks finished, but no marker")
        (self.root / "deliveries/.hidden.md").write_text(handoff.COMPLETE)
        self.assertEqual(self.cursor.watch(once=True)["status"], "waiting")
        (self.root / "deliveries/partial.md").write_text("# Done\n交付完成\n")
        self.assertEqual(self.cursor.watch(once=True)["events"][0]["path"], "deliveries/partial.md")

    def test_exit_does_not_consume_and_hash_bound_ack_survives_restart(self):
        event = self.publish()
        first = self.cursor.watch(once=True)
        restarted = handoff.Cursor(self.cursor.path)
        self.assertEqual(restarted.watch(once=True), first)
        with self.assertRaises(handoff.HandoffError):
            restarted.ack(event["path"], "0" * 64)
        restarted.ack(event["path"], event["sha256"])
        self.assertEqual(self.cursor.watch(once=True)["events"], [])

    def test_mutation_after_ack_is_reported_not_silently_consumed(self):
        event = self.publish()
        self.cursor.ack(event["path"], event["sha256"])
        (self.root / event["path"]).write_text("# Mutated\n" + handoff.COMPLETE)
        result = self.cursor.watch(once=True)
        self.assertEqual(result["events"][0]["kind"], "mutated_record")

    def test_explicit_historical_baseline_and_role_filter(self):
        self.publish()
        self.publish("reviews/review.md", owner="review")
        second = handoff.Cursor(self.area / "build.json")
        second.init(self.root, "build", baseline=True)
        self.assertEqual(second.watch(once=True)["events"], [])
        self.publish("deliveries/new.md")
        self.assertEqual(second.watch(once=True)["events"], [])
        self.publish("reviews/new.md", owner="review")
        self.assertEqual(second.watch(once=True)["events"][0]["path"], "reviews/new.md")

    def test_stop_resume_preserves_unhandled_work(self):
        self.publish()
        self.cursor.control(True, "human decision required")
        self.assertEqual(self.cursor.watch(once=True)["status"], "paused")
        self.cursor.control(False, "human resolved issue")
        self.assertEqual(self.cursor.watch(once=True)["status"], "changed")

    def test_corrupt_cursor_and_unreadable_folder_are_not_reset(self):
        self.cursor.path.write_text("broken")
        with self.assertRaises(ValueError):
            self.cursor.watch(once=True)
        self.assertEqual(self.cursor.path.read_text(), "broken")
        self.cursor.path.unlink()
        self.cursor.init(self.root, "review")
        (self.root / "deliveries").rmdir()
        # v0.3.1 retries peer scan failures; corrupt cursor behavior above stays fatal.
        first = self.cursor.watch(once=True)
        self.assertEqual(first["status"], "retrying")
        self.assertIn("Missing peer", first["error"])
        self.assertEqual(self.cursor.watch(once=True)["status"], "retrying")
        self.assertEqual(self.cursor.watch(once=True)["status"], "error")
        self.assertTrue(self.cursor.path.exists())

    def test_paths_and_log_symlinks_cannot_escape(self):
        token = self.writer.acquire("owner", "test")
        try:
            for path in ("../escape.md", "/absolute.md", ".lock/overwrite.md"):
                with self.assertRaises(handoff.HandoffError):
                    self.writer.publish("owner", token, path, "no")
            (self.root / "deliveries/escape.md").symlink_to(self.area / "outside.md")
            with self.assertRaises(handoff.HandoffError):
                self.writer.publish("owner", token, "deliveries/escape.md", "no")
            (self.root / "updates.log").symlink_to(self.area / "outside.log")
            with self.assertRaises(OSError):
                self.writer.log("owner", token, "no")
            self.assertFalse((self.area / "outside.log").exists())
        finally:
            self.writer.release("owner", token)

    def test_failed_atomic_publication_does_not_leave_final_or_log(self):
        with patch.object(handoff.os, "link", side_effect=OSError("fault before publication")):
            with self.assertRaises(OSError):
                self.publish()
        self.assertEqual(list((self.root / "deliveries").iterdir()), [])
        self.assertFalse((self.root / "updates.log").exists())

    def test_background_process_is_quiet_then_exits_on_delivery(self):
        process = subprocess.Popen([sys.executable, str(ROOT / "scripts/handoff.py"), "watch",
                                    "--cursor", str(self.cursor.path), "--interval", "0.02"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while self.cursor.load()["watcher"] is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertIsNotNone(self.cursor.load()["watcher"])
            self.assertIsNone(process.poll(), "Idle watch must not complete and wake the client")
            with self.assertRaisesRegex(handoff.HandoffError, "Another watcher"):
                self.cursor.watch(once=True)
            event = self.publish()
            out, err = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, err)
            self.assertEqual(json.loads(out)["events"][0]["sha256"], event["sha256"])
            self.assertEqual(self.cursor.load()["seen"], {}, "Wake is not acknowledgement")
            self.assertIsNone(self.cursor.load()["watcher"])
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=5)

    def test_two_roles_exchange_without_a_human_courier(self):
        build = handoff.Cursor(self.area / "build.json")
        build.init(self.root, "build")
        delivery = self.publish(body="# Candidate\nSHA: " + "a" * 40)
        observed = self.cursor.watch(once=True)["events"][0]
        self.assertEqual(observed["sha256"], delivery["sha256"])
        review = self.publish("reviews/one.md", "# Approved\nSHA: " + "a" * 40, "fixture review")
        self.cursor.ack(delivery["path"], delivery["sha256"])
        self.assertEqual(build.watch(once=True)["events"][0]["sha256"], review["sha256"])
        accepted = self.publish("deliveries/accepted.md", "# Accepted\nSHA: " + "a" * 40)
        build.ack(review["path"], review["sha256"])
        self.assertEqual(self.cursor.watch(once=True)["events"][0]["sha256"], accepted["sha256"])
        self.cursor.ack(accepted["path"], accepted["sha256"])
        self.cursor.control(True, "same SHA approved and accepted")
        build.control(True, "same SHA approved and accepted")
        self.assertEqual(self.cursor.watch(once=True)["status"], "paused")
        self.assertEqual(build.watch(once=True)["status"], "paused")


if __name__ == "__main__":
    unittest.main()
