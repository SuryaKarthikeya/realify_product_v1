"""R11.1 Part F — the guided-run TELEPROMPTER. Replaces the hub-bound step list with a persistent bar
that rides EVERY surface (rendered by site/backbar from session['guided']) and DRIVES the real product:
each Next performs real navigation + a real grant assume (or an injector), landing the presenter on the
actual page — the fleet, a scope-switched five-lens brand, a client portal, the admin fleet. Two
cross-persona scripts on the loaded world's real brands/decisions. No simulation."""
from . import sandbox

# Step fields: persona (who you are), instr (one clean line), nav (real URL), setup (how to set the
# session before landing: {'persona':..} | {'kind':..,'tenant_id':..} | None), inject (kind|None).
def _steps(name, b0, b0name, b1, b1name):
    if name == "vc":
        return [
            ("Realify Admin", "The fleet across ALL agencies — leverage, decisions pool, MRR at a glance.",
             "/ops/agency/admin", {"persona": "admin"}, None),
            ("Realify Admin", "One agency's leverage & acceptance rate — the ROI multiple they're buying.",
             "/ops/agency/admin", {"persona": "admin"}, None),
            ("Agency AM", f"Drill into {b0name} — the real operating surface, bounded by its envelope.",
             f"/agency/brand/{b0}", {"persona": "client_lead"}, None),
            ("Brand owner", f"Fast flip: {b0name}'s own portal — the same numbers, the client's view.",
             f"/brand/portal/{b0}", {"kind": "managed_brand", "tenant_id": b0}, None),
            ("Agency AM", "Close on the ledger — hash-chained, verified, every action reversible.",
             f"/brand/portal/{b0}", {"persona": "client_lead"}, None),
        ]
    # customer (default)
    return [
        ("Agency AM", "Your fleet — client brands ranked by $ at stake. The colored edge is health.",
         "/agency/console", {"persona": "client_lead"}, None),
        ("Agency AM", f"Drill into {b0name} — its real five-lens account, scoped to this one brand.",
         f"/agency/brand/{b0}", {"persona": "client_lead"}, None),
        ("Agency AM", f"A competitor just undercut {b0name} — watch a fresh pricing decision appear.",
         f"/agency/brand/{b0}", {"persona": "client_lead"}, {"kind": "undercut", "tenant_id": b0}),
        ("Agency AM", "Act on the top decision — approve the ACoS cut / reorder (envelope-enforced).",
         f"/agency/brand/{b0}", None, None),
        ("Brand owner", f"Flip to how the CLIENT sees it — {b0name}'s portal: transparency log + approvals.",
         f"/brand/portal/{b0}", {"kind": "managed_brand", "tenant_id": b0}, None),
        ("Agency AM", "Back to the fleet — triage the next brand that needs attention.",
         "/agency/console", {"persona": "client_lead"}, None),
        ("Agency AM", f"Open {b0name}'s day-0 report — the money story you send the client.",
         f"/brand/day0/{b0}", {"persona": "client_lead"}, None),
    ]


def build_run(cur, scenario, name):
    """Concrete steps for the loaded world (real brand ids/names). [] if no world loaded."""
    st = sandbox.sandbox_state(cur, scenario)
    brands = (st or {}).get("brands") or []
    if not brands:
        return []
    b0 = brands[0]["tenant_id"]; b0name = brands[0]["name"]
    b1 = brands[1]["tenant_id"] if len(brands) > 1 else b0
    b1name = brands[1]["name"] if len(brands) > 1 else b0name
    out = []
    for persona, instr, nav, setup, inject in _steps(name, b0, b0name, b1, b1name):
        out.append({"persona": persona, "instr": instr, "nav": nav, "setup": setup, "inject": inject})
    return out


_TITLES = {"customer": "Customer walkthrough", "vc": "Investor walkthrough"}


def title(name):
    return _TITLES.get(name, "Guided run")
