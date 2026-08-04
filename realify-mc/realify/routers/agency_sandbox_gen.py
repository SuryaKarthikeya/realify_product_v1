"""R9 sandbox generator / impersonation / email short-circuit routes — split from agency_sandbox.py to
keep each router file under the 400-line cap. Shares the world-job registry + auth helpers with
agency_sandbox. All superlogin/admin-gated, sandbox-only, ledgered."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from .. import superlogin, billing, db
from ..agency import sandbox, ledger, tenancy, db as agency_db
from ..agency.guard import require_agency_console
from .agency_sandbox import (_sb_auth, _body, _safe, _tenant_kind, _job_start, _world_txn,
                             _grant_seller_access, _nm, _do_inject)
from ..agency import guided as _guided

router = APIRouter()


def _gr_apply(request, pt, setup):
    """Set the session persona for a guided step (mirrors sb_assume/sb_impersonate for brands[0])."""
    if not setup:
        return
    if setup.get("persona") == "admin":
        request.session["acting_as"] = {"role": "Realify Admin", "tenant": "fleet", "via": None}
    elif setup.get("persona") == "client_lead":
        request.session["uid"] = pt["client_lead_uid"]; request.session["tid"] = pt["brand_owner_tenant"]
        request.session["acting_as"] = {"role": "Agency operator", "tenant": _nm(pt["agency_id"], True), "via": None}
    elif setup.get("kind") == "managed_brand":
        request.session["uid"] = pt["brand_owner_uid"]; request.session["tid"] = pt["brand_owner_tenant"]
        request.session["acting_as"] = {"role": "Managed Brand Owner", "tenant": _nm(pt["brand_owner_tenant"]),
                                        "via": _nm(pt["agency_id"], True)}


def _gr_set(request, name, steps, i):
    s = steps[i]
    request.session["guided"] = {"name": name, "i": i, "total": len(steps), "persona": s["persona"],
                                 "instr": s["instr"], "title": _guided.title(name)}


def _gr_land(request, name, steps, i):
    """Apply step i (persona + optional injector) and return its real navigation target."""
    conn = agency_db.agency_connect()
    try:
        pt = sandbox.persona_targets(conn.cursor()); conn.rollback()
    finally:
        conn.close()
    if not pt:
        return None
    _gr_apply(request, pt, steps[i]["setup"])
    inj = steps[i]["inject"]
    if inj:
        try:
            _do_inject(inj["kind"], inj["tenant_id"])       # fires on the real world (best-effort)
        except Exception:
            pass
    _gr_set(request, name, steps, i)
    return steps[i]["nav"]


@router.post("/api/ops/sandbox/guided-run/start", dependencies=[Depends(require_agency_console)])
async def gr_start(request: Request):
    """R11.1 teleprompter: begin a cross-persona script on the loaded world; land on step 1's real page."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    name = "vc" if b.get("name") == "vc" else "customer"
    conn = agency_db.agency_connect()
    try:
        steps = _guided.build_run(conn.cursor(), None, name); conn.rollback()
    finally:
        conn.close()
    if not steps:
        return JSONResponse({"ok": False, "error": "Load a world first."}, status_code=400)
    nav = _gr_land(request, name, steps, 0)
    return JSONResponse({"ok": True, "redirect": nav, "total": len(steps)})


