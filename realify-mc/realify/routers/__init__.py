"""HTTP layer: thin FastAPI routers (split from the former monolithic run.py in #005 1a/1f).

Routers are grouped by concern (pages, auth, onboarding, insights, cards, settings, admin) and
wired together in run.py's make_app(). Shared request helpers live in deps.py (identity/authz)
and helpers.py (filesystem, tracking, import logging). Handlers hold no SQL — they call the
service layer (realify.api) and repositories, exactly as before the split.
"""
