"""Feature/Version Registry — the standard rollout convention.

Verifies: default = baseline / gates off (deploy = no-op); query pin > tenant pin > scope for version
features; the Ops version picker + rollback; behavior gates independent of version; list_state shape; the
`/api/admin/rollout` catalog endpoint; and that home()'s v4 branch stays a dormant no-op until the
parallel template exists. Backward-compat aliases (resolve_skin) still work.
"""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_flags_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import flags  # noqa: E402


class _Req:
    def __init__(self, q=None, sess=None):
        self.query_params = q or {}
        self.session = sess if sess is not None else {}


def test_default_is_baseline_and_gates_off():
    assert flags.active_version("app_ui", _Req()) == "legacy"     # baseline; deploy changes nothing
    assert flags.resolve_skin(_Req()) == "legacy"                  # alias
    assert flags.feature_enabled("ask") is False and flags.feature_enabled("agents") is False


def test_query_pin_sticky_and_alias():
    sess = {}
    assert flags.active_version("app_ui", _Req(q={"skin": "v4"}, sess=sess)) == "v4"   # ?skin= alias
    assert sess.get("reg.app_ui") == "v4"                          # sticky for the session
    assert flags.active_version("app_ui", _Req(sess=sess)) == "v4"
    assert flags.active_version("app_ui", _Req(q={"app_ui": "legacy"}, sess=sess)) == "legacy"  # generic key
    assert flags.active_version("app_ui", _Req(q={"skin": "bogus"})) == "legacy"       # invalid -> baseline


def test_version_picker_scope_and_rollback():
    # pick the build + turn scope on -> everyone gets it
    flags.set_selected("app_ui", "v4"); flags.set_scope("app_ui", "on")
    assert flags.active_version("app_ui", _Req()) == "v4"
    # ROLLBACK by scope
    flags.set_scope("app_ui", "off")
    assert flags.active_version("app_ui", _Req()) == "legacy"
    # ROLLBACK by selecting the previous build (even with scope on)
    flags.set_scope("app_ui", "on"); flags.set_selected("app_ui", "legacy")
    assert flags.active_version("app_ui", _Req()) == "legacy"
    # internal scope = baseline globally, opt-in still works
    flags.set_selected("app_ui", "v4"); flags.set_scope("app_ui", "internal")
    assert flags.active_version("app_ui", _Req()) == "legacy"
    assert flags.active_version("app_ui", _Req(q={"skin": "v4"})) == "v4"
    flags.set_scope("app_ui", "off"); flags.set_selected("app_ui", "v4")


def test_tenant_pin_overrides_global():
    flags.set_scope("app_ui", "on"); flags.set_selected("app_ui", "v4")
    flags.set_tenant_pin("app_ui", 99, "legacy")
    assert flags.active_version("app_ui", _Req(), tenant_id=99) == "legacy"    # tenant opt-out wins
    assert flags.active_version("app_ui", _Req()) == "v4"                       # others still v4
    flags.set_scope("app_ui", "off")


def test_gates_and_v4_dependency():
    flags.set_scope("app_ui", "on"); flags.set_selected("app_ui", "v4")   # v4 rolled out
    assert flags.feature_enabled("agents") is False                # gate still OFF by default
    flags.set_feature("agents", True)
    assert flags.feature_gate("agents") is True and flags.feature_available("agents") is True
    assert flags.feature_enabled("agents") is True                 # gate AND dependency
    flags.set_feature("agents", False, tenant_id=7)                # per-tenant override
    assert flags.feature_enabled("agents", tenant_id=7) is False
    assert flags.feature_enabled("agents") is True
    flags.set_feature("agents", False)

