"""Ads fallback resolution (spec Part 3). A silent fallback is indistinguishable from a bug, so absence,
no-match and failure are DISTINCT, counted states — never the same empty render.

  reason:   NO_ENTITY_DATA | UNMAPPED | RENDERED_OK | QUERY_ERROR
  fidelity: FULL | CAMPAIGN_SKU | SKU_ONLY   (SKU_ONLY = the fallback view)

Invariants:
  * `entity_rows` is the independent tiebreaker — read straight from ad_entity_perf, BEFORE any
    mapping/recommendation pipeline. A SKU-level view while entity_rows>0 is therefore provably a render
    bug, not a legitimate fallback.
  * We fall back (fell_back=True) ONLY on entity_rows==0. Never inside a catch — a caught exception is
    QUERY_ERROR (a distinct, alarming state), never the plain SKU view.
  * entity_rows>0 with NOTHING mapped (mapped_rows==0) is UNMAPPED — data exists, no SKU matched — an
    alarm, not a benign fallback. (Refinement over a literal "recommendations==0" rule: a HEALTHY mapped
    account legitimately produces zero prescriptions and must read as RENDERED_OK, not an error.)
"""
FULL, CAMPAIGN_SKU, SKU_ONLY = "FULL", "CAMPAIGN_SKU", "SKU_ONLY"
NO_ENTITY_DATA, UNMAPPED, RENDERED_OK, QUERY_ERROR = (
    "NO_ENTITY_DATA", "UNMAPPED", "RENDERED_OK", "QUERY_ERROR")

_FIDELITY_FROM_SUMMARY = {"KEYWORD": FULL, "CAMPAIGN_SKU": CAMPAIGN_SKU}


def _mk(fidelity, entity_rows, mapped_rows, coverage_pct, recommendations, reason, fell_back):
    return {"fidelity": fidelity, "entity_rows": entity_rows, "mapped_rows": mapped_rows,
            "coverage_pct": coverage_pct, "recommendations": recommendations,
            "reason": reason, "fell_back": fell_back}


def resolve(entity_rows, mapped_rows, coverage_pct, recommendations, summary_fidelity=None, error=False):
    er, mr, recs = int(entity_rows or 0), int(mapped_rows or 0), int(recommendations or 0)
    if error:                                    # caught exception — alarm, never the SKU view
        return _mk(SKU_ONLY, er, mr, coverage_pct, recs, QUERY_ERROR, False)
    if er == 0:                                  # genuinely no campaign-level data — the ONLY fallback
        return _mk(SKU_ONLY, er, mr, coverage_pct, recs, NO_ENTITY_DATA, True)
    if mr == 0:                                  # data exists but nothing matched a SKU — alarm
        return _mk(SKU_ONLY, er, mr, coverage_pct, recs, UNMAPPED, False)
    fidelity = _FIDELITY_FROM_SUMMARY.get(summary_fidelity, CAMPAIGN_SKU)
    return _mk(fidelity, er, mr, coverage_pct, recs, RENDERED_OK, False)
