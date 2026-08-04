"""Per-tenant country profiles. Country is stored per-tenant in tenant_settings
(key='country'), NOT in .env — so two accounts can run IN and US side by side.
This module resolves a country code to marketplace routing (Keepa domain, recall
region, news/trends locale, currency) AND to a synthetic-economics profile (price
bands, fee schedule, seasonality) so US data is data-correct, not rupee-logic with
a dollar sign."""
from . import db, config
from .repositories.seller_repo import SellerRepository

PROFILES = {
    "IN": {
        "country": "IN", "marketplace": "amazon.in", "keepa_domain": "IN",
        "recall_region": "IN", "news_locale": "in", "trends_geo": "IN",
        "currency": "INR", "symbol": "\u20b9",            # ₹
        # economics (synthetic): price bands by category, fee schedule, seasonality
        "price_band": (299, 2499),
        "referral_pct": 0.155,                            # typical IN referral
        "fba_fee_base": 70.0, "fba_fee_per_band": 28.0,
        "fba_fee_pct": 0.06, "fba_fee_floor": 20.0,       # R11.1: FBA scales with price (size proxy)
        "cogs_pct_of_price": (0.30, 0.55),
        "ad_cost_unit_pct": (0.04, 0.12),
        "peak_months": [10, 11],                          # Diwali / Great Indian Festival (Oct–Nov)
        "peak_label": "Diwali / Great Indian Festival",
    },
    "US": {
        "country": "US", "marketplace": "amazon.com", "keepa_domain": "US",
        "recall_region": "US", "news_locale": "us", "trends_geo": "US",
        "currency": "USD", "symbol": "$",
        "price_band": (9.99, 79.99),
        "referral_pct": 0.15,                             # typical US referral
        "fba_fee_base": 3.22, "fba_fee_per_band": 1.20,
        "fba_fee_pct": 0.11, "fba_fee_floor": 1.50,       # R11.1: FBA scales with price (size proxy)
        "cogs_pct_of_price": (0.25, 0.50),
        "ad_cost_unit_pct": (0.05, 0.14),
        "peak_months": [7, 11],                           # Prime Day (Jul) / Black Friday–Cyber Monday (Nov)
        "peak_label": "Prime Day / Black Friday",
    },
}
DEFAULT = "IN"

def normalize(code):
    return (code or DEFAULT).upper() if (code or DEFAULT).upper() in PROFILES else DEFAULT

def profile(code):
    return PROFILES[normalize(code)]


def estimate_fees(price, prof, rnd=None):
    """R11.1 realistic fees: referral scales with price; FBA scales with price too (a size/weight proxy)
    with a small floor and capped at a sane fraction of price — so a low-priced unit never carries a
    flat fee bigger than itself (the ₹115-FBA-on-₹29 bug that produced −381% margins). Returns
    (referral_fee, fba_fee), both per-unit, both < price."""
    price = float(price or 0)
    referral = round(price * prof["referral_pct"], 2)
    rate = prof.get("fba_fee_pct", 0.10)
    jitter = 1.0 if rnd is None else (0.85 + 0.30 * rnd.random())     # ±15% variety, deterministic via rnd
    fba = round(min(max(prof.get("fba_fee_floor", 0.0), price * rate * jitter), price * 0.35), 2)
    return referral, fba

def tenant_country(tenant_id, con=None):
    """The tenant's configured country (set at onboarding). Falls back to the
    server default if unset (older tenants)."""
    own = con is None
    if own: con = db.connect()
    try:
        c = db.get_setting(con, tenant_id, "country", None)
    except Exception:
        c = None
    if own: con.close()
    return normalize(c)

def tenant_profile(tenant_id, con=None):
    return profile(tenant_country(tenant_id, con))

def tenant_terms(tenant_id, con=None, n=6):
    """Search terms derived from the tenant's UPLOADED catalog — distinct categories and
    product types (subcategories) from seller_skus. Used to localize the News query and
    Trends terms to what the seller actually sells, instead of a hard-coded vertical.
    Falls back to a generic term if the catalog isn't loaded yet."""
    own = con is None
    if own: con = db.connect()
    terms = []
    try:
        for col in ("category", "ptype"):
            for v in SellerRepository(con).distinct_values(tenant_id, col):
                v = (v or "").strip()
                if v and v.lower() not in {t.lower() for t in terms}:
                    terms.append(v)
    except Exception:
        pass
    if own: con.close()
    return terms[:n] or ["consumer products"]

# ---- per-run active profile so the money formatters localize symbol + scale ----
import threading as _threading
_local = _threading.local()
def set_active(prof):
    _local.prof = prof
def active():
    return getattr(_local, "prof", PROFILES[DEFAULT])
def use_tenant(tenant_id, con=None):
    set_active(tenant_profile(tenant_id, con)); return active()

def fmt_money(x, prof=None):
    """Locale-aware money: ₹..L/cr for IN, $..K/M for US."""
    prof = prof or active()
    sym = prof["symbol"]
    try: x = float(x)
    except (TypeError, ValueError): return f"{sym}0"
    if prof["country"] == "IN":
        if x >= 1e7: return f"{sym}{x/1e7:.1f}cr"
        if x >= 1e5: return f"{sym}{x/1e5:.1f}L"
        if x >= 1e3: return f"{sym}{x/1e3:.0f}K"
        return f"{sym}{x:.0f}"
    # US / western grouping
    if x >= 1e6: return f"{sym}{x/1e6:.2f}M"
    if x >= 1e3: return f"{sym}{x/1e3:.1f}K"
    return f"{sym}{x:,.2f}" if x < 100 else f"{sym}{x:,.0f}"
