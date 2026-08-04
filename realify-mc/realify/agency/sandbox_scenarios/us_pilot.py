"""US Pilot — the BrightPeak story (R9 Part B). One agency, 8 managed USD brands + 1 direct brand,
Home/Pet/Outdoor, Amazon US / Walmart / Shopify. Single-country (USD, Western $ grouping). Deterministic
from seed us-pilot-v1. Built through the shared synth spec builder so it uses the same locale-aware path
as the parametric generator."""
from ..synth import spec_from_params

SEED = "us-pilot-v1"
SPEC = spec_from_params({
    "country": "US",
    "categories": ["Home & Kitchen", "Pet Supplies", "Outdoor"],
    "sku_count": 480,
    "brands_per_agency": 8,
    "direct_brands": 1,
    "depth": "rich",
    "moments": ["stockout", "acos_over_breakeven", "competitor_undercut", "expired_conn"],
    "seed": SEED,
    "agency_name": "BrightPeak Commerce",
})
