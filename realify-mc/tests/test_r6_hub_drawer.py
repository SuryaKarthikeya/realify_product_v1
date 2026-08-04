"""R6 (main/SQLite suite): tester-hub rendered-UI + no-dead-controls, the busy-modal component, the
/api/me tenant_kind field, and the resynthesize ALLOWLIST guard + double-fire rejection. The Postgres
sandbox engine + bridge authz live in tests/agency/test_r6_sandbox.py."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import auth, db, inflight        # noqa: E402
from realify.site.hub import hub_html                    # noqa: E402  (R9 reimagined hub)
from realify.site.busy_modal import SNIPPET as MODAL     # noqa: E402


def _client():
    from run import make_app
    from fastapi.testclient import TestClient
    return TestClient(make_app())


def _login(c, email="r6@x.com"):
    uid, tid = auth.signup(email, "hunter2pw", "R6 Co")
    assert c.post("/api/login", json={"email": email, "password": "hunter2pw"}).status_code == 200
    return uid, tid


# ---- no dead controls on the R9 hub: every button is wired (id+listener, .ent class, or onclick) ----
def test_hub_no_dead_controls():
    html = hub_html("staff@realify.ai")
    for m in re.finditer(r'<button\b([^>]*)>', html):
        attrs = m.group(1)
        bid = re.search(r'id=([A-Za-z0-9_]+)', attrs)
        if bid:
            assert f"getElementById('{bid.group(1)}')" in html and ".addEventListener" in html, \
                f"hub button #{bid.group(1)} has no handler"
        elif "gr-start" in attrs:
            assert ".gr-start" in html and ".addEventListener" in html   # R11.1 guided-run buttons wired by class
        elif "ent" in attrs:
            assert ".ent" in html and ".addEventListener" in html   # role Enter buttons wired by class
        elif "data-preset" in attrs or "data-saved" in attrs:
            assert "[data-preset]" in html and "[data-saved]" in html  # seed-list buttons wired on render
        else:
            assert "onclick=" in attrs, f"dead hub button: {attrs}"
    # role doorways are wired by the [data-role]/.ent listeners
    assert "data-role=" in html and ".ent" in html


# ---- state header renders every required field ----
def test_hub_state_header_fields_and_empty_state():
    html = hub_html("staff@realify.ai")
    for label in ("Scenario", "Seed", "Country", "Brands", "Last loaded", "Next reset"):
        assert label in html, f"state header missing field: {label}"
    assert "Nothing loaded yet" in html                       # empty-state guidance
    assert "US Pilot" in html and "India Pilot" in html       # points at the presets


# ---- roles render disabled-by-default (unlocked by JS after a world loads) ----
def test_hub_personas_disabled_until_loaded():
    html = hub_html("staff@realify.ai")
    assert html.count('class="role dis"') == 4                # all four roles start disabled
    assert "load a dataset first" in html
    # R14 Part A: the two-state machine locks Role until a world loads, then locks Data (via _setRoleLocked)
    assert "function _setRoleLocked(lock)" in html and "_setRoleLocked(!on)" in html


# ---- busy-modal component present + accept-then-poll wiring ----
def test_busy_modal_markup_on_hub():
    html = hub_html("staff@realify.ai")
    assert 'id="realifyBusyModal"' in html and "RealifyBusy" in html
    assert html.count("RealifyBusy.runJob") >= 3              # generate / preset / reset / clock
    assert "/api/ops/sandbox/job" in html                     # the chip polls the job-status endpoint


# ---- R6.1 defect #1: no synchronous XHR anywhere (blocking the main thread) ----
def test_no_sync_xhr_anywhere():
    import glob
    surfaces = [os.path.join(os.path.dirname(__file__), "..", f)
                for f in ("frontend.html", "login.html", "admin.html", "analytics.html")]
    blobs = [open(p, encoding="utf-8").read() for p in surfaces if os.path.exists(p)]
    blobs.append(MODAL)
    blobs.append(hub_html("s@realify.ai"))
    bad = re.compile(r"async\s*:\s*false|\.open\([^)]*,\s*false\s*\)|new\s+XMLHttpRequest|XMLHttpRequest\s*\(")
    for b in blobs:
        m = bad.search(b)
        assert not m, f"synchronous XHR / busy-wait found: {m.group(0)!r}"
    # the modal drives work with async fetch + await, never a sync request
    assert "await" in MODAL and "fetch(" in MODAL


# ---- R6.1 defect #3: empty-state text is baked in (renders even before JS runs) ----
def test_hub_empty_state_baked_in():
    html = hub_html("staff@realify.ai")
    head = html.split('id=stateHead', 1)[1][:400]
    assert "Nothing loaded yet" in head                       # not a blank box before JS runs


# ---- C2 server-side double-fire rejection ----


def test_busy_modal_component_contract():
    for token in ('id="realifyBusyModal"', "rb-elapsed", "RealifyBusy", "focus()",
                  "runJob", "realifyJobChips", "aria-modal"):
        assert token in MODAL, f"busy-modal missing {token}"
    # Escape is trapped (blocking modal), and a backgrounded job converts to a chip (async honesty)
    assert "e.key==='Escape'" in MODAL and "chip(" in MODAL


# ---- /api/me includes tenant_kind ----
def test_api_me_includes_tenant_kind():
    c = _client(); _login(c)
    d = c.get("/api/me").json()
    assert d["authed"] is True and "tenant_kind" in d


# ---- B4 allowlist guard on /api/settings/resynthesize (fresh tenant per case; account_type locks at
#      provisioning, so each case is set up independently) ----
def test_resynth_allowlist_guard(monkeypatch):
    from realify import scheduler
    monkeypatch.setattr(scheduler, "resynthesize", lambda tid, mode: {"ok": True, "mode": mode})

    # account_type None on a plain (unprovisioned) tenant -> 403 (this was the fail-open hole)
    c1 = _client(); _login(c1, "b4none@x.com")
    assert c1.post("/api/settings/resynthesize", json={"mode": "reroll"}).status_code == 403

    # synthetic + tester -> allowed (not 403)
    c2 = _client(); _u2, t2 = _login(c2, "b4tester@x.com")
    con = db.connect(); db.set_account_type(con, t2, "tester")
    db.set_tenant_provisioned(con, t2, "synthetic"); con.close()
    assert c2.post("/api/settings/resynthesize", json={"mode": "reroll"}).status_code != 403

    # synthetic + customer -> 403 (existing behavior preserved)
    c3 = _client(); _u3, t3 = _login(c3, "b4cust@x.com")
    con = db.connect(); db.set_account_type(con, t3, "customer")
    db.set_tenant_provisioned(con, t3, "synthetic"); con.close()
    assert c3.post("/api/settings/resynthesize", json={"mode": "reroll"}).status_code == 403


# ---- drawer: Sandbox actions box is wired (no dead controls) + gated on tenant_kind ----
def test_frontend_drawer_sandbox_actions_wired():
    html = open(os.path.join(os.path.dirname(__file__), "..", "frontend.html"), encoding="utf-8").read()
    assert 'id="sandboxActionsBox"' in html
    kinds = re.findall(r'class="btn-muted sbinj" data-kind="([a-z_]+)"', html)
    assert set(kinds) == {"undercut", "stockout", "ad_overspend", "fx_swing"}   # all four injectors
    # each .sbinj is wired, and it posts to the bridge via the busy modal
    assert ".sbinj" in html and ".addEventListener" in html and "/api/sandbox/inject/" in html
    assert "RealifyBusy.run" in html                                            # resynth + injectors use the modal
    # JS gate keys off tenant_kind (server 403 is the real gate)
    assert "me.tenant_kind === 'sandbox'" in html and "sandboxActionsBox" in html
    # the modal placeholder is present for serve-time injection
    assert "<!--BUSY_MODAL-->" in html


# ---- served frontend injects the shared busy modal ----
def test_served_frontend_injects_busy_modal():
    from realify import billing
    c = _client(); _uid, tid = _login(c, "r6front@x.com")
    billing.synthesize_paid(tid)
    con = db.connect(); db.set_tenant_provisioned(con, tid, "synthetic")
    db.set_account_type(con, tid, "tester"); con.close()
    body = c.get("/").text
    assert 'id="realifyBusyModal"' in body and "RealifyBusy" in body            # modal injected at serve time
    assert "<!--BUSY_MODAL-->" not in body                                      # placeholder replaced


# ---- C2 server-side double-fire rejection ----
def test_resynth_double_fire_rejected(monkeypatch):
    from realify import scheduler
    monkeypatch.setattr(scheduler, "resynthesize", lambda tid, mode: {"ok": True})
    c = _client(); _uid, tid = _login(c)
    con = db.connect(); db.set_tenant_provisioned(con, tid, "synthetic")
    db.set_account_type(con, tid, "tester"); con.close()
    inflight.acquire("resynthesize", tid)                     # simulate an in-flight request
    try:
        assert c.post("/api/settings/resynthesize", json={"mode": "reroll"}).status_code == 409
    finally:
        inflight.release("resynthesize", tid)
    # lock released -> succeeds again
    assert c.post("/api/settings/resynthesize", json={"mode": "reroll"}).status_code == 200
