"""Spec P4.2: the portfolio band recomputes per cohort with the CORRECT metric + label (the audit found it
stuck on 'Recoverable ₹3,23,706' even under SCALE). SCALE must read 'upside', not 'recoverable'; each
bucket shows its own figure/label sourced from the per-bucket config.
"""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_band_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def test_band_uses_per_bucket_label_and_total():
    # the band label + total come from the active bucket config (bk), recomputed each paint
    assert "cmaaSecHead').innerHTML" in _HTML
    band = _HTML[_HTML.index("portfolio band"):_HTML.index("portfolio band") + 700]
    assert "bandTot=bk.key?rows.reduce" in band                     # total is the bucket's own metric
    assert "_esc(bk.vlab||bk.vlbl)" in band                          # label is the bucket's own label
    assert "rows.length" in band                                     # N SKUs in the band


def _vlab(bucket):
    blk = re.search(re.escape(bucket) + r"':\s*\{[^}]*\}", _HTML).group(0)
    return blk.split("vlab:")[1].split(",")[0]


def test_scale_label_is_upside_not_recoverable():
    assert "Upside" in _vlab("'SCALE") and "Recoverable" not in _vlab("'SCALE")
    assert "Recoverable" in _vlab("'FIX ADS")


def test_fix_margin_and_cut_divest_labels():
    # VERIFY 4: each cohort's band label is its own metric, never 'recoverable'/'upside' bled from another.
    # CUT/DIVEST reads 'bleed to stop'; FIX MARGIN is a margin metric (key=null -> band shows count only,
    # never a misleading 'recoverable'/'upside' figure).
    cut = _vlab("'CUT/DIVEST")
    assert "Bleed" in cut and "Upside" not in cut
    fixmargin = re.search(r"'FIX MARGIN':\s*\{[^}]*\}", _HTML).group(0)
    assert "key:null" in fixmargin.replace(" ", "")                  # no ad-money metric -> count-only band
    # the band only prints a ₹ label when the bucket HAS a metric key, so FIX MARGIN never shows upside/recoverable ₹
    assert "bandTot=bk.key?rows.reduce" in _HTML and "bandTot!=null?" in _HTML


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("band_per_cohort_label OK")
