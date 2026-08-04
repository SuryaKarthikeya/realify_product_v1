"""PDP — the single Policy Decision Point for the agency console. Import `decide` from here everywhere;
never re-implement permission logic in a route (agency-plan §1b non-negotiable)."""
from .decide import Action, Decision, decide
from .templates import ENVELOPES, KIND_RANK, LENSES, ROLES, caps

__all__ = ["Action", "Decision", "decide", "ENVELOPES", "ROLES", "LENSES", "KIND_RANK", "caps"]
