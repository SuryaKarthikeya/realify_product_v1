"""Checklist derivation (spec §9) — DERIVED from the topology's emitted rows, never a separate source of
truth. Same file_row_id from multiple nodes collapses to one item (emitted_by accumulates); grouping is
fixed (Amazon·Shopify·Ads·COGS, ESSENTIAL→SUPPORTING→OPTIONAL within a group) and the group SEQUENCE is
re-ordered by the chosen goal. Removing the last emitter drops a PENDING item but keeps a RECEIVED one as
NO_LONGER_REQUIRED (ingested data is preserved)."""
from .. import topology
from ..topology_model import (ChecklistItem, PENDING, RECEIVED, NO_LONGER_REQUIRED,
                              PROFIT_AFTER_ADS, AD_EFFICIENCY, CATEGORY_INTEL, EVERYTHING)

_GROUPS = (topology.AMAZON, topology.SHOPIFY, topology.ADS, topology.COGS)
_ESSENT_ORDER = {topology.ESSENTIAL: 0, topology.SUPPORTING: 1, topology.OPTIONAL: 2}
# group sequence per goal (§9): profit → revenue/COGS before ads; ad-efficiency → ads first, COGS demoted.
_GROUP_ORDER = {
    PROFIT_AFTER_ADS: (topology.AMAZON, topology.SHOPIFY, topology.COGS, topology.ADS),
    AD_EFFICIENCY:    (topology.ADS, topology.AMAZON, topology.SHOPIFY, topology.COGS),
    CATEGORY_INTEL:   (topology.AMAZON, topology.SHOPIFY, topology.COGS, topology.ADS),
    EVERYTHING:       _GROUPS,
}


def _acq_mode(m):
    if m.csv:
        return "MANUAL_CSV"
    if m.inline:
        return "INLINE"
    return "CONNECTED_API"


def derive(emitted, primary_goal=None, received=None, prior=None):
    """emitted: {file_row_id: {'essentiality', 'emitted_by'[]}} (from nodegraph.resolve_answers + any
    detection emits). received: set of file_row_ids already uploaded. prior: the previous checklist (for
    NO_LONGER_REQUIRED). Returns [ChecklistItem] grouped + goal-ordered."""
    received = set(received or ())
    prior_by_id = {ci.file_row_id: ci for ci in (prior or [])}
    items = []
    for fid, info in emitted.items():
        m = topology.by_id(fid)
        if not m:
            continue                                          # referential integrity is test-enforced upstream
        items.append(ChecklistItem(
            file_row_id=fid, group=m.group, essentiality=info.get("essentiality", m.essentiality),
            status=RECEIVED if fid in received else PENDING,
            where_to_find=(m.csv.where_to_find if m.csv else ""),
            arrival_hint=(m.csv.arrival_hint if m.csv else "INSTANT"),
            emitted_by=list(info.get("emitted_by", [])), satisfiable_by=m.satisfiable_by(),
            acquisition_mode=_acq_mode(m)))
    # a row in the prior checklist that's no longer emitted: keep it as NO_LONGER_REQUIRED if data already
    # arrived (don't discard ingested data), otherwise drop it silently.
    for fid, ci in prior_by_id.items():
        if fid not in emitted and (ci.status == RECEIVED or fid in received):
            ci.status = NO_LONGER_REQUIRED
            items.append(ci)
    order = _GROUP_ORDER.get(primary_goal, _GROUPS)
    gi = {g: i for i, g in enumerate(order)}
    items.sort(key=lambda ci: (gi.get(ci.group, 99), _ESSENT_ORDER.get(ci.essentiality, 9), ci.file_row_id))
    return items
