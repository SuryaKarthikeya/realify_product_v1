"""SES mail driver (prod) — Amazon SES via boto3. boto3 is imported lazily so dev/CI machines without
boto3 or AWS creds are never affected by merely importing realify.mail."""
import os


class SesMailer:
    def send(self, to, subject, body, **headers):
        import boto3
        region = os.environ.get("AWS_REGION") or os.environ.get("SES_REGION") or "us-east-1"
        source = headers.get("from_addr") or os.environ.get("MAIL_FROM") or "no-reply@realifyai.app"
        client = boto3.client("ses", region_name=region)
        kw = {}
        reply_to = headers.get("reply_to")
        if reply_to:
            kw["ReplyToAddresses"] = [reply_to]
        msg_body = {"Text": {"Data": body}}
        if headers.get("html"):                                # R16 — branded HTML alongside the text part
            msg_body["Html"] = {"Data": headers["html"]}
        resp = client.send_email(
            Source=source,
            Destination={"ToAddresses": [to]},
            Message={"Subject": {"Data": subject}, "Body": msg_body},
            **kw)
        return {"driver": "ses", "message_id": resp.get("MessageId")}
