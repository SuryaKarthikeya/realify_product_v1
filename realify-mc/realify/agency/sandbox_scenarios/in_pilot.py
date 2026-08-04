"""India Pilot (R9 Part B). One agency, 8 managed INR brands + 1 direct brand, auto-accessories,
Amazon.in / Flipkart / Shopzee, Diwali ramp. Single-country (₹, en-IN lakh grouping). Deterministic from
seed in-pilot-v1. Built through the shared synth spec builder (locale = India)."""
from ..synth import spec_from_params

SEED = "in-pilot-v1"
SPEC = spec_from_params({
    "country": "IN",
    "categories": ["Car cover", "Dashcam", "Phone mount", "Tyre inflator"],
    "sku_count": 480,
    "brands_per_agency": 8,
    "direct_brands": 1,
    "depth": "rich",
    "moments": ["stockout", "acos_over_breakeven", "competitor_undercut", "expired_conn"],
    "seed": SEED,
    "agency_name": "Kavery Commerce",
})
