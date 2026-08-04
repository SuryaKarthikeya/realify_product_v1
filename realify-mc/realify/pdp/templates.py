"""PDP capability templates as DATA (agency-plan P1). Envelopes are what a brand grants an agency;
roles are what a user is assigned within an engagement. Effective capability = intersection(envelope,
grant) — enforced by decide(). Caps are the same shape stored in envelopes.caps / grants.caps (jsonb):

    {lens: {"max_kind": "none|read|propose|execute", "autonomy_ceiling": int}}

max_kind is the top of the read<propose<execute ladder allowed on that lens; autonomy_ceiling is the
highest autonomy level that may be SET on that lens (0 = manual only). A lens absent from a caps dict
means no capability there (deny).
"""

LENSES = ["pricing", "ads", "inventory", "listings", "reporting"]
KIND_RANK = {"none": 0, "read": 1, "propose": 2, "execute": 3}


def caps(default_kind, default_ceiling=0, **overrides):
    """Build a caps dict over all LENSES with a default, then apply per-lens overrides."""
    c = {lens: {"max_kind": default_kind, "autonomy_ceiling": default_ceiling} for lens in LENSES}
    for lens, spec in overrides.items():
        c[lens] = spec
    return c


def _cap(kind, ceiling=0):
    return {"max_kind": kind, "autonomy_ceiling": ceiling}


# ---- 5 envelope templates (what the brand permits the agency) ----
ENVELOPES = {
    "Full Operate":       caps("execute", 3),
    "Operate ex-Pricing": caps("execute", 3, pricing=_cap("read", 0)),
    "Ads Only":           caps("read", 0, ads=_cap("execute", 3)),
    "Advise":             caps("propose", 0),
    "Read-only":          caps("read", 0),
}

# ---- 8 role templates (what the user may do within an engagement) ----
ROLES = {
    "agency_admin":       caps("execute", 3),
    "account_manager":    caps("execute", 2),
    "ads_manager":        caps("propose", 0, ads=_cap("execute", 3)),
    "pricing_manager":    caps("propose", 0, pricing=_cap("execute", 3)),
    "inventory_planner":  caps("read", 0, inventory=_cap("execute", 2)),
    "content_specialist": caps("read", 0, listings=_cap("execute", 2)),
    "analyst":            caps("propose", 0),
    "viewer":             caps("read", 0),
}
