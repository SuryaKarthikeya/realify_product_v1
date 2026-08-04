"""Agents orchestration — roster + hiring + the tester seed.

Honest-by-default: an agent is created in Observe; nothing ACTS until flags.feature_enabled('agents')
AND the RIA models are live (Act stays gated). For tester/sandbox accounts we SEED a Pricing specialist
+ a sample Autonomy Ledger so the surface demos real — the same synthetic path as the rest of the app.
Real customers stay honest-empty until they hire an agent.
"""
from realify import db, flags
from realify.repositories.agent_repo import AgentRepository
from . import catalog


def _is_tester(tenant_id):
    try:
        con = db.connect()
        try:
            at = db.get_account_type(con, tenant_id)
            t = db.get_tenant(con, tenant_id) or {}
        finally:
            con.close()
        return at == "tester" or (t.get("tenant_kind") in ("sandbox", "internal"))
    except Exception:
        return False


def roster(tenant_id):
    con = db.connect()
    try:
        repo = AgentRepository(con)
        agents = repo.list(tenant_id)
        if not agents and _is_tester(tenant_id):
            _seed_tester(con, tenant_id)          # populate a demo so testers see a live-looking workforce
            agents = repo.list(tenant_id)
        # attach task counts + decision counts
        for a in agents:
            a["task_count"] = len(repo.tasks(tenant_id, a["id"]))
        return {"agents": agents, "specialists": catalog.SPECIALISTS,
                "autonomy": catalog.AUTONOMY, "guardrails": catalog.GUARDRAILS,
                "feature_on": flags.feature_enabled("agents", tenant_id)}
    finally:
        con.close()


def agent_detail(tenant_id, agent_id):
    con = db.connect()
    try:
        repo = AgentRepository(con)
        a = repo.get(tenant_id, agent_id)
        if not a:
            return None
        a["tasks"] = repo.tasks(tenant_id, agent_id)
        a["spec"] = catalog.specialist(a["specialist"])
        a["recent"] = repo.ledger(tenant_id, limit=8)
        return a
    finally:
        con.close()


def hire(tenant_id, specialist_id, name=None, autonomy="observe"):
    spec = catalog.specialist(specialist_id)
    if not spec:
        return None
    con = db.connect()
    try:
        repo = AgentRepository(con)
        aid = repo.create(tenant_id, specialist_id, name or spec["name"], autonomy=autonomy,
                          guardrails=catalog.default_guardrails(), scope={"catalog": "all"})
        for t in spec.get("default_tasks", []):
            repo.add_task(tenant_id, aid, t["name"], clock=t.get("clock", ""),
                          cadence=t.get("cadence", "daily"), autonomy=t.get("autonomy", "observe"))
        con.commit()
        return aid
    finally:
        con.close()


def set_status(tenant_id, agent_id, status):
    con = db.connect()
    try:
        AgentRepository(con).set_status(tenant_id, agent_id, status); con.commit()
    finally:
        con.close()


def ledger(tenant_id, limit=100, state=None):
    con = db.connect()
    try:
        repo = AgentRepository(con)
        if not repo.ledger(tenant_id, limit=1) and _is_tester(tenant_id):
            _seed_tester(con, tenant_id)
        return {"decisions": repo.ledger(tenant_id, limit=limit, state=state),
                "intact": repo.ledger_intact(tenant_id)}
    finally:
        con.close()


# --- tester seed: a Pricing specialist + a realistic Autonomy Ledger (the deck's worked examples) ---
_SEED = [
    ("S1 competitor", "Margin", "Ceramic Dutch Oven 6QT",
     "Held price at ₹79.99 — rival −6% is a traffic play; Margin/Destination at peak, cover healthy (41d)",
     "+₹312 / mo", 0.89, "applied"),
    ("S1 + cover", "Inventory", "Nonstick Fry Pan 10\"",
     "Restock, held price — Traffic/KVI would follow sharp, but cover 6d fired the cover-block gate",
     "₹540 / mo risk", 0.83, "handoff"),
    ("S2 margin", "Margin", "Cast Iron Skillet 12\"",
     "TACoS over target — cut ad reliance", "+₹180 / mo", 0.78, "applied"),
    ("S3 sell-through", "Inventory", "Mug Set of 4",
     "Slow vs curve — markdown step 1 (within budget)", "−₹90 mgn", 0.72, "applied"),
    ("S4 promo", "Ads", "Bamboo Cutting Board",
     "BFCM window — staged event price, cover pre-checked", "planned", 0.80, "awaiting"),
]


def _seed_tester(con, tenant_id):
    repo = AgentRepository(con)
    if repo.list(tenant_id):
        return
    aid = repo.create(tenant_id, "pricing", "Pricing & Margin Specialist", autonomy="assist",
                      guardrails=catalog.default_guardrails(), scope={"catalog": "all"})
    spec = catalog.specialist("pricing")
    for t in spec["default_tasks"]:
        repo.add_task(tenant_id, aid, t["name"], clock=t.get("clock", ""),
                      cadence=t.get("cadence", "daily"), autonomy=t.get("autonomy", "observe"))
    # a fixed, deterministic timeline (no Date.now in migrations/services elsewhere; here we can use it
    # since this is request-time, not a workflow) — stagger so the ledger reads like a real day.
    import datetime
    base = datetime.datetime.now(datetime.timezone.utc)
    for i, (signal, lens, sku, action, val, conf, state) in enumerate(_SEED):
        ts = (base - datetime.timedelta(hours=i)).isoformat(timespec="seconds")
        repo.log_decision(tenant_id, aid, None, signal, lens, sku, action,
                          {"arbiter": "ITL-ARB-01"}, val, conf, state, created_at=ts)
    con.commit()
