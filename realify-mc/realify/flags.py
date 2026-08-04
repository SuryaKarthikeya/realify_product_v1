"""Feature / Version Registry — the standard convention for shipping new work safely.

Every new feature or UI version ships DARK behind this registry and is turned on / rolled back entirely
from the Ops page (/ops → "Rollout"). Two flag kinds:

  • VERSION features — multiple coexisting versions (e.g. the seller UI: legacy vs v4). One is the
    `baseline` (always safe, backward-compatible). Ops picks which version is SELECTED to roll out and
    its SCOPE (off / internal / on); rollback = pick another version or drop the scope. Never destructive.
  • GATE features — a capability that may ACT (e.g. ask, agents). on/off, default off. Behavior gates are
    INDEPENDENT of UI version: hiding a surface never runs it; showing one never forces it to act.

All state is DB-backed (system pseudo-tenant 0 + per-tenant overrides in `tenant_settings`, which has no
FK — id 0 is safe) and read PER REQUEST → instant flip, no redeploy. Everything defaults to baseline/off,
so deploying a new feature changes nothing until it's turned on from Ops.

Backward-compatibility convention (see FEATURE-REGISTRY.md): new work is ADDITIVE (new endpoints/tables/
nullable columns), never renames/removes an existing contract in place; behavior changes go expand→
contract; the old version stays runnable until its usage is zero, then it is sunset from Ops.
"""
from . import db

_SYSTEM_TID = 0

# The manifest — declare every feature + (for version features) its coexisting versions here.
# Adding a feature = one entry + shipping its code behind the resolver. Nothing else.
FEATURES = {
    "app_ui": {
        "label": "Seller app UI",
        "kind": "version",
        "versions": [
            {"id": "legacy", "label": "Legacy", "baseline": True},
            {"id": "v4", "label": "V4 (DLS)"},
        ],
    },
    # Forward features that ONLY exist in the V4 UI: they declare a dependency on app_ui=v4 so Ops can
    # grey them out under a legacy build and feature_enabled() resolves to a defined state in every combo.
    "ask":    {"label": "Ask — conversational home", "kind": "gate",
               "requires": {"feature": "app_ui", "version": "v4"}},
    "agents": {"label": "Agents — workforce",         "kind": "gate",
               "requires": {"feature": "app_ui", "version": "v4"}},
    # INTERNAL PREVIEW of the HELD ads model (family #10). Turning this on does NOT ship anything to
    # sellers: routers/intelligence.py additionally requires account_type=='tester', and tenant 12
    # (the demo account) is a `customer`, so the demo never shows it even with this flag on. Both
    # locks are required because tenant_kind=='internal' is TRUE for the demo tenant — the usual
    # isTester() check is not a safe boundary here.
    "ads_preview": {"label": "Ads uplift — internal preview (unvalidated)", "kind": "gate",
                    "requires": {"feature": "app_ui", "version": "v4"}},
}


# ---- low-level settings (cross-dialect via SettingsRepository; tid 0 = global, no FK) ----
def _get(tid, key, default=None):
    con = db.connect()
    try:
        return db.get_setting(con, tid, key, default)
    except Exception:
        return default
    finally:
        con.close()


def _set(tid, key, value):
    con = db.connect()
    try:
        db.set_setting(con, tid, key, value)
        con.commit()
    finally:
        con.close()


def _versions(key):
    return FEATURES.get(key, {}).get("versions", [])


def _baseline(key):
    for v in _versions(key):
        if v.get("baseline"):
            return v["id"]
    return _versions(key)[0]["id"] if _versions(key) else None


def _valid(key, vid):
    return any(v["id"] == vid for v in _versions(key))


# ---- version features ----
def selected(key):
    """The version Ops has chosen to roll out. Default = newest declared version."""
    s = _get(_SYSTEM_TID, f"reg.{key}.selected")
    if _valid(key, s):
        return s
    vs = _versions(key)
    return vs[-1]["id"] if vs else None


def scope(key):
    """'off' | 'internal' | 'on' (default 'off')."""
    return (_get(_SYSTEM_TID, f"reg.{key}.scope", "off") or "off").lower()


