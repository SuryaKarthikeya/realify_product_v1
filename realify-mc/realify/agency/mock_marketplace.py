"""IN-PROCESS mock marketplace (agency-plan P5). This is a plain Python object — it makes NO network
calls and there is NO real marketplace client anywhere in the codebase. It models: per-account token
buckets (throttle), idempotency-key dedup (a repeated key never writes twice), mutable per-account
state (for snapshot/rollback), and a state hash (rollback verification)."""
import hashlib
import json
import os

_APP_MOCK = None


def get_mock():
    """Process-wide mock marketplace singleton — the write target the execution routes use in prod
    (still purely in-process; no real API). Capacity is generous by default; the token bucket still
    enforces per-account throttling."""
    global _APP_MOCK
    if _APP_MOCK is None:
        _APP_MOCK = MockMarketplace(capacity=int(os.environ.get("MOCK_MKT_CAPACITY", "1000")))
    return _APP_MOCK


class ThrottleExceeded(Exception):
    pass


class MockMarketplace:
    def __init__(self, capacity=1):
        self.capacity = capacity
        self.state = {}          # account -> value
        self.applied = {}        # idempotency_key -> result (dedup)
        self.buckets = {}        # account -> tokens consumed this window
        self.violations = 0
        self.write_count = 0

    def value(self, account):
        return self.state.get(account)

    def write(self, account, idempotency_key, value):
        """Apply a write. Idempotent by key (no duplicate). Consumes a token; over capacity => throttle."""
        if idempotency_key in self.applied:
            return self.applied[idempotency_key]
        used = self.buckets.get(account, 0)
        if used >= self.capacity:
            self.violations += 1
            raise ThrottleExceeded(account)
        self.buckets[account] = used + 1
        prev = self.state.get(account)
        self.state[account] = value
        self.write_count += 1
        res = {"account": account, "prev": prev, "value": value, "idempotency_key": idempotency_key}
        self.applied[idempotency_key] = res
        return res

    def restore(self, account, value):
        """Rollback primitive: set state directly (bypasses bucket/idempotency)."""
        if value is None:
            self.state.pop(account, None)
        else:
            self.state[account] = value

    def has_tokens(self, account):
        return self.buckets.get(account, 0) < self.capacity

    def state_hash(self):
        return hashlib.sha256(json.dumps(self.state, sort_keys=True, default=str).encode()).hexdigest()

    def reset_buckets(self):
        self.buckets = {}
