"""Dev mail driver — writes each message as JSON under the mailbox dir (default ./.mailbox, override
with env MAILBOX_DIR), so tests can assert on exactly what would have been sent and no mail leaves the
machine. Filenames are ``{ts_ns}-{seq}.json`` so they sort in send order."""
import itertools
import json
import os
import time

_seq = itertools.count()


def mailbox_dir():
    return os.environ.get("MAILBOX_DIR") or os.path.join(os.getcwd(), ".mailbox")


class DevMailer:
    def send(self, to, subject, body, **headers):
        d = mailbox_dir()
        os.makedirs(d, exist_ok=True)
        n = time.time_ns()
        msg = {"to": to, "subject": subject, "body": body, "headers": headers, "ts_ns": n}
        path = os.path.join(d, f"{n}-{next(_seq)}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(msg, fh, ensure_ascii=False, indent=2)
        return {"driver": "dev", "path": path, **msg}


def inbox(to=None):
    """All captured messages (optionally filtered by recipient), oldest first."""
    d = mailbox_dir()
    if not os.path.isdir(d):
        return []
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(d, fn), encoding="utf-8") as fh:
                    out.append(json.load(fh))
            except (OSError, ValueError):
                pass
    return out if to is None else [m for m in out if m.get("to") == to]


def clear():
    """Empty the mailbox (test hygiene)."""
    d = mailbox_dir()
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".json"):
                os.remove(os.path.join(d, fn))
