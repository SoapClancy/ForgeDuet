#!/usr/bin/env python3
"""Local Markdown handoff: cooperative writer lock, publication, durable polling.

No model calls, shell execution, peer command execution, or GUI wakeup here.
Run watch in a client that actually resumes its session on background completion,
or use a native scheduler / the separately configured relay CLI adapters.
"""
import argparse
import contextlib
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import uuid

COMPLETE = "<!-- FORGEDUET_COMPLETE -->"
INPUTS = {"build": "reviews", "review": "deliveries"}


class HandoffError(Exception):
    pass


class ScanError(HandoffError):
    """A failed peer-file observation, not corrupt cursor state or a path violation."""


def require(ok, message):
    if not ok:
        raise HandoffError(message)


def stamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def line(value):
    require(isinstance(value, str) and bool(value.strip()) and
            not any(c in value for c in "\r\n\x00"), "Expected nonempty single-line text")
    return value


def root_path(value):
    path = Path(value).absolute()
    require(path.is_dir() and path.resolve() == path, "Root must be an existing real directory")
    return path


def inside(root, relative):
    part = Path(relative)
    require(not part.is_absolute() and part.parts and
            all(p not in ("..", ".lock") for p in part.parts), "Invalid shared relative path")
    path = root / part
    require(path.resolve().is_relative_to(root), "Shared path escapes root")
    for candidate in (path, *path.parents):
        if candidate == root:
            break
        require(not candidate.is_symlink(), "Symlink in shared path")
    return path


