#!/usr/bin/env python3
"""ForgeDuet local transport. Stdlib only; macOS/Linux, local filesystem.

Protocol state is deliberately not an authorization or hostile-process boundary.
Never execute peer content. Adapter argv comes only from frozen human config.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import uuid

VERSION = 2
RELAY_VERSION = "0.3.0"
RUNTIME_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ROLES = ("build", "review")
KINDS = {
    "task": ("human", "build"),
    "candidate": ("build", "review"),
    "changes_requested": ("review", "build"),
    "review_approved": ("review", "build"),
    "build_accepted": ("build", "review"),
    "needs_human": (None, "human"),
}
RESPONSES = {
    "task": {"candidate", "needs_human"},
    "candidate": {"changes_requested", "review_approved", "needs_human"},
    "changes_requested": {"candidate", "needs_human"},
    "review_approved": {"build_accepted", "candidate", "needs_human"},
}


class RelayError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise RelayError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def packed(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise RelayError("Cannot read JSON {}: {}. Preserve it; do not reset.".format(path, exc)) from exc


def atomic(path, value):
    """Replace one file durably. Readers see old or new bytes, never a prefix."""
    atomic_bytes(path, packed(value))


def atomic_bytes(path, data):
    path = Path(path)
    require(not path.is_symlink(), "Refusing symlink state destination: {}".format(path))
    fd, name = tempfile.mkstemp(prefix=".write-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, str(path))
        parent_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def positive(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0, label + " must be positive")


def absolute_dir(value, label):
    require(isinstance(value, str) and Path(value).is_absolute(), label + " must be absolute")
    path = Path(value).resolve()
    require(path.is_dir(), label + " must exist")
    return path


def relative_file(root, relative):
    root = Path(root).resolve()
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(),
            "Report/rules path must be project-relative")
    require(".." not in Path(relative).parts, "Parent traversal is forbidden")
    path = (root / relative).resolve()
    require(path != root and root in path.parents, "Path escapes project root")
    require(path.is_file() and path.suffix.lower() == ".md", "Expected a readable Markdown file")
    return path


def check_sha(root, sha):
    require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha),
            "Use a full lowercase commit SHA")
    answer = subprocess.run(["git", "-C", str(root), "cat-file", "-t", sha],
                            capture_output=True, text=True)
    require(answer.returncode == 0 and answer.stdout.strip() == "commit",
            "SHA does not identify a commit in the configured project")


def verification(setting):
    # Accept the old config spelling honestly, without silently promoting false.
    return setting.get("verification", "verified" if setting.get("settings_verified") is True else "unavailable")


def validate_config(cfg):
    require(isinstance(cfg, dict) and cfg.get("schema_version") == VERSION, "Unsupported configuration version")
    require(cfg.get("setup_confirmed") is True and bool(cfg.get("authorization_source")),
            "Record actual human choices and authority before init")
    root = absolute_dir(cfg.get("project_root"), "project_root")
    require(isinstance(cfg.get("report_language"), str) and bool(cfg["report_language"].strip()),
            "Choose the report/handoff language explicitly")
    relative_file(root, cfg.get("rules_file"))
    mailbox = cfg.get("mailbox")
    require(isinstance(mailbox, str) and Path(mailbox).is_absolute(), "mailbox must be absolute")
    perms = cfg.get("permissions", {})
    require(perms.get("confirmed") is True, "Confirm actual permission boundaries first")
    for key in ("read_roots", "write_roots", "execution"):
        require(isinstance(perms.get(key), list), "permissions." + key + " must be a list")
    require(isinstance(perms.get("network"), str) and bool(perms["network"]), "Record network boundary")
    budgets = cfg.get("budgets", {})
    require(budgets.get("confirmed") is True, "Ask about budgets, including a deliberate no-cap choice")
    for key in ("tokens", "usd", "wall_seconds", "max_rounds", "max_stall_reviews"):
        require(key in budgets, "Missing budget choice: " + key)
        if budgets[key] is not None:
            positive(budgets[key], "budget " + key)
    for key in ("tokens", "max_rounds", "max_stall_reviews"):
        require(budgets[key] is None or isinstance(budgets[key], int), key + " must be an integer or null")
    positive(cfg.get("lease_seconds", 120), "lease_seconds")
    positive(cfg.get("poll_seconds", 60), "poll_seconds")
    require(cfg.get("lease_seconds", 120) >= 10, "lease_seconds must be at least 10")
    roles = cfg.get("roles", {})
    for role in ROLES:
        setting = roles.get(role, {})
        for key in ("provider", "model", "effort"):
            require(isinstance(setting.get(key), str) and bool(setting[key].strip()),
                    "Explicit " + role + " " + key + " is required")
        require(verification(setting) in ("verified", "self_reported", "unavailable"),
                role + " verification must be verified, self_reported, or unavailable")
        if verification(setting) == "verified":
            require(isinstance(setting.get("verification_source"), str) and bool(setting["verification_source"].strip()),
                    role + " verified settings require a verification_source")
        absolute_dir(setting.get("workdir"), role + " workdir")
        skill = setting.get("skill_file")
        require(isinstance(skill, str) and Path(skill).is_absolute() and Path(skill).is_file(),
                role + " skill_file must be an existing absolute path")
        argv = setting.get("adapter_argv", [])
        require(isinstance(argv, list) and all(isinstance(a, str) and a for a in argv),
                "adapter_argv must be a trusted argv list")
        if argv:
            require(Path(argv[0]).is_absolute() and os.access(argv[0], os.X_OK),
                    "Adapter executable must be an absolute executable path")
    require(Path(roles["build"]["workdir"]).resolve() != Path(roles["review"]["workdir"]).resolve(),
            "Build and review must have separate working directories")
    return root


class Mailbox:
    def __init__(self, path):
        original = Path(path)
        require(not original.is_symlink(), "Mailbox cannot be a symlink")
        self.path = original.resolve()

    @staticmethod
    def init(config_path):
        source = Path(config_path).resolve()
        cfg = read_json(source)
        root = validate_config(cfg)
        box = Mailbox(cfg["mailbox"])
        box.path.mkdir(parents=True, exist_ok=True)
        with box.lock():
            require(not (box.path / "state.json").exists(), "Mailbox already initialized; use another directory for a new run")
            require(not (box.path / "state.json").is_symlink(), "State path is a symlink")
            for folder in ("messages", "jobs", "logs", "rules"):
                p = box.path / folder
                require(not p.is_symlink(), "Mailbox subdirectory is a symlink")
                p.mkdir(exist_ok=True)
            now = time.time()
            rules_bytes = relative_file(root, cfg["rules_file"]).read_bytes()
            rules_hash = digest(rules_bytes)
            atomic_bytes(box.path / "rules" / (rules_hash + ".md"), rules_bytes)
            state = {"schema_version": VERSION, "run_id": uuid.uuid4().hex,
                     "relay_version": RELAY_VERSION, "relay_sha256": RUNTIME_SHA256,
                     "phase": "working", "reason": None, "config": cfg,
                     "config_source": str(source), "config_hash": digest(packed(cfg)),
                     "rules_hash": rules_hash, "dispatch_hold": None, "rules_history": [],
                     "created_at": now, "sequence": 0, "rounds": 0, "current_sha": None,
                     "review_approved_sha": None, "build_accepted_sha": None,
                     "jobs": {}, "dedupe": {}, "usage": {"tokens": 0, "usd": 0.0},
                     "unknown_usage": {"tokens": False, "usd": False},
                     "previous_blockers": None, "stall_reviews": 0}
            atomic(box.path / "state.json", state)
        return box

    @contextlib.contextmanager
    def lock(self):
        require(self.path.is_dir(), "Mailbox directory does not exist")
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(str(self.path / "lock"), flags, 0o600)
        except OSError as exc:
            raise RelayError("Cannot lock mailbox: " + str(exc)) from exc
        with os.fdopen(fd, "a+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def load(self):
        for name in ("state.json", "messages", "jobs", "logs", "rules"):
            require(not (self.path / name).is_symlink(), "Mailbox path replaced by symlink: " + name)
        state = read_json(self.path / "state.json")
        require(isinstance(state, dict) and state.get("schema_version") == VERSION
                and state.get("phase") in ("working", "needs_human", "done")
                and isinstance(state.get("jobs"), dict) and isinstance(state.get("config"), dict),
                "Invalid mailbox state; retain evidence and recover manually")
        fields = {"run_id", "reason", "config_source", "config_hash", "rules_hash", "created_at",
                  "sequence", "rounds", "current_sha", "review_approved_sha", "build_accepted_sha",
                  "dedupe", "usage", "unknown_usage", "previous_blockers", "stall_reviews",
                  "relay_version", "relay_sha256", "dispatch_hold", "rules_history"}
        require(fields.issubset(state), "Incomplete mailbox state; preserve it for recovery")
        require(state["relay_version"] == RELAY_VERSION and state["relay_sha256"] == RUNTIME_SHA256,
                "Relay version/hash mismatch; use the exact same relay for both roles, preserve this run")
        require(isinstance(state["usage"], dict) and isinstance(state["unknown_usage"], dict)
                and {"tokens", "usd"}.issubset(state["usage"])
                and {"tokens", "usd"}.issubset(state["unknown_usage"]), "Invalid usage state")
        for ident, job in state["jobs"].items():
            require(isinstance(job, dict) and job.get("id") == ident
                    and re.fullmatch(r"[0-9a-f]{32}", ident)
                    and job.get("status") in ("pending", "active", "done", "obsolete")
                    and job.get("recipient") in (*ROLES, "human")
                    and {"message_hash", "claim", "completion"}.issubset(job), "Invalid job state")
            if job["status"] == "active":
                require(isinstance(job["claim"], dict)
                        and {"token", "owner", "started_at", "expires_at"}.issubset(job["claim"]),
                        "Invalid active claim state")
        cfg = state["config"]
        require(digest(packed(cfg)) == state.get("config_hash"), "Stored config changed")
        require(digest(packed(read_json(state["config_source"]))) == state["config_hash"],
                "Config source changed; review it and start a new run")
        root = Path(cfg["project_root"]).resolve()
        snapshot = self.path / "rules" / (state["rules_hash"] + ".md")
        require(not snapshot.is_symlink() and digest(snapshot.read_bytes()) == state["rules_hash"],
                "Pinned rules snapshot changed; preserve the run")
        try:
            current_hash = digest(relative_file(root, cfg["rules_file"]).read_bytes())
        except (RelayError, OSError) as exc:
            state["dispatch_hold"] = {"reason": "Rules unreadable; current job retains pinned rules", "detail": str(exc), "observed_hash": None}
        else:
            if current_hash != state["rules_hash"]:
                state["dispatch_hold"] = {"reason": "Rules changed; human adoption required", "observed_hash": current_hash}
        return state

    def save(self, state):
        atomic(self.path / "state.json", state)

    @staticmethod
    def stop(state, reason):
        state["phase"] = "needs_human"
        state["reason"] = reason

    def budget_reason(self, state, now, new_candidate=False):
        budget = state["config"]["budgets"]
        for key in ("tokens", "usd"):
            if budget[key] is not None:
                if state["unknown_usage"][key]:
                    return "Unknown {} usage with configured budget".format(key)
                if state["usage"][key] >= budget[key]:
                    return "{} budget reached".format(key)
        if budget["wall_seconds"] is not None and now - state["created_at"] >= budget["wall_seconds"]:
            return "Wall-time budget reached"
        if new_candidate and budget["max_rounds"] is not None and state["rounds"] >= budget["max_rounds"]:
            return "Candidate-round budget reached"
        return None

    def sweep(self, state, now):
        if state["phase"] != "working":
            return
        for job in state["jobs"].values():
            if job["status"] == "active" and now >= job["claim"]["expires_at"]:
                state["unknown_usage"]["tokens"] = state["unknown_usage"]["usd"] = True
                self.stop(state, "Lease expired for {}; verify the old worker stopped before recovery".format(job["id"]))
                return
        reason = self.budget_reason(state, now)
        if state["phase"] == "working" and reason:
            self.stop(state, reason)

    def message(self, state, job):
        message = read_json(self.path / "messages" / (job["id"] + ".json"))
        require(digest(packed(message)) == job["message_hash"], "Published message changed")
        root = Path(state["config"]["project_root"]).resolve()
        report = relative_file(root, message["report"])
        require(digest(report.read_bytes()) == message["report_sha256"], "Published report changed; supersede, do not overwrite")
        decision = message.get("human_decision")
        if decision:
            path = relative_file(root, decision["report"])
            require(digest(path.read_bytes()) == decision["report_sha256"], "Published human decision changed")
        return message

    def linked_context(self, state, message):
        """Include actual immutable inputs, not just an instruction to find them."""
        history, seen = [], set()
        parent = message.get("reply_to")
        while parent is not None:
            require(parent not in seen and parent in state["jobs"], "Invalid message context chain")
            seen.add(parent)
            record = self.message(state, state["jobs"][parent])
            history.append(record)
            parent = record.get("reply_to")
        return list(reversed(history))

    def redispatch(self, state, recipient, report, note, event):
        """Human control appends context while preserving the original task/delivery."""
        records = [self.message(state, job) for job in state["jobs"].values()]
        records.sort(key=lambda item: item["sequence"])
        if recipient == "review":
            candidates = [m for m in records if m["kind"] == "candidate" and m["sender"] == "build"
                          and m["sha"] == state["current_sha"]]
            require(bool(candidates), "No original build candidate to review")
            source = candidates[-1]
        else:
            tasks = [m for m in records if m["kind"] == "task" and not m.get("human_decision")]
            require(bool(tasks), "No original task; publish a human task first")
            source = tasks[0]
        path = relative_file(Path(state["config"]["project_root"]), report)
        decision = {"kind": event, "report": report, "report_sha256": digest(path.read_bytes()), "note": note}
        # The latest message links the full intervening feedback/escalation chain.
        # Sender is human: these are routing decisions, not new model deliveries.
        return self.publish(state, "human", "candidate" if recipient == "review" else "task",
                            source["report"], state["current_sha"], note, records[-1]["id"],
                            decision=decision, source_message_id=source["id"])

    def publish(self, state, sender, kind, report, sha=None, summary="", reply_to=None, execution=None,
                decision=None, source_message_id=None):
        require(kind in KINDS, "Unknown handoff kind")
        expected, recipient = KINDS[kind]
        require(expected is None or expected == sender
                or (sender == "human" and kind == "candidate" and decision is not None),
                "Role cannot publish that handoff")
        root = Path(state["config"]["project_root"]).resolve()
        report_path = relative_file(root, report)
        require(isinstance(summary, str) and len(summary) <= 2000, "summary must be at most 2000 characters")
        if sha is not None:
            check_sha(root, sha)
        require(kind in ("task", "needs_human") or sha is not None, "This handoff needs a commit SHA")
        ident = uuid.uuid4().hex
        state["sequence"] += 1
        message = {"schema_version": VERSION, "run_id": state["run_id"], "id": ident,
                   "sequence": state["sequence"], "sender": sender, "recipient": recipient,
                   "kind": kind, "sha": sha, "report": report,
                   "report_sha256": digest(report_path.read_bytes()), "summary": summary,
                   "reply_to": reply_to, "created_at": time.time()}
        if decision is not None:
            message["human_decision"] = decision
            message["source_message_id"] = source_message_id
        message["rules_hash"] = state["rules_hash"]
        message["report_language"] = state["config"]["report_language"]
        if execution is not None:
            message["execution"] = execution
        if sender in ROLES:
            setting = state["config"]["roles"][sender]
            message["settings_verification"] = verification(setting)
        # Message first, state second. An interrupted publication leaves an ignored
        # orphan message, never a dispatchable job missing its published payload.
        atomic(self.path / "messages" / (ident + ".json"), message)
        state["jobs"][ident] = {"id": ident, "recipient": recipient,
                               "status": "pending" if recipient in ROLES else "done",
                               "message_hash": digest(packed(message)), "claim": None,
                               "completion": None}
        return message

    def task(self, report, key=None, sha=None, summary=""):
        with self.lock():
            state = self.load()
            self.sweep(state, time.time())
            content = {"report": report, "sha": sha, "summary": summary,
                       "hash": digest(relative_file(Path(state["config"]["project_root"]), report).read_bytes())}
            if key and key in state["dedupe"]:
                old = state["dedupe"][key]
                require(old["content"] == content, "Dedupe key reused for different content")
                return old["message_id"]
            if state["phase"] != "working":
                self.save(state)
                raise RelayError("Run is stopped: " + str(state["reason"]))
            require(not state["dispatch_hold"], "New dispatch is held; use human-confirmed adopt-rules")
            require(not any(j["status"] in ("active", "pending") for j in state["jobs"].values()),
                    "A task is already in progress; finish or escalate it first")
            message = self.publish(state, "human", "task", report, sha, summary)
            if key:
                state["dedupe"][key] = {"content": content, "message_id": message["id"]}
            self.save(state)
            return message["id"]

    def claim(self, role, owner):
        require(role in ROLES, "Unknown role")
        require(isinstance(owner, str) and bool(owner), "Record a nonempty owner identity")
        with self.lock():
            state = self.load()
            now = time.time()
            self.sweep(state, now)
            if state["phase"] != "working" or state["dispatch_hold"]:
                self.save(state)
                return None
            if any(j["status"] == "active" and j["recipient"] == role for j in state["jobs"].values()):
                return None
            for job in state["jobs"].values():
                if job["status"] == "pending" and job["recipient"] == role:
                    try:
                        message = self.message(state, job)
                        context = self.linked_context(state, message)
                        for adoption in state["rules_history"]:
                            path = relative_file(Path(state["config"]["project_root"]), adoption["report"])
                            require(digest(path.read_bytes()) == adoption["report_sha256"], "Rules adoption report changed")
                    except RelayError as exc:
                        self.stop(state, str(exc))
                        self.save(state)
                        raise
                    if message["kind"] in ("task", "changes_requested"):
                        reason = self.budget_reason(state, now, new_candidate=True)
                        if reason:
                            self.stop(state, reason)
                            self.save(state)
                            return None
                    token = uuid.uuid4().hex
                    claim = {"token": token, "owner": owner, "started_at": now,
                             "expires_at": now + state["config"].get("lease_seconds", 120)}
                    job["status"], job["claim"] = "active", claim
                    job_path = self.path / "jobs" / (job["id"] + "-" + token + ".json")
                    payload = {"schema_version": VERSION, "run_id": state["run_id"],
                               "message": message, "context_messages": context,
                               "rules_history": state["rules_history"], "claim": claim, "role": role,
                               "settings": state["config"]["roles"][role],
                               "project_root": state["config"]["project_root"],
                               "rules_file": state["config"]["rules_file"],
                               "rules_hash": state["rules_hash"],
                               "rules_snapshot": str(self.path / "rules" / (state["rules_hash"] + ".md")),
                               "report_language": state["config"]["report_language"],
                               "authorization_source": state["config"]["authorization_source"],
                               "permissions": state["config"]["permissions"],
                               "budgets": state["config"]["budgets"],
                               "remaining_context": {"current_sha": state["current_sha"],
                                                     "rounds": state["rounds"], "usage": state["usage"]}}
                    atomic(job_path, payload)
                    self.save(state)
                    return {"id": job["id"], "token": token, "job_file": str(job_path)}
            return None

    def active(self, state, ident, token, now):
        job = state["jobs"].get(ident)
        require(job is not None and job["status"] == "active" and job["claim"]["token"] == token,
                "Stale or invalid claim token")
        require(now < job["claim"]["expires_at"], "Claim lease expired; result is fenced")
        require(state["phase"] == "working", "Run paused; inspect and recover instead of committing a late result")
        return job

    def heartbeat(self, ident, token):
        with self.lock():
            state = self.load()
            now = time.time()
            job = self.active(state, ident, token, now)
            job["claim"]["expires_at"] = now + state["config"].get("lease_seconds", 120)
            self.save(state)

    def finish(self, ident, token, result):
        require(isinstance(result, dict), "Result must be an object")
        result_hash = digest(packed(result))
        with self.lock():
            state = self.load()
            job = state["jobs"].get(ident)
            # A caller can lose the response after a successful state write.
            # Retry returns the same completion without counting usage twice.
            if job and job["status"] == "done" and job["completion"]:
                old = job["completion"]
                require(old["token"] == token and old["result_hash"] == result_hash,
                        "Completion retry changed content or token")
                return old["message_id"]
            job = self.active(state, ident, token, time.time())
            message = self.message(state, job)
            role = job["recipient"]
            kind = result.get("kind")
            require(kind in RESPONSES[message["kind"]], "Invalid response to this task")
            settings = state["config"]["roles"][role]
            execution = result.get("execution", {})
            level = verification(settings)
            require(all(execution.get(k) == settings[k] or (level == "unavailable" and execution.get(k) is None)
                        for k in ("provider", "model", "effort")),
                    "Worker identity differs from the human-selected settings; no fallback")
            require(execution.get("verification", level) == level,
                    "Worker cannot promote the configured settings verification level")
            blockers = result.get("blocking_issue_ids")
            require(isinstance(blockers, list) and all(isinstance(i, str) and i for i in blockers)
                    and len(blockers) == len(set(blockers)), "blocking_issue_ids must be unique stable IDs")
            if kind in ("review_approved", "build_accepted"):
                require(result.get("required_gates_passed") is True and not blockers,
                        "Approval/acceptance needs passed gates and no blockers")
            if kind == "changes_requested":
                require(bool(blockers), "Changes requested needs stable blocking issue IDs; use needs_human for unknown gates")
            sha = result.get("sha")
            if kind in ("changes_requested", "review_approved", "build_accepted"):
                require(sha == state["current_sha"] == message["sha"], "Stale SHA cannot change current approval state")
            if role == "review" and kind != "needs_human":
                head = subprocess.run(["git", "-C", settings["workdir"], "rev-parse", "HEAD"],
                                      capture_output=True, text=True)
                require(head.returncode == 0 and head.stdout.strip() == sha,
                        "Reviewer worktree HEAD must be the exact reported candidate SHA")
            if kind == "build_accepted":
                require(sha == state["review_approved_sha"], "Build acceptance needs exact-SHA review approval")
            if kind == "candidate":
                reason = self.budget_reason(state, time.time(), new_candidate=True)
                require(reason is None, reason or "Budget reached")
            usage = result.get("usage", {})
            require(isinstance(usage.get("source"), str) and bool(usage["source"]), "Record usage source or why unknown")
            counts = {}
            for field in ("tokens", "usd"):
                value = usage.get(field)
                require(value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)
                                         and math.isfinite(value) and value >= 0), "Invalid usage count")
                if field == "tokens":
                    require(value is None or isinstance(value, int), "tokens must be an integer or null")
                counts[field] = value
            outgoing = self.publish(state, role, kind, result.get("report"), sha,
                                    result.get("summary", ""), ident,
                                    {**{k: execution.get(k) for k in ("provider", "model", "effort")},
                                     "verification": level, "source": settings.get("verification_source")
                                     or "Legacy configuration assertion; not remote attestation"})
            job["status"] = "done"
            job["completion"] = {"token": token, "result_hash": result_hash, "message_id": outgoing["id"]}
            for field, value in counts.items():
                if value is None:
                    state["unknown_usage"][field] = True
                else:
                    state["usage"][field] += value
            if kind == "candidate":
                state["current_sha"] = sha
                state["review_approved_sha"] = state["build_accepted_sha"] = None
                state["rounds"] += 1
            elif kind == "review_approved":
                state["review_approved_sha"] = sha
            elif kind == "build_accepted":
                state["build_accepted_sha"] = sha
                state["phase"] = "working" if state["dispatch_hold"] else "done"
                state["jobs"][outgoing["id"]]["status"] = "done"
            elif kind == "changes_requested":
                previous = state["previous_blockers"]
                state["stall_reviews"] = (state["stall_reviews"] + 1
                                           if previous is not None and set(previous).issubset(set(blockers)) else 0)
                state["previous_blockers"] = blockers
                limit = state["config"]["budgets"]["max_stall_reviews"]
                if limit is not None and state["stall_reviews"] >= limit:
                    self.stop(state, "Repeated blocking issues; human decision needed")
            elif kind == "needs_human":
                self.stop(state, result.get("summary") or "Worker requested a human decision")
            # Budget overrun, even on final acceptance, is surfaced. A usage cap
            # cannot be satisfied by silently treating unknown usage as zero.
            reason = self.budget_reason(state, time.time())
            if reason:
                self.stop(state, reason)
            self.save(state)
            return outgoing["id"]

    def fail(self, ident, token, reason, usage_unknown=True):
        with self.lock():
            state = self.load()
            job = state["jobs"].get(ident)
            require(job and job["status"] == "active" and job["claim"]["token"] == token,
                    "Cannot fail a stale claim")
            job["failure_reason"] = reason
            if usage_unknown:
                state["unknown_usage"]["tokens"] = state["unknown_usage"]["usd"] = True
            self.stop(state, reason)
            self.save(state)

    def pause(self, note):
        require(isinstance(note, str) and bool(note.strip()), "Record the human stop decision")
        with self.lock():
            state = self.load()
            require(state["phase"] != "done", "Run already completed")
            self.stop(state, "Human pause: " + note)
            self.save(state)

    def recover(self, ident, note, owner_stopped):
        require(owner_stopped is True and bool(note.strip()),
                "Verify the prior owner stopped and record human authorization")
        with self.lock():
            state = self.load()
            require(state["phase"] == "needs_human", "Only stopped runs need recovery")
            job = state["jobs"].get(ident)
            require(job and job["status"] == "active", "Recovery needs the interrupted active job")
            job["status"], job["claim"] = "pending", None
            state["recovery_note"] = note
            state["phase"], state["reason"] = "working", None
            require(self.budget_reason(state, time.time()) is None, "Budget still blocks; start a newly authorized run")
            self.save(state)

    def resume(self, report, recipient, note):
        """Human resumes after a completed needs_human or repeated-blocker stop.

        A task to build requests more implementation; a candidate to review
        asks review of the current SHA. Existing active work must be recovered.
        """
        require(recipient in ROLES and bool(note.strip()), "Record the human resume decision and recipient")
        with self.lock():
            state = self.load()
            require(not state["dispatch_hold"], "Adopt changed rules before resuming dispatch")
            require(state["phase"] == "needs_human", "Resume is for a paused run")
            require(not any(j["status"] == "active" for j in state["jobs"].values()),
                    "An active owner must be stopped and recovered first")
            require(self.budget_reason(state, time.time()) is None, "Budget still blocks; start a newly authorized run")
            for job in state["jobs"].values():
                if job["status"] == "pending":
                    job["status"] = "obsolete"
            state["phase"], state["reason"] = "working", None
            state["stall_reviews"] = 0
            state["resume_note"] = note
            if recipient == "review":
                require(state["current_sha"] is not None, "No current candidate to review")
                state["review_approved_sha"] = state["build_accepted_sha"] = None
            message = self.redispatch(state, recipient, report, note, "resume")
            message_id = message["id"]
            state["human_resume_message"] = message_id
            self.save(state)
            return message_id

    def adopt_rules(self, expected_hash, report, note):
        """Human adoption after active work drains. Changed rules re-open review."""
        require(isinstance(note, str) and bool(note.strip()), "Record actual human rules adoption")
        with self.lock():
            state = self.load()
            require(state["phase"] in ("working", "needs_human"), "Completed runs need a new task/run")
            require(state["dispatch_hold"], "No rules change is awaiting adoption")
            require(not any(j["status"] == "active" for j in state["jobs"].values()),
                    "Wait for current worker to finish, or explicitly pause/stop and recover it")
            root = Path(state["config"]["project_root"])
            data = relative_file(root, state["config"]["rules_file"]).read_bytes()
            new_hash = digest(data)
            require(expected_hash == new_hash, "Rules changed again; review the current hash before adoption")
            report_path = relative_file(root, report)
            require(self.budget_reason(state, time.time()) is None, "Budget still blocks adoption")
            old_hash = state["rules_hash"]
            atomic_bytes(self.path / "rules" / (new_hash + ".md"), data)
            state["rules_hash"], state["dispatch_hold"] = new_hash, None
            state["rules_history"].append({"old_hash": old_hash, "new_hash": new_hash,
                                           "report": report, "report_sha256": digest(report_path.read_bytes()),
                                           "human_note": note, "at": time.time()})
            if old_hash != new_hash:
                state["review_approved_sha"] = state["build_accepted_sha"] = None
                for job in state["jobs"].values():
                    if job["status"] == "pending":
                        job["status"] = "obsolete"
                # A separately paused run stays paused; resume dispatches once.
                if state["phase"] == "working" and state["jobs"]:
                    message = self.redispatch(state, "review" if state["current_sha"] else "build",
                                              report, note, "rules_adoption")
                    state["human_resume_message"] = message["id"]
            elif state["phase"] == "working" and state["current_sha"] and state["build_accepted_sha"] == state["review_approved_sha"] == state["current_sha"]:
                state["phase"] = "done"
            self.save(state)

    def status(self):
        with self.lock():
            state = self.load()
            self.sweep(state, time.time())
            self.save(state)
            return {k: state[k] for k in ("run_id", "phase", "reason", "current_sha", "rounds",
                                          "review_approved_sha", "build_accepted_sha", "usage", "unknown_usage", "jobs",
                                          "dispatch_hold", "rules_hash", "relay_version", "relay_sha256")}


def terminate_child(process):
    """Stop only our own adapter process group, never arbitrary peer PIDs."""
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    except ProcessLookupError:
        process.wait()


def run_claim(box, role, claim):
    payload = read_json(claim["job_file"])
    settings = payload["settings"]
    argv = settings.get("adapter_argv", [])
    if not argv:
        box.fail(claim["id"], claim["token"], "No trusted adapter configured; use manual claim/finish", usage_unknown=False)
        return
    result_path = box.path / "jobs" / (claim["id"] + "-" + claim["token"] + "-result.json")
    log_path = box.path / "logs" / (claim["id"] + "-" + claim["token"] + ".log")
    process = None
    try:
        with open(log_path, "xb") as log:
            process = subprocess.Popen(argv + [claim["job_file"], str(result_path)],
                                       cwd=settings["workdir"], stdout=log, stderr=subprocess.STDOUT,
                                       shell=False, start_new_session=True)
            # Tiny local waits/heartbeats; no model calls or file lock held.
            lease = 0.0
            while process.poll() is None:
                now = time.time()
                if now >= lease:
                    box.heartbeat(claim["id"], claim["token"])
                    lease = now + min(30, payload["claim"]["expires_at"] - payload["claim"]["started_at"]) / 3
                with box.lock():
                    state = box.load()
                    require(state["phase"] == "working", "Run stopped while adapter was active")
                    reason = box.budget_reason(state, now)
                require(reason is None, reason or "Budget reached")
                time.sleep(1)
        require(process.returncode == 0, "Adapter exited {} (see private log {})".format(process.returncode, log_path))
        box.finish(claim["id"], claim["token"], read_json(result_path))
    except BaseException as exc:
        if process:
            terminate_child(process)
        try:
            box.fail(claim["id"], claim["token"], "Adapter failed: " + str(exc))
        except RelayError:
            pass
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        print("ForgeDuet stopped: " + str(exc), file=sys.stderr)


def watch(box, role, once=False):
    owner = "poller:{}:{}".format(os.getpid(), uuid.uuid4().hex)
    while True:
        claim = box.claim(role, owner)
        if claim:
            run_claim(box, role, claim)
        state = box.status()
        if once or state["phase"] != "working" or state["dispatch_hold"]:
            return
        with box.lock():
            interval = box.load()["config"].get("poll_seconds", 60)
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Initialize a frozen, human-configured run")
    init.add_argument("--config", required=True)
    for cmd in ("task", "status", "claim", "heartbeat", "finish", "recover", "resume", "pause", "adopt-rules", "watch"):
        p = sub.add_parser(cmd)
        p.add_argument("--mailbox", required=True)
        if cmd in ("task", "resume", "adopt-rules"):
            p.add_argument("--report", required=True)
        if cmd == "task":
            p.add_argument("--key")
            p.add_argument("--sha")
            p.add_argument("--summary", default="")
        if cmd in ("claim", "watch", "resume"):
            p.add_argument("--role", choices=ROLES, required=True)
        if cmd == "claim":
            p.add_argument("--owner", required=True)
        if cmd in ("heartbeat", "finish", "recover"):
            p.add_argument("--id", required=True)
        if cmd in ("heartbeat", "finish"):
            p.add_argument("--token", required=True)
        if cmd == "finish":
            p.add_argument("--result", required=True)
        if cmd in ("recover", "resume", "pause", "adopt-rules"):
            p.add_argument("--human-note", required=True)
        if cmd == "recover":
            p.add_argument("--owner-stopped", action="store_true")
        if cmd == "watch":
            p.add_argument("--once", action="store_true", help="One dispatch pass; useful for integration checks")
        if cmd == "adopt-rules":
            p.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            box = Mailbox.init(args.config)
            answer = box.status()
        else:
            box = Mailbox(args.mailbox)
            if args.command == "task":
                answer = box.task(args.report, args.key, args.sha, args.summary)
            elif args.command == "status":
                answer = box.status()
            elif args.command == "claim":
                answer = box.claim(args.role, args.owner)
            elif args.command == "heartbeat":
                answer = box.heartbeat(args.id, args.token)
            elif args.command == "finish":
                answer = box.finish(args.id, args.token, read_json(args.result))
            elif args.command == "recover":
                answer = box.recover(args.id, args.human_note, args.owner_stopped)
            elif args.command == "resume":
                answer = box.resume(args.report, args.role, args.human_note)
            elif args.command == "pause":
                answer = box.pause(args.human_note)
            elif args.command == "adopt-rules":
                answer = box.adopt_rules(args.expected_sha256, args.report, args.human_note)
            else:
                watch(box, args.role, args.once)
                answer = box.status()
        print(json.dumps(answer, ensure_ascii=False, indent=2))
        return 0
    except (RelayError, OSError, ValueError) as exc:
        print("ForgeDuet: " + str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
