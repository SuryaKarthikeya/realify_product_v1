"""1b ingestion writer — persist a report-aware ingest into own-data, with provenance.

Takes the IngestResult from realify/ingest/report_ingest.py and writes, per SKU:
  * seller_skus real values (paid-only ASP, actual fees — the reconciled PoC math),
  * per-unit economics via realify/domain/economics.py (same math the PoC and the CMAA tab use),
  * sku_field_provenance rows (basis/source per field, plus the estimate alternate for fees).

Sticky edits: a field a seller has edited (provenance basis='seller', edited=1) is NOT overwritten
by a re-uploaded report; the report's differing value is recorded in provenance as the report basis,
flagged for review, but the seller value stays the value-of-record. No fabrication: fields absent
from the reports stay NULL.
"""
from realify.domain import economics
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.provenance_repo import ProvenanceRepository
from realify.repositories.ad_performance_repo import AdPerformanceRepository
from realify.repositories.revenue_period_repo import RevenuePeriodRepository
from realify.repositories.order_repo import OrderRepository
from realify.repositories.fact_repos import SettlementRepository
from realify.repositories.channel_repo import StorageFeeRepository, ReturnsRepository

# fields we lift from the ingest into seller_skus, with the provenance basis each carries
_VALUE_FIELDS = ["title", "category", "price", "cogs", "referral_fee", "fba_fee",
                 "units_month", "returns_rate", "buybox_pct", "replacement_units", "mcf_units",
                 "provisional_units", "tacos", "stock_on_hand"]
# fields a seller can own; a seller edit on these is sticky against re-upload
_SELLER_OWNED = {"cogs", "margin_floor", "lifecycle_flag", "title_override"}


def write_ingest(con, tenant_id, result):
    """Write an IngestResult for a tenant. Returns a small summary dict."""
    seller = SellerRepository(con)
    prov = ProvenanceRepository(con)
    written = 0
    for sku, rec in result.skus.items():
        existing = seller.get_full(tenant_id, sku) or {}
        row = {"internal_sku": sku, "channel": "amazon",
               "asin": (rec["asin"].value if "asin" in rec else None) or existing.get("asin") or sku}

        for f in _VALUE_FIELDS:
            if f not in rec:
                continue
            fld = rec[f]
            # sticky: don't overwrite a seller-edited value; record the report value for review
            if f in _SELLER_OWNED and prov.is_seller_edited(tenant_id, sku, f):
                prov.set(tenant_id, sku, f, fld.basis, fld.source, fld.value, edited=0)  # report alternate
                continue
            row[f] = fld.value
            prov.set(tenant_id, sku, f, fld.basis, fld.source, fld.value, edited=0)
            # keep the losing-basis alternate (e.g. the fee-preview ESTIMATE beside the actual)
            for alt_val, alt_basis in getattr(fld, "alternates", [])[:1]:
                if alt_basis != fld.basis:
                    prov.set(tenant_id, sku, f, alt_basis, alt_basis, alt_val, edited=0)

        # carry any prior seller edit forward as the value-of-record
        for f in _SELLER_OWNED:
            if prov.is_seller_edited(tenant_id, sku, f) and existing.get(f) is not None:
                row[f] = existing[f]

        _apply_economics(row)
        # merge over existing so unrelated columns (rating, stock, etc.) aren't clobbered
        merged = {**existing, **{k: v for k, v in row.items() if v is not None}}
        merged.update({k: row[k] for k in ("internal_sku", "asin", "channel") if k in row})
        seller.upsert_full(tenant_id, merged)
        written += 1

    # period-aware ad dimension (Step 2): persist SKU-resolved ad periods
    ad_written = 0
    for rec in (result.ad_periods or []):
        if rec.get("internal_sku"):
            AdPerformanceRepository(con).upsert(
                tenant_id, rec["internal_sku"], rec["period_start"], rec["grain"],
                rec["spend"], rec["sales"], source="sp_report_upload")
            ad_written += 1

    # per-period settled revenue (Step 4): TACoS denominator
    rev_written = 0
    for rec in (result.revenue_periods or []):
        RevenuePeriodRepository(con).upsert(
            tenant_id, rec["internal_sku"], rec["period_start"], rec["grain"],
            rec["revenue"], rec["units"])
        rev_written += 1

    # raw per-order rows (Unified Transaction 'Order' lines) — the row-level detail ad_periods/
    # revenue_periods (period-aggregated) don't cover, feeding seller_orders/settlements directly.
    # Replaces this channel's prior rows wholesale (delete-then-insert) so a re-upload doesn't
    # accumulate duplicates on top of an unchanged order set.
    orders_written = settlements_written = 0
    if result.settlement_rows:
        sku_to_asin = {sku: (rec["asin"].value if "asin" in rec else None) for sku, rec in result.skus.items()}
        order_repo, settle_repo = OrderRepository(con), SettlementRepository(con)
        order_repo.delete_by_channel(tenant_id, "amazon")
        settle_repo.delete_by_channel(tenant_id, "amazon")
        order_batch, settle_batch = [], []
        for r in result.settlement_rows:
            sku = r["sku"]
            asin = sku_to_asin.get(sku) or sku
            order_batch.append((tenant_id, r["order_id"], asin, r["order_date"], r["units"],
                               r["gross"], r["referral_fee"], r["fba_fee"], "amazon", sku))
            settle_batch.append((tenant_id, "amazon", sku, r["order_id"], r["settlement_date"],
                                r["gross"], r["fees"], r["payout"], None))
        order_repo.insert_many_imported(order_batch)
        settle_repo.insert_many(settle_batch)
        orders_written, settlements_written = len(order_batch), len(settle_batch)

    # per-period storage fee rows (Storage Fee report) — real monthly_storage_fee per SKU/period,
    # feeding the storage_fees table CM2 already reads. aged_surcharge/volume_cuft/age_days stay
    # None: not present in this report type (surcharge/age) or unit-ambiguous (volume) — see
    # realify.ingest.periods._storage_fee_rows.
    storage_fees_written = 0
    if result.storage_fee_rows:
        storage_repo = StorageFeeRepository(con)
        storage_repo.delete_by_channel(tenant_id, "amazon")
        storage_batch = [(tenant_id, "amazon", r["internal_sku"], r["period"], r["monthly_storage_fee"],
                          None, None, None) for r in result.storage_fee_rows]
        storage_repo.insert_many(storage_batch)
        storage_fees_written = len(storage_batch)

    # real refund rows (Unified Transaction 'Refund' lines) — the dollar-refund data the FBA
    # Customer Returns report can't supply (it only has a unit count, no $ column). Feeds the
    # returns table CM2/Net Revenue already read.
    returns_written = 0
    if result.return_rows:
        returns_repo = ReturnsRepository(con)
        returns_repo.delete_by_channel(tenant_id, "amazon")
        returns_batch = [(tenant_id, "amazon", r["sku"], r["return_date"], r["order_id"],
                         r["units"], None, r["refund_amount"]) for r in result.return_rows]
        returns_repo.insert_many(returns_batch)
        returns_written = len(returns_batch)

    # rev_share_pct: each SKU's share of total annual revenue (needs the full set, so second pass)
    all_rows = seller.all(tenant_id)
    total_rev = sum((r.get("annual_rev_inr") or 0) for r in all_rows) or 1
    for r in all_rows:
        ar = r.get("annual_rev_inr")
        if ar is not None:
            seller.update_fields_by_asin(tenant_id, r["asin"], {"rev_share_pct": round(ar / total_rev * 100, 2)})

    # refresh model-estimated COGS suggestions now that cost inputs may have changed
    try:
        from realify import models
        models.recompute_cogs(con, tenant_id)
    except Exception:
        pass  # suggestions are advisory; never block an ingest on the estimator

    return {"skus_written": written, "identity_map": len(result.identity_map),
            "unmapped_asins": len(result.unmapped_asins),
            "ad_periods_written": ad_written, "revenue_periods_written": rev_written,
            "orders_written": orders_written, "settlements_written": settlements_written,
            "storage_fees_written": storage_fees_written, "returns_written": returns_written}


