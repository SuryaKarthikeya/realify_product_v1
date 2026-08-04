"""OPT-IN Stripe integration test — hits the REAL Stripe TEST-mode API. Not collected in CI (see
tests/agency/conftest: needs STRIPE_LIVE_TEST=1 + a sk_test_ key in STRIPE_SECRET_KEY). Everything
else in P6 mocks Stripe; this is the one place the real test-mode API is exercised."""
import os

from realify.agency import billing_agency


def test_stripe_testmode_customer_roundtrip():
    key = os.environ["STRIPE_SECRET_KEY"]
    billing_agency.require_test_mode(key)                 # refuses non sk_test_
    cust = billing_agency.sync_customer(key, "Realify QA Agency", "qa@realify.ai")
    assert cust["id"].startswith("cus_") and cust["livemode"] is False
