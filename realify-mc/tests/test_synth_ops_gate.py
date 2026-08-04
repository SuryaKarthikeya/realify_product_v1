"""The destructive-synthetic-ops gate (`_synth_ops_allowed`) — full truth table, hermetic SQLite.

WHY THIS EXISTS. On 2026-07-27 the demo tenant 12 was found one click away from having real production
data overwritten. Two things were wrong at once:

  1. Its `data_mode` was still the stale 'synthetic' from before real Seller-Central reports were
     promoted into it — by then it held 690 real order-days (rebuilt from the real Unified Transaction
     export), 691 real ad-days, 44 real SKUs and real COGS.
  2. The gate permitted `account_type='customer'` whenever `tenant_kind` was 'internal' — and tenant 12
     is exactly that shape. `scheduler.resynthesize(mode='full')` regenerates economics from the
     catalog, so the combination was live.

(1) was a data correction. (2) is the code fix this test locks down: account_type is now a hard veto,
the SAME boundary `ads_preview_allowed` already uses for the same reason ("tenant_kind='internal' is TRUE
for the account we demo with"). The point of the fix is DEFENCE IN DEPTH — restoring the stale label
alone must no longer be enough to arm a destructive op.
"""
import os
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="realify_synthgate_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                                          # noqa: E402
from realify.routers.helpers import _synth_ops_allowed          # noqa: E402


def _tenant(data_mode, tenant_kind, account_type):
    """Create a tenant with an exact (data_mode, tenant_kind, account_type) shape and return its id."""
    con = db.connect()
    try:
        db.init(con) if hasattr(db, "init") else None
        tid = db.create_returning_id(
            con, "INSERT INTO tenants(name, created_at, provisioned) VALUES(?, datetime('now'), 1)",
            [f"t-{data_mode}-{tenant_kind}-{account_type}"])
        con.execute("UPDATE tenants SET data_mode=?, tenant_kind=? WHERE id=?",
                    (data_mode, tenant_kind, tid))
        if account_type is not None:
            db.set_account_type(con, tid, account_type)
        con.commit()
        return tid
    finally:
        con.close()


def test_customer_is_denied_even_when_synthetic_and_internal():
    """The exact tenant-12 shape. This is the near-miss; it must be DENIED."""
    tid = _tenant("synthetic", "internal", "customer")
    assert _synth_ops_allowed(tid) is False


def test_customer_is_denied_in_a_sandbox_too():
    tid = _tenant("synthetic", "sandbox", "customer")
    assert _synth_ops_allowed(tid) is False


def test_uploaded_data_is_denied_whatever_the_account():
    """Real (uploaded) data is never resynthesizable — the first line of defence, still intact."""
    for kind in ("internal", "sandbox", "seller"):
        for at in ("tester", "customer", None):
            tid = _tenant("uploaded", kind, at)
            assert _synth_ops_allowed(tid) is False, (kind, at)


def test_synthetic_tester_is_still_allowed():
    """The fix must not break the legitimate case the gate exists to permit."""
    tid = _tenant("synthetic", "seller", "tester")
    assert _synth_ops_allowed(tid) is True


def test_synthetic_internal_non_customer_is_still_allowed():
    tid = _tenant("synthetic", "internal", None)
    assert _synth_ops_allowed(tid) is True


def test_null_data_mode_is_denied():
    """Not-yet-provisioned tenants have data_mode NULL and must fail closed."""
    tid = _tenant(None, "internal", "tester")
    assert _synth_ops_allowed(tid) is False
