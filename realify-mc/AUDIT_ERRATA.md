# AUDIT ERRATA

Honest corrections to previously reported AUDIT_BLOCK invariants.

## P6 — `deeplink_tokens_verified` was a FALSE GREEN

The Phase P6 AUDIT_BLOCK reported `deeplink_tokens_verified: true`. **This was inaccurate.**

- **Cause.** The deep-link / OTP-skip token helpers in `realify/agency/approvals.py`
  (`create_deeplink`, `validate_deeplink`, `make_otp_skip_token`, `verify_otp_skip_token`) were
  **property-tested at the domain layer but never wired into the route.** The mobile-approval
  endpoint `POST /api/agency/approvals/{id}/decide` treated *any* non-empty `code` field — or a
  plain `agency_device_otp=1` cookie — as verification. So the invariant the AUDIT claimed did
  not hold for actual HTTP requests.
- **Impact.** A money-moving approval could be decided without a valid, `(approval, user)`-bound
  token; the signed-token machinery was dead code.
- **Detected by.** The post-launch conformance audit (screen #15, mobile approval).
- **Remediation (R0, this change).** `decide()` now requires a valid deep-link token resolved via
  `approvals.resolve_deeplink()` — constant-time hash match, bound to `(approval, user)`, expires
  with the approval. Absent/wrong token ⇒ **403**; an arbitrary code ⇒ **403**; the acting user is
  taken from the token binding (not the client); the signed device cookie now stores
  `make_otp_skip_token()`. The dead free-pass path was removed. Covered by
  `tests/agency/test_mobile_approval_security.py`.

**Lesson.** A green invariant asserted from domain/property tests is **not** evidence that the
code path is reachable in production. Route-level tests are required before claiming any
"verified in production" invariant.
