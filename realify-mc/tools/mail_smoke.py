"""One-shot SES deliverability smoke test — sends ONE real email via the SES driver DIRECTLY, without
touching the global MAIL_DRIVER (prod stays on 'dev'). Permanently useful ops tool.

    python -m tools.mail_smoke --to someone@example.com

Uses the app's existing AWS credentials/role. Respects the P6 suppression list if it exists; if P6
isn't built (no Postgres / no table), the check is skipped silently. Prints a MAIL_BLOCK.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys


def _sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main(argv):
    ap = argparse.ArgumentParser(prog="tools.mail_smoke")
    ap.add_argument("--to", required=True, help="recipient address")
    args = ap.parse_args(argv[1:])
    to = args.to.strip()

    email_domain = os.environ.get("EMAIL_DOMAIN") or "realifyai.app"
    from_addr = f"no-reply@{email_domain}"
    reply_to = os.environ.get("REPLY_TO_ADDRESS") or f"notifications@{email_domain}"
    region = os.environ.get("AWS_REGION") or os.environ.get("SES_REGION") or "us-east-1"
    sha = _sha()
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    subject = f"Realify mail smoke — {sha} — {ts}"
    body = ("This is a one-time Realify SES deliverability test. No action is needed.\n\n"
            f"Commit: {sha}\nUTC:    {ts}\n")

    # (3) respect the P6 suppression list if it exists; skip silently if P6 isn't built.
    try:
        from realify.agency import suppression
        if suppression.is_suppressed(to):
            print(f"ABORT: {to} is on the SES suppression list — not sending.", file=sys.stderr)
            return 2
    except Exception:
        pass

    # (1) instantiate the SES driver directly — does NOT read/change MAIL_DRIVER.
    from realify.mail.ses import SesMailer
    try:
        receipt = SesMailer().send(to=to, subject=subject, body=body,
                                   from_addr=from_addr, reply_to=reply_to)
    except Exception as e:
        msg = str(e)
        low = msg.lower()
        if "accessdenied" in low or "not authorized" in low or "ses:sendemail" in low:
            print(f"FAILED: ses:SendEmail is DENIED for the app's AWS identity — {msg}", file=sys.stderr)
        elif "unable to locate credentials" in low or "nocredentials" in low:
            print(f"FAILED: no AWS credentials available to the app — {msg}", file=sys.stderr)
        elif "not verified" in low or "messagerejected" in low:
            print(f"FAILED: SES rejected the message (identity not verified / sandbox?) — {msg}",
                  file=sys.stderr)
        else:
            print(f"FAILED: SES send error — {msg}", file=sys.stderr)
        return 1

    block = {"ses_message_id": receipt.get("message_id"), "from": from_addr, "to": to,
             "region": region, "driver": "ses",
             "prod_mail_driver_env": os.environ.get("MAIL_DRIVER") or "(unset)"}
    print("===MAIL_BLOCK_START===")
    print(json.dumps(block, indent=2))
    print("===MAIL_BLOCK_END===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
