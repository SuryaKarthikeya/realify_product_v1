"""R15 Part C — Profit & Ads locale-label leak. A US ($) world must never show ₹/"rupee" in the P&A
brief/prose or column headers; values already localize (via _cur/_cmInr and money.format_money). This
grep-locks the LENS TEMPLATES against re-introducing hardcoded currency words/symbols in labels/prose,
and checks the domain evidence builder localizes its prose.
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def test_profitads_brief_and_labels_are_currency_neutral():
    src = _read("frontend.html")
    # brief (h1) + surface dek were reworded off the hardcoded "rupees" noun
    assert "certain rupees above break-even" not in src
    # the Profit & Ads bucket column labels (_CMBK.vlbl) carry no hardcoded ₹ — the symbol is appended
    # per-tenant from CUR.symbol at render (so a US world shows "Recoverable $", IN shows "Recoverable ₹").
    assert "vlbl:'Recoverable ₹'" not in src
    assert "Upside ₹" not in src and "Bleed ₹" not in src
    # the CSV export header + hero zero-state also localize (no bare ₹ literal in those templates)
    assert "'Value ₹'" not in src
    assert "₹0 is recoverable" not in src


def test_domain_evidence_prose_has_no_hardcoded_currency_words():
    cm = _read("realify/domain/cmaa.py")
    assert "every rupee is above break-even" not in cm
    assert "recoverable ₹" not in cm


def test_cmaa_recommend_localizes_to_dollar_world():
    # recommend() formats all money through its symbol arg — a $ world's prose carries no ₹/"rupee".
    from realify.domain import cmaa
    row = {"internal_sku": "SKU-1", "ad_spend": 120.0, "ad_sales": 0.0, "price": 20.0,
           "cogs": 6.0, "referral_fee": 2.0, "fba_fee": 1.0, "units_month": 50, "bucket": "FIX ADS"}
    rec = cmaa.recommend(row, symbol="$")
    blob = str(rec).lower()
    assert "₹" not in str(rec) and "rupee" not in blob


if __name__ == "__main__":
    test_profitads_brief_and_labels_are_currency_neutral()
    test_domain_evidence_prose_has_no_hardcoded_currency_words()
    test_cmaa_evidence_localizes_symbol()
    print("R15 Part C locale-label tests passed")
