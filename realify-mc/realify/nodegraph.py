"""Wizard node graph as DATA (spec §6 + Table 1). A node is {id, prompt, type, field, gate, options};
an option carries its topology write + emits[] + arms[]. Adding Walmart/TikTok/an ad partner = new rows
here, no code branch. The emit resolver walks answered nodes → a TenantTopology + the union of emitted
manifest file_row_ids + armed flags. Referential integrity (every emit → a real manifest row) is
test-enforced against realify.topology.MANIFEST.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple

from .topology import ESSENTIAL as E, SUPPORTING as S, OPTIONAL as O
from . import topology_model as tm

SINGLE, MULTI = "single", "multi"


@dataclass(frozen=True)
class Opt:
    label: str
    value: object = None                 # value written to the node's topology field (Resolved.stated)
    emits: Tuple = ()                    # ((file_row_id, essentiality), ...)
    arms: Tuple = ()                     # (flag_id, ...)
    channel: Optional[Tuple] = None      # (platform, status) for CHANNELS options
    ad_partner: Optional[str] = None     # partner id for AD1 options
    mode: Optional[str] = None           # fulfilment mode added for S1 (multi)


@dataclass(frozen=True)
class Node:
    id: str
    prompt: str
    type: str
    field: Optional[str] = None          # topology.resolved field this node sets (single-select)
    always: bool = False                 # always shown (C1, AD1) — no gate
    optional: bool = False               # skippable (G1)
    baseline_emits: Tuple = ()           # emitted whenever the node is reached (S1/S3 baselines)
    options: Tuple = ()
    gate: Optional[Callable] = None      # (state) -> bool; state = the accumulating resolve context


def _has_channel(state, platform):
    return any(c["platform"] == platform and c["status"] == "ACTIVE" for c in state["channels"])


def _s2_gate(state):
    modes = set(state["resolved"].get("shopify_modes", ()) or ())
    amz = state["resolved"].get("amazon_mode")
    return ("MCF" in modes) or (amz in ("FBA", "BOTH") and _has_channel(state, "SHOPIFY"))


NODES = (
    Node("CHANNELS", "Where do you sell today?", MULTI, options=(
        Opt("Amazon", channel=("AMAZON", "ACTIVE")),
        Opt("Shopify", channel=("SHOPIFY", "ACTIVE"), emits=(("SHOP_BILLS", O),)),
        Opt("Other website", channel=("OTHER_WEB", "COMING_SOON")),
        Opt("Walmart", channel=("WALMART", "COMING_SOON")),
        Opt("eBay", channel=("EBAY", "COMING_SOON")),
        Opt("TikTok Shop", channel=("TIKTOK", "COMING_SOON")),
    )),
    Node("A1", "How do you fulfill Amazon orders?", SINGLE, field="amazon_mode",
         gate=lambda s: _has_channel(s, "AMAZON"), options=(
             Opt("FBA", "FBA", emits=(("AMZ_SETTLEMENT", E), ("AMZ_ORDERS", E), ("AMZ_INV_FBA", E))),
             Opt("FBM", "FBM", emits=(("AMZ_SETTLEMENT", E), ("AMZ_ORDERS", E), ("AMZ_INV_FBM", E))),
             Opt("Both", "BOTH", emits=(("AMZ_SETTLEMENT", E), ("AMZ_ORDERS", E),
                                        ("AMZ_INV_FBA", E), ("AMZ_INV_FBM", E))),
         )),
    Node("S1", "How do your Shopify orders get shipped?", MULTI,
         gate=lambda s: _has_channel(s, "SHOPIFY"),
         baseline_emits=(("SHOP_ORDERS", E), ("SHOP_INVENTORY", E)), options=(
             Opt("Self", mode="SELF", arms=("SHIP_COST_ESTIMATED",)),
             Opt("3PL", mode="THIRD_PL", arms=("SHIP_COST_ESTIMATED",)),
             Opt("MCF", mode="MCF", emits=(("AMZ_MCF_FEES", E),),
                 arms=("SHARED_INVENTORY", "MCF_FEE_REQUIRED")),
         )),
    Node("S2", "Do your Amazon and Shopify listings use the same SKU codes?", SINGLE, field="sku_parity",
         gate=_s2_gate, options=(
             Opt("Identical", "IDENTICAL"),
             Opt("Mostly", "MOSTLY", arms=("CROSSWALK_RECONCILE",)),
             Opt("No / Not sure", "NONE", arms=("CROSSWALK_RECONCILE",)),
         )),
    Node("S3", "How do customers pay on your Shopify store?", SINGLE, field="gateway",
         gate=lambda s: _has_channel(s, "SHOPIFY"),
         baseline_emits=(("SHOP_PAYOUTS", E), ("SHOP_PAYOUT_RECON", S), ("SHOP_PAYMENTS_SUMMARY", S)),
         options=(
             Opt("Shopify Payments only", "SP_ONLY"),
             Opt("Shopify Payments + others", "SP_PLUS", arms=("FEE_GAP",)),
             Opt("Mostly others", "MOSTLY_OTHER", arms=("FEE_GAP",)),
         )),
    Node("C1", "Do you track your product cost per unit?", SINGLE, field="cogs_source", always=True, options=(
        Opt("In Shopify", "SHOPIFY", emits=(("SHOP_PRODUCTS", E),)),
        Opt("Spreadsheet", "SPREADSHEET", emits=(("COGS_INLINE", E),)),
        Opt("Not yet", "NONE", emits=(("COGS_INLINE", O),), arms=("MARGIN_UNAVAILABLE",)),
    )),
    Node("AD1", "Where do you run ads?", MULTI, always=True, options=(
        Opt("Amazon Ads", ad_partner="AMAZON", emits=(("AD_AMAZON", E),)),
        Opt("Meta", ad_partner="META", emits=(("AD_META", E),)),
        Opt("Google", ad_partner="GOOGLE", emits=(("AD_GOOGLE", E),)),
        Opt("TikTok", ad_partner="TIKTOK", emits=(("AD_TIKTOK", E),)),
        Opt("Walmart Connect", ad_partner="WALMART_CONNECT", emits=(("AD_WALMART", E),)),
        Opt("None yet", arms=("AD_SPEND_ABSENT",)),
    )),
    Node("G1", "What do you want to see first?", SINGLE, field="primary_goal", always=True, optional=True,
         options=(Opt("Profit after ads", tm.PROFIT_AFTER_ADS), Opt("Ad efficiency", tm.AD_EFFICIENCY),
                  Opt("Category intel", tm.CATEGORY_INTEL), Opt("Everything", tm.EVERYTHING))),
)
_BY_ID = {n.id: n for n in NODES}


def node(node_id):
    return _BY_ID.get(node_id)


def _opts_for(node_obj, chosen):
    labels = chosen if isinstance(chosen, (list, tuple, set)) else [chosen]
    return [o for o in node_obj.options if o.label in labels]


def resolve_answers(answers):
    """Walk the answered nodes → (TenantTopology, emitted, armed). `answers` maps node_id -> selected
    label (single) or list of labels (multi). emitted: {file_row_id: {'essentiality', 'emitted_by'[]}}.
    This is the STATED seed (wizard path); detection later reconciles via Resolved.observe()."""
    topo = tm.TenantTopology(tenant_id=None, entry_path=tm.WIZARD)
    emitted = {}

    def _emit(fid, essent, node_id):
        row = emitted.setdefault(fid, {"essentiality": essent, "emitted_by": []})
        if node_id not in row["emitted_by"]:
            row["emitted_by"].append(node_id)

    for n in NODES:
        if n.id not in answers:
            continue
        for fid, essent in n.baseline_emits:
            _emit(fid, essent, n.id)
        for opt in _opts_for(n, answers[n.id]):
            if opt.channel:
                topo.channels.append({"platform": opt.channel[0], "status": opt.channel[1],
                                      "account_ref": None})
            if opt.ad_partner:
                if opt.ad_partner not in topo.ad_partners:
                    topo.ad_partners.append(opt.ad_partner)
            if opt.mode:                                     # S1 multi → set of fulfilment modes
                r = topo.resolved.setdefault("shopify_modes", tm.Resolved.from_stated([]))
                if opt.mode not in r.stated:
                    r.stated = list(r.stated) + [opt.mode]
                    r.effective = r.stated
            if n.field and opt.value is not None:
                topo.resolved[n.field] = tm.Resolved.from_stated(opt.value)
                if n.field == "primary_goal":
                    topo.primary_goal = opt.value
            for fid, essent in opt.emits:
                _emit(fid, essent, n.id)
            for flag_id in opt.arms:
                tm.arm(topo.flags, flag_id, n.id)
    return topo, emitted
