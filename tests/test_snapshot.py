import json
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile

import test_relay as base
import snapshot


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.case = base.RelayTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.out = self.case.area / "snapshot"

    def export(self):
        result = snapshot.export(self.case.root, self.case.sha, self.out)
        return self.out / "snapshot.json", result

    def test_snapshot_is_committed_source_and_verifies_without_git(self):
        (self.case.root / "code.txt").write_text("unsaved work must not appear\n")
        manifest, result = self.export()
        destination = self.case.area / "extracted"
        with patch("snapshot.git", side_effect=AssertionError("Reviewer must not need Git")):
            snapshot.verify(manifest, self.case.sha, result["archive_sha256"])
            snapshot.extract(manifest, self.case.sha, result["archive_sha256"], destination)
        self.assertEqual((destination / "code.txt").read_text(), "base\n")
        self.assertFalse((destination / ".git").exists())

    def test_wrong_commit_or_archive_hash_is_rejected(self):
        manifest, result = self.export()
        for commit, sha in (("0" * 40, result["archive_sha256"]), (self.case.sha, "0" * 64)):
            with self.assertRaises(ValueError):
                snapshot.verify(manifest, commit, sha)

    def test_altered_manifest_content_is_rejected(self):
        manifest, result = self.export()
        result["files"][0]["sha256"] = "0" * 64
        manifest.write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError, "file content"):
            snapshot.verify(manifest, self.case.sha, result["archive_sha256"])

    def test_symlink_and_traversal_archives_are_rejected(self):
        for name, mode in (("../escape", 0o100644), ("link", 0o120777)):
            path = self.case.area / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.comment = self.case.sha.encode("ascii")
                info = zipfile.ZipInfo(name)
                info.external_attr = mode << 16
                z.writestr(info, "outside")
            with zipfile.ZipFile(path) as z:
                with self.assertRaises(ValueError):
                    snapshot.entries(z, self.case.sha)
        self.assertFalse((self.case.area / "escape").exists())

    def test_export_attributes_cannot_silently_omit_source(self):
        (self.case.root / ".gitattributes").write_text("code.txt export-ignore\n")
        self.case.git("add", ".gitattributes")
        self.case.git("commit", "-qm", "export attribute")
        commit = self.case.git("rev-parse", "HEAD").strip()
        with self.assertRaisesRegex(ValueError, "committed tree"):
            snapshot.export(self.case.root, commit, self.out)
        self.assertFalse(self.out.exists())

    def test_existing_extract_target_is_not_overwritten(self):
        manifest, result = self.export()
        destination = self.case.area / "existing"
        destination.mkdir()
        (destination / "personal.txt").write_text("keep")
        with self.assertRaisesRegex(ValueError, "already exists"):
            snapshot.extract(manifest, self.case.sha, result["archive_sha256"], destination)
        self.assertEqual((destination / "personal.txt").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
