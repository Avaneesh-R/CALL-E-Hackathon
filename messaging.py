"""
SMS fallback messaging.
Provider selected via SMS_PROVIDER env var (default: fast2sms).
  fast2sms  — Indian SMS, set FAST2SMS_API_KEY (free tier)
  twilio    — set TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER
  mock      — logs only, no real send
"""
import os
from models import get_conn, _mask_phone


def send_sms_text(phone: str, body: str) -> dict:
    """Send any arbitrary message body directly via the active provider."""
    provider = os.environ.get("SMS_PROVIDER", "fast2sms")
    if provider == "whatsapp":
        result = _send_whatsapp(phone, body)
    elif provider == "twilio":
        result = _send_twilio(phone, body)
    elif provider == "mock":
        result = _send_mock(phone, body)
    else:
        result = _send_fast2sms(phone, body)
    _log_message(None, None, phone, body, provider, result.get("status", "unknown"))
    print(f"  [MSG] {_mask_phone(phone)} via {provider}: {result['status']}")
    return result


def _send_whatsapp(phone: str, body: str) -> dict:
    """Send via local Baileys WhatsApp server (localhost:3001)."""
    try:
        import urllib.request as _ur, json as _j
        payload = _j.dumps({"phone": phone, "message": body}).encode()
        req = _ur.Request("http://127.0.0.1:3001/send", data=payload,
                          headers={"Content-Type": "application/json"}, method="POST")
        with _ur.urlopen(req, timeout=10) as resp:
            data = _j.loads(resp.read())
            if data.get("ok"):
                return {"provider": "whatsapp", "status": "sent", "jid": data.get("jid")}
            return {"provider": "whatsapp", "status": "failed", "detail": data.get("error")}
    except ConnectionRefusedError:
        print("  [WA] Server not running — start whatsapp_server.js first")
        return {"provider": "whatsapp", "status": "failed", "detail": "server_not_running"}
    except Exception as e:
        print(f"  [WA] Error: {e}")
        return {"provider": "whatsapp", "status": "failed", "detail": str(e)}


def send_sms(phone: str, product: str, lead_id: int = None, campaign_id: int = None) -> dict:
    """Send an SMS fallback message to a vendor after retries are exhausted."""
    provider = os.environ.get("SMS_PROVIDER", "fast2sms")
    body = (
        f"Hi, we're looking to source {product} in bulk and couldn't reach you by phone. "
        f"If you can supply, please call us back at your convenience. Thank you."
    )
    if provider == "whatsapp":
        result = _send_whatsapp(phone, body)
    elif provider == "twilio":
        result = _send_twilio(phone, body)
    elif provider == "mock":
        result = _send_mock(phone, body)
    else:
        result = _send_fast2sms(phone, body)

    _log_message(lead_id, campaign_id, phone, body, provider, result.get("status", "unknown"))
    masked = _mask_phone(phone)
    print(f"  [MSG] Sent to {masked} via {provider}: {result['status']}")
    return result


def _send_fast2sms(phone: str, body: str) -> dict:
    api_key = os.environ.get("FAST2SMS_API_KEY")
    if not api_key:
        print("  [SMS] FAST2SMS_API_KEY not set — falling back to mock")
        return _send_mock(phone, body)
    try:
        import urllib.request, urllib.parse, json as _json
        # Strip country code — Fast2SMS takes 10-digit Indian numbers only
        digits = ''.join(c for c in phone if c.isdigit())
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        if len(digits) != 10:
            print(f"  [SMS] Fast2SMS: non-Indian number {_mask_phone(phone)}, skipping")
            return {"provider": "fast2sms", "status": "skipped_non_indian"}
        payload = urllib.parse.urlencode({
            "route":   "q",        # quick/transactional route
            "message": body,
            "language":"english",
            "flash":   0,
            "numbers": digits,
        }).encode()
        req = urllib.request.Request(
            "https://www.fast2sms.com/dev/bulkV2",
            data=payload,
            headers={"authorization": api_key, "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"  [SMS] Fast2SMS HTTP {e.code}: {err_body}")
            return {"provider": "fast2sms", "status": "failed", "detail": err_body}
        if data.get("return") is True:
            return {"provider": "fast2sms", "status": "sent", "request_id": data.get("request_id")}
        else:
            print(f"  [SMS] Fast2SMS error: {data}")
            return {"provider": "fast2sms", "status": "failed", "detail": str(data)}
    except Exception as e:
        print(f"  [SMS] Fast2SMS exception: {e}")
        return {"provider": "fast2sms", "status": "failed", "detail": str(e)}


def _send_mock(phone: str, body: str) -> dict:
    print(f"  [SMS-MOCK] Would send to {_mask_phone(phone)}: {body[:80]}...")
    return {"provider": "mock", "status": "mock_sent", "sid": None}


def _send_twilio(phone: str, body: str) -> dict:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    if not all([account_sid, auth_token, from_number]):
        print("  [SMS] Twilio creds missing — falling back to mock")
        return _send_mock(phone, body)
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=body, from_=from_number, to=phone)
        return {"provider": "twilio", "status": "sent", "sid": msg.sid}
    except ImportError:
        print("  [SMS] twilio package not installed — falling back to mock")
        return _send_mock(phone, body)
    except Exception as e:
        print(f"  [SMS] Twilio error: {e}")
        return {"provider": "twilio", "status": "failed", "sid": None}


def _log_message(lead_id, campaign_id, phone, body, provider, status):
    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO messages (lead_id, campaign_id, phone, body, provider, status)
                   VALUES (?,?,?,?,?,?)""",
                (lead_id, campaign_id, phone, body, provider, status)
            )
            conn.commit()
    except Exception:
        pass  # Don't break calling code if messages table not yet migrated
