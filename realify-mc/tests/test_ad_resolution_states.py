"""The three scenarios resolve to exactly the right state: ads_full -> RENDERED_OK, ads_none ->
NO_ENTITY_DATA (+fallback), ads_unmapped -> UNMAPPED (+alarm, NOT fallback)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_ars_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, scheduler                                       # noqa: E402
from realify.ingest.synthetic import SyntheticSource                    # noqa: E402
from realify.ingest.synth_ad_graph import synthesize_ad_graph           # noqa: E402
from realify.repositories.tenant_repo import TenantRepository           # noqa: E402
from realify.routers import ads                                         # noqa: E402


def test_three_scenarios_resolve_exactly():
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); db.set_account_type(con, tid, "tester"); con.commit()
    scheduler.provision_own_data(tid, SyntheticSource(), log=lambda *a: None)   # ads_full

    def res():
        with db.connect() as con:
            r, _ = ads._resolve(con, tid)
        return r

    full = res()
    assert full["reason"] == "RENDERED_OK" and full["fell_back"] is False
    assert full["entity_rows"] > 0 and full["mapped_rows"] > 0 and full["recommendations"] > 0

    with db.connect() as con:
        synthesize_ad_graph(con, tid, "ads_unmapped"); con.commit()
    unm = res()
    assert unm["reason"] == "UNMAPPED" and unm["fell_back"] is False           # alarm, not a fallback
    assert unm["entity_rows"] > 0 and unm["mapped_rows"] == 0

    with db.connect() as con:
        synthesize_ad_graph(con, tid, "ads_none"); con.commit()
    none = res()
    assert none["reason"] == "NO_ENTITY_DATA" and none["fell_back"] is True    # the only legitimate fallback
    assert none["entity_rows"] == 0


if __name__ == "__main__":
    test_three_scenarios_resolve_exactly()
    print("ad_resolution_states OK")
