"""Spec §4 enforcement: every number the Fix-Ads surface renders must resolve to a registered formula.

We enumerate the metric renderers used by the modal (the payload's header/footer `formulas` block, the
per-recommendation `formula_id`, and the simulate block's `formula_id` + `tripwire_formula_id`) and assert
each id exists in the admin formula registry. A rendered number with no registered formula fails the build.
Also asserts the registry is the SINGLE source — the ids the frontend cites via `data-fx` are all registered,
and every registered expression carries a `· admin registry` source stamp through tag()."""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_fx_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_diagnosis as D, ad_recommend as R      # noqa: E402
from realify.domain import formula_registry as FR                    # noqa: E402
from realify.domain.ad_fidelity import KEYWORD                       # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SLICES = [{"campaign": "Campaign A", "ad_group": "AG1", "spend": 800.0, "sales": 300.0, "orders": 5},
           {"campaign": "Campaign B", "ad_group": "AG2", "spend": 400.0, "sales": 250.0, "orders": 3}]
_TERMS = {("Campaign A", "AG1"): [{"customer_search_term": "car perfume", "targeting": "t",
                                   "match_type": "BROAD", "spend": 250.0, "sales": 0.0, "orders": 0.0}]}


def _rec():
    dg = D.diagnose("SKU-CAF-11", 0.25, _SLICES, _TERMS, KEYWORD)
    return R.build("SKU-CAF-11", {"cmaa_now": -1240.0, "monthly_loss": 1240.0, "title": "Cabin Air Filter",
                                  "sym": "₹"}, dg, KEYWORD, 92.0)


def _rendered_ids(rec):
    """Every formula_id the modal will render for this rec — the exact set the enforcement covers."""
    ids = set()
    for tag in rec["formulas"].values():          # header/footer metrics, each already a tag()
        ids.add(tag["formula_id"])
    ids.add(rec["combined_formula_id"])            # footer "Projected if all applied"
    for a in rec["actions"]:
        if a.get("formula_id"):                    # per-rec +₹/mo projection ƒ
            ids.add(a["formula_id"])
    sim = rec.get("simulate")
    if sim:
        ids.add(sim["formula_id"])                 # 30/60/90 projection
        ids.add(sim["tripwire_formula_id"])        # tripwire
    return ids


def test_every_rendered_number_has_registered_formula():
    ids = _rendered_ids(_rec())
    assert ids, "no formula ids rendered — the surface must tag its numbers"
    missing = [fid for fid in ids if not FR.has(fid)]
    assert not missing, f"rendered numbers with no registered formula: {missing}"


def test_header_tags_carry_expression_substitution_and_admin_source():
    rec = _rec()
    for name, tag in rec["formulas"].items():
        assert FR.has(tag["formula_id"]), name
        # the ƒ reveal needs all three: the registry expression, the SKU-substituted string, the source
        assert tag["expression"] == FR.get(tag["formula_id"])["expression"]
        assert tag["substituted"] and tag["value"] is not None
        assert tag["source"] == FR.SOURCE == "admin registry"


def test_tag_rejects_unregistered_formula():
    try:
        FR.tag("not_a_real_formula", "x = y", 1)
    except KeyError:
        return
    raise AssertionError("tag() must raise on an unregistered formula_id (single-source enforcement)")


def test_frontend_data_fx_ids_are_all_registered():
    """Any formula_id the modal template cites (data-fx="...") must be in the registry — catches a hand-
    authored ƒ tag in frontend.html that was never registered."""
    html = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()
    cited = set(re.findall(r'data-fx=["\']([a-z_]+)["\']', html))
    unknown = [c for c in cited if not FR.has(c)]
    assert not unknown, f"frontend cites unregistered formula ids: {unknown}"


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("every_number_has_registered_formula OK")