def active_version(key, request=None, tenant_id=None):
    """Resolve the version to serve. Precedence: query pin > tenant pin > (scope 'on' ? selected :
    baseline). Default baseline. Fail-safe: any error → baseline."""
    base = _baseline(key)
    try:
        if request is not None:
            qp = getattr(request, "query_params", {}) or {}
            for qk in ([key, "skin"] if key == "app_ui" else [key]):   # ?skin= alias for app_ui
                v = (qp.get(qk) or "").lower()
                if _valid(key, v):
                    try: request.session[f"reg.{key}"] = v
                    except Exception: pass
                    return v
            try:
                s = request.session.get(f"reg.{key}")
                if _valid(key, s):
                    return s
            except Exception:
                pass
        if tenant_id is not None:
            t = _get(tenant_id, f"reg.{key}.pin")
            if _valid(key, t):
                return t
        return selected(key) if scope(key) == "on" else base
    except Exception:
        return base


# ---- gate features ----
def feature_gate(key, tenant_id=None):
    """The RAW operator-set gate (on/off), ignoring any dependency. Used by the V4 UI rail — being in V4
    already satisfies the dependency, so the rail honors exactly what the operator toggled."""
    if tenant_id is not None:
        t = _get(tenant_id, f"reg.{key}.gate")
        if t in ("on", "off"):
            return t == "on"
    return (_get(_SYSTEM_TID, f"reg.{key}.gate", "off") or "off").lower() == "on"


def feature_available(key):
    """Is this gate feature's dependency satisfied at the GLOBAL rollout level? A feature that `requires`
    app_ui=v4 is available only when v4 is the selected build AND it is actually being rolled out
    (scope != 'off'). No requires → always available. This is what greys the Ops toggle + keeps behavior
    from arming under a legacy build."""
    req = FEATURES.get(key, {}).get("requires")
    if not req:
        return True
    dep = req.get("feature")
    return selected(dep) == req.get("version") and scope(dep) != "off"


def feature_enabled(key, tenant_id=None):
    """EFFECTIVE state = operator gate AND dependency satisfied. So an 'on' gate under a legacy build
    resolves to off — the app is never in an undefined state. Behavior (scheduler/agents) reads this."""
    return feature_gate(key, tenant_id) and feature_available(key)


# ---- Ops setters (all instant, no redeploy) ----
def set_selected(key, vid):
    if _valid(key, vid):
        _set(_SYSTEM_TID, f"reg.{key}.selected", vid)


def set_scope(key, val):
    v = (val or "off").lower()
    _set(_SYSTEM_TID, f"reg.{key}.scope", v if v in ("off", "internal", "on") else "off")


def set_tenant_pin(key, tenant_id, vid):
    _set(tenant_id, f"reg.{key}.pin", vid if _valid(key, vid) else "")


def set_feature(key, on, tenant_id=None):
    val = "on" if (on is True or on == "on") else "off"
    _set(_SYSTEM_TID if tenant_id is None else tenant_id, f"reg.{key}.gate", val)


def list_state():
    """Full registry state for the Ops catalog page."""
    out = []
    for key, meta in FEATURES.items():
        row = {"key": key, "label": meta["label"], "kind": meta["kind"]}
        if meta["kind"] == "version":
            row.update(versions=meta["versions"], selected=selected(key),
                       scope=scope(key), baseline=_baseline(key))
        else:
            row["enabled"] = feature_gate(key)          # raw toggle state (what the switch shows)
            row["effective"] = feature_enabled(key)      # gate AND dependency (what actually applies)
            req = meta.get("requires")
            if req:
                row["requires"] = req
                row["available"] = feature_available(key)
        out.append(row)
    return out


# ---- backward-compat aliases (earlier callers: pages.home, admin, tests) ----
def resolve_skin(request, tenant_id=None):
    return "v4" if active_version("app_ui", request, tenant_id) == "v4" else "legacy"


def global_skin():
    return scope("app_ui")


def set_global_skin(value):
    set_scope("app_ui", value)


def set_tenant_skin(tenant_id, value):
    set_tenant_pin("app_ui", tenant_id, value)
