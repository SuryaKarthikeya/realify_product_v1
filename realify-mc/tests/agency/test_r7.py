"""R7 (Postgres/agency suite): seed health (connected-by-default queue), work-queue UI fidelity,
fleet exclusion of internal/sandbox + relabeled counters + gates control, and the prod-hygiene sweep +
reaper."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realify.agency import sandbox, connections, tenancy, sweep


# ---- Part 1: after load, most brands are LIVE (not paused); queue has spread; top impact positive ----
def test_pilot_loads_connected_with_spread(owner_conn):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur); owner_conn.commit()
    brand_ids = [b["tenant_id"] for b in st["brands"]]
    paused = []
    for t in brand_ids:
        paused.append(connections.decisions_paused(cur, t))
    live = sum(1 for p in paused if not p)
    assert live >= 6, f"most brands must be live/actionable, got {live}/8"
    assert 1 <= (8 - live) <= 2, "exactly 1-2 brands demo the paused state"
    # queue across the live book: >1 action type, top item positive $-impact
    from realify.agency import queue
    live_ids = [t for t, p in zip(brand_ids, paused) if not p]
    tenancy.set_brand_scope(cur, live_ids)
    items = queue.build(cur, live_ids)
    assert items and items[0]["rank_usd_minor"] > 0                 # top item positive
    kinds = {(i["lens"], i["kind"]) for i in items}
    assert len(kinds) > 1                                            # >1 action type
    # most live brands have >=1 non-paused decision
    with_dec = {i["tenant_id"] for i in items}
    assert len(with_dec) >= 6


# ---- Part 2: /agency/queue rendered to screen-19 fidelity, actions via busy-modal ----
def test_queue_ui_fidelity(agency_client, owner_conn):
    client, H = agency_client
    sandbox.load_preset(owner_conn.cursor()); owner_conn.commit()
    r = client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "client_lead"})
    assert r.status_code == 200
    import re
    # R11: the cross-brand queue is retired. Triage happens on the FLEET GRID (h7); acting happens in the
    # per-brand DRILL-IN (h8). This asserts fidelity of both.
    fleet = client.get("/agency/console").text
    assert "Fleet" in fleet and "at stake" in fleet and "need attention" in fleet   # h7 header + $-at-stake
    assert re.search(r"hb-(sage|gold|terra)", fleet)                 # health bands on the left edge
    assert "hb-terra" in fleet                                       # the 1-2 expired brands render at-risk
    ids = re.findall(r"/agency/brand/(\d+)", fleet)
    assert ids                                                       # cards link into the scope-switcher drill-in
    # R15 Part 0 — h8 drill-in is UNIFIED: "Open brand →" scope-switches into the REAL five-lens app
    # (no bespoke wrapper). The envelope + identity ride the session; the real app gates in-lens acts.
    r0 = client.get(f"/agency/brand/{ids[0]}", follow_redirects=False)
    assert r0.status_code == 303 and r0.headers["location"] == "/"
    scope = client.get("/api/scope").json()["agency_scope"]
    assert scope and scope["caps"] and scope.get("brand")           # envelope caps + brand identity in scope
    app = client.get("/").text
    assert "Per-brand decisions" not in app and "surfaceLabel" in app   # retired wrapper gone; real SPA renders


# ---- Part 3a/3b: fleet excludes internal/sandbox by default; toggle reveals; counters relabeled ----
def test_fleet_excludes_internal_and_counter_language(agency_client, owner_conn):
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name,hq_country) VALUES('Acme Real Agency','US')")
    cur.execute("INSERT INTO agencies(name,hq_country) VALUES('R2 Live Verify','US')")
    owner_conn.commit()
    sweep.sweep(cur); owner_conn.commit()                           # retire the verify agency (reversible)
    client, H = agency_client
    default = client.get("/ops/agency/admin", headers=H).text
    assert "Acme Real Agency" in default                            # real agency shown
    assert "R2 Live Verify" not in default                          # internal hidden by default
    assert "seller tenants (billable" in default and "paying accounts" in default   # internal-ops relabel
    assert "revenue accounts" not in default                        # old misleading label gone
    shown = client.get("/ops/agency/admin?internal=1", headers=H).text
    assert "R2 Live Verify" in shown                                # toggle reveals internal/sandbox


# ---- Part 3c: gates panel is the designed control (no stray EXPIRED dropdown artifact) ----
def test_gates_panel_control(agency_client, owner_conn):
    client, H = agency_client
    body = client.get("/ops/agency/admin", headers=H).text
    assert "Set auto gate" in body                                  # designed control present
    assert "<option>EXPIRED</option>" not in body and ">EXPIRED<" not in body   # artifact removed
    assert "Gates" in body


# ---- Part 3d: quality console is tiles + precision-by-action (not a <pre> dump) ----
def test_quality_console_ui(agency_client, owner_conn):
    client, H = agency_client
    body = client.get("/ops/agency/quality", headers=H).text
    assert "<pre" not in body
    assert "Precision by action class" in body and "class=kpi" in body


# ---- Part 0: sweep categorizes + retires reversibly; reaper retires stale VERIFY-* ----
def test_sweep_by_category_and_reaper(owner_conn):
    cur = owner_conn.cursor()
    for nm in ("R2 Live Verify", "R3 Feeder Verify", "VERIFY-r7-x", "Sandbox Agency", "Acme Real"):
        cur.execute("INSERT INTO agencies(name,hq_country) VALUES(%s,'US')", (nm,))
    owner_conn.commit()
    counts = sweep.sweep(cur); owner_conn.commit()
    assert counts["live_verify"] >= 1 and counts["feeder_verify"] >= 1
    assert counts["verify_prefix"] >= 1 and counts["legacy_sandbox_agency"] >= 1
    # real agency untouched; verify ones flagged internal
    cur.execute("SELECT internal FROM agencies WHERE name='Acme Real'"); assert cur.fetchone()[0] is False
    cur.execute("SELECT count(*) FROM agencies WHERE name LIKE '%Verify%' AND internal"); assert cur.fetchone()[0] >= 2
    # reaper: an OLD VERIFY-* agency is retired; a fresh one is not
    cur.execute("INSERT INTO agencies(name,hq_country,created_at) VALUES('VERIFY-old','US',now()-interval '10 days')")
    cur.execute("INSERT INTO agencies(name,hq_country) VALUES('VERIFY-fresh','US')")
    owner_conn.commit()
    reaped = sweep.reap_verify(cur, older_than_days=7); owner_conn.commit()
    assert reaped >= 1
    cur.execute("SELECT internal FROM agencies WHERE name='VERIFY-old'"); assert cur.fetchone()[0] is True
    cur.execute("SELECT internal FROM agencies WHERE name='VERIFY-fresh'"); assert cur.fetchone()[0] is False
