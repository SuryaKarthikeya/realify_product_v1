"""In-process in-flight registry for double-fire prevention (R6 C2). A long-running action acquires a
lock keyed by (action, tenant); a duplicate request for the SAME action+tenant while the first is
still running is rejected (409) instead of doing the work twice. Single-container scope — the prod app
is one uvicorn process, so a module-level thread-safe set is the honest lock (no cross-host claim).

The client also disables its button while in flight; this is the server-side half of the guarantee."""
import threading

_lock = threading.Lock()
_inflight = set()


def key(action, tenant_id):
    return f"{action}:{tenant_id}"


def acquire(action, tenant_id):
    """True if the lock was taken (caller may proceed); False if the same action+tenant is in flight."""
    k = key(action, tenant_id)
    with _lock:
        if k in _inflight:
            return False
        _inflight.add(k)
        return True


def release(action, tenant_id):
    with _lock:
        _inflight.discard(key(action, tenant_id))


class Guard:
    """Context manager: `with Guard(action, tid) as ok:` — ok is False if a duplicate is in flight."""
    def __init__(self, action, tenant_id):
        self.action, self.tenant_id, self.ok = action, tenant_id, False

    def __enter__(self):
        self.ok = acquire(self.action, self.tenant_id)
        return self.ok

    def __exit__(self, *exc):
        if self.ok:
            release(self.action, self.tenant_id)
        return False
