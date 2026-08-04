"""Amazon SNS message signature verification (agency-plan P7 rider) for /api/ses/notifications.
Rejects unsigned / structurally-invalid / non-AWS payloads outright; for a well-formed message it
verifies the RSA-SHA1 signature over the canonical string against the (AWS-hosted) signing cert."""
import base64


class SNSVerificationError(Exception):
    pass


_SIG_KEYS = {
    "Notification": ["Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type"],
    "SubscriptionConfirmation": ["Message", "MessageId", "SubscribeURL", "Timestamp", "Token",
                                 "TopicArn", "Type"],
    "UnsubscribeConfirmation": ["Message", "MessageId", "SubscribeURL", "Timestamp", "Token",
                                "TopicArn", "Type"],
}


def _cert_url_ok(url):
    from urllib.parse import urlparse
    p = urlparse(url or "")
    return p.scheme == "https" and (p.netloc.endswith(".amazonaws.com"))


def _canonical(msg):
    keys = _SIG_KEYS.get(msg.get("Type"))
    parts = []
    for k in keys:
        if k in msg and msg[k] is not None:
            parts.append(k)
            parts.append(str(msg[k]))
    return ("\n".join(parts) + "\n").encode()


def verify(msg, fetch_cert=None):
    """Raise SNSVerificationError unless `msg` is a structurally valid, AWS-signed SNS message.
    `fetch_cert` (bytes PEM) is injectable for tests; in prod it fetches SigningCertURL."""
    if not isinstance(msg, dict) or msg.get("Type") not in _SIG_KEYS:
        raise SNSVerificationError("not an SNS message")
    if not msg.get("Signature"):
        raise SNSVerificationError("missing signature")
    if msg.get("SignatureVersion") != "1":
        raise SNSVerificationError("unsupported signature version")
    if not _cert_url_ok(msg.get("SigningCertURL")):
        raise SNSVerificationError("signing cert URL is not an AWS https endpoint")
    pem = fetch_cert() if fetch_cert else _fetch(msg["SigningCertURL"])
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    try:
        cert = x509.load_pem_x509_certificate(pem)
        cert.public_key().verify(base64.b64decode(msg["Signature"]), _canonical(msg),
                                 padding.PKCS1v15(), hashes.SHA1())
    except Exception as e:
        raise SNSVerificationError(f"signature verification failed: {e}")
    return True


def confirm_subscription(subscribe_url, fetch=None):
    """Complete the SNS handshake by GETting the AWS-hosted SubscribeURL. SSRF-guarded: only an https
    .amazonaws.com endpoint is fetched. Call ONLY after verify() has validated the signature (the
    signature covers SubscribeURL, so a verified message means the URL is authentic AWS content).
    `fetch` is injectable for tests. Raises SNSVerificationError on a non-AWS URL."""
    if not _cert_url_ok(subscribe_url):
        raise SNSVerificationError("SubscribeURL is not an AWS https endpoint")
    return fetch(subscribe_url) if fetch else _get(subscribe_url)


def _fetch(url):  # pragma: no cover - network
    import urllib.request
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read()


def _get(url):  # pragma: no cover - network
    import urllib.request
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status
