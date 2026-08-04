"""Source-aware file manifest — rules-as-DATA for cross-channel onboarding (spec §4 / §4.1).

Each row is a DATA NEED, not a file. It carries a slot per acquisition mode — `csv` and `inline` are
wired in v1; `api` is declared-but-DORMANT (the future connected-source lane, §14) so wiring it later is
a job, not a reshape. `natural_keys` are SHARED across acquisition modes, so a CSV upload and a future
API pull of the same records idempotently converge on the same rows (record-level dedup, §4).

Adding a channel or ad partner = adding rows here — no new code branch. The recognizer (Shopify
signatures) and the onboarding checklist both read these rows; the wizard node graph (§6) emits their
`file_row_id`s, and referential integrity (every emit → a real manifest row) is test-enforced.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

# groups (fixed display order Amazon · Shopify · Ads · COGS) + essentiality vocabulary
AMAZON, SHOPIFY, ADS, COGS = "AMAZON", "SHOPIFY", "ADS", "COGS"
ESSENTIAL, SUPPORTING, OPTIONAL = "ESSENTIAL", "SUPPORTING", "OPTIONAL"


@dataclass(frozen=True)
class CsvSlot:
    fingerprint_tokens: Tuple      # header tokens (str, or an ANY-OF tuple); ALL required to classify
    where_to_find: str             # checklist copy
    arrival_hint: str              # INSTANT | EMAILED (drives resumability copy)


@dataclass(frozen=True)
class InlineSlot:
    control: str                   # in-app control id (e.g. COGS_INLINE)


@dataclass(frozen=True)
class ApiSlot:                     # DORMANT in v1 — declared so §14 is a wiring job, not a reshape
    provider: str
    pull: str


@dataclass(frozen=True)
class ManifestEntry:
    file_row_id: str
    group: str
    essentiality: str
    data_need: str
    natural_keys: Tuple            # SHARED across acquisition modes → idempotent record-level upsert
    csv: Optional[CsvSlot] = None
    inline: Optional[InlineSlot] = None
    api: Optional[ApiSlot] = None

    def satisfiable_by(self):
        """Acquisition modes this need supports — derived from which slots are non-null. v1 renders
        UPLOAD/INLINE; CONNECT shows once the api slot is wired (§9)."""
        modes = []
        if self.csv:
            modes.append("UPLOAD")
        if self.inline:
            modes.append("INLINE")
        if self.api:
            modes.append("CONNECT")
        return tuple(modes)


def _amz(fid, essent, need, keys, where, arrival, tokens, provider, pull):
    return ManifestEntry(fid, AMAZON, essent, need, keys,
                         csv=CsvSlot(tokens, where, arrival), api=ApiSlot(provider, pull))


MANIFEST = [
    # ---- SHOPIFY (new; recognizer sources its fingerprints from these rows) ----
    ManifestEntry("SHOP_ORDERS", SHOPIFY, ESSENTIAL, "Shopify booked orders (units, gross, discount, tax)",
                  ("order_name", "lineitem_id"),
                  csv=CsvSlot(("Name", "Lineitem sku", "Lineitem quantity", "Financial Status", "Fulfillment Status"),
                              "Admin → Orders → Export (by date; >50 orders emailed)", "EMAILED"),
                  api=ApiSlot("Shopify Admin API", "Orders")),
    ManifestEntry("SHOP_PRODUCTS", SHOPIFY, ESSENTIAL, "Shopify product cost (COGS) & variants",
                  ("variant_id",),
                  csv=CsvSlot(("Handle", "Variant SKU", "Cost per item"), "Admin → Products → Export", "INSTANT"),
                  api=ApiSlot("Shopify Admin API", "Products/Variants (incl. cost)")),
    ManifestEntry("SHOP_INVENTORY", SHOPIFY, ESSENTIAL, "Shopify inventory by location",
                  ("sku", "location"),
                  csv=CsvSlot(("SKU", "Location", ("Available", "On hand")),
                              "Admin → Products → Inventory → Export", "INSTANT"),
                  api=ApiSlot("Shopify Admin API", "Inventory levels by location")),
    ManifestEntry("SHOP_PAYOUTS", SHOPIFY, ESSENTIAL, "Shopify settled revenue & processing fees",
                  ("transaction_id",),
                  csv=CsvSlot(("Type", "Fee", "Net", "Payout Date"),
                              "Admin → Settings → Payments → View payouts → View transactions → Export", "EMAILED"),
                  api=ApiSlot("Shopify Payments", "Balance transactions")),
    ManifestEntry("SHOP_PAYOUT_RECON", SHOPIFY, SUPPORTING, "Shopify payout reconciliation",
                  ("payout_id",),
                  csv=CsvSlot(("Gross", "Fees", "Net", "Payout"),
                              "Admin → Finance → Documents (payout reconciliation report)", "EMAILED")),
    ManifestEntry("SHOP_PAYMENTS_SUMMARY", SHOPIFY, SUPPORTING, "Shopify payments / finances summary",
                  ("period",),
                  csv=CsvSlot(("Net sales", "Refunds", "Taxes"),
                              "Admin → Analytics → Reports → Payments / Finances summary", "INSTANT")),
    ManifestEntry("SHOP_BILLS", SHOPIFY, OPTIONAL, "Shopify billing statements",
                  ("bill_id",),
                  csv=CsvSlot(("Bill", "Type", "Amount"), "Admin → Settings → Billing → Export bills", "EMAILED")),
    # ---- AMAZON (existing recognizer owns detection; rows here drive checklist + emit integrity) ----
    _amz("AMZ_SETTLEMENT", ESSENTIAL, "Amazon settled revenue & fees", ("settlement_id", "order_id"),
         "Seller Central → Payments → Date Range Reports (Transaction)", "EMAILED",
         ("settlement id", "product sales", "selling fees", "fba fees"), "SP-API", "Finances"),
    _amz("AMZ_ORDERS", ESSENTIAL, "Amazon orders (units sold)", ("amazon_order_id", "sku"),
         "Seller Central → Reports → Business Reports / Orders", "EMAILED",
         ("(child) asin", "sessions - total", "units ordered"), "SP-API", "Reports/Orders"),
    _amz("AMZ_INV_FBA", ESSENTIAL, "Amazon FBA inventory on hand", ("sku",),
         "Seller Central → FBA Inventory report", "INSTANT",
         ("estimated-monthly-storage-fee", "average-quantity-on-hand"), "SP-API", "FBA Inventory"),
    _amz("AMZ_INV_FBM", ESSENTIAL, "Amazon FBM (merchant) inventory", ("seller-sku",),
         "Seller Central → All Listings report", "INSTANT",
         ("seller-sku", "asin1"), "SP-API", "Listings"),
    _amz("AMZ_MCF_FEES", ESSENTIAL, "Amazon MCF / multi-channel fulfilment fees (required only when MCF)",
         ("sku", "period"), "Seller Central → MCF / fulfilment fee report", "EMAILED",
         ("multi-channel", "fulfillment fee"), "SP-API", "Fulfillment fees"),
    # ---- ADS (partner exports; tokens are placeholders — recognizer wiring is Team-7/future) ----
    ManifestEntry("AD_AMAZON", ADS, ESSENTIAL, "Amazon ad spend & attributed sales", ("advertised_asin", "period"),
                  csv=CsvSlot(("advertised asin", "spend", "total advertising cost of sales"),
                              "Amazon Ads console export", "EMAILED"),
                  api=ApiSlot("Amazon Ads API", "reports")),
    ManifestEntry("AD_META", ADS, ESSENTIAL, "Meta ad spend", ("campaign_ref", "period"),
                  csv=CsvSlot(("Amount spent", "Campaign name"), "Meta Ads Manager export", "EMAILED"),
                  api=ApiSlot("Meta Ads API", "insights")),
    ManifestEntry("AD_GOOGLE", ADS, ESSENTIAL, "Google ad spend", ("campaign_ref", "period"),
                  csv=CsvSlot(("Campaign", "Cost"), "Google Ads export", "EMAILED"),
                  api=ApiSlot("Google Ads API", "reports")),
    ManifestEntry("AD_TIKTOK", ADS, ESSENTIAL, "TikTok ad spend", ("campaign_ref", "period"),
                  csv=CsvSlot(("Cost", "Campaign name"), "TikTok Ads export", "EMAILED"),
                  api=ApiSlot("TikTok Ads API", "reports")),
    ManifestEntry("AD_WALMART", ADS, ESSENTIAL, "Walmart Connect ad spend", ("campaign_ref", "period"),
                  csv=CsvSlot(("Ad Spend", "Campaign Name"), "Walmart Connect export", "EMAILED"),
                  api=ApiSlot("Walmart Connect API", "reports")),
    # ---- COGS (inline entry; not a fingerprinted file) ----
    ManifestEntry("COGS_INLINE", COGS, OPTIONAL, "Product cost per unit (inline entry)",
                  ("canonical_sku",), inline=InlineSlot("COGS_INLINE")),
]

_BY_ID = {m.file_row_id: m for m in MANIFEST}


def by_id(file_row_id):
    return _BY_ID.get(file_row_id)


def all_ids():
    return tuple(m.file_row_id for m in MANIFEST)


def csv_fingerprints():
    """{file_row_id: fingerprint_tokens} for SHOPIFY rows — the recognizer's Shopify signature source.
    Amazon detection stays inline in the recognizer (behavior-preserving); ad-partner tokens are
    placeholders not yet wired into detection."""
    return {m.file_row_id: m.csv.fingerprint_tokens for m in MANIFEST
            if m.csv and m.group == SHOPIFY}
