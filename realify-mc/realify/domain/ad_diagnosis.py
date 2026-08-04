"""SKU-slice diagnosis (spec A5) — evaluate a losing SKU at the campaign->target grain, NEVER a campaign
average. Pure logic; reuses the locked CMAA math (acos, wasted_spend). Inputs are the SKU's per-(campaign,
ad_group) slices from AdEntityPerfRepository (already the SKU slice, so a campaign that's healthy overall
but bleeding on THIS SKU is evaluated on its slice, not hidden) and the SP search terms for those slices.
"""
from realify.domain import cmaa
from realify.domain.ad_fidelity import KEYWORD


def _acos(spend, sales):
    return cmaa.acos(spend, sales)


def diagnose(sku, break_even_acos, slices, terms_by_adgroup=None, fidelity=None):
    """Return the SKU's ad diagnosis. `slices` = [{campaign, ad_group, spend, sales, clicks, orders}].
    `terms_by_adgroup` = {(campaign, ad_group): [term rows]} (only used at KEYWORD fidelity)."""
    terms_by_adgroup = terms_by_adgroup or {}
    by_campaign = {}
    for s in slices:
        c = by_campaign.setdefault(s["campaign"], {"campaign": s["campaign"], "spend": 0.0, "sales": 0.0,
                                                   "orders": 0.0, "ad_groups": set()})
        c["spend"] += s.get("spend") or 0.0
        c["sales"] += s.get("sales") or 0.0
        c["orders"] += s.get("orders") or 0.0
        c["ad_groups"].add((s["campaign"], s["ad_group"]))
    total_spend = round(sum(c["spend"] for c in by_campaign.values()), 2)
    total_sales = round(sum(c["sales"] for c in by_campaign.values()), 2)

    campaigns = []
    for c in by_campaign.values():
        ac = _acos(c["spend"], c["sales"])
        waste = cmaa.wasted_spend(c["spend"], c["sales"], break_even_acos) or 0.0
        offending = (ac is not None and break_even_acos is not None and ac > break_even_acos)
        campaigns.append({
            "campaign": c["campaign"], "spend": round(c["spend"], 2), "sales": round(c["sales"], 2),
            "acos_for_sku": ac, "wasted_spend": round(waste, 2),
            "spend_share": (c["spend"] / total_spend) if total_spend > 0 else 0.0,
            "offending": offending, "ad_groups": sorted(c["ad_groups"])})
    # rank campaigns by share of THIS SKU's ad spend (A5: "rank campaigns by share of the SKU's spend")
    campaigns.sort(key=lambda x: -x["spend_share"])
    offending_campaigns = sorted([c for c in campaigns if c["offending"]],
                                 key=lambda x: -x["wasted_spend"])

    # KEYWORD fidelity: rank offending targets/terms by wasted spend (spend above break-even, low/no conv)
    offending_terms = []
    if fidelity == KEYWORD:
        for c in campaigns:
            for ag in c["ad_groups"]:
                for t in terms_by_adgroup.get(ag, []):
                    ac = _acos(t.get("spend"), t.get("sales"))
                    waste = cmaa.wasted_spend(t.get("spend"), t.get("sales"), break_even_acos) or 0.0
                    over = ac is None or (break_even_acos is not None and ac > break_even_acos)
                    if waste > 0 and over:
                        offending_terms.append({
                            "campaign": ag[0], "ad_group": ag[1],
                            "customer_search_term": t.get("customer_search_term"),
                            "targeting": t.get("targeting"), "match_type": t.get("match_type"),
                            "spend": round(t.get("spend") or 0.0, 2), "sales": round(t.get("sales") or 0.0, 2),
                            "acos": ac, "orders": t.get("orders") or 0.0, "wasted_spend": round(waste, 2),
                            "no_conversion": (t.get("orders") or 0.0) == 0})
        offending_terms.sort(key=lambda x: -x["wasted_spend"])

    return {"sku": sku, "break_even_acos": break_even_acos,
            "total_ad_spend": total_spend, "total_ad_sales": total_sales,
            "sku_acos": _acos(total_spend, total_sales),
            "wasted_spend_total": round(sum(c["wasted_spend"] for c in offending_campaigns), 2),
            "campaigns": campaigns, "offending_campaigns": offending_campaigns,
            "offending_terms": offending_terms}
