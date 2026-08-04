"""Envelope-versioning TOCTOU (agency-plan P3): an action composed under envelope version N is
re-checked at EXECUTE against the engagement's CURRENT active envelope. If the brand narrowed the
envelope (a newer version) so the action is no longer permitted, execution is denied. Brand-scoped
(envelopes RLS): the caller sets the brand scope."""
from ..pdp import decide


def current_envelope(cur, engagement_id):
    cur.execute("SELECT version, caps FROM envelopes WHERE engagement_id=%s AND active=true "
                "ORDER BY version DESC LIMIT 1", (engagement_id,))
    row = cur.fetchone()
    return (row[0], row[1]) if row else (None, None)


def check_at_execute(cur, engagement_id, composed_version, grant_caps, action):
    """Re-decide `action` against the current active envelope. Returns {allow, reason, toctou_changed,
    current_version}. allow is False if the current envelope no longer permits the action."""
    version, caps = current_envelope(cur, engagement_id)
    if caps is None:
        return {"allow": False, "reason": "no active envelope", "toctou_changed": True,
                "current_version": None}
    d = decide(caps, grant_caps, action)
    return {"allow": d.allow, "reason": d.reason, "toctou_changed": version != composed_version,
            "current_version": version}
