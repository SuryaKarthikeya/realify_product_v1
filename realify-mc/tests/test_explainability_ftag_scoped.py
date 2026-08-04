"""Spec: the explainability ƒ toggle must reveal the CLICKED card's own formula block — not a modal-wide
first match (the live bug: clicking card 1/2's ƒ revealed card 0's block, because per-card ƒ tags share
data-frev="cmaa_projection").

This runs the REAL `_famTf` handler (extracted from frontend.html) against a minimal DOM shim in Node,
with three actionable cards that all share the same data-frev. For N = 0, 1, 2 it clicks card N's ƒ and
asserts only card N's formula toggles. A header ƒ tag (no .fam-card ancestor, unique data-frev) confirms
the modal-wide fallback still works. If the handler regresses to a modal/document-wide first-match, N=1
and N=2 fail — exactly the reported defect.
"""
import os
import shutil
import subprocess
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_NODE = shutil.which("node")

_HARNESS = r'''
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const m = html.match(/function _famTf\([\s\S]*?\n\}/);
if (!m) { console.error('FAIL: _famTf not found'); process.exit(2); }

// ---- minimal DOM shim: only what _famTf touches (closest, querySelector, getAttribute, classList) ----
class El {
  constructor(tag, cls = [], attrs = {}) {
    this.tag = tag; this.cls = new Set(cls); this.attrs = attrs; this.children = []; this.parent = null;
    const self = this;
    this.classList = {
      toggle(c) { self.cls.has(c) ? self.cls.delete(c) : self.cls.add(c); return self.cls.has(c); },
      contains(c) { return self.cls.has(c); },
    };
  }
  append(c) { c.parent = this; this.children.push(c); return c; }
  getAttribute(k) { return this.attrs[k] !== undefined ? this.attrs[k] : null; }
  _matches(sel) {
    const mm = sel.match(/^\.([\w-]+)(?:\[([\w-]+)="([^"]*)"\])?$/);
    if (!mm) return false;
    const [, cls, attr, val] = mm;
    return this.cls.has(cls) && (attr == null || this.getAttribute(attr) === val);
  }
  closest(sel) { let n = this; while (n) { if (n._matches(sel)) return n; n = n.parent; } return null; }
  querySelector(sel) {
    const dfs = (n) => {
      for (const c of n.children) { if (c._matches(sel)) return c; const r = dfs(c); if (r) return r; }
      return null;
    };
    return dfs(this);
  }
}

// build: modal > [header ftag+formula(acos)] + 3 cards each [ftag + formula(cmaa_projection)]
const modal = new El('div', ['fam-modal']);
const head = modal.append(new El('div', ['fam-head']));
const headTag = head.append(new El('span', ['fx', 'fam-ftag'], { 'data-fx': 'acos' }));
const headForm = head.append(new El('div', ['fam-formula'], { 'data-frev': 'acos' }));
const cards = [];
for (let i = 0; i < 3; i++) {
  const card = modal.append(new El('div', ['fam-card']));
  const ftag = card.append(new El('span', ['fx', 'fam-ftag'], { 'data-fx': 'cmaa_projection' }));
  const form = card.append(new El('div', ['fam-formula'], { 'data-frev': 'cmaa_projection' }));
  cards.push({ card, ftag, form });
}

const _famTf = eval('(' + m[0].replace(/^function _famTf/, 'function') + ')');

// N = 0,1,2 : clicking card N's ƒ opens ONLY card N's formula
for (let N = 0; N < 3; N++) {
  _famTf(cards[N].ftag);
  for (let j = 0; j < 3; j++) {
    const open = cards[j].form.classList.contains('open');
    if (j === N && !open) { console.error(`FAIL: card ${N} ftag did not open its OWN formula`); process.exit(1); }
    if (j !== N && open) { console.error(`FAIL: card ${N} ftag opened card ${j}'s formula (scoping bug)`); process.exit(1); }
  }
  _famTf(cards[N].ftag); // toggle back to clean state
}

// header ƒ (unique data-frev, no .fam-card ancestor) falls back to the modal and opens its own block
_famTf(headTag);
if (!headForm.classList.contains('open')) { console.error('FAIL: header ƒ fallback did not open'); process.exit(1); }
console.log('OK');
'''


def test_ftag_toggle_is_scoped_to_the_clicked_card():
    if not _NODE:
        import pytest
        pytest.skip("node not available")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(_HARNESS)
        harness = f.name
    try:
        r = subprocess.run([_NODE, harness, os.path.join(_ROOT, "frontend.html")],
                           capture_output=True, text=True, timeout=30)
    finally:
        os.unlink(harness)
    assert r.returncode == 0, f"ƒ scoping regression:\n{r.stdout}\n{r.stderr}"
    assert "OK" in r.stdout


def test_handler_uses_card_scope_not_modal_first_match():
    # source-level guard mirroring test_resimulate_recomputes: the handler must resolve within .fam-card
    html = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()
    import re
    fn = re.search(r"function _famTf\(.*?\n\}", html, re.S).group(0)
    assert "el.closest('.fam-card')" in fn, "ƒ toggle must scope to the clicked tag's card"


if __name__ == "__main__":
    test_ftag_toggle_is_scoped_to_the_clicked_card()
    test_handler_uses_card_scope_not_modal_first_match()
    print("explainability_ftag_scoped OK")
