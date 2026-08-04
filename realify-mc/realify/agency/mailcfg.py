"""Agency mail addressing (agency-plan P7 addendum). The sending domain defaults to the SES-verified
identity realifyai.app (the earlier default was an unverified domain and is fixed here). REPLY_TO_ADDRESS
must be a ROUTED mailbox: consent@ and notifications@ forward; agencies@ does NOT — so defaults use
notifications@ / consent@."""
import os


def email_domain():
    return os.environ.get("EMAIL_DOMAIN") or "realifyai.app"


def from_addr(local="no-reply"):
    return f"{local}@{email_domain()}"


def reply_to(local="notifications"):
    return os.environ.get("REPLY_TO_ADDRESS") or f"{local}@{email_domain()}"


def ops_recipient():
    """R16 — the OPERATOR inbox for real inbound signals (new agency applications). This must be a
    monitored HUMAN mailbox, distinct from reply_to() (a routed no-reply forwarder): the R16 live repro
    was that the ops notification went to the forwarder and never reached a person. Defaults to
    shiva@realify.ai; override with OPS_EMAIL. (SES can send TO any address; only the FROM is verified.)"""
    return os.environ.get("OPS_EMAIL") or "shiva@realify.ai"