@router.post("/api/ops/sandbox/guided-run/next", dependencies=[Depends(require_agency_console)])
async def gr_next(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    g = request.session.get("guided")
    if not g:
        return JSONResponse({"ok": True, "done": True})
    name = g["name"]; i = int(g.get("i", 0)) + 1
    conn = agency_db.agency_connect()
    try:
        steps = _guided.build_run(conn.cursor(), None, name); conn.rollback()
    finally:
        conn.close()
    if not steps or i >= len(steps):
        request.session.pop("guided", None)                # end of script → clear the bar
        return JSONResponse({"ok": True, "done": True})
    nav = _gr_land(request, name, steps, i)
    return JSONResponse({"ok": True, "redirect": nav})


@router.post("/api/ops/sandbox/guided-run/exit", dependencies=[Depends(require_agency_console)])
async def gr_exit(request: Request):
    request.session.pop("guided", None)                    # clear the bar; stay on the current surface
    return JSONResponse({"ok": True})


def _sc_email(request):
    """The superlogin staff email (owner of saved worlds); '' if only the admin key was used."""
    return superlogin.verify_session(request.cookies.get("superlogin_session") or "") or "staff@realify.ai"


# ================= PARAMETRIC GENERATOR (Part A) — background accept-then-poll =================
@router.post("/api/ops/sandbox/generate", dependencies=[Depends(require_agency_console)])
async def sb_generate(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    from ..agency import synth
    b = await _body(request)
    try:
        # R15 Part G.5 — direct vs managed is explicit: a Brand name with NO Agency name creates a DIRECT
        # brand (seller tenant, no agency envelope/grant); an Agency name makes the brand MANAGED under it.
        _bn = (b.get("brand_name") or "").strip()
        _an = (b.get("agency_name") or "").strip()
        _direct = bool(_bn and not _an)
        params = {
            "country": (b.get("country") or "US").upper(),
            "categories": b.get("categories") or None,
            "sku_count": int(b.get("sku_count") or 480),
            "brands_per_agency": int(b.get("brands_per_agency") or b.get("brands") or 8),
            "direct_brands": int(b.get("direct_brands") or 0),
            "depth": b.get("depth") or "rich",
            "moments": b.get("moments") or [],
            "seed": (b.get("seed") or "gen-default").strip(),
            # R15.1 Part A — blank agency name ⇒ synth draws a real, locale-appropriate name from the
            # AGENCIES bank (no "VERIFY …" placeholder in any user-facing name; the reaper identifies
            # sandbox agencies by sandbox_scenario/tenant_kind, not the display name). `brand_name` names
            # the first MANAGED brand only when the user actually named an agency.
            "agency_name": _an,
            "brand_name": (_bn if _an else ""),
            "direct_brand_name": (_bn if _direct else ""),   # else the brand name names a DIRECT brand
        }
        if _direct:
            params["direct_brands"] = max(1, params["direct_brands"])   # ensure a direct slot carries the name
        spec = synth.spec_from_params(params)                # validates country early (fast 400)
    except (ValueError, KeyError) as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    wk = synth.world_key(spec["seed"])
    save_as = (b.get("save_as") or "").strip()
    email = _sc_email(request)

    def work(cur):
        synth.generate_world(cur, params)
        if save_as:
            synth.save_world(cur, email, save_as, params)
    started, job = _job_start(wk, "generate", lambda: _world_txn(work))
    return JSONResponse({"ok": True, "started": True, "already": (not started),
                         "action": "generate", "world_key": wk, "started_at": job["started_at"]})


@router.get("/api/ops/sandbox/worlds", dependencies=[Depends(require_agency_console)])
def sb_worlds(request: Request):
    """Realify presets (read-only) + this tester's saved worlds — for 'Pick existing seed'."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    from ..agency import synth
    from ..agency.sandbox_scenarios import SCENARIOS, PRESETS
    presets = [{"key": k, "name": SCENARIOS[k].get("agency_name", k), "seed": SCENARIOS[k]["seed"],
                "country": SCENARIOS[k].get("country", SCENARIOS[k]["hq_country"]),
                "brands": len(SCENARIOS[k].get("brands", [])), "readonly": True} for k in PRESETS]
    conn = agency_db.agency_connect()
    try:
        saved = synth.list_saved(conn.cursor(), _sc_email(request))
        conn.rollback()
    except Exception:
        saved = []
    finally:
        conn.close()
    return JSONResponse({"ok": True, "presets": presets, "saved": saved})


# ================= CAPTURED-SEED REUSE (R17 Part D) — provision from a rescued catalog =================
@router.get("/api/ops/sandbox/captured-seeds", dependencies=[Depends(require_agency_console)])
def sb_captured_seeds(request: Request):
    """List catalogs rescued on brand deletion (captured_seeds) — a first-class 'seed from a real
    catalog' pick for the hub. Same gate as the other sandbox hub endpoints. Reads the shared RDS via
    db.connect() (owner PG in the harness), where lifecycle.py wrote them on delete."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    from .. import lifecycle
    con = db.connect()
    try:
        seeds = lifecycle.list_captured_seeds(con)
    finally:
        con.close()
    return JSONResponse({"ok": True, "seeds": seeds})


def _provision_from_seed(seed_id, seed, ctry):
    """Mint (or REUSE) a sandbox SELLER tenant for a captured catalog and provision it via the SELLER
    synth stack — expand_minimal_seed + SyntheticSource — exactly as scheduler.resynthesize(mode='full')
    and routers/onboarding do (NOT the agency world builder, per R17). Tagged tenant_kind='sandbox' +
    sandbox=1 + a captured-* sandbox_scenario so the reaper's exclusion convention holds (sandbox rows
    with a NULL sandbox_scenario are what cleanup_strays retires). Idempotent per seed."""
    from .. import country as _country
    from ..ingest.seed import expand_minimal_seed
    from ..ingest.synthetic import SyntheticSource
    scen = f"captured-{seed_id}"
    brand = seed.get("brand_name") or f"Captured seed {seed_id}"
    con = db.connect()
    try:
        row = con.execute("SELECT id FROM tenants WHERE sandbox_scenario=? ORDER BY id LIMIT 1",
                          (scen,)).fetchone()
        tid = row["id"] if row else db.create_tenant(con, brand)
        con.execute("UPDATE tenants SET name=?, sandbox=1, tenant_kind='sandbox', sandbox_scenario=?, "
                    "data_mode='synthetic', provisioned=1 WHERE id=?", (brand, scen, tid))
        db.set_setting(con, tid, "country", ctry)
        con.commit()
    finally:
        con.close()
    seed_full = expand_minimal_seed(seed["catalog"], prof=_country.profile(ctry))
    SyntheticSource(seed_skus=seed_full).provision(tid)     # writes the captured ASINs/titles/categories
    return tid


@router.post("/api/ops/sandbox/generate-from-seed", dependencies=[Depends(require_agency_console)])
async def sb_generate_from_seed(request: Request):
    """Provision a sandbox seller tenant from a captured catalog and land in the real five-lens app
    (mirrors /impersonate kind='direct': paid access synthesized, owner user bound, session set)."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    seed_id = b.get("seed_id")
    if seed_id in (None, ""):
        return JSONResponse({"ok": False, "error": "seed_id required"}, status_code=400)
    from .. import lifecycle, country
    con = db.connect()
    try:
        seed = lifecycle.captured_seed_catalog(con, int(seed_id))
    finally:
        con.close()
    if not seed or not seed.get("catalog"):
        return JSONResponse({"ok": False, "error": "no such captured seed"}, status_code=404)
    ctry = country.normalize(seed.get("country") or "US")
    tid = _provision_from_seed(int(seed_id), seed, ctry)
    _grant_seller_access(tid)                               # seller app gates on billing → synth paid + tester
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        owner_uid = sandbox._ensure_user(cur, f"sandbox-owner-t{tid}@realify.ai", tenant_id=tid)
        tenancy.set_brand_scope(cur, [tid])
        ledger.append(cur, tid, None, "sandbox.generate_from_seed",
                      payload={"seed_id": int(seed_id), "tenant_id": tid})
        conn.commit()
    finally:
        conn.close()
    request.session.pop("agency_envelope", None)
    request.session["uid"] = owner_uid; request.session["tid"] = tid
    request.session["acting_as"] = {"role": "Direct Brand Owner", "tenant": _nm(tid), "via": None}
    return JSONResponse({"ok": True, "redirect": "/", "tenant_id": tid})


# ================= DYNAMIC IMPERSONATION (Part C) — become ANY sandbox tenant =================
@router.post("/api/ops/sandbox/impersonate", dependencies=[Depends(require_agency_console)])
async def sb_impersonate(request: Request):
    """Assume a grant into ANY tenant in the loaded world (explicit ids from the hub pickers). authz:
    the target tenant must be sandbox/internal; ledgered. Sets the session + back-bar acting_as."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    request.session.pop("agency_envelope", None)             # R15 Part 0: switching persona drops any prior brand envelope
    kind = b.get("kind")                                     # 'agency' | 'managed_brand' | 'direct' | 'admin'
    if kind == "admin":
        request.session["acting_as"] = {"role": "Realify Admin", "tenant": "fleet", "via": None}
        return JSONResponse({"ok": True, "redirect": "/ops/agency/admin"})
    tid = b.get("tenant_id")
    if not tid:
        return JSONResponse({"ok": False, "error": "tenant_id required"}, status_code=400)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        if _tenant_kind(cur, tid) not in ("sandbox", "internal"):
            conn.rollback()
            return JSONResponse({"ok": False, "error": "impersonation is sandbox-only"}, status_code=403)
        wk = sandbox.current_world_key(cur)
        pt = sandbox.persona_targets(cur, wk)
        # find the agency for this brand (managed) via engagements
        cur.execute("SELECT a.id, a.name FROM engagements e JOIN agencies a ON a.id=e.agency_id "
                    "WHERE e.tenant_id=%s AND e.status<>'terminated' LIMIT 1", (tid,))
        agrow = cur.fetchone()
        # a brand/direct portal authorises by users.tenant_id == tenant — bind an owner user to THIS tenant
        if kind in ("managed_brand", "direct"):
            owner_uid = sandbox._ensure_user(cur, f"sandbox-owner-t{tid}@realify.ai", tenant_id=tid)
        tenancy.set_brand_scope(cur, [tid])        # ledger is RLS-forced (realify_app on prod)
        ledger.append(cur, tid, None, "sandbox.impersonate", payload={"kind": kind, "tenant_id": tid})
        conn.commit()
    finally:
        conn.close()
    if kind == "direct":
        _grant_seller_access(tid)
        request.session["uid"] = owner_uid; request.session["tid"] = tid
        request.session["acting_as"] = {"role": "Direct Brand Owner", "tenant": _nm(tid), "via": None}
        return JSONResponse({"ok": True, "redirect": "/"})
    if kind == "agency":
        request.session["uid"] = (pt or {}).get("client_lead_uid"); request.session["tid"] = tid
        request.session["acting_as"] = {"role": "Agency operator",
                                        "tenant": (agrow[1] if agrow else "agency"), "via": None}
        return JSONResponse({"ok": True, "redirect": "/agency/console"})
    request.session["uid"] = owner_uid; request.session["tid"] = tid
    request.session["acting_as"] = {"role": "Managed Brand Owner", "tenant": _nm(tid),
                                    "via": (agrow[1] if agrow else None)}
    return JSONResponse({"ok": True, "redirect": f"/brand/portal/{tid}"})


@router.post("/api/ops/sandbox/return", dependencies=[Depends(require_agency_console)])
def sb_return(request: Request):
    """Back-to-hub. A REAL agency customer operating one of its brands (agency_envelope set, NO superlogin
    session) returns to the AGENCY HOME — the fleet — with its login intact; only the brand drill-in scope
    is dropped. A sandbox/superlogin TESTER drops the whole impersonation and returns to the tester hub."""
    from .. import superlogin
    is_tester = bool(superlogin.verify_session(request.cookies.get("superlogin_session") or ""))
    if request.session.get("agency_envelope") and not is_tester:
        for k in ("acting_as", "agency_envelope", "tid"):    # exit the brand, keep the agency session
            request.session.pop(k, None)
        return JSONResponse({"ok": True, "redirect": "/agency/console"})
    for k in ("uid", "tid", "acting_as", "agency_envelope"):
        request.session.pop(k, None)
    return JSONResponse({"ok": True, "redirect": "/superlogin/hub"})


# ================= EMAIL SHORT-CIRCUIT (Part D) — sandbox-global toggle + inline approve =================
def _shortcircuit_on(cur):
    cur.execute("SELECT value FROM sandbox_settings WHERE key='email_short_circuit'")
    r = cur.fetchone()
    return bool(r and r[0] == "on")


@router.get("/api/ops/sandbox/shortcircuit", dependencies=[Depends(require_agency_console)])
def sb_sc_get(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    conn = agency_db.agency_connect()
    try:
        on = _shortcircuit_on(conn.cursor()); conn.rollback()
    finally:
        conn.close()
    return JSONResponse({"ok": True, "on": on})


@router.post("/api/ops/sandbox/shortcircuit", dependencies=[Depends(require_agency_console)])
async def sb_sc_set(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    on = "on" if b.get("on") in (True, "true", "on", 1, "1") else "off"
    conn = agency_db.agency_connect()
    try:
        conn.cursor().execute(
            "INSERT INTO sandbox_settings(key,value) VALUES('email_short_circuit',%s) "
            "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=now()", (on,))
        conn.commit()
    finally:
        conn.close()
    return JSONResponse({"ok": True, "on": on == "on"})


@router.post("/api/ops/sandbox/consent/{consent_id}/approve-inline",
             dependencies=[Depends(require_agency_console)])
async def sb_sc_approve(consent_id: int, request: Request):
    """Short-circuit approve a pending consent as-if the recipient clicked (SANDBOX only; server-enforced).
    Requires short-circuit ON. Ledgered as impersonated."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    from ..agency import consent
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        if not _shortcircuit_on(cur):
            conn.rollback()
            return JSONResponse({"ok": False, "error": "email short-circuit is OFF"}, status_code=409)
        cur.execute("SELECT tenant_id FROM brand_consents WHERE id=%s", (consent_id,))
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return JSONResponse({"ok": False, "error": "no such consent"}, status_code=404)
        if _tenant_kind(cur, row[0]) not in ("sandbox", "internal"):
            conn.rollback()   # SERVER-ENFORCED sandbox-only (not just hidden in the UI)
            return JSONResponse({"ok": False, "error": "short-circuit is sandbox-only"}, status_code=403)
        res = consent.impersonate_grant(cur, consent_id)
        conn.commit()
        return JSONResponse({"ok": True, "message": "Approved as recipient (impersonated click).", **res})
    except consent.ConsentStateError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()

