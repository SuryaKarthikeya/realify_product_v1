"""Sandbox controls (R6). Two surfaces:

 • Hub OPS controls (superlogin-session OR staff admin key — `_sb_auth`, unchanged): load/reset a
   deterministic preset, advance the clock, read state, and "assume a persona" (set the browser
   session to a persona identity and hand back a redirect). World-level only — no per-SKU injectors.

 • The BRIDGE (`POST /api/sandbox/inject/{kind}`): a NORMAL tenant-session endpoint. It fires the
   EXISTING sandbox.py injectors on the caller's OWN tenant, but only when that tenant is
   internal/sandbox — this is what puts injectors in the Account & data drawer (R6 Part B). Every
   injection is ledgered; the response always carries {ok, message, link}.

World-level loads run in the BACKGROUND (accept-then-poll) so the click never blocks the browser
thread on a long request; the UI shows the busy-modal → progress chip and polls status. Injections and
resynth are fast/synchronous. All work is double-fire guarded (realify.inflight / the job registry)."""
import datetime
import threading
import uuid

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from .. import superlogin, inflight, billing, db
from ..agency import sandbox, decisions, tenancy, ledger, db as agency_db
from ..agency.guard import require_agency_console
from .deps import current

router = APIRouter()

# ---- background world-job registry (in-process; prod is a single container) ----
_JOB_LOCK = threading.Lock()
_JOBS = {}                       # scenario -> {state, action, started_at, error}
_LOAD_BUDGET_MS = 90_000         # hard per-statement budget so a stuck load can't hold locks forever
_LOAD_LOCK_KEY = 823701          # advisory-lock key: only one world-load per scenario at a time


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _job_start(scenario, action, fn):
    """Start `fn` on a daemon thread unless a job for `scenario` is already running. Returns
    (started, job_snapshot)."""
    with _JOB_LOCK:
        j = _JOBS.get(scenario)
        if j and j["state"] == "running":
            return False, dict(j)
        _JOBS[scenario] = {"state": "running", "action": action, "started_at": _now_iso(), "error": None}
        snap = dict(_JOBS[scenario])

    def _run():
        try:
            fn()
            with _JOB_LOCK:
                _JOBS[scenario].update(state="done", error=None)
        except Exception as e:                                  # pragma: no cover - defensive
            with _JOB_LOCK:
                _JOBS[scenario].update(state="error", error=str(e)[:300])
    threading.Thread(target=_run, daemon=True).start()
    return True, snap


def _world_txn(fn):
    """Run `fn(cur)` in one budgeted, advisory-locked transaction on its own direct connection."""
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute(f"SET statement_timeout = {int(_LOAD_BUDGET_MS)}")    # ≤90s/statement (SET can't bind params)
        cur.execute("SELECT pg_try_advisory_xact_lock(%s)", (_LOAD_LOCK_KEY,))
        if not cur.fetchone()[0]:
            conn.rollback()
            raise RuntimeError("another sandbox world-load is already running")
        fn(cur)
        conn.commit()
    finally:
        conn.close()
    # R14 Part C: after the world commits, synthesize the other four lenses (Profit&Ads, Channels,
    # Intelligence, Category Analyst) for its brands — the builders need the committed seller_skus.
    try:
        from ..agency import lens_synth
        lens_synth.finalize_current_world()
    except Exception as e:                                              # pragma: no cover - defensive
        print(f"[sandbox] cross-lens synthesis failed: {e}", flush=True)

_INJECTORS = {"undercut": sandbox.inject_undercut, "stockout": sandbox.inject_stockout,
              "ad_overspend": sandbox.inject_ad_overspend, "fx_swing": sandbox.inject_fx_swing}
_MSG = {
    "undercut": lambda r: f"Undercut injected on {r.get('hero','the hero SKU')} — buy-box dropped {r.get('drop_pct',10)}%.",
    "stockout": lambda r: "Stockout injected — days-of-cover cut to 3 across the brand's SKUs.",
    "ad_overspend": lambda r: "Ad overspend injected — ACOS pushed +20 across the brand.",
    "fx_swing": lambda r: "FX swing injected — INR −6% overnight.",
}


def _safe(d):
    return {k: (str(v) if isinstance(v, uuid.UUID) else v) for k, v in (d or {}).items()}


def _sb_auth(request):
    """Superlogin session OR staff admin key (unchanged from P7)."""
    from fastapi import HTTPException
    from .deps import require_admin
    if superlogin.verify_session(request.cookies.get("superlogin_session") or ""):
        return True
    try:
        require_admin(request)
        return True
    except HTTPException:
        return False


