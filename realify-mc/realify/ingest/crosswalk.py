"""SKU crosswalk + record-level dedup for cross-channel onboarding (spec §5).

Unify Amazon + Shopify at the SKU level: map (channel, store_id, external_sku, external_variant_id) ->
canonical_sku_id (= internal_sku, R4). Auto-map when a Shopify Variant SKU equals an existing Amazon
SKU; park blank-SKU and bundle/kit variants into an unmapped bucket (surfaced, never distorting
rollups); flag same-product-different-SKU for manual reconcile.

Dedup is RECORD-level, not file-hash: Shopify exports are overlapping date-range slices, so we upsert on
each row's shared natural_keys (from the manifest) — a wider re-export never double-counts. File-hash
(recognizer.content_hash / IngestedReportRepository) stays advisory ("you already uploaded this file").
"""
from realify.topology_model import RECONCILED  # noqa: F401  (kept for symmetry with reconcile flow)

MAPPED, UNMAPPED, PARKED = "MAPPED", "UNMAPPED", "PARKED"


def _clean(v):
    s = "" if v is None else str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def auto_map(shopify_variants, amazon_skus, store_id="", parity="MOSTLY", bundle_skus=None):
    """Resolve Shopify product variants to canonical SKUs.

    shopify_variants: [{sku, variant_id, handle?}] from an ingested SHOP_PRODUCTS.
    amazon_skus: set of existing canonical internal_skus.
    parity: the stated/effective sku_parity (IDENTICAL | MOSTLY | NONE) — governs how a present-but-
            unmatched Shopify SKU is treated (a stated-IDENTICAL mismatch is parked + arms reconcile).

    Returns (entries, summary, arm_reconcile). Each entry is a crosswalk upsert dict; canonical_sku_id is
    the shared SKU when it maps, else None for a parked row.
    """
    amazon = {str(s) for s in (amazon_skus or set())}
    bundles = {str(s) for s in (bundle_skus or set())}
    entries, mapped, parked_blank, parked_bundle, unmatched = [], 0, 0, 0, 0
    for v in shopify_variants:
        sku = _clean(v.get("sku"))
        vid = _clean(v.get("variant_id"))
        base = {"channel": "shopify", "store_id": store_id or "", "external_sku": sku,
                "external_variant_id": vid}
        if not sku:                                              # blank SKU → unmapped bucket
            entries.append({**base, "canonical_sku_id": None, "status": UNMAPPED}); parked_blank += 1
        elif sku in bundles:                                     # bundle/kit → park (v1: flag, don't decompose)
            entries.append({**base, "canonical_sku_id": None, "status": PARKED}); parked_bundle += 1
        elif sku in amazon:                                      # auto-map: shared SKU code
            entries.append({**base, "canonical_sku_id": sku, "status": MAPPED}); mapped += 1
        elif amazon and parity == "IDENTICAL":                   # stated identical, but this one doesn't line up
            entries.append({**base, "canonical_sku_id": None, "status": PARKED}); unmatched += 1
        else:                                                    # a legitimately distinct SKU → its own canonical
            entries.append({**base, "canonical_sku_id": sku, "status": MAPPED}); mapped += 1
    summary = {"mapped": mapped, "unmapped_blank": parked_blank, "parked_bundle": parked_bundle,
               "unmatched": unmatched, "total": len(shopify_variants)}
    return entries, summary, unmatched > 0                       # arm CROSSWALK_RECONCILE when a mismatch parks


def dedupe_records(records, natural_keys):
    """Record-level dedup/upsert: collapse rows sharing the same natural-key tuple, LAST wins (an upsert,
    never a sum). Rows missing a key are kept as-is (can't be deduped without their identity). Overlapping
    re-exports of the same slice converge; a genuinely new row survives."""
    keys = tuple(natural_keys or ())
    out, seen = [], {}
    for rec in records:
        if keys and all(k in rec for k in keys):
            kt = tuple(_clean(rec.get(k)) for k in keys)
            if kt in seen:
                out[seen[kt]] = rec                              # upsert: later export replaces the row
                continue
            seen[kt] = len(out)
        out.append(rec)
    return out
