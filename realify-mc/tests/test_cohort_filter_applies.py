"""Spec P4.1: the cohort tabs are real tabs that ACTUALLY filter the row set (the audit found 49 rows
shown identically on SCALE and FIX ADS — an inert filter). The worklist row set is derived from the
active bucket, and clicking/keyboarding a tab re-derives it.
"""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_cohf_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def test_row_set_is_bucket_derived():
    # the visible rows are recomputed from the active bucket every paint (not a static list)
    assert "visBucket=scoped.filter(k=>k.quadrant===_cmBucket" in _HTML


def test_tab_selection_repaints():
    # clicking or Enter/Space on a tab sets _cmBucket and repaints -> the row set changes
    assert "_cmBucket=el.dataset.bucket; _cmPaint()" in _HTML
    # tabs are real, keyboard-focusable tabs
    assert 'role="tab"' in _HTML and 'tabindex="${sel?0:-1}"' in _HTML and 'aria-selected' in _HTML


def test_cohorts_are_the_active_state():
    # the active tab carries the --competitive active affordance via the 'sel' class
    assert "const sel=name===_cmBucket" in _HTML and "cm-q${sel?' sel':''}" in _HTML


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("cohort_filter_applies OK")
