"""Resolved<T> provenance (spec §5/§7/§12): stated→detected→reconciled transitions; detection wins the
number immediately; the RAW path sets DETECTED. Plus a TenantTopology persistence round-trip."""
import os
import sys
import tempfile

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_topo_"), "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                                        # noqa: E402
from realify.topology_model import (Resolved, TenantTopology, ReliabilityFlag,  # noqa: E402
                                     STATED, DETECTED, RECONCILED, WIZARD, RAW)
from realify.repositories.topology_repo import TopologyRepository, SkuCrosswalkRepository, MAPPED, UNMAPPED  # noqa: E402


def test_stated_only_before_files():
    r = Resolved.from_stated("FBA")
    assert r.effective == "FBA" and r.source == STATED and r.conflict is False


def test_detection_agrees_keeps_stated():
    r = Resolved.from_stated("FBA").observe("FBA")
    assert r.effective == "FBA" and r.conflict is False and r.source == STATED


def test_detection_conflicts_detected_wins_the_number():
    r = Resolved.from_stated("FBA").observe("FBM")
    assert r.conflict is True and r.effective == "FBM"        # detected wins the number immediately
    assert r.source == STATED                                # provenance not yet reconciled
    r.confirm("2026-07-07T00:00:00")
    assert r.source == RECONCILED and r.confirmed_at and r.effective == "FBM"


def test_raw_path_sets_detected():
    r = Resolved.from_detected("BOTH")
    assert r.effective == "BOTH" and r.source == DETECTED and r.stated is None


def test_resolved_round_trips_through_dict():
    r = Resolved.from_stated("SP_ONLY").observe("SP_PLUS")
    r2 = Resolved.from_dict(r.to_dict())
    assert r2.effective == "SP_PLUS" and r2.conflict is True and r2.stated == "SP_ONLY"


def test_topology_persist_round_trip():
    db.init_db()
    con = db.connect()
    tid = 4242
    topo = TenantTopology(tenant_id=tid, entry_path=WIZARD, primary_goal="PROFIT_AFTER_ADS",
                          channels=[{"platform": "AMAZON", "status": "ACTIVE", "account_ref": "A1"},
                                    {"platform": "SHOPIFY", "status": "ACTIVE", "account_ref": "store-1"}],
                          ad_partners=["META"])
    topo.resolved["gateway"] = Resolved.from_stated("SP_ONLY").observe("SP_PLUS")
    topo.flags.append(ReliabilityFlag("FEE_GAP", armed_by="S3"))
    TopologyRepository(con).save(tid, topo)
    con.commit()
    got = TopologyRepository(con).get(tid)
    assert got is not None and got.entry_path == WIZARD and got.primary_goal == "PROFIT_AFTER_ADS"
    assert [c["platform"] for c in got.channels] == ["AMAZON", "SHOPIFY"] and got.ad_partners == ["META"]
    assert got.resolved["gateway"].effective == "SP_PLUS" and got.resolved["gateway"].conflict is True
    assert got.flag("FEE_GAP") is not None and got.flag("FEE_GAP").satisfied_by == "gateway_fee_file"
    assert TopologyRepository(con).get(999999) is None       # tenant-scoped: another tenant sees nothing
    con.close()


def test_crosswalk_resolve_and_scoping():
    db.init_db()
    con = db.connect()
    xw = SkuCrosswalkRepository(con)
    xw.upsert(1, "shopify", "WIDGET-1", "WIDGET-1", MAPPED, store_id="store-1", external_variant_id="v99")
    xw.upsert(1, "shopify", "GADGET-9", None, UNMAPPED, store_id="store-1", external_variant_id="v12")
    xw.upsert(1, "amazon", "WIDGET-1", "WIDGET-1", MAPPED)          # amazon: no store/variant dims ('')
    con.commit()
    assert xw.resolve(1, "shopify", "WIDGET-1", store_id="store-1", external_variant_id="v99") == "WIDGET-1"
    assert xw.resolve(1, "amazon", "WIDGET-1") == "WIDGET-1"
    assert xw.resolve(1, "shopify", "WIDGET-1", store_id="store-2", external_variant_id="v99") is None  # wrong store
    assert xw.resolve(2, "shopify", "WIDGET-1", store_id="store-1", external_variant_id="v99") is None  # other tenant
    assert len(xw.unmapped(1)) == 1 and xw.count(1) == 3
    con.close()


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("topology_resolution OK")
