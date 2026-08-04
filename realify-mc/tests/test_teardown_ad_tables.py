"""P2.5 / QW-1 (de-vacuumed): synth now POPULATES the three ad tables, so they must be torn down
everywhere synth data is — wipe, account delete, and full resynth (clear-before-rebuild, no orphan/double)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_tad_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, scheduler                                       # noqa: E402
from realify.ingest.synthetic import SyntheticSource                    # noqa: E402
from realify.repositories.tenant_repo import TenantRepository           # noqa: E402

_AD_TABLES = ("ad_entity_perf", "ad_search_term", "ad_ingest_summary")


def _tester():
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); db.set_account_type(con, tid, "tester"); con.commit()
    scheduler.provision_own_data(tid, SyntheticSource(), log=lambda *a: None)   # ads_full by default
    return tid


def _counts(tid):
    with db.connect() as con:
        return {t: con.execute(f"SELECT COUNT(*) c FROM {t} WHERE tenant_id=?", (tid,)).fetchone()["c"]
                for t in _AD_TABLES}


def test_synth_populates_then_wipe_and_delete_clear_all():
    tid = _tester()
    assert all(v > 0 for v in _counts(tid).values()), _counts(tid)       # de-vacuum: really populated
    with db.connect() as con:
        db.wipe_tenant_data(con, tid)
    assert all(v == 0 for v in _counts(tid).values()), _counts(tid)      # wipe clears them

    tid2 = _tester()
    assert all(v > 0 for v in _counts(tid2).values())
    with db.connect() as con:
        TenantRepository(con).delete(tid2)
    assert all(v == 0 for v in _counts(tid2).values())                   # account delete leaves no orphans


def test_full_resynth_is_idempotent_no_double_no_orphan():
    tid = _tester()
    before = _counts(tid)
    assert all(v > 0 for v in before.values())
    scheduler.resynthesize(tid, "full")
    after1 = _counts(tid)
    scheduler.resynthesize(tid, "full")
    after2 = _counts(tid)
    # clear-before-rebuild: repopulated (non-empty) and stable across runs (no doubling, no orphan)
    assert all(v > 0 for v in after1.values()) and after1 == after2, (after1, after2)


if __name__ == "__main__":
    test_synth_populates_then_wipe_and_delete_clear_all()
    test_full_resynth_is_idempotent_no_double_no_orphan()
    print("teardown_ad_tables OK")
