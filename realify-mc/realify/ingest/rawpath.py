"""Raw-path detection + reconcile (spec §3/§8). After the recognizer classifies dropped files, this
builds the identify response: the recognized-report checklist (as before) PLUS the detection signals
reconcile.py needs, the tenant's topology (persisted wizard answers, or a fresh RAW one), and the
stated-vs-detected reconcile prompts. Detection wins the number; the prompt captures the correction.

Kept out of onboarding.py (at the 400-line cap); the endpoint stays a thin async wrapper."""
from realify import db
from . import recognizer as rz, extractors_shopify as ex, report_catalog as cat, conflicts as cflt
from .periods import _file_periods
from .report_ingest import detect_overlaps
from .normalize_finance import inventory_allocation
from ..pipeline import reconcile as rc
from .. import topology_model as tm
from ..repositories.topology_repo import TopologyRepository

_AMZ_TYPES = {rz.UNIFIED_TRANSACTION, rz.BUSINESS_REPORT, rz.FEE_PREVIEW, rz.ALL_LISTINGS,
              rz.STORAGE_FEE, rz.FBA_RETURNS, rz.AD_REPORT}


def _by_type(tables):
    out = {}
    for _name, df in tables:
        out.setdefault(rz.detect_report_type(df.columns), []).append(df)
    return out


def detect_signals(tables):
    """The recognizer's read of the uploaded files, as the signal dict reconcile.py consumes. Only
    reliably-detectable signals are set; the harder ones stay conservative so RCs never false-fire."""
    bt = _by_type(tables)
    sig = {}
    inv = [r for df in bt.get("SHOP_INVENTORY", []) for r in ex.inventory(df)]
    if inv:
        sig["mcf_location"] = inventory_allocation(inv)["mcf_detected"]
    prods = [r for df in bt.get("SHOP_PRODUCTS", []) for r in ex.products(df)]
    if prods:
        sig["blank_cost_skus"] = sum(1 for p in prods if p.get("cost") is None and p.get("sku"))
    chans = set()
    if any(t.startswith("SHOP_") for t in bt):
        chans.add("SHOPIFY")
    if any(t in _AMZ_TYPES for t in bt):
        chans.add("AMAZON")
    sig["_present"] = chans
    allcols = [c for _n, df in tables for c in df.columns]
    sig["has_amz_mcf_fees"] = any("fulfillment fee" in rz._norm(c) or "multi-channel" in rz._norm(c)
                                  for c in allcols)
    return sig


def _reconcile(tid, tables):
    with db.connect() as con:
        topo = TopologyRepository(con).get(tid)
    if topo is None:
        topo = tm.TenantTopology(tenant_id=tid, entry_path=tm.RAW)
    sig = detect_signals(tables)
    have = {c["platform"] for c in topo.channels}
    sig["extra_channels"] = [c for c in sig.pop("_present", set()) if c not in have]
    # RC-8 (raw-path confirm) applies only once detection has populated a topology that had nothing stated
    sig["raw_path"] = topo.entry_path == tm.RAW and any(r.detected is not None for r in topo.resolved.values())
    return {k: v for k, v in sig.items() if not k.startswith("_")}, rc.evaluate(topo, sig)


def identify_payload(tid, tables, files):
    """The full /api/ingest/identify response: recognition + checklist (Amazon + Shopify) + overlaps +
    conflicts + the new detection signals & reconcile prompts."""
    covered = {f["type"] for f in files if f["recognized"]}
    checklist = [{**c, "present": c["type"] in covered}
                 for ch in cat.CHANNELS if ch["active"]
                 for c in cat.channel_checklist(ch["channel"])]
    detected, reconcile = _reconcile(tid, tables)
    return {"ok": True, "files": files, "checklist": checklist,
            "overlaps": detect_overlaps(tables), "conflicts": cflt.detect_conflicts(tables),
            "ready": bool(covered & cat.SKU_SOURCES), "has_cogs": rz.COGS in covered,
            "detected": detected, "reconcile": reconcile}


def file_meta(filename, df, rt):
    return {"filename": filename, "type": rt, "label": cat.LABELS.get(rt),
            "recognized": rt in cat.LABELS, "rows": int(len(df)) if df is not None else 0,
            "periods": sorted(_file_periods(df)) if df is not None else []}