def sync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    require(not path.is_symlink(), "Refusing symlink state")
    fd, name = tempfile.mkstemp(prefix=".handoff-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, str(path))
        sync_dir(path.parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Writer:
    """mkdir .lock interoperates with the earlier WristFiles shell helper."""
    def __init__(self, root):
        self.root = root_path(root)
        self.lock = self.root / ".lock"

    def status(self):
        require(not self.lock.is_symlink(), "Symlink lock")
        if not self.lock.exists():
            return None
        try:
            owner = self.lock / "owner"
            require(not owner.is_symlink(), "Symlink lock owner")
            return owner.read_text(encoding="utf-8")
        except FileNotFoundError:
            return "Lock exists; owner metadata not yet written or unavailable"

    def acquire(self, owner, purpose, wait=0):
        line(owner), line(purpose)
        require(math.isfinite(wait) and wait >= 0, "Invalid lock wait")
        end = time.monotonic() + wait
        token = uuid.uuid4().hex
        while True:
            try:
                self.lock.mkdir()
                break
            except FileExistsError:
                if time.monotonic() >= end:
                    raise HandoffError("Busy; never breaking peer lock: " + str(self.status()))
                time.sleep(min(0.1, max(0, end - time.monotonic())))
        # If metadata creation fails, leave the lock for explicit recovery.
        with (self.lock / "owner").open("x", encoding="utf-8") as out:
            out.write("who: {}\npurpose: {}\nsince: {}\ntoken: {}\n".format(owner, purpose, stamp(), token))
            out.flush()
            os.fsync(out.fileno())
        sync_dir(self.lock)
        return token

    def check(self, owner, token):
        fields = dict(row.split(": ", 1) for row in (self.status() or "").splitlines() if ": " in row)
        require(bool(token) and fields.get("who") == owner and fields.get("token") == token,
                "Not this lock's owner/token; preserve peer lock")

    def release(self, owner, token):
        self.check(owner, token)
        require({p.name for p in self.lock.iterdir()} == {"owner"},
                "Unexpected lock contents; retain for human recovery")
        (self.lock / "owner").unlink()
        self.lock.rmdir()

    def log(self, owner, token, message):
        self.check(owner, token)
        line(message)
        fd = os.open(str(self.root / "updates.log"),
                     os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as out:
            out.write("{} | {} | {}\n".format(stamp(), line(owner), message))
            out.flush()
            os.fsync(out.fileno())

    def publish(self, owner, token, relative, body):
        self.check(owner, token)
        target = inside(self.root, relative)
        require(target.suffix == ".md", "Published reports must be Markdown")
        require(target.parent.is_dir(), "Create role directories during setup")
        require(bool(body.strip()), "Empty report")
        data = ("- Author: {}\n- Created: {}\n\n{}\n\n交付完成\n{}\n".format(
            line(owner), stamp(), body.rstrip(), COMPLETE)).encode("utf-8")
        fd, temporary = tempfile.mkstemp(prefix=".publish-", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            # Atomic temp -> final publication, with no overwrite of immutable records.
            os.link(temporary, str(target))
            sync_dir(target.parent)
        finally:
            os.unlink(temporary)
        sha = hashlib.sha256(data).hexdigest()
        self.log(owner, token, "published {} sha256={}".format(relative, sha))
        return {"path": relative, "sha256": sha}


def complete(data):
    lines = data.decode("utf-8").rstrip().splitlines()
    tail = lines[-1].strip() if lines else ""
    # Keep the terminal declaration precise; questions/unfinished prose are not completion.
    return tail == COMPLETE or tail in ("交付完成", "交付完成。", "交付完成.",
                                        "交付完成．", "交付完成!", "交付完成！")


def inspect_records(root, role):
    directory = inside(root, INPUTS[role])
    if not directory.is_dir():
        raise ScanError("Missing peer directory: " + str(directory))
    try:
        paths = sorted(directory.iterdir())
    except OSError as exc:
        raise ScanError("Cannot list {}: {}".format(directory, exc)) from exc
    result, unmarked = {}, {}
    for path in paths:
        if path.name.startswith(".") or path.suffix != ".md":
            continue
        inside(root, str(path.relative_to(root)))
        try:
            before = path.stat()
            data = path.read_bytes()
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_ino, after.st_size, after.st_mtime_ns):
                raise ScanError("Record changed while reading; retry: " + str(path))
            destination = result if complete(data) else unmarked
            destination[str(path.relative_to(root))] = hashlib.sha256(data).hexdigest()
        except (OSError, UnicodeError) as exc:
            raise ScanError("Cannot read {}: {}".format(path, exc)) from exc
    return result, unmarked


def scan(root, role):
    return inspect_records(root, role)[0]


class Cursor:
    """Acknowledgement is explicit: a watcher exit never consumes the work."""
    def __init__(self, path):
        self.path = Path(path).absolute()
        require(self.path.parent.resolve() == self.path.parent and self.path.parent.is_dir(),
                "Cursor parent must be an existing real directory")

    @contextlib.contextmanager
    def guard(self, suffix=".guard", nonblock=False):
        fd = os.open(str(self.path) + suffix,
                     os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "a+") as out:
            try:
                fcntl.flock(out.fileno(), fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblock else 0))
            except BlockingIOError as exc:
                raise HandoffError("Another watcher already owns this cursor") from exc
            try:
                yield
            finally:
                fcntl.flock(out.fileno(), fcntl.LOCK_UN)

    def load(self):
        require(not self.path.is_symlink(), "Symlink cursor")
        value = json.loads(self.path.read_text(encoding="utf-8"))
        require(isinstance(value, dict) and value.get("schema") == 1 and value.get("role") in INPUTS and
                isinstance(value.get("seen"), dict) and isinstance(value.get("paused"), bool),
                "Invalid cursor; retain rather than resetting")
        # Additive v0.3.1 fields: preserve v0.3 handled hashes and pause state.
        for key in ("unmarked", "warning_seen"):
            value.setdefault(key, {})
            require(isinstance(value[key], dict), "Invalid cursor diagnostics; preserve state")
        value.setdefault("scan_errors", 0)
        value.setdefault("last_check", None)
        require(type(value["scan_errors"]) is int and value["scan_errors"] >= 0 and
                (value["last_check"] is None or isinstance(value["last_check"], dict)),
                "Invalid cursor diagnostics; preserve state")
        require(all(isinstance(item, dict) and isinstance(item.get("sha256"), str) and
                    type(item.get("first_seen")) in (int, float) and math.isfinite(item["first_seen"])
                    for item in value["unmarked"].values()), "Invalid unmarked state; preserve cursor")
        return value

    def init(self, root, role, baseline=False):
        root = root_path(root)
        with self.guard():
            require(not self.path.exists(), "Cursor already exists; resume it instead")
            state = {"schema": 1, "root": str(root), "role": role,
                     "seen": scan(root, role) if baseline else {}, "paused": False,
                     "reason": None, "watcher": None}
            atomic_json(self.path, state)
            return state

    def ack(self, relative, expected):
        with self.guard():
            state = self.load()
            observed = scan(root_path(state["root"]), state["role"])
            require(observed.get(relative) == expected, "Record missing, incomplete or hash changed; not acknowledged")
            state["seen"][relative] = expected
            atomic_json(self.path, state)

    def ack_warning(self, relative, expected):
        """Deduplicate an inspected warning; never mark a delivery handled."""
        with self.guard():
            state = self.load()
            _, unmarked = inspect_records(root_path(state["root"]), state["role"])
            require(unmarked.get(relative) == expected and
                    state["unmarked"].get(relative, {}).get("sha256") == expected,
                    "Warning missing or hash changed; not acknowledged")
            state["warning_seen"][relative] = expected
            atomic_json(self.path, state)

    def control(self, paused, reason):
        with self.guard():
            state = self.load()
            state.update(paused=paused, reason=line(reason))
            if not paused:
                state["scan_errors"] = 0  # Explicit resume starts a fresh retry budget, retaining last error.
            atomic_json(self.path, state)
            return state

    def check(self, interval, unmarked_after=120, max_scan_errors=3):
        require(math.isfinite(unmarked_after) and unmarked_after >= 0 and
                type(max_scan_errors) is int and max_scan_errors >= 1, "Invalid scan policy")
        with self.guard():
            state = self.load()
            if state["paused"]:
                return {"status": "paused", "reason": state["reason"], "events": [], "notices": []}
            try:
                current, unmarked = inspect_records(root_path(state["root"]), state["role"])
            except ScanError as exc:
                state["scan_errors"] += 1
                state["last_scan_error"] = {"message": str(exc), "at": stamp()}
                result = {"status": "error" if state["scan_errors"] >= max_scan_errors else "retrying",
                          "error": str(exc), "consecutive_errors": state["scan_errors"],
                          "events": [], "notices": []}
            else:
                state["scan_errors"] = 0
                events = [{"path": p, "sha256": h,
                           "kind": "mutated_record" if p in state["seen"] else "new_record"}
                          for p, h in current.items() if state["seen"].get(p) != h]
                now, pending, notices = time.time(), {}, []
                for path, sha in unmarked.items():
                    item = state["unmarked"].get(path, {})
                    if item.get("sha256") != sha:
                        item = {"sha256": sha, "first_seen": now}
                    pending[path] = item
                    age = max(0, now - item["first_seen"])
                    if age >= unmarked_after and state["warning_seen"].get(path) != sha:
                        notices.append({"kind": "unmarked_record", "path": path,
                                        "sha256": sha, "stable_seconds": age})
                state["unmarked"] = pending
                state["warning_seen"] = {p: h for p, h in state["warning_seen"].items() if p in pending}
                result = {"status": "changed" if events else ("attention" if notices else "waiting"),
                          "events": events, "notices": notices}
            state["last_check"], state["last_check_at"] = result, stamp()
            state["watcher"] = {"pid": os.getpid(), "heartbeat": stamp(), "interval_seconds": interval}
            atomic_json(self.path, state)
            return result

    def watch(self, interval=60, once=False, unmarked_after=120, max_scan_errors=3):
        require(math.isfinite(interval) and interval > 0, "Invalid poll interval")
        with self.guard(".watcher", nonblock=True):
            try:
                while True:
                    event = self.check(interval, unmarked_after, max_scan_errors)
                    if once or event["status"] not in ("waiting", "retrying"):
                        return event
                    time.sleep(interval)
            finally:
                with self.guard():
                    state = self.load()
                    state["watcher"] = None
                    atomic_json(self.path, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("lock", "unlock", "log", "publish", "lock-status"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--root", required=True)
        if name != "lock-status":
            cmd.add_argument("--owner", required=True)
        if name in ("unlock", "log", "publish"):
            cmd.add_argument("--token", required=True)
        if name == "lock":
            cmd.add_argument("--purpose", required=True)
            cmd.add_argument("--wait", type=float, default=0)
        if name == "log":
            cmd.add_argument("--message", required=True)
        if name == "publish":
            cmd.add_argument("--path", required=True)
            cmd.add_argument("--source", required=True)
    for name in ("init", "watch", "ack", "ack-warning", "stop", "resume", "status"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--cursor", required=True)
        if name == "init":
            cmd.add_argument("--root", required=True)
            cmd.add_argument("--role", required=True, choices=INPUTS)
            cmd.add_argument("--baseline-existing", action="store_true")
        if name == "watch":
            cmd.add_argument("--interval", type=float, default=60)
            cmd.add_argument("--once", action="store_true")
            cmd.add_argument("--unmarked-after", type=float, default=120)
            cmd.add_argument("--max-scan-errors", type=int, default=3)
        if name in ("ack", "ack-warning"):
            cmd.add_argument("--path", required=True)
            cmd.add_argument("--sha256", required=True)
        if name in ("stop", "resume"):
            cmd.add_argument("--reason", required=True)
    args = parser.parse_args()
    try:
        if args.command in ("lock", "unlock", "log", "publish", "lock-status"):
            writer = Writer(args.root)
            if args.command == "lock":
                answer = {"token": writer.acquire(args.owner, args.purpose, args.wait)}
            elif args.command == "lock-status":
                answer = {"owner": writer.status()}
            elif args.command == "unlock":
                writer.release(args.owner, args.token)
                answer = {"released": True}
            elif args.command == "log":
                writer.log(args.owner, args.token, args.message)
                answer = {"logged": True}
            else:
                answer = writer.publish(args.owner, args.token, args.path,
                                        Path(args.source).read_text(encoding="utf-8"))
        else:
            cursor = Cursor(args.cursor)
            if args.command == "init":
                answer = cursor.init(args.root, args.role, args.baseline_existing)
            elif args.command == "watch":
                answer = cursor.watch(args.interval, args.once, args.unmarked_after, args.max_scan_errors)
            elif args.command == "ack":
                cursor.ack(args.path, args.sha256)
                answer = {"acknowledged": True}
            elif args.command == "ack-warning":
                cursor.ack_warning(args.path, args.sha256)
                answer = {"warning_acknowledged": True, "delivery_acknowledged": False}
            elif args.command in ("stop", "resume"):
                answer = cursor.control(args.command == "stop", args.reason)
            else:
                with cursor.guard():
                    answer = cursor.load()
        print(json.dumps(answer, ensure_ascii=False))
        return {"paused": 3, "error": 2}.get(answer.get("status"), 0)
    except (HandoffError, OSError, ValueError, UnicodeError) as exc:
        print("ForgeDuet handoff: " + str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