async def _body(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


def _ccy(cur, tenant_id):
    cur.execute("SELECT impact_currency FROM decisions WHERE tenant_id=%s LIMIT 1", (tenant_id,))
    r = cur.fetchone()
    return (r[0] if r else "USD")


def _tenant_kind(cur, tenant_id):
    cur.execute("SELECT tenant_kind FROM tenants WHERE id=%s", (tenant_id,))
    r = cur.fetchone()
    return (r[0] if r else None)


# ================= HUB OPS CONTROLS (superlogin/admin) =================
@router.post("/api/ops/sandbox/preset", dependencies=[Depends(require_agency_console)])
async def sb_preset(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    scenario = b.get("scenario") or "us_pilot"
    started, job = _job_start(scenario, "load", lambda: _world_txn(
        lambda cur: sandbox.load_preset(cur, scenario=scenario)))
    return JSONResponse({"ok": True, "started": True, "already": (not started),
                         "action": "load", "started_at": job["started_at"]})


@router.post("/api/ops/sandbox/reset", dependencies=[Depends(require_agency_console)])
async def sb_reset(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    scenario = b.get("scenario") or "us_pilot"
    started, job = _job_start(scenario, "reset", lambda: _world_txn(
        lambda cur: sandbox.reset_to_seed(cur, scenario=scenario)))
    return JSONResponse({"ok": True, "started": True, "already": (not started),
                         "action": "reset", "started_at": job["started_at"]})


@router.post("/api/ops/sandbox/clock", dependencies=[Depends(require_agency_console)])
async def sb_clock(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    scenario = b.get("scenario") or "us_pilot"
    days = int(b.get("days", 30) or 30)
    started, job = _job_start(scenario, "clock", lambda: _world_txn(
        lambda cur: sandbox.advance_clock(cur, scenario=scenario, days=days)))
    return JSONResponse({"ok": True, "started": True, "already": (not started),
                         "action": "clock", "started_at": job["started_at"]})


@router.get("/api/ops/sandbox/job", dependencies=[Depends(require_agency_console)])
def sb_job(request: Request):
    """Poll the current world-job for a scenario (chip polls this). done => the modal/chip can finish."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    scenario = request.query_params.get("scenario")
    with _JOB_LOCK:
        if scenario and scenario in _JOBS:
            j = dict(_JOBS[scenario])
        else:                                          # no key given (or unknown) -> report any running job
            run = next((dict(v) for v in _JOBS.values() if v["state"] == "running"), None)
            j = run or {"state": "idle"}
    return JSONResponse({"ok": True, "done": j.get("state") in ("done", "error", "idle"),
                         "state": j.get("state", "idle"), "action": j.get("action"),
                         "started_at": j.get("started_at"), "error": j.get("error")})


@router.get("/api/ops/sandbox/state", dependencies=[Depends(require_agency_console)])
def sb_state(request: Request):
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    # SHORT, budgeted read on its own connection — never queues behind a running world-load. If a load
    # is in progress we surface it from the in-process registry (no probing the load's locks).
    st = {"loaded": False}
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 5000")             # fail fast, never hang the tab
        st = sandbox.sandbox_state(cur)
        st["personas"] = sandbox.persona_targets(cur)
        conn.rollback()
    except Exception as e:                                      # pragma: no cover - defensive
        try:
            conn.rollback()
        except Exception:
            pass
        st = {"loaded": False, "state_error": str(e)[:160]}
    finally:
        conn.close()
    with _JOB_LOCK:                                    # surface ANY running world-job (the world may not
        run = next(((k, dict(v)) for k, v in _JOBS.items() if v["state"] == "running"), None)
    if run:
        st["loading"] = {"in_progress": True, "since": run[1]["started_at"],
                         "action": run[1]["action"], "scenario": run[0]}
    return JSONResponse({"ok": True, **_safe(st)})


@router.post("/api/ops/sandbox/assume", dependencies=[Depends(require_agency_console)])
async def sb_assume(request: Request):
    """Set the browser session to a persona identity and return the redirect. Realify Admin needs no
    session change (the superlogin cookie authorises /ops); the other three set uid/tid."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    b = await _body(request)
    request.session.pop("agency_envelope", None)             # R15 Part 0: fixed-persona assume drops any prior brand envelope
    persona = b.get("persona")
    conn = agency_db.agency_connect()
    try:
        pt = sandbox.persona_targets(conn.cursor())
        conn.rollback()
    finally:
        conn.close()
    if not pt:
        return JSONResponse({"ok": False, "error": "Load a scenario first."}, status_code=400)
    if persona == "admin":
        request.session["acting_as"] = {"role": "Realify Admin", "tenant": "fleet", "via": None}
        return JSONResponse({"ok": True, "redirect": pt["admin_url"]})
    if persona == "client_lead":
        request.session["uid"] = pt["client_lead_uid"]; request.session["tid"] = pt["brand_owner_tenant"]
        request.session["acting_as"] = {"role": "Agency operator", "tenant": _nm(pt["agency_id"], True),
                                        "via": None}
        return JSONResponse({"ok": True, "redirect": pt["queue_url"]})
    if persona == "brand_owner":
        request.session["uid"] = pt["brand_owner_uid"]; request.session["tid"] = pt["brand_owner_tenant"]
        request.session["acting_as"] = {"role": "Managed Brand Owner",
                                        "tenant": _nm(pt["brand_owner_tenant"]), "via": _nm(pt["agency_id"], True)}
        return JSONResponse({"ok": True, "redirect": pt["portal_url"]})
    if persona == "direct":
        _grant_seller_access(pt["direct_tenant"])
        request.session["uid"] = pt["direct_uid"]; request.session["tid"] = pt["direct_tenant"]
        request.session["acting_as"] = {"role": "Direct Brand Owner", "tenant": _nm(pt["direct_tenant"]),
                                        "via": None}
        return JSONResponse({"ok": True, "redirect": pt["direct_url"]})
    return JSONResponse({"ok": False, "error": "unknown persona"}, status_code=400)


def _grant_seller_access(tenant_id):
    """The seller app (`/`) gates on billing — synthesize sandbox access + tester type so a direct
    brand impersonation lands in the real five-lens app."""
    try:
        billing.synthesize_paid(tenant_id)
        c = db.connect(); db.set_account_type(c, tenant_id, "tester"); c.close()
    except Exception:
        pass


def _nm(ident, is_agency=False):
    """Display name for a tenant id or agency uuid (best-effort, own short connection)."""
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        if is_agency:
            cur.execute("SELECT name FROM agencies WHERE id=%s", (ident,))
        else:
            cur.execute("SELECT name FROM tenants WHERE id=%s", (ident,))
        r = cur.fetchone(); conn.rollback()
        return r[0] if r else str(ident)
    finally:
        conn.close()



# (R11.1: the old /api/ops/sandbox/guided/{tenant_id} step-list is retired — see the guided-run
#  teleprompter routes /api/ops/sandbox/guided-run/{start,next,exit} in agency_sandbox_gen.py.)


@router.post("/api/ops/sandbox/inject/{kind}/{tenant_id}", dependencies=[Depends(require_agency_console)])
async def sb_inject_ops(kind: str, tenant_id: int, request: Request):
    """Legacy ops-side inject (kept, _sb_auth unchanged). Ledgered like the bridge."""
    if not _sb_auth(request):
        return JSONResponse({"ok": False, "error": "sandbox auth required"}, status_code=403)
    return _do_inject(kind, tenant_id)


# ================= BRIDGE: injectors in the Account & data drawer =================
@router.post("/api/sandbox/inject/{kind}", dependencies=[Depends(require_agency_console)])
async def sb_inject_bridge(kind: str, request: Request):
    """Fire an injector on the CALLER'S OWN tenant. Allowed only for a normal tenant session whose
    tenant is internal/sandbox; 403 otherwise. Reuses the sandbox.py injectors (no logic duplicated)."""
    uid, tid = current(request)
    if not tid:
        return JSONResponse({"ok": False, "message": "Sign in required.", "link": None}, status_code=401)
    if kind not in _INJECTORS:
        return JSONResponse({"ok": False, "message": f"Unknown injector '{kind}'.", "link": None}, status_code=400)
    conn = agency_db.agency_connect()
    try:
        kindk = _tenant_kind(conn.cursor(), tid)
        conn.rollback()
    finally:
        conn.close()
    if kindk not in ("internal", "sandbox"):
        return JSONResponse({"ok": False, "message": "Sandbox actions are only available on sandbox or "
                             "internal tenants.", "link": None}, status_code=403)
    return _do_inject(kind, tid, actor=uid)


def _do_inject(kind, tenant_id, actor=None):
    fn = _INJECTORS.get(kind)
    if not fn:
        return JSONResponse({"ok": False, "message": f"Unknown injector '{kind}'.", "link": None}, status_code=400)
    with inflight.Guard(f"inject_{kind}", tenant_id) as ok:
        if not ok:
            return JSONResponse({"ok": False, "message": f"An {kind} injection is already in progress.",
                                 "link": None}, status_code=409)
        conn = agency_db.agency_connect()
        try:
            cur = conn.cursor()
            tenancy.set_brand_scope(cur, [tenant_id])
            result = fn(cur, tenant_id)
            if not isinstance(result, dict):        # fx_swing returns a (id, rate_ppm) tuple
                result = {"result": str(result)}
            if kind != "fx_swing":
                decisions.generate(cur, tenant_id, _ccy(cur, tenant_id), datetime.date(2026, 7, 1))
            ledger.append(cur, tenant_id, actor, f"sandbox.inject.{kind}",
                          payload={"kind": kind, **{k: str(v) for k, v in result.items()}})
            conn.commit()
        except Exception as e:                          # surface the engine's reason — never a bare "Failed."
            conn.rollback()
            return JSONResponse({"ok": False, "message": f"Injection failed: {e}", "link": None}, status_code=500)
        finally:
            conn.close()
    msg = _MSG[kind](result)
    link = "/agency/console"
    return JSONResponse({"ok": True, "kind": kind, "tenant_id": tenant_id, "message": msg, "link": link})
