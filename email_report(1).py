"""ARCHVIQ transactional PDF delivery via Resend."""

from __future__ import annotations

import base64
import re

import resend
import streamlit as st

FROM_EMAIL = "ARCHVIQ <reports@archviq.com>"

SUBJECT = {
    "RU": "Ваш отчёт ARCHVIQ",
    "EN": "Your ARCHVIQ report",
}

BODY_HTML = {
    "RU": """
        <div style="font-family:Arial,sans-serif;color:#1A1F2B;max-width:520px;margin:0 auto;">
          <p style="color:#B9791F;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px;">ARCHVIQ</p>
          <h2 style="color:#0D1220;margin-top:0;">Ваш отчёт готов</h2>
          <p>PDF-отчёт ARCHVIQ прикреплён к этому письму.</p>
          <p style="color:#5B6478;font-size:13px;margin-top:24px;border-top:1px solid #D8DCE6;padding-top:12px;">
            Это исследовательская вычислительная модель, а не медицинский диагноз.
          </p>
        </div>
    """,
    "EN": """
        <div style="font-family:Arial,sans-serif;color:#1A1F2B;max-width:520px;margin:0 auto;">
          <p style="color:#B9791F;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px;">ARCHVIQ</p>
          <h2 style="color:#0D1220;margin-top:0;">Your report is ready</h2>
          <p>Your ARCHVIQ PDF report is attached to this email.</p>
          <p style="color:#5B6478;font-size:13px;margin-top:24px;border-top:1px solid #D8DCE6;padding-top:12px;">
            This is a research computational model, not a medical diagnosis.
          </p>
        </div>
    """,
}

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def is_valid_email(value: str) -> bool:
    """Lightweight UI validation; Resend performs final address validation."""
    return bool(_EMAIL_RE.fullmatch((value or "").strip()))


def send_report_email(
    to_email: str,
    pdf_bytes: bytes,
    lang: str = "RU",
) -> dict:
    """Send the already-generated ARCHVIQ PDF. Recipient is not persisted here."""
    recipient = (to_email or "").strip()
    if not is_valid_email(recipient):
        raise ValueError("Invalid email address")
    if not pdf_bytes:
        raise ValueError("PDF is empty")

    api_key = st.secrets.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    resend.api_key = api_key
    lang = lang if lang in SUBJECT else "RU"
    attachment_b64 = base64.b64encode(bytes(pdf_bytes)).decode("ascii")

    params: resend.Emails.SendParams = {
        "from": FROM_EMAIL,
        "to": [recipient],
        "subject": SUBJECT[lang],
        "html": BODY_HTML[lang],
        "attachments": [
            {
                "filename": "archviq_report.pdf",
                "content": attachment_b64,
            }
        ],
    }
    return resend.Emails.send(params)
