"""PDP (realify/pdp) — T-P1-03 goldens (>=120 cases) + T-P1-04 property. Pure logic, no DB, so it runs
in the default suite. Effective capability = intersection(envelope, grant)."""
import os
import sys

from hypothesis import given, strategies as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.pdp import decide, Action, ENVELOPES, ROLES, LENSES     # noqa: E402

_RANK = {"none": 0, "read": 1, "propose": 2, "execute": 3}


def _within(caps, action):
    """Independent oracle for one side: is the action permitted by this caps dict alone?"""
    c = caps.get(action.lens) if isinstance(caps, dict) else None
    if not c:
        return False
    if action.kind == "autonomy_set":
        return action.level <= int(c.get("autonomy_ceiling", 0))
    if action.kind not in ("read", "propose", "execute"):
        return False
    return _RANK[action.kind] <= _RANK.get(c.get("max_kind", "none"), 0)


def _oracle(env, grant, action):
    return _within(env, action) and _within(grant, action)


# ---- hand-verified anchors (pin the oracle itself against the real templates) --------------------
def _d(env_name, role_name, lens, kind, level=0):
    return decide(ENVELOPES[env_name], ROLES[role_name], Action(lens, kind, level))


def test_anchor_cases():
    assert _d("Full Operate", "agency_admin", "pricing", "execute").allow            # both full
    assert _d("Ads Only", "ads_manager", "ads", "execute").allow                     # ads path
    assert _d("Full Operate", "analyst", "pricing", "propose").allow                 # grant caps propose

    # envelope is the binding constraint
    r = _d("Advise", "agency_admin", "ads", "execute")
    assert not r.allow and "envelope" in r.reason
    r = _d("Ads Only", "agency_admin", "pricing", "execute")
    assert not r.allow and "envelope" in r.reason
    r = _d("Operate ex-Pricing", "agency_admin", "pricing", "execute")
    assert not r.allow and "envelope" in r.reason
    assert _d("Operate ex-Pricing", "agency_admin", "inventory", "execute").allow

    # grant is the binding constraint
    r = _d("Full Operate", "viewer", "ads", "execute")
    assert not r.allow and "grant" in r.reason
    r = _d("Full Operate", "analyst", "pricing", "execute")
    assert not r.allow and "grant" in r.reason

    # autonomy_set gated by the lower ceiling
    assert _d("Full Operate", "account_manager", "ads", "autonomy_set", 2).allow     # min(3,2)=2
    assert not _d("Full Operate", "account_manager", "ads", "autonomy_set", 3).allow  # grant ceiling 2
    assert not _d("Read-only", "agency_admin", "ads", "autonomy_set", 1).allow        # envelope ceiling 0

    # unknown lens / unknown kind -> deny
    assert not _d("Full Operate", "agency_admin", "unknown_lens", "read").allow
    assert not _d("Full Operate", "agency_admin", "ads", "bogus").allow


# ---- T-P1-03: >=120 golden cases, every one matching the independent oracle ----------------------
def test_goldens_cover_all_envelopes_roles_and_match_oracle():
    cases = 0
    for env_name, env in ENVELOPES.items():
        for role_name, grant in ROLES.items():
            for lens in LENSES:
                for kind in ("read", "propose", "execute"):
                    a = Action(lens, kind)
                    assert decide(env, grant, a).allow == _oracle(env, grant, a), (env_name, role_name, lens, kind)
                    cases += 1
                for level in (0, 1, 2, 3):
                    a = Action(lens, "autonomy_set", level)
                    assert decide(env, grant, a).allow == _oracle(env, grant, a), (env_name, role_name, lens, level)
                    cases += 1
    assert cases >= 120, f"only {cases} golden cases (need >=120)"


# ---- T-P1-04: property — allow => action within envelope AND within grant ------------------------
_cap = st.fixed_dictionaries({"max_kind": st.sampled_from(["none", "read", "propose", "execute"]),
                              "autonomy_ceiling": st.integers(min_value=0, max_value=3)})
_caps = st.dictionaries(st.sampled_from(LENSES), _cap)
_action = st.builds(Action,
                    lens=st.sampled_from(LENSES + ["unknown"]),
                    kind=st.sampled_from(["read", "propose", "execute", "autonomy_set", "bogus"]),
                    level=st.integers(min_value=-1, max_value=4))


@given(_caps, _caps, _action)
def test_allow_implies_within_both_sides(env, grant, action):
    d = decide(env, grant, action)
    if d.allow:
        assert _within(env, action) and _within(grant, action)
    assert d.allow == _oracle(env, grant, action)      # exact intersection semantics
