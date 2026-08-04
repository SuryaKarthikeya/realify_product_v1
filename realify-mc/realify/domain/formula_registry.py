"""Formula registry — the single PROGRAMMATIC source for every number the Fix-Ads surface shows.

Rules-as-data: `formula_id -> {expression, inputs, source}`. The UI renders `expression` with a SKU's
actual inputs substituted (the ƒ explainability reveal, spec §4); the payload tags each number with its
`formula_id` so `test_every_number_has_registered_formula` can assert nothing is rendered without a
registered formula. Mirrored on the admin page (/ops/formulas ← docs/FORMULAS.md) so the two stay in
lockstep — expressions here match FORMULAS.md's "CMAA" + "SIMULATE" sections; the fix-ads-specific ones
(coverage / recoverable / projection / tripwire / combined) were backfilled into FORMULAS.md alongside.
"""
SOURCE = "admin registry"

FORMULAS = {
    "break_even_acos": {
        "expression": "break_even_acos = contribution_before_ads ÷ net_settled_revenue",
        "inputs": ("contribution_before_ads", "net_settled_revenue")},
    "acos": {
        "expression": "acos = ad_spend ÷ ad_attributed_sales",
        "inputs": ("ad_spend", "ad_attributed_sales")},
    "cmaa": {
        "expression": "cmaa = settled_revenue − cogs − fees − ad_spend",
        "inputs": ("settled_revenue", "cogs", "fees", "ad_spend")},
    "recoverable": {   # FORMULAS.md "₹ above break-even (certain waste)" — the real source, not the mockup's toy
        "expression": "recoverable = max(ad_spend − ad_attributed_sales × break_even_acos, 0)",
        "inputs": ("ad_spend", "ad_attributed_sales", "break_even_acos")},
    "ad_coverage": {
        "expression": "coverage = mapped_ad_spend ÷ total_ad_spend",
        "inputs": ("mapped_ad_spend", "total_ad_spend")},
    "cmaa_projection": {
        "expression": "proj_cmaa_gain(t) = saved_spend(bid,t) − lost_margin_from_volume(bid,t)",
        "inputs": ("bid_change", "horizon_days", "recoverable", "organic_hold", "margin")},
    "tripwire_units": {
        "expression": "tripwire = units_wk < baseline_units_wk × (1 − 0.15)",
        "inputs": ("units_wk", "baseline_units_wk")},
    "combined_projection": {
        "expression": "combined = Σ proj_gain(recommendation_i)",
        "inputs": ("per_recommendation_gains",)},
}


def get(formula_id):
    """The registered formula (with a source stamp) or None."""
    f = FORMULAS.get(formula_id)
    return {**f, "formula_id": formula_id, "source": SOURCE} if f else None


def has(formula_id):
    return formula_id in FORMULAS


def all_ids():
    return list(FORMULAS)


def tag(formula_id, substituted, value):
    """Build a UI-ready formula tag for one rendered number: the registered expression + a substituted
    string (`= ₹8,200 ÷ ₹20,000 = 41%`) + the source stamp. Raises if the formula_id is unregistered —
    a rendered number must always resolve to a registered formula (spec §4 enforcement)."""
    f = get(formula_id)
    if not f:
        raise KeyError(f"formula_id '{formula_id}' is not in the admin registry")
    return {"formula_id": formula_id, "expression": f["expression"],
            "substituted": substituted, "value": value, "source": SOURCE}
