"""R15.1 hermetic — hub world-summary chip + role-picker suffixes are DRIVEN by the world's real
currency/symbol (not hardcoded USD). The country SELECTOR in the generator form legitimately lists both
"United States · USD" and "India · ₹" (user picks); this locks the WORLD-SUMMARY chip + picker suffixes.
"""
from realify.site import hub

_H = hub.hub_html("tester@realify.ai")


def test_picker_suffix_uses_tenant_symbol():
    assert "b.symbol||b.currency" in _H                       # managed picker suffix → real symbol
    assert "d.symbol||(st.symbol||'$')" in _H                 # direct picker suffix → real symbol
    assert "(managed · '+esc(b.currency)+')" not in _H        # old hardcoded-code suffix gone


def test_country_chip_driven_by_world_state():
    assert "st.symbol" in _H and "st.country" in _H           # chip reads the world's real country/currency
    # the chip VALUE is not a fixed literal (no "US · USD" hardcoded as the summary value)
    assert "<div class=v>US · USD</div>" not in _H
