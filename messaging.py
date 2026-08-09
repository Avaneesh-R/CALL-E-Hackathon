"""
SMS / WhatsApp fallback messaging.
Provider is selected via SMS_PROVIDER env var (default: mock).
Set SMS_PROVIDER=twilio and TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER for live sends.
"""
import os
from models import get_conn, _mask_phone


def send_sms(phone: str, product: str, lead_id: int = None, campaign_id: int = None) -> dict:
    """Send an SMS/WhatsApp fallback message to a vendor after retries are exhausted."""
    provider = os.environ.get("SMS_PROVIDER", "mock")
    body = (
        f"Hi, we're looking to source {product} in bulk and couldn't reach you by phone. "
        f"If you can supply, please call us back at your convenience. Thank you."
    )
    if provider == "twilio":
        result = _send_twilio(phone, body)
    else:
        result = _send_mock(phone, body)

    _log_message(lead_id, campaign_id, phone, body, provider, result.get("status", "unknown"))
    masked = _mask_phone(phone)
    print(f"  [SMS] Sent to {masked} via {provider}: {result['status']}")
    return result


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
