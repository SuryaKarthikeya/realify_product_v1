"""P6 pure tests (default suite): T-P6-01 factuality gate, T-P6-02 reconciliation property, Stripe
test-mode guard, T-P6-07 signed OTP-skip token."""
import os
import sys

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import reports, billing_agency, approvals   # noqa: E402


# ---- T-P6-01 ----
def test_factuality_good_report_passes():
    figs = {"gmv": "$1,560", "tacos": "12.80%", "savings": "₹1,31,000"}
    out = reports.generate("GMV {{gmv}}, TACoS {{tacos}}, saved {{savings}}.", figs,
                           {"agency_name": "Acme", "color": "#0a0"})
    assert "$1,560" in out and "₹1,31,000" in out and "12.80%" in out


def test_factuality_corrupted_template_is_blocked():
    with pytest.raises(reports.FactualityError):        # literal $9,999 not in engine figures
        reports.generate("GMV {{gmv}} and a surprise $9,999 bonus!", {"gmv": "$1,560"})


# ---- T-P6-02 (property) ----
@settings(max_examples=200)
@given(qtys=st.dictionaries(st.integers(1, 60), st.integers(0, 25), min_size=1, max_size=8),
       unit=st.integers(0, 5000), base=st.integers(0, 100000))
def test_reconciliation_delta_always_zero(qtys, unit, base):
    lines = billing_agency.allocate(qtys, unit, base)
    assert billing_agency.reconciliation_delta(qtys, lines, unit, base) == 0
    assert sum(l["base_usd_minor"] for l in lines.values()) == base   # proration-safe split


def test_stripe_test_mode_only():
    assert billing_agency.require_test_mode("sk_test_abc123") is True
    for bad in ("sk_live_abc", "", "pk_test_x", None):
        with pytest.raises(billing_agency.StripeModeError):
            billing_agency.require_test_mode(bad)


# ---- T-P6-07 (signed OTP-skip token; identity-free) ----
def test_otp_skip_token_is_signed_and_identity_free():
    tok = approvals.make_otp_skip_token()
    assert approvals.verify_otp_skip_token(tok) is True
    assert approvals.verify_otp_skip_token(tok + "tamper") is False
    assert approvals.verify_otp_skip_token("not-a-token") is False
    assert approvals.verify_otp_skip_token(tok, max_age=-1) is False   # expiry enforced
