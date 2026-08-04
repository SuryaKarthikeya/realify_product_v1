"""Fidelity ladder (spec A2) — how precise a recommendation can be, decided purely by which ad reports
are present. Pure logic, no I/O. The value stamps every recommendation so the UI shows its grade.

  KEYWORD      — Search Term report present -> can name specific targets/terms -> NEGATIVE_KEYWORD and
                 target-specific BID_DOWN are possible.
  CAMPAIGN_SKU — Advertised Product present, no Search Term -> campaign/ad-group precision -> BID_DOWN at
                 campaign/ad-group level + REMOVE_PRODUCT_AD.
  CHANNEL_ONLY — only a campaign-summary file -> CMAA at channel level, no per-SKU actions.
"""
KEYWORD = "KEYWORD"
CAMPAIGN_SKU = "CAMPAIGN_SKU"
CHANNEL_ONLY = "CHANNEL_ONLY"

#: raised when only a campaign-summary file is present — per-SKU attribution is impossible, not faked.
AD_GRANULARITY_INSUFFICIENT = "AD_GRANULARITY_INSUFFICIENT"


def fidelity(has_advertised_product, has_search_term, has_campaign_only=False):
    if has_advertised_product and has_search_term:
        return KEYWORD
    if has_advertised_product:
        return CAMPAIGN_SKU
    return CHANNEL_ONLY


def granularity_flag(has_advertised_product, has_campaign_only):
    """AD_GRANULARITY_INSUFFICIENT when the tenant uploaded only a campaign-summary file (no advertised
    product), so we show channel-level CMAA and prompt for the Advertised Product export."""
    if not has_advertised_product and has_campaign_only:
        return AD_GRANULARITY_INSUFFICIENT
    return None
