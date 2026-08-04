"""Realify prototype entrypoint (multi-tenant).

CLI:
  python run.py init            # create schema (run once after overlaying new code)
  python run.py demo            # create demo@realify.ai / demo123 (no data — pick a source in-app)
  python run.py serve           # serve UI + API (auth-gated) from existing DB — NO pulls
  python run.py start           # serve + background 4h scheduler across provisioned tenants
  python run.py status          # source-config panel

Auth: users sign up, pick synthetic-or-upload onboarding, see only their own data.
tenant_id is always resolved from the session, never trusted from the client."""
import sys, os, json
from realify import db, config, auth, scheduler, api, statuscheck, opsdoc
from realify.repositories.card_repo import CardRepository
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.pull_repo import PullLogRepository
from realify.repositories.metrics_repo import MetricsRepository
from realify.repositories.tenant_repo import TenantRepository
from realify.repositories.user_repo import UserRepository
from realify.repositories.channel_repo import ChannelRepository
from realify.repositories.analytics_repo import AnalyticsRepository, SystemRepository

def cmd_init():
    from realify import dbengine
    dbengine.assert_backend()          # FAIL-CLOSED (R10.1): prod/agency mode must be on reachable Postgres
    dbengine.assert_prod_env()         # ENV-DRIFT GUARD (R11): required launch vars set in prod (no dev fallback)
    db.init_db()
    from realify import rules as rules_mod
    rules_mod.seed_catalog()
    from realify.routers.deps import effective_admin_key
    if not effective_admin_key():
        print("[init] WARNING: REALIFY_ADMIN_KEY is unset or a known-weak value — admin endpoints "
              "are LOCKED (fail closed). Set a strong key in .env to enable the operator console.")
    print(f"[init] schema + rules catalog ready at {config.DB_PATH}")

def cmd_status(): statuscheck.check()


def _smoke_postgres():
    """`run.py doctor --postgres` — one-command Postgres smoke. Spins up a throwaway Postgres in
    Docker, runs `init` + the full test suite against it (conftest recreates the schema per test),
    then tears the container down. Catches the dialect gaps (e.g. the executemany class of bug) that
    a SQLite-only suite structurally cannot. Requires Docker. Exit 0 = suite green on real Postgres."""
    import shutil, subprocess, time
    if not shutil.which("docker"):
        print("[smoke-pg] Docker not found on PATH — it is required for --postgres. "
              "Install/start Docker, or run the SQLite suite with: python run.py doctor")
        sys.exit(1)
    name = "realify-smoke-pg"
    port = os.environ.get("SMOKE_PG_PORT", "55432")
    url = f"postgresql+psycopg://postgres:smoke@localhost:{port}/realify"
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)   # clear any leftover
    print(f"[smoke-pg] starting throwaway Postgres ({name}) on :{port} …")
    up = subprocess.run(["docker", "run", "-d", "--name", name,
                         "-e", "POSTGRES_PASSWORD=smoke", "-e", "POSTGRES_DB=realify",
                         "-p", f"{port}:5432", "postgres:18"], capture_output=True, text=True)
    if up.returncode != 0:
        print("[smoke-pg] could not start Postgres:\n" + up.stderr.strip()); sys.exit(1)
    rc = 1
    try:
        import psycopg
        deadline = time.time() + 45
        ready = False
        while time.time() < deadline:
            try:
                psycopg.connect(f"postgresql://postgres:smoke@localhost:{port}/realify",
                                connect_timeout=2).close()
                ready = True; break
            except Exception:
                time.sleep(1)
        if not ready:
            print("[smoke-pg] Postgres did not become ready in time."); return
        print("[smoke-pg] Postgres ready — running init + suite against it (this is slower than SQLite) …")
        env = dict(os.environ, DATABASE_URL=url)
        if subprocess.run([sys.executable, "run.py", "init"], env=env).returncode != 0:
            print("[smoke-pg] FAIL — `init` (schema + migrations) did not apply on Postgres."); return
        rc = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], env=env).returncode
        print("[smoke-pg] " + ("PASS — suite is green against real Postgres."
                                if rc == 0 else "FAIL — a gap surfaced on Postgres (see output above)."))
    finally:
        print(f"[smoke-pg] tearing down {name} …")
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    sys.exit(rc)


