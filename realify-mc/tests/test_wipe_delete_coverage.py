"""Account delete must leave NO tenant-scoped rows anywhere; resynthesize must not leave stale
ad/revenue rows. These guard the exact drift that orphaned the new CMAA tables."""
import pytest
from realify import db
from realify.repositories.tenant_repo import TenantRepository
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.ad_performance_repo import AdPerformanceRepository


def _all_tenant_scoped(con):
    from realify import dbengine
    if dbengine.dialect() == "postgresql":
        tabs = [r["table_name"] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' "
            "AND table_type='BASE TABLE' AND table_name NOT LIKE 'alembic%'").fetchall()]
        scoped = []
        for t in tabs:
            cols = [r["column_name"] for r in con.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name=?", (t,)).fetchall()]
            if "tenant_id" in cols:
                scoped.append(t)
        return scoped
    tabs = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "AND name NOT LIKE 'alembic%'").fetchall()]
    scoped = []
    for t in tabs:
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})").fetchall()]
        if "tenant_id" in cols:
            scoped.append(t)
    return scoped


def test_account_delete_leaves_no_orphans_in_any_tenant_table():
    with db.connect() as con:
        tid = TenantRepository(con).create("DeleteMe"); con.commit()
    # provision synthetic data so the CMAA + all tables get populated
    from realify.ingest.synthetic import SyntheticSource
    SyntheticSource().provision(tid)
    # Synthetic provisioning never touches the report-ingest tables (ingested_reports,
    # cogs_suggestions), so seed them directly — otherwise the invariant below is vacuously
    # true for them and drift (like 0008/0009 adding tables) slips through unnoticed.
    from realify.repositories.ingested_report_repo import IngestedReportRepository
    from realify.repositories.cogs_suggestion_repo import CogsSuggestionRepository
    from realify.repositories.ad_entity_repo import (
        AdEntityPerfRepository, AdSearchTermRepository, AdIngestSummaryRepository)
    with db.connect() as con:
        IngestedReportRepository(con).record(tid, "deadbeef", "MonthlyUnifiedTransaction", "march.csv")
        CogsSuggestionRepository(con).upsert(tid, "SKU-1", 12.5, "high", "~50% of price")
        # The ad-graph tables (0012) are written ONLY by the customer report-upload path, never by synth,
        # so seed them directly — otherwise the orphan invariant is vacuously true for them and drift
        # (the omission from TENANT_DATA_TABLES this test now guards) slips through unnoticed.
        AdEntityPerfRepository(con).upsert(tid, "Camp A", "AG1", "ASIN1", "SKU-1", "SKU-1",
                                           "2026-06-01", "month", 100, 120, 10, 2)
        AdSearchTermRepository(con).upsert(tid, "Camp A", "AG1", "kw", "BROAD", "term",
                                           "2026-06-01", "month", 30, 0, 5, 0)
        AdIngestSummaryRepository(con).upsert(tid, 80.0, 100.0, 20.0, "KEYWORD", None, 1, 1, 0)
        con.commit()
    with db.connect() as con:
        scoped = _all_tenant_scoped(con)
        # sanity: the new tables really did get rows before delete
        assert con.execute("SELECT COUNT(*) c FROM ad_performance WHERE tenant_id=?", (tid,)).fetchone()["c"] > 0
        assert con.execute("SELECT COUNT(*) c FROM ingested_reports WHERE tenant_id=?", (tid,)).fetchone()["c"] > 0
        assert con.execute("SELECT COUNT(*) c FROM cogs_suggestions WHERE tenant_id=?", (tid,)).fetchone()["c"] > 0
        assert con.execute("SELECT COUNT(*) c FROM ad_entity_perf WHERE tenant_id=?", (tid,)).fetchone()["c"] > 0
        assert con.execute("SELECT COUNT(*) c FROM ad_search_term WHERE tenant_id=?", (tid,)).fetchone()["c"] > 0
        assert con.execute("SELECT COUNT(*) c FROM ad_ingest_summary WHERE tenant_id=?", (tid,)).fetchone()["c"] > 0
        TenantRepository(con).delete(tid); con.commit()
        leftovers = {t: con.execute(f"SELECT COUNT(*) c FROM {t} WHERE tenant_id=?", (tid,)).fetchone()["c"]
                     for t in scoped}
    orphaned = {t: n for t, n in leftovers.items() if n}
    assert not orphaned, f"account delete orphaned rows in: {orphaned}"


def test_resynthesize_does_not_leave_stale_ad_rows():
    with db.connect() as con:
        tid = TenantRepository(con).create("Tester"); con.commit()
        db.set_account_type(con, tid, "tester"); db.set_tenant_provisioned(con, tid, "synthetic"); con.commit()
    from realify.ingest.synthetic import SyntheticSource
    SyntheticSource().provision(tid)
    with db.connect() as con:
        before = con.execute("SELECT COUNT(*) c FROM ad_performance WHERE tenant_id=?", (tid,)).fetchone()["c"]
    # a second provision (as a resynthesize would) must not accumulate rows
    SyntheticSource().provision(tid)
    with db.connect() as con:
        after = con.execute("SELECT COUNT(*) c FROM ad_performance WHERE tenant_id=?", (tid,)).fetchone()["c"]
    assert after == before, f"resynthesize accumulated ad rows: {before} -> {after}"
