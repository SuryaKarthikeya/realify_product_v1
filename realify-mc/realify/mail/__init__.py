"""Mail plumbing for the agency console (P0.5). Two drivers, selected by env MAIL_DRIVER:

  * ``dev`` (default) — writes each message as JSON under ./.mailbox so tests can assert on sends and
    nothing leaves the machine in dev/CI.
  * ``ses`` — Amazon SES via boto3 (prod).

Everything that emails a human — email-OTP codes, brand consent invites, break-glass notifications —
goes through ``send()``. Callers pass plain text (no HTML templating here); the ``reply_to`` header is
supported so consent mail can be From: via-Realify, Reply-To: the account manager (plan P3).
"""
import os

from .dev import DevMailer
from .ses import SesMailer

_DRIVERS = {"dev": DevMailer, "ses": SesMailer}


def driver_name():
    return (os.environ.get("MAIL_DRIVER") or "dev").strip().lower()


def get_mailer():
    cls = _DRIVERS.get(driver_name())
    if cls is None:
        raise ValueError(f"unknown MAIL_DRIVER {driver_name()!r} (expected one of {sorted(_DRIVERS)})")
    return cls()


def send(to, subject, body, **headers):
    """Send one message via the configured driver — UNLESS the address is on the SES suppression list
    (hard bounce / complaint), in which case the send is refused (agency-plan P6 rider). Returns a
    driver-specific receipt dict, or {"suppressed": True} if refused."""
    try:
        from ..agency import suppression
        if suppression.is_suppressed(to):
            return {"suppressed": True, "to": to, "driver": driver_name()}
    except Exception:
        pass
    return get_mailer().send(to=to, subject=subject, body=body, **headers)