def cmd_doctor():
    """Preflight check — validate DB config, connection, and admin key WITHOUT starting the app.
    Run this before flipping `.env`: `python run.py doctor`. Exit 0 = safe to start.
    `python run.py doctor --postgres` runs the full suite against a throwaway Postgres instead."""
    if "--postgres" in sys.argv[2:]:
        return _smoke_postgres()
    from realify import dbengine
    from realify.routers.deps import effective_admin_key
    ok = True
    print(f"[doctor] dialect: {dbengine.dialect()}")
    try:
        dbengine.validate_url()
        print("[doctor] DATABASE_URL shape: OK")
    except SystemExit as e:
        print(f"[doctor] DATABASE_URL shape: FAIL — {e}"); ok = False
    if ok:
        try:
            con = db.connect(); con.execute("SELECT 1").fetchone(); con.close()
            print("[doctor] DB connection: OK")
        except Exception as e:
            print(f"[doctor] DB connection: FAIL — {str(e).splitlines()[0]}"); ok = False
    if effective_admin_key():
        print("[doctor] admin key: OK (strong key set)")
    else:
        print("[doctor] admin key: LOCKED — REALIFY_ADMIN_KEY unset or weak; admin endpoints denied "
              "(set a strong key in .env to enable them)")
    print("[doctor] " + ("ALL CHECKS PASSED — safe to start." if ok else "PROBLEMS FOUND — fix before starting."))
    sys.exit(0 if ok else 1)


def cmd_migrate_pg():
    """1g — copy data SQLite -> Postgres. `python run.py migrate-pg [--dry-run]`."""
    from realify import migrate_sqlite_to_pg as mig
    dry = "--dry-run" in sys.argv[2:]
    dest = config.DATABASE_URL.split("@")[-1] if "@" in config.DATABASE_URL else config.DATABASE_URL
    print(f"[migrate-pg] source={config.DB_PATH}  dest={dest}{'  (dry-run)' if dry else ''}")
    report = mig.migrate(dry_run=dry)
    ok = True
    for table, n_src, n_dst in report:
        mism = (not dry) and n_src != n_dst
        ok = ok and not mism
        print(f"  {table:24} src={n_src:<8} dst={'-' if n_dst is None else n_dst}{'   <-- MISMATCH' if mism else ''}")
    if dry:
        print("[migrate-pg] dry run complete — no writes.")
    else:
        print("[migrate-pg] " + ("OK — all row counts match." if ok else "DONE WITH MISMATCHES — investigate above before cutover."))

def cmd_demo():
    cmd_init()
    try:
        uid, tid = auth.signup("demo@realify.ai", "demo123", "Autofy (demo)")
        print("[demo] created account demo@realify.ai / demo123")
    except ValueError:
        con=db.connect(); u=db.get_user_by_email(con,"demo@realify.ai"); db.wipe_tenant_data(con, u["tenant_id"]); con.close()
        print("[demo] reset existing account demo@realify.ai / demo123")
    print("[demo] No data provisioned yet — by design.")
    print("[demo] Now: python run.py serve  ->  log in  ->  choose 'Use demo ASINs' or 'Upload my ASINs'.")
    print("[demo] All Keepa / market pulls run only AFTER you pick an option in the app.")

def cmd_serve():
    from realify import dbengine
    dbengine.assert_backend()          # FAIL-CLOSED (R10.1): prod/agency mode must be on reachable Postgres
    dbengine.assert_prod_env()         # ENV-DRIFT GUARD (R11): required launch vars set in prod (no dev fallback)
    if dbengine.dialect() != "postgresql" and not os.path.exists(config.DB_PATH):
        print("[serve] no database — run `python run.py init` (and `demo`) first."); return
    print(f"[serve] http://localhost:{config.PORT}  (auth-gated; no pulls)")
    try:
        import uvicorn; uvicorn.run(make_app(), host="0.0.0.0", port=config.PORT)
    except ImportError:
        print("[serve] pip install fastapi uvicorn")

def cmd_start():
    cmd_init(); statuscheck.check(); scheduler.start_background()
    try:
        import uvicorn; uvicorn.run(make_app(), host="0.0.0.0", port=config.PORT)
    except ImportError:
        print("[start] pip install fastapi uvicorn"); import time
        while True: time.sleep(3600)