def test_forward_feature_greys_out_under_legacy():
    # gate ON but the build is legacy -> dependency unmet -> effective OFF, available False
    flags.set_feature("agents", True); flags.set_feature("ask", True)
    flags.set_scope("app_ui", "off")                               # v4 not rolled out
    assert flags.feature_available("agents") is False and flags.feature_available("ask") is False
    assert flags.feature_enabled("agents") is False                # inert despite the 'on' gate
    assert flags.feature_gate("agents") is True                    # raw toggle still records 'on'
    st = {f["key"]: f for f in flags.list_state()}
    assert st["agents"]["available"] is False and st["agents"]["enabled"] is True and st["agents"]["effective"] is False
    # roll v4 back out -> becomes available again, no re-toggle needed
    flags.set_scope("app_ui", "on"); flags.set_selected("app_ui", "v4")
    assert flags.feature_available("agents") is True and flags.feature_enabled("agents") is True
    flags.set_scope("app_ui", "off"); flags.set_feature("agents", False); flags.set_feature("ask", False)


def test_list_state_shape():
    st = {f["key"]: f for f in flags.list_state()}
    assert st["app_ui"]["kind"] == "version" and st["app_ui"]["baseline"] == "legacy"
    assert [v["id"] for v in st["app_ui"]["versions"]] == ["legacy", "v4"]
    assert st["ask"]["kind"] == "gate" and "enabled" in st["ask"]


def test_rollout_endpoint_picks_build_and_gates():
    os.environ["REALIFY_ADMIN_KEY"] = "rollout-test-key-9x"
    from starlette.testclient import TestClient
    import run
    c = TestClient(run.make_app()); hdr = {"x-realify-admin": "rollout-test-key-9x"}
    d = c.get("/api/admin/rollout", headers=hdr).json()
    assert d["ok"] and any(f["key"] == "app_ui" for f in d["features"])
    # pick v4 + scope on
    c.post("/api/admin/rollout", json={"feature": "app_ui", "version": "v4"}, headers=hdr)
    c.post("/api/admin/rollout", json={"feature": "app_ui", "scope": "on"}, headers=hdr)
    c.post("/api/admin/rollout", json={"feature": "ask", "on": True}, headers=hdr)
    assert flags.active_version("app_ui", _Req()) == "v4" and flags.feature_enabled("ask") is True
    assert c.get("/api/admin/rollout").status_code in (401, 403)   # no key -> forbidden
    # rollback via endpoint
    c.post("/api/admin/rollout", json={"feature": "app_ui", "scope": "off"}, headers=hdr)
    c.post("/api/admin/rollout", json={"feature": "ask", "on": False}, headers=hdr)
    assert flags.active_version("app_ui", _Req()) == "legacy" and flags.feature_enabled("ask") is False


def test_home_serves_legacy_by_default_and_v4_when_flagged():
    """The parallel skin: default (no flag) serves the legacy SPA; ?skin=v4 serves frontend_v4.html.
    A logged-in customer is required so home() reaches the app shell (not the marketing/onboarding path)."""
    import run
    from starlette.testclient import TestClient
    from realify import auth as _auth, db as _db
    c = TestClient(run.make_app())
    _auth.signup("v4home@x.com", "secret123", "V4Co")
    assert c.post("/api/login", json={"email": "v4home@x.com", "password": "secret123"}).status_code == 200
    with _db.connect() as con:
        tid = con.execute("SELECT tenant_id FROM users WHERE email=?", ("v4home@x.com",)).fetchone()["tenant_id"]
        _db.set_account_type(con, tid, "customer")
        _db.set_tenant_provisioned(con, tid, "uploaded")   # has data -> app shell, not the wizard
        from realify.repositories.tenant_repo import TenantRepository
        TenantRepository(con).set_subscription(tid, subscription_status="active")   # clear the billing gate
        con.commit()
    legacy = c.get("/").text
    assert "frontend_v4" not in legacy or "surface-wrap" not in legacy   # default = legacy SPA
    v4 = c.get("/?skin=v4").text
    assert 'class="rail"' in v4 and 'id="surface"' in v4                  # the V4 shell markup
    # and the file exists (branch is now live, not dormant)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert os.path.exists(os.path.join(root, "frontend_v4.html"))


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_") and _f.__code__.co_argcount == 0:
            _f()
    print("flags OK")
