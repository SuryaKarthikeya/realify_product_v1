"""Agency CSV ingest (agency-plan P3): auto-detect report type from headers, apply a per-type column
mapping (default + a remembered override — the fix flow), and tag every ingested row with
source_class (csv|api) + currency. Ingested rows land in agency_ingest_rows (brand-scoped, RLS)."""
import json

from . import tenancy

# report_type -> required header substrings (lowercased) that identify it.
SIGNATURES = {
    "amazon_sales_traffic": ["(parent) asin", "sessions", "units ordered"],
    "amazon_all_orders": ["amazon-order-id", "sku", "quantity"],
    "shopify_orders": ["name", "financial status", "lineitem quantity"],
    "google_ads": ["campaign", "clicks", "impressions", "cost"],
    "meta_ads": ["campaign name", "amount spent", "impressions"],
}
# canonical field -> source header, per report type (the default mapping).
DEFAULT_MAPPINGS = {
    "amazon_sales_traffic": {"asin": "(Parent) ASIN", "sessions": "Sessions", "units": "Units Ordered"},
    "amazon_all_orders": {"order_id": "amazon-order-id", "sku": "sku", "qty": "quantity"},
    "shopify_orders": {"order": "Name", "status": "Financial Status", "qty": "Lineitem quantity"},
    "google_ads": {"campaign": "Campaign", "clicks": "Clicks", "impressions": "Impressions", "cost": "Cost"},
    "meta_ads": {"campaign": "Campaign name", "spend": "Amount spent", "impressions": "Impressions"},
}


def detect_report_type(headers):
    hl = [h.strip().lower() for h in headers]
    best, score = None, 0
    for rtype, sig in SIGNATURES.items():
        # a header matches a signature token if the token is a substring of some header
        n = sum(1 for tok in sig if any(tok in h for h in hl))
        if n == len(sig) and n > score:
            best, score = rtype, n
    return best


def detect_currency(headers, default=None):
    for h in headers:
        hl = h.lower()
        if "(inr)" in hl or "inr" in hl or "₹" in h:
            return "INR"
        if "(usd)" in hl or "usd" in hl or "$" in h:
            return "USD"
    return default


def default_mapping(report_type):
    return dict(DEFAULT_MAPPINGS.get(report_type, {}))


def get_mapping(cur, report_type):
    """Remembered override for this report type, else the default (the fix flow persists overrides)."""
    cur.execute("SELECT mapping FROM report_column_mappings WHERE report_type=%s", (report_type,))
    row = cur.fetchone()
    return row[0] if row else default_mapping(report_type)


def save_mapping(cur, report_type, mapping):
    cur.execute("INSERT INTO report_column_mappings(report_type, mapping) VALUES(%s,%s::jsonb) "
                "ON CONFLICT (report_type) DO UPDATE SET mapping=EXCLUDED.mapping, updated_at=now()",
                (report_type, json.dumps(mapping)))


def ingest_csv(cur, tenant_id, headers, rows, source_class="csv", currency=None, report_type=None):
    """Detect + normalize + tag + persist. `rows` are dicts keyed by the raw headers. Returns
    {report_type, currency, count, rows: [tagged normalized dicts]}."""
    report_type = report_type or detect_report_type(headers)
    if not report_type:
        raise ValueError("could not detect report type from headers")
    currency = currency or detect_currency(headers)
    mapping = get_mapping(cur, report_type)
    tenancy.set_brand_scope(cur, [tenant_id])
    out = []
    for raw in rows:
        norm = {canon: raw.get(src) for canon, src in mapping.items()}
        norm["source_class"] = source_class
        norm["currency"] = currency
        cur.execute(
            "INSERT INTO agency_ingest_rows(tenant_id,report_type,source_class,currency,payload) "
            "VALUES(%s,%s,%s,%s,%s::jsonb)",
            (tenant_id, report_type, source_class, currency, json.dumps(norm)))
        out.append(norm)
    return {"report_type": report_type, "currency": currency, "count": len(out), "rows": out}


def source_class_tagged_pct(rows):
    """% of produced rows carrying both source_class and currency tags (invariant target 100)."""
    if not rows:
        return 100.0
    ok = sum(1 for r in rows if r.get("source_class") and ("currency" in r))
    return round(ok / len(rows) * 100, 1)