def _apply_economics(row):
    """Compute per-unit economics from the reconciled inputs (no fabrication when inputs missing)."""
    e = economics.per_unit(row.get("price"), row.get("cogs"),
                           row.get("referral_fee"), row.get("fba_fee"),
                           row.get("return_cost_unit"), row.get("ad_cost_unit"))
    for k, v in e.items():
        if v is not None:
            row[k] = v
    # revenue projections from monthly units + price, so the pipeline's revenue-ranked detectors
    # (and the dashboard's exposure figures) have real numbers to work with. Only when both exist —
    # never fabricated. days_of_cover stays absent until BOTH stock_on_hand (from a Storage Fee
    # report) and velocity_day (derived here) exist; detectors that need it skip rather than guess.
    um, price = row.get("units_month"), row.get("price")
    if um is not None and price is not None:
        row["units_year"] = um * 12
        row["annual_rev_inr"] = round(um * 12 * price, 2)
        row["velocity_day"] = round(um / 30.0, 3)
    if row.get("stock_on_hand") is not None:
        # Amazon's Storage Fee report gives an AVERAGE daily on-hand quantity, naturally
        # fractional (stock fluctuates day to day) — round to a whole unit count for storage.
        row["stock_on_hand"] = int(round(row["stock_on_hand"]))
        if row.get("velocity_day"):
            row["days_of_cover"] = round(row["stock_on_hand"] / row["velocity_day"], 1)


def recompute_one(con, tenant_id, sku):
    """After a seller edit, recompute this SKU's economics from its current stored values."""
    seller = SellerRepository(con)
    row = seller.get_full(tenant_id, sku)
    if not row:
        return None
    _apply_economics(row)
    seller.upsert_full(tenant_id, row)
    return row
