"""The single Policy Decision Point (agency-plan §1b, §1c-1). ONE pure function, imported everywhere;
no per-route permission logic. Effective capability = intersection(envelope, grant): an action is
allowed only if BOTH the brand's envelope and the user's grant permit it, and the reason names the
binding side so the UI/ledger can explain every deny.
"""
from dataclasses import dataclass

from .templates import KIND_RANK

_LADDER = ("read", "propose", "execute")


@dataclass(frozen=True)
class Action:
    lens: str
    kind: str            # read | propose | execute | autonomy_set
    level: int = 0       # autonomy level, only meaningful when kind == "autonomy_set"


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str


def _lens_cap(caps, lens):
    return caps.get(lens) if isinstance(caps, dict) else None


def decide(envelope, grant, action):
    """Decide one action against a brand envelope and a user grant (both caps dicts). Pure."""
    e = _lens_cap(envelope, action.lens)
    g = _lens_cap(grant, action.lens)
    if e is None:
        return Decision(False, f"envelope grants no capability on '{action.lens}'")
    if g is None:
        return Decision(False, f"grant gives this user no capability on '{action.lens}'")

    if action.kind == "autonomy_set":
        ec, gc = int(e.get("autonomy_ceiling", 0)), int(g.get("autonomy_ceiling", 0))
        limit = min(ec, gc)
        if action.level <= limit:
            return Decision(True, f"autonomy level {action.level} within ceiling {limit} on '{action.lens}'")
        binding = "envelope" if ec <= gc else "grant"
        return Decision(False, f"autonomy level {action.level} exceeds {binding} ceiling {limit} on '{action.lens}'")

    if action.kind not in _LADDER:
        return Decision(False, f"unknown action kind '{action.kind}'")

    want = KIND_RANK[action.kind]
    em = KIND_RANK.get(e.get("max_kind", "none"), 0)
    gm = KIND_RANK.get(g.get("max_kind", "none"), 0)
    limit = min(em, gm)
    if want <= limit:
        return Decision(True, f"'{action.kind}' on '{action.lens}' within effective capability")
    binding = "envelope" if em <= gm else "grant"
    allowed = next(k for k, v in KIND_RANK.items() if v == limit)
    return Decision(False, f"'{action.kind}' on '{action.lens}' exceeds {binding} limit '{allowed}'")
