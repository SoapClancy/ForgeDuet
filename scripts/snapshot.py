#!/usr/bin/env python3
"""Export/verify exact committed source for offline or browser-based review.

Checks integrity against a separately received expected archive hash. The commit
comment is provenance metadata, not a signature or independent Git object proof.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile

MAX_BYTES = 2 * 1024 ** 3
MAX_FILES = 100000


def need(value, message):
    if not value:
        raise ValueError(message)


def file_hash(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def entries(archive, commit):
    need(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit), "Expected a full lowercase commit SHA")
    need(archive.comment.decode("ascii").strip() == commit, "Archive commit comment differs from expected commit")
    files, names, size = [], set(), 0
    need(len(archive.infolist()) <= MAX_FILES, "Too many archive entries")
    for info in archive.infolist():
        name = info.filename.rstrip("/")
        parts = PurePosixPath(name).parts
        need(name and not name.startswith("/") and "\\" not in name and all(p not in ("..", ".git") for p in parts),
             "Unsafe archive path")
        need(not info.flag_bits & 1, "Encrypted archives are unsupported")
        mode = (info.external_attr >> 16) & 0o170000
        need(mode in (0, 0o100000, 0o040000), "Symlinks/special files are unsupported; use a worktree")
        if info.is_dir():
            continue
        key = unicodedata.normalize("NFC", name).casefold()
        need(key not in names, "Duplicate or case/Unicode-colliding path")
        names.add(key)
        size += info.file_size
        need(size <= MAX_BYTES, "Snapshot exceeds the 2 GiB uncompressed limit")
        sha, blob = hashlib.sha256(), hashlib.new("sha1" if len(commit) == 40 else "sha256")
        blob.update(("blob {}\0".format(info.file_size)).encode("ascii"))
        count = 0
        with archive.open(info) as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                count += len(chunk)
                need(count <= info.file_size, "Archive size mismatch")
                sha.update(chunk)
                blob.update(chunk)
        need(count == info.file_size, "Archive truncated")
        executable = bool((info.external_attr >> 16) & 0o111)
        files.append({"path": name, "size": count, "sha256": sha.hexdigest(),
                      "git_blob": blob.hexdigest(), "mode": "100755" if executable else "100644"})
    return sorted(files, key=lambda item: item["path"])


def export(root, commit, destination):
    root, destination = Path(root).resolve(), Path(destination).absolute()
    need(not destination.exists(), "Destination already exists; snapshots are immutable")
    need(git(root, "cat-file", "-t", commit).strip() == b"commit", "Not a commit")
    need(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit), "Use a full commit SHA")
    tree = {}
    for item in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
        if not item:
            continue
        header, name = item.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        need(kind == "blob" and mode in ("100644", "100755"), "Submodules/symlinks require a worktree or separate evidence")
        tree[name.decode("utf-8")] = (mode, oid)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=str(destination.parent)) as temp:
        folder = Path(temp)
        archive_path = folder / "source.zip"
        git(root, "archive", "--format=zip", "--output=" + str(archive_path), commit)
        with zipfile.ZipFile(archive_path) as archive:
            files = entries(archive, commit)
        need({f["path"]: (f["mode"], f["git_blob"]) for f in files} == tree,
             "Export differs from committed tree (check export-ignore/export-subst attributes)")
        manifest = {"schema_version": 1, "commit": commit, "archive": "source.zip",
                    "archive_sha256": file_hash(archive_path), "files": files}
        (folder / "snapshot.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        need(not destination.exists(), "Destination appeared during export")
        os.rename(folder, destination)
    return manifest


def verify(manifest_path, expected_commit, expected_archive_hash):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    need(manifest.get("schema_version") == 1 and manifest.get("commit") == expected_commit, "Manifest commit/version mismatch")
    need(manifest.get("archive") == "source.zip", "Unexpected archive filename")
    archive_path = manifest_path.parent / "source.zip"
    need(not archive_path.is_symlink(), "Archive cannot be a symlink")
    need(file_hash(archive_path) == manifest.get("archive_sha256") == expected_archive_hash,
         "Archive SHA-256 differs from the separately supplied expected value")
    with zipfile.ZipFile(archive_path) as archive:
        need(entries(archive, expected_commit) == manifest.get("files"), "Manifest file content differs from archive")
    return manifest


def extract(manifest_path, expected_commit, expected_archive_hash, destination):
    manifest = verify(manifest_path, expected_commit, expected_archive_hash)
    destination = Path(destination).absolute()
    need(not destination.exists(), "Extraction destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".review-", dir=str(destination.parent)) as temp:
        folder = Path(temp)
        with zipfile.ZipFile(Path(manifest_path).parent / "source.zip") as archive:
            for item in manifest["files"]:
                path = folder / item["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item["path"]) as source, path.open("xb") as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                need(file_hash(path) == item["sha256"], "Archive changed while extracting")
                path.chmod(0o755 if item["mode"] == "100755" else 0o644)
        need(not destination.exists(), "Destination appeared during extraction")
        os.rename(folder, destination)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("export")
    create.add_argument("--project", required=True)
    create.add_argument("--commit", required=True)
    create.add_argument("--out", required=True)
    for command in ("verify", "extract"):
        p = sub.add_parser(command)
        p.add_argument("--manifest", required=True)
        p.add_argument("--expected-commit", required=True)
        p.add_argument("--expected-sha256", required=True)
        if command == "extract":
            p.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        if args.command == "export":
            result = export(args.project, args.commit, args.out)
        elif args.command == "verify":
            result = verify(args.manifest, args.expected_commit, args.expected_sha256)
        else:
            result = extract(args.manifest, args.expected_commit, args.expected_sha256, args.out)
        print(json.dumps({k: result[k] for k in ("commit", "archive_sha256")}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        print("Snapshot: " + str(exc), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