# ============================ web app ============================
def make_app():
    from fastapi import FastAPI
    from starlette.middleware.sessions import SessionMiddleware
    from realify.routers import pages, onboarding, insights, cards, settings, admin, skus, analyst, wizard, assistant, intelligence, workspace
    from realify.routers import auth as auth_api
    from realify.routers import cmaa as cmaa_api
    from realify.routers import marketing, billing as billing_api, ads as ads_api
    app = FastAPI(title="Realify")
    # same_site/https_only default to "lax"/False (same-site localhost dev). Cross-site setups —
    # e.g. a dev-tunneled backend (https://*.devtunnels.ms) talking to a frontend on localhost —
    # need SESSION_SAMESITE=none + SESSION_HTTPS_ONLY=true, else the browser withholds the session
    # cookie on cross-site XHR/fetch and every authenticated route 401s past the initial page load.
    app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET, max_age=60*60*24*14,
                       same_site=config.SESSION_SAMESITE, https_only=config.SESSION_HTTPS_ONLY)
    # The realifyAi SPA is a separate origin (Vite dev server, or its own prod
    # domain) and auths via this session cookie, so cross-origin requests must
    # carry credentials — which the CORS spec forbids combining with a "*"
    # origin. APP_URL is the same knob billing.py already reads for building
    # Stripe redirect URLs; local Vite dev origins are included so `npm run
    # dev` works without also requiring APP_URL to be set.
    from fastapi.middleware.cors import CORSMiddleware
    _cors_origins = [o for o in [config.APP_URL, "http://localhost:5173", "http://127.0.0.1:5173"] if o]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # R11.1: serve the real logo assets LOCALLY (no realify.ai hotlink) — the whole realify/assets dir.
    from fastapi.staticfiles import StaticFiles
    app.mount("/assets", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            "realify", "assets")), name="assets")
    # Unversioned routers keep their absolute /api paths (existing UI unchanged).
    app.include_router(pages.router)
    app.include_router(marketing.router)                     # public marketing shell + auth pages
    app.include_router(billing_api.router)                   # Stripe signup / status / portal / webhook / billing
    app.include_router(auth_api.router)
    app.include_router(onboarding.router)
    app.include_router(wizard.router)                        # guided cross-channel onboarding wizard
    app.include_router(settings.router)
    app.include_router(admin.router)
    app.include_router(assistant.router)   # RIA chat widget → bot proxy (same-origin)
    # Partner-facing read + action surface: mounted at /api (existing UI) AND /api/v1 (frozen contract).
    app.include_router(insights.router, prefix="/api")
    app.include_router(insights.router, prefix="/api/v1")
    app.include_router(cards.router, prefix="/api")
    app.include_router(cards.router, prefix="/api/v1")
    app.include_router(skus.router, prefix="/api")
    app.include_router(workspace.router, prefix="/api")       # Workspace KPI cards: 5 main + per-domain substats
    app.include_router(cmaa_api.router, prefix="/api")
    app.include_router(cmaa_api.router, prefix="/api/v1")
    app.include_router(analyst.router, prefix="/api")        # Your Category Analyst (synthesis-led read surface)
    app.include_router(analyst.router, prefix="/api/v1")
    app.include_router(ads_api.router, prefix="/api")        # attributable ads: coverage + Fix-Ads recommendations
    app.include_router(intelligence.router, prefix="/api")   # explainability: AI recs + reason trace + backtested accuracy
    from realify.routers import graph_ads as graph_ads_api
    app.include_router(graph_ads_api.router, prefix="/api")  # bot proxies: signal graph + CVaR ad budget (gated)
    from realify.routers import ask as ask_api
    app.include_router(ask_api.router, prefix="/api")        # Ask: conversational home (agent skeleton + stub model)
    from realify.routers import agents as agents_api
    app.include_router(agents_api.router, prefix="/api")     # Agents: the workforce (framework + Pricing flagship)
    from realify.routers import agency as agency_api
    app.include_router(agency_api.router)                    # agency funnel (P2) — self-gated by AGENCY_CONSOLE
    from realify.routers import agency_consent as agency_consent_api
    app.include_router(agency_consent_api.router)            # brand consent + connections (P3)
    from realify.routers import agency_console as agency_console_api
    app.include_router(agency_console_api.router)            # portfolio console + work queue (P4)
    from realify.routers import agency_execution as agency_execution_api
    app.include_router(agency_execution_api.router)          # bulk execution + undo (R2/R3)
    from realify.routers import agency_approvals as agency_approvals_api
    app.include_router(agency_approvals_api.router)          # approvals + execution controls (P5)
    from realify.routers import agency_billing as agency_billing_api
    app.include_router(agency_billing_api.router)            # reporting, billing, pilot (P6)
    from realify.routers import agency_admin as agency_admin_api
    app.include_router(agency_admin_api.router)              # internal admin, quality, superlogin (P7)
    from realify.routers import agency_deletion as agency_deletion_api
    app.include_router(agency_deletion_api.router)           # R17 deletion close-out queue actions
    from realify.routers import agency_brand as agency_brand_api
    app.include_router(agency_brand_api.router)              # brand surfaces: data sources, portal, day-0, offboarding (R3)
    from realify.routers import agency_sandbox as agency_sandbox_api
    app.include_router(agency_sandbox_api.router)            # sandbox hub controls (R4)
    from realify.routers import agency_sandbox_gen as agency_sandbox_gen_api
    app.include_router(agency_sandbox_gen_api.router)        # R9 generator / impersonation / short-circuit
    from realify.routers import agency_team as agency_team_api
    app.include_router(agency_team_api.router)               # R10 agency user management
    from realify.routers import agency_queue as agency_queue_api
    app.include_router(agency_queue_api.router)              # R11: /agency/queue retired -> redirects to fleet
    from realify.routers import agency_scope as agency_scope_api
    app.include_router(agency_scope_api.router)              # R11 scope-switcher drill-in (h8)
    return app

if __name__ == "__main__":
    args = sys.argv[1:]; cmd = args[0] if args else "serve"
    {"init":cmd_init, "demo":cmd_demo, "serve":cmd_serve, "start":cmd_start,
     "status":cmd_status, "migrate-pg":cmd_migrate_pg, "doctor":cmd_doctor}.get(cmd, cmd_serve)()
