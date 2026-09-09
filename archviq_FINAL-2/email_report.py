"""
ARCHVIQ — отправка PDF-отчёта клиенту на почту через Resend.

НАСТРОЙКА (один раз):

1. pip install resend
   (и добавь строку "resend>=1.0.0" в requirements.txt)

2. Зарегистрируйся на resend.com -> API Keys -> Create API Key.
   Скопируй ключ (начинается с "re_").

3. Помести ключ в Streamlit secrets — НЕ в код:
   - Локально: файл .streamlit/secrets.toml в папке проекта:
         RESEND_API_KEY = "re_xxxxxxxxxxxx"
   - На Streamlit Cloud: Settings -> Secrets -> вставь ту же строку.

4. ВАЖНО про адрес отправителя (FROM_EMAIL):
   Пока домен archviq.com не подтверждён в Resend (раздел Domains -> Add Domain,
   прописать несколько DNS-записей у регистратора домена), отправлять можно
   ТОЛЬКО на тот email, которым ты зарегистрирован в Resend — это ограничение
   тестового режима, не баг.
   После верификации домена (обычно 10-30 минут на распространение DNS)
   поменяй FROM_EMAIL ниже на свой адрес, например "reports@archviq.com" —
   и сможешь слать любому клиенту.

ИСПОЛЬЗОВАНИЕ в app.py:

    from email_report import send_report_email

    to = st.text_input("Email для отчёта" if L=="RU" else "Email for the report")
    if st.button("Отправить PDF на почту" if L=="RU" else "Email me the PDF"):
        with st.spinner("Отправляем..." if L=="RU" else "Sending..."):
            try:
                send_report_email(to, profile, interp, lang=L)
                st.success("Отчёт отправлен!" if L=="RU" else "Report sent!")
            except Exception as e:
                st.error(f"Не получилось отправить: {e}" if L=="RU" else f"Could not send: {e}")
"""

from __future__ import annotations

import resend
import streamlit as st

from pdf_report import build_pdf

resend.api_key = st.secrets["RESEND_API_KEY"]

# После верификации домена в Resend поменяй на "ARCHVIQ <reports@archviq.com>"
FROM_EMAIL = "ARCHVIQ <onboarding@resend.dev>"

SUBJECT = {
    "RU": "Ваш архитектурный отчёт ARCHVIQ",
    "EN": "Your ARCHVIQ architecture report",
}

BODY_HTML = {
    "RU": """
        <div style="font-family:Arial,sans-serif;color:#1A1F2B;max-width:520px;margin:0 auto;">
          <p style="color:#B9791F;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px;">ARCHVIQ</p>
          <h2 style="color:#0D1220;margin-top:0;">Ваш отчёт готов</h2>
          <p>Здравствуйте{name_part}!</p>
          <p>Ваш архитектурный отчёт — во вложении (PDF). Если возникнут вопросы по интерпретации — просто ответьте на это письмо.</p>
          <p style="color:#5B6478;font-size:13px;margin-top:24px;border-top:1px solid #D8DCE6;padding-top:12px;">
            Это исследовательская вычислительная модель, а не медицинский диагноз.
          </p>
        </div>
    """,
    "EN": """
        <div style="font-family:Arial,sans-serif;color:#1A1F2B;max-width:520px;margin:0 auto;">
          <p style="color:#B9791F;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px;">ARCHVIQ</p>
          <h2 style="color:#0D1220;margin-top:0;">Your report is ready</h2>
          <p>Hi{name_part},</p>
          <p>Your architecture report is attached as a PDF. If you have questions about the interpretation, just reply to this email.</p>
          <p style="color:#5B6478;font-size:13px;margin-top:24px;border-top:1px solid #D8DCE6;padding-top:12px;">
            This is a research computational model, not a medical diagnosis.
          </p>
        </div>
    """,
}


def send_report_email(to_email: str, profile: dict, interp: dict | None = None, lang: str = "RU") -> dict:
    """
    Строит PDF из profile/interp (те же словари, что из profile_engine.compute_profile()
    и interpret_engine.interpret()) и отправляет его на to_email через Resend.

    Возвращает ответ Resend API (dict с полем "id" при успехе).
    При ошибке Resend бросает исключение — оборачивай вызов в try/except.
    """
    lang = lang if lang in SUBJECT else "RU"
    pdf_bytes = build_pdf(profile, interp, lang=lang)

    name = (profile or {}).get("name", "").strip()
    name_part = f", {name}" if name else ""

    params = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": SUBJECT[lang],
        "html": BODY_HTML[lang].format(name_part=name_part),
        "attachments": [
            {
                "filename": "archviq_report.pdf",
                "content": list(pdf_bytes),
            }
        ],
    }
    return resend.Emails.send(params)
