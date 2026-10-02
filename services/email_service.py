"""Transactional email delivery for authentication codes."""

import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
RESEND_API_URL = "https://api.resend.com/emails"
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailDeliveryError(RuntimeError):
    """Raised when Brevo cannot accept a transactional email."""


def _send_otp_email(email: str, otp: str, subject: str, heading: str) -> None:
    resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    sender_email = os.getenv("RESEND_SENDER_EMAIL", "").strip() or os.getenv("BREVO_SENDER_EMAIL", "").strip()
    sender_name = os.getenv("RESEND_SENDER_NAME", "").strip() or os.getenv("BREVO_SENDER_NAME", "PocketSmart AI").strip()
    if resend_api_key:
        sender_email = sender_email or "onboarding@resend.dev"
    if not resend_api_key and (not api_key or not sender_email):
        logger.error("Transactional email configuration is incomplete")
        raise EmailDeliveryError("Email delivery is not configured")

    html_content = f"""
    <div style=\"font-family:Arial,sans-serif;line-height:1.6;color:#172033;max-width:560px\">
      <h2>{heading}</h2>
      <p>Your PocketSmart AI code is:</p>
      <p style=\"font-size:32px;font-weight:700;letter-spacing:8px;color:#0e7490\">{otp}</p>
      <p>This code expires in 10 minutes.</p>
      <p style=\"color:#64748b\">If you did not request this code, you can ignore this email.</p>
    </div>
    """
    if resend_api_key:
        payload = {
            "from": f"{sender_name} <{sender_email}>",
            "to": [email],
            "subject": subject,
            "html": html_content,
        }
        headers = {"accept": "application/json", "authorization": f"Bearer {resend_api_key}", "content-type": "application/json"}
        endpoint = RESEND_API_URL
    else:
        payload = {
            "sender": {"email": sender_email, "name": sender_name},
            "to": [{"email": email}],
            "subject": subject,
            "htmlContent": html_content,
        }
        headers = {"accept": "application/json", "api-key": api_key, "content-type": "application/json"}
        endpoint = BREVO_API_URL
    try:
        response = httpx.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.exception("Brevo transactional email failed: %s", exc)
        raise EmailDeliveryError("Transactional email delivery failed") from exc


def send_verification_otp(email: str, otp: str) -> None:
    _send_otp_email(email, otp, "Verify your PocketSmart AI account", "Verify your PocketSmart AI account")


def send_login_otp(email: str, otp: str) -> None:
    _send_otp_email(email, otp, "Your PocketSmart AI login code", "Your PocketSmart AI login code")