"""Guided onboarding wizard (spec §6/§9). A thin interview (the node graph) resolves the seller's
answers into a TenantTopology + a personalized, goal-ordered checklist + a per-goal completeness
preview, and persists the topology so the raw path (recognizer) can reconcile against it later.

Extracted into its own router because onboarding.py is at the 400-line cap. Tenant-scoped, fail-closed;
the wizard never accepts a client-supplied tenant.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from realify import db, nodegraph, topology as topo_manifest
from realify.ingest import report_catalog as cat
from realify.pipeline import checklist as cl, completeness as comp
from realify.topology_model import GOALS, ARMED
from realify.repositories.topology_repo import TopologyRepository
from .deps import require_tenant


def _checklist_row(ci):
    """Serialize a ChecklistItem for the UI, enriched with a human label + the recognizer type(s) that
    tick it, so the single live checklist can check items off + show filenames as files are recognized."""
    d = ci.to_dict()
    m = topo_manifest.by_id(d["file_row_id"])
    d["label"] = m.data_need if m else d["file_row_id"]
    d["match_types"] = cat.SATISFIED_BY_TYPES.get(d["file_row_id"], [])
    return d

router = APIRouter()

# which channel selection reveals a gated node (client-side show/hide; the server resolve is authoritative)
_CHANNEL_REQ = {"A1": "Amazon", "S1": "Shopify", "S2": "Shopify", "S3": "Shopify"}


def _graph():
    return [{"id": n.id, "prompt": n.prompt, "type": n.type, "always": n.always, "optional": n.optional,
             "field": n.field, "requires": _CHANNEL_REQ.get(n.id),
             "options": [o.label for o in n.options]} for n in nodegraph.NODES]


def _topology_summary(topo):
    return {"entry_path": topo.entry_path, "primary_goal": topo.primary_goal,
            "channels": topo.channels, "ad_partners": topo.ad_partners,
            "resolved": {k: v.effective for k, v in topo.resolved.items()},
            "flags": [{"id": f.id, "state": f.state} for f in topo.flags]}


@router.get("/api/wizard/graph")
def wizard_graph(request: Request):
    require_tenant(request)
    return JSONResponse({"ok": True, "nodes": _graph()})


@router.post("/api/wizard/resolve")
async def wizard_resolve(request: Request):
    """Answers -> TenantTopology + checklist + completeness (persisted). `answers` maps node_id ->
    label (single) or [labels] (multi). Nothing is uploaded here; this arms the raw path."""
    tid = require_tenant(request)
    body = await request.json()
    answers = body.get("answers") or {}
    topo, emitted = nodegraph.resolve_answers(answers)
    topo.tenant_id = tid
    goal = topo.primary_goal
    items = cl.derive(emitted, primary_goal=goal)
    completeness = comp.compute(topo, emitted, received=set())
    topo.completeness = {g: completeness[g]["state"] for g in GOALS}
    with db.connect() as con:
        TopologyRepository(con).save(tid, topo)
        con.commit()
    preview = {g: {"state": completeness[g]["state"], "reasons": completeness[g]["reasons"],
                   "line": comp.preview_line(g, completeness)} for g in GOALS}
    return JSONResponse({"ok": True, "topology": _topology_summary(topo),
                         "checklist": [_checklist_row(ci) for ci in items], "completeness": preview,
                         "armed_flags": [f.id for f in topo.flags if f.state == ARMED]})
