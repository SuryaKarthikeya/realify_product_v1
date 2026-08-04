"""Reconcile prompts (spec §8, Table 2) — the stated-vs-detected corrections that sit above the existing
record-level reconciles. Detection wins the NUMBER (effective follows detected); the prompt captures the
user's correction. Each RC is DATA: a trigger over (stated topology, detected signals), a verbatim
headline + actions, and an effective resolution that mutates the topology (Resolved.observe / flag arm).

`detected` is the recognizer's read: {mcf_location, detected_amazon_mode, unmatched_shopify_skus,
non_sp_gateway_orders, extra_channels[], blank_cost_skus, has_amz_mcf_fees, raw_path}.
"""
from dataclasses import dataclass
from typing import Callable, Tuple

from .. import topology_model as tm


def _stated(topo, field):
    r = topo.resolved.get(field)
    return r.stated if r else None


def _modes(topo):
    r = topo.resolved.get("shopify_modes")
    return set(r.effective or []) if r else set()


def _add_mode(topo, mode):
    r = topo.resolved.setdefault("shopify_modes", tm.Resolved.from_detected([]))
    if mode not in (r.effective or []):
        r.effective = list(r.effective or []) + [mode]
        r.detected = r.effective


@dataclass
class Rc:
    id: str
    headline: str
    actions: Tuple
    trigger: Callable          # (topo, detected) -> bool
    resolve: Callable          # (topo, detected) -> None  (mutates topo)


def _rc1(topo, d):
    _add_mode(topo, "MCF")
    tm.arm(topo.flags, "SHARED_INVENTORY", "detection")
    tm.arm(topo.flags, "MCF_FEE_REQUIRED", "detection")


def _rc3(topo, d):
    topo.resolved.setdefault("amazon_mode", tm.Resolved()).observe(d.get("detected_amazon_mode"))


def _rc6(topo, d):
    have = {c["platform"] for c in topo.channels}
    for ch in d.get("extra_channels", []):
        if ch not in have:
            topo.channels.append({"platform": ch, "status": "ACTIVE", "account_ref": None, "source": tm.DETECTED})


def _rc8(topo, d):
    for r in topo.resolved.values():
        if r.stated is None and r.detected is not None:
            r.source = tm.DETECTED


RCS = (
    Rc("RC-1", "Looks like Amazon fulfills some of your Shopify orders.", ("That's right", "No, that's not MCF"),
       lambda t, d: bool(d.get("mcf_location")) and "MCF" not in _modes(t), _rc1),
    Rc("RC-2", "We haven't spotted Amazon fulfillment in your files yet.", ("Add MCF fees", "I don't use MCF after all"),
       lambda t, d: "MCF" in set(_stated(t, "shopify_modes") or []) and not d.get("mcf_location")
       and not d.get("has_amz_mcf_fees"),
       lambda t, d: tm.arm(t.flags, "MCF_FEE_REQUIRED", "detection")),
    Rc("RC-3", "Your Amazon fulfillment looks different from what you picked.", ("Use my data", "Keep my choice"),
       lambda t, d: d.get("detected_amazon_mode") and _stated(t, "amazon_mode")
       and d["detected_amazon_mode"] != _stated(t, "amazon_mode"), _rc3),
    Rc("RC-4", "Some SKUs don't line up across Amazon and Shopify.", ("Review unmatched", "They're intentionally different"),
       lambda t, d: _stated(t, "sku_parity") == "IDENTICAL" and d.get("unmatched_shopify_skus", 0) > 0,
       lambda t, d: tm.arm(t.flags, "CROSSWALK_RECONCILE", "detection")),
    Rc("RC-5", "Not everything went through Shopify Payments.", ("Continue with estimates", "Add gateway fees"),
       lambda t, d: _stated(t, "gateway") == "SP_ONLY" and d.get("non_sp_gateway_orders", 0) > 0,
       lambda t, d: tm.arm(t.flags, "FEE_GAP", "detection")),
    Rc("RC-6", "We found data for a channel you didn't add.", ("Add channel", "Leave it out"),
       lambda t, d: bool(d.get("extra_channels")), _rc6),
    Rc("RC-7", "Some products are missing a cost.", ("Enter costs", "Skip for now"),
       lambda t, d: _stated(t, "cogs_source") == "SHOPIFY" and d.get("blank_cost_skus", 0) > 0,
       lambda t, d: tm.arm(t.flags, "MARGIN_UNAVAILABLE", "detection")),
    Rc("RC-8", "Here's what we detected from your files.", ("Yes", "Adjust"),
       lambda t, d: bool(d.get("raw_path")) and any(r.stated is None and r.detected is not None
                                                    for r in t.resolved.values()), _rc8),
)
_BY_ID = {r.id: r for r in RCS}


def evaluate(topo, detected):
    """Return the reconcile prompts that fire for this (stated topology, detected signals) — headline +
    actions + id. Does NOT mutate; call apply() with the user's choice (or the auto path) to resolve."""
    return [{"id": r.id, "headline": r.headline, "actions": list(r.actions)}
            for r in RCS if r.trigger(topo, detected)]


def apply(topo, rc_id, detected):
    """Apply an RC's effective resolution to the topology (detection wins the number). Idempotent per RC."""
    rc = _BY_ID.get(rc_id)
    if rc:
        rc.resolve(topo, detected)
    return topo
