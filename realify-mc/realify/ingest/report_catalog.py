"""Canonical, engine-backed report catalog — the reports the ingestion engine actually understands,
with the label and the dashboard capability each one unlocks. This drives the onboarding upload
checklist, so what the user sees named + checked off is exactly what lights up their dashboard
(unlike the older aspirational report list, whose CSV parsers were stubbed).
"""
from realify.ingest.report_ingest import (
    UNIFIED_TRANSACTION, FEE_PREVIEW, AD_REPORT, BUSINESS_REPORT,
    FBA_RETURNS, STORAGE_FEE, ALL_LISTINGS, COGS)

LABELS = {
    UNIFIED_TRANSACTION: "Monthly Unified Transaction",
    COGS: "COGS / unit costs",
    FEE_PREVIEW: "Fee Preview (Estimated Fees)",
    AD_REPORT: "Sponsored Products – Advertised Product",
    BUSINESS_REPORT: "Business Report (Sales & Traffic)",
    FBA_RETURNS: "FBA Customer Returns",
    STORAGE_FEE: "FBA Storage Fees",
    ALL_LISTINGS: "All Listings",
}

UNLOCKS = {
    UNIFIED_TRANSACTION: "true selling price, actual fees, velocity, returns, channel split",
    COGS: "margin & profit-after-ads",
    FEE_PREVIEW: "SKU↔ASIN mapping + estimated-vs-actual fees",
    AD_REPORT: "ACoS, TACoS-over-time, and ad spend above break-even",
    BUSINESS_REPORT: "Buy Box / Featured Offer %",
    FBA_RETURNS: "returns signal",
    STORAGE_FEE: "storage cost per SKU",
    ALL_LISTINGS: "catalog / ASIN mapping",
}

# display order for the Amazon channel checklist
AMAZON_REPORTS = [UNIFIED_TRANSACTION, COGS, FEE_PREVIEW, AD_REPORT,
                  BUSINESS_REPORT, FBA_RETURNS, STORAGE_FEE, ALL_LISTINGS]

# Shopify report types + copy sourced from the source-aware manifest (single source of truth), so the
# recognized-reports checklist and the recognizer stay in lockstep as rows are added.
from realify import topology as _topo  # noqa: E402
SHOPIFY_REPORTS = [m.file_row_id for m in _topo.MANIFEST if m.group == _topo.SHOPIFY]
LABELS.update({m.file_row_id: m.data_need for m in _topo.MANIFEST if m.group == _topo.SHOPIFY})
UNLOCKS.update({
    "SHOP_ORDERS": "Shopify units, gross, discounts & tax (booked revenue)",
    "SHOP_PRODUCTS": "Shopify COGS & variants → margin",
    "SHOP_INVENTORY": "Shopify stock by location (+ shared-FBA / MCF detection)",
    "SHOP_PAYOUTS": "settled net-of-fee revenue (the true Shopify margin base)",
    "SHOP_PAYOUT_RECON": "payout reconciliation detail",
    "SHOP_PAYMENTS_SUMMARY": "payments / finances summary",
    "SHOP_BILLS": "Shopify subscription / app billing",
})

# file_row_id -> recognizer type(s) that satisfy a checklist row (drives live ticking as files upload).
# Shopify rows are their own recognizer type; Amazon manifest rows map to the existing recognizer types;
# ad-partner + MCF-fee rows aren't recognized yet (they show on the checklist but don't auto-tick).
SATISFIED_BY_TYPES = {
    "AMZ_SETTLEMENT": [UNIFIED_TRANSACTION], "AMZ_ORDERS": [BUSINESS_REPORT],
    "AMZ_INV_FBA": [STORAGE_FEE], "AMZ_INV_FBM": [ALL_LISTINGS], "AMZ_MCF_FEES": [],
    "AD_AMAZON": [AD_REPORT], "AD_META": [], "AD_GOOGLE": [], "AD_TIKTOK": [], "AD_WALMART": [],
    "COGS_INLINE": [COGS],
}
SATISFIED_BY_TYPES.update({fid: [fid] for fid in SHOPIFY_REPORTS})

# any one of these establishes the SKU spine; COGS then unlocks margin
SKU_SOURCES = {UNIFIED_TRANSACTION, FEE_PREVIEW, ALL_LISTINGS, "SHOP_ORDERS", "SHOP_PRODUCTS"}

# channels the user can upload against. Amazon + Shopify are wired; the rest are coming-soon placeholders
# so the tab UI stays honest about what's live vs coming.
CHANNELS = [
    {"channel": "amazon", "label": "Amazon", "active": True, "reports": AMAZON_REPORTS},
    {"channel": "shopify", "label": "Shopify", "active": True, "reports": SHOPIFY_REPORTS},
    {"channel": "walmart", "label": "Walmart", "active": False, "reports": []},
]


def channel_checklist(channel="amazon"):
    codes = next((c["reports"] for c in CHANNELS if c["channel"] == channel), [])
    return [{"type": t, "label": LABELS[t], "unlocks": UNLOCKS.get(t, ""),
             "sku_source": t in SKU_SOURCES, "is_cogs": t == COGS} for t in codes]
