"""The lever taxonomy — the spine of the Fix-Ads feature (spec §0). Rules-as-DATA: every lever is a row
here, never an `if lever == ...` branch scattered downstream. Each lever's `action_class` is the HARD
boundary that governs whether Realify may act on it, enforced everywhere (UI, guardrails, audit, autopilot).

  REALIFY_ACTIONABLE — Realify may deliver as instruction (Part A) and execute on one click (Part B).
                       All are reversible and reduce (or hold) spend. Exactly three, forever, unless a
                       spec change + customer consent graduates a new one.
  ADVISORY_ONLY      — Realify explains what/why/impact + "how to" steps + a deep link. NO Apply button,
                       ever, including under autopilot. No execute path exists in code for these.

A lever never silently changes class: graduation ADVISORY_ONLY -> REALIFY_ACTIONABLE is an explicit spec
edit here plus customer consent, never code elsewhere.
"""

REALIFY_ACTIONABLE = "REALIFY_ACTIONABLE"
ADVISORY_ONLY = "ADVISORY_ONLY"

# change.type vocabulary carried in an Action (the executable intent; advisory levers carry text)
BID_PCT = "BID_PCT"
NEGATIVE_ADD = "NEGATIVE_ADD"
REMOVE_AD = "REMOVE_AD"
ADVISORY_TEXT = "ADVISORY_TEXT"

# One row per lever. (lever_id, action_class, needs_search_term, change_type, label, how_to)
_LEVER_ROWS = [
    ("BID_DOWN", REALIFY_ACTIONABLE, False, BID_PCT,
     "Lower bid on a keyword/target",
     "Open the campaign → ad group → targeting tab, select the target, and lower its bid by the shown %."),
    ("NEGATIVE_KEYWORD", REALIFY_ACTIONABLE, True, NEGATIVE_ADD,
     "Add a non-converting search term as a negative",
     "Open the campaign → Negative keywords, add the shown term(s) as negative exact."),
    ("REMOVE_PRODUCT_AD", REALIFY_ACTIONABLE, False, REMOVE_AD,
     "Remove one SKU from a shared campaign",
     "Open the campaign → ad group → Products (advertised), and remove this SKU's product ad."),
    ("BUDGET_DOWN_PAUSE", ADVISORY_ONLY, False, ADVISORY_TEXT,
     "Lower or pause the whole-campaign budget",
     "Open the campaign settings and reduce the daily budget (or pause the campaign). Realify does not "
     "change whole-campaign budgets automatically."),
    ("CAMPAIGN_SPLIT", ADVISORY_ONLY, False, ADVISORY_TEXT,
     "Split a campaign to isolate a SKU",
     "Create a new campaign for this SKU alone so its bids/budget can be tuned without affecting the "
     "others, then move the product ad into it."),
    ("SCALE_WINNER", ADVISORY_ONLY, False, ADVISORY_TEXT,
     "Raise bid/budget on a profitable SKU",
     "This SKU earns above break-even — consider raising its bids/budget to capture more volume. "
     "Realify never raises spend automatically."),
]

# Rendered views derived once from the rows (data, not logic).
LEVERS = {r[0]: {"lever_id": r[0], "action_class": r[1], "needs_search_term": r[2],
                 "change_type": r[3], "label": r[4], "how_to": r[5]} for r in _LEVER_ROWS}

#: The ONLY levers Realify may ever execute. Exactly the three REALIFY_ACTIONABLE rows.
ACTIONABLE_LEVERS = frozenset(lid for lid, lev in LEVERS.items()
                              if lev["action_class"] == REALIFY_ACTIONABLE)


def get(lever_id):
    """The lever row, or None if unknown. Callers must treat unknown as non-actionable."""
    return LEVERS.get(lever_id)


def action_class_of(lever_id):
    lev = LEVERS.get(lever_id)
    return lev["action_class"] if lev else None


def is_actionable(lever_id):
    """True only for the three REALIFY_ACTIONABLE levers — the single gate every execute path checks."""
    return lever_id in ACTIONABLE_LEVERS


def needs_search_term(lever_id):
    lev = LEVERS.get(lever_id)
    return bool(lev and lev["needs_search_term"])


def is_valid(lever_id):
    return lever_id in LEVERS
