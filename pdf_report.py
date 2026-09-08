"""
ARCHVIQ — генератор PDF-отчёта для клиента.

Вход: словари ровно того вида, что возвращают
  profile_engine.compute_profile()  -> profile
  interpret_engine.interpret()      -> interp

Выход: bytes готового PDF (можно сохранить в файл или сразу приложить к письму).

Использование в app.py:

    from pdf_report import build_pdf
    pdf_bytes = build_pdf(profile, interp, lang="RU")
    st.download_button("Скачать PDF", pdf_bytes, file_name="archviq_report.pdf")
"""

from __future__ import annotations
from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)

# ---------------------------------------------------------------------------
# Брендовая палитра ARCHVIQ (адаптирована под печать: тёмный текст на белом,
# акценты — тот же navy/gold/teal, что и на сайте)
# ---------------------------------------------------------------------------
NAVY   = colors.HexColor("#0D1220")
GOLD   = colors.HexColor("#B9791F")   # затемнённое золото — на белом читается лучше, чем светлый #E3A34E
TEAL   = colors.HexColor("#1C8F7A")   # затемнённая бирюза — то же соображение
MUTED  = colors.HexColor("#5B6478")
LINE   = colors.HexColor("#D8DCE6")

STYLES = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22,
                             leading=26, textColor=NAVY, spaceAfter=4),
    "tagline": ParagraphStyle("tagline", fontName="Helvetica-Oblique", fontSize=12,
                               leading=16, textColor=MUTED, spaceAfter=18),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14,
                          leading=18, textColor=NAVY, spaceBefore=18, spaceAfter=8),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10.5,
                            leading=15, textColor=colors.HexColor("#1A1F2B"), spaceAfter=6),
    "muted": ParagraphStyle("muted", fontName="Helvetica", fontSize=9,
                             leading=13, textColor=MUTED),
    "meta": ParagraphStyle("meta", fontName="Helvetica", fontSize=9,
                            leading=13, textColor=MUTED, alignment=TA_LEFT),
    "index_title": ParagraphStyle("index_title", fontName="Helvetica-Bold", fontSize=11,
                                   leading=14, textColor=NAVY),
    "index_desc": ParagraphStyle("index_desc", fontName="Helvetica", fontSize=9.5,
                                  leading=13.5, textColor=colors.HexColor("#1A1F2B")),
    "footer": ParagraphStyle("footer", fontName="Helvetica", fontSize=8,
                              leading=11, textColor=MUTED),
}

I18N = {
    "RU": {
        "report_title": "Архитектурный отчёт",
        "generated": "Сформирован",
        "axes": "Оси RS1–RS4",
        "type": "Архитектурный тип",
        "indices": "Функциональные индексы",
        "gap": "GAP-анализ",
        "priorities": "Приоритеты",
        "insights": "Наблюдения",
        "recommendations": "Рекомендации",
        "disclaimer": (
            "Это исследовательская вычислительная модель, а не медицинский диагноз. "
            "Результат — проверяемая гипотеза об архитектуре, уточняемая через "
            "когнитивные тесты и наблюдение, а не окончательное заключение о человеке."
        ),
        "engine_demo_warning": (
            "Внимание: расчёт выполнен в демонстрационном режиме — производственный "
            "движок 43 не был найден. Эти значения нельзя использовать как реальный "
            "результат клиента."
        ),
    },
    "EN": {
        "report_title": "Architecture Report",
        "generated": "Generated",
        "axes": "RS1–RS4 Axes",
        "type": "Architecture Type",
        "indices": "Functional Indices",
        "gap": "GAP Analysis",
        "priorities": "Priorities",
        "insights": "Insights",
        "recommendations": "Recommendations",
        "disclaimer": (
            "This is a research computational model, not a medical diagnosis. "
            "The result is a testable hypothesis about architecture, refined through "
            "cognitive testing and observation — not a final conclusion about the person."
        ),
        "engine_demo_warning": (
            "Warning: this was computed in demo fallback mode — the production engine 43 "
            "was not found. These values must not be used as a real client result."
        ),
    },
}


def _axis_row(label, value):
    pct = max(0, min(100, round(float(value))))
    bar_width = 70 * mm
    filled = max(1, bar_width * pct / 100)
    empty = max(1, bar_width - filled)

    bar = Table([["", ""]], colWidths=[filled, empty], rowHeights=[2.6 * mm])
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), TEAL),
        ("BACKGROUND", (1, 0), (1, 0), LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    t = Table(
        [[label, bar, f"{value:.1f}"]],
        colWidths=[28 * mm, bar_width, 16 * mm],
    )
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, 0), NAVY),
        ("TEXTCOLOR", (2, 0), (2, 0), MUTED),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def build_pdf(profile: dict, interp: dict | None = None, lang: str = "RU") -> bytes:
    """Собирает PDF-отчёт. profile — из profile_engine.compute_profile().
    interp — из interpret_engine.interpret() (можно None, если ещё не считали GAP)."""
    tr = I18N.get(lang, I18N["RU"])
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=20 * mm, bottomMargin=18 * mm,
    )
    story = []

    # --- Header ---
    story.append(Paragraph("ARCHVIQ", ParagraphStyle(
        "brand", fontName="Helvetica-Bold", fontSize=13, textColor=GOLD, spaceAfter=2)))
    story.append(Paragraph(tr["report_title"], STYLES["title"]))
    name = profile.get("name", "—")
    story.append(Paragraph(
        f"{tr['generated']}: {date.today().isoformat()} &nbsp;&middot;&nbsp; {name}",
        STYLES["meta"]))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceBefore=10, spaceAfter=14))

    if profile.get("engine_source", "").startswith("DETERMINISTIC") or profile.get("engine_error"):
        story.append(Paragraph(tr["engine_demo_warning"],
                                ParagraphStyle("warn", parent=STYLES["body"],
                                               textColor=colors.HexColor("#8A4B00"),
                                               backColor=colors.HexColor("#FBEFDD"),
                                               borderPadding=8)))
        story.append(Spacer(1, 10))

    # --- Type ---
    story.append(Paragraph(tr["type"], STYLES["h2"]))
    story.append(Paragraph(f"<b>{profile.get('type_name','—')}</b> — {profile.get('tagline','')}",
                            STYLES["body"]))

    # --- RS axes ---
    story.append(Paragraph(tr["axes"], STYLES["h2"]))
    for label in ["rs1", "rs2", "rs3", "rs4"]:
        if label in profile:
            story.append(_axis_row(label.upper(), profile[label]))
            story.append(Spacer(1, 4))

    # --- Indices (from interpret_engine, if provided) ---
    if interp and interp.get("indices"):
        story.append(Paragraph(tr["indices"], STYLES["h2"]))
        for key, idx in interp["indices"].items():
            row = Table(
                [[Paragraph(f"{idx['title']}", STYLES["index_title"]),
                  Paragraph(f"{idx['value']}  ({idx['level']})", STYLES["muted"])]],
                colWidths=[130 * mm, 30 * mm],
            )
            row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(row)
            story.append(Paragraph(idx["description"], STYLES["index_desc"]))
            story.append(Spacer(1, 8))

        if interp.get("gap_text"):
            story.append(Paragraph(tr["gap"], STYLES["h2"]))
            story.append(Paragraph(interp["gap_text"], STYLES["body"]))

        if interp.get("top_priorities"):
            story.append(Paragraph(tr["priorities"], STYLES["h2"]))
            for p in interp["top_priorities"]:
                story.append(Paragraph(f"— {p}", STYLES["body"]))

    # --- Insights / recommendations from profile_engine ---
    if profile.get("insights"):
        story.append(Paragraph(tr["insights"], STYLES["h2"]))
        for line in profile["insights"]:
            story.append(Paragraph(f"— {line}", STYLES["body"]))

    if profile.get("recommendations"):
        story.append(Paragraph(tr["recommendations"], STYLES["h2"]))
        for line in profile["recommendations"]:
            story.append(Paragraph(f"— {line}", STYLES["body"]))

    # --- Footer / disclaimer ---
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=8))
    story.append(Paragraph(tr["disclaimer"], STYLES["footer"]))

    doc.build(story)
    return buf.getvalue()


if __name__ == "__main__":
    # Демо-прогон на примерных данных той же формы, что реально отдают
    # profile_engine.compute_profile() и interpret_engine.interpret()
    demo_profile = {
        "name": "Тестовый клиент",
        "type_name": "FLUID",
        "tagline": "Adaptive integration and flexible reconfiguration",
        "rs1": 62.0, "rs2": 55.0, "rs3": 48.0, "rs4": 58.0,
        "tension": 34.0, "adaptive": 61.0,
        "engine_source": "ENGINE 43 · NO_LAG · 43_universal_full_cascade_engine.py",
        "engine_error": "",
        "insights": [
            "RS1–RS4 summarize rhythm, synchrony, functional segregation and integration.",
            "The interpretation layer compares this prior with measured cognition and behavior.",
        ],
        "recommendations": [
            "Use the cognitive test to measure the architecture–function GAP.",
            "Keep wake time stable for 14 days before evaluating a sleep intervention.",
        ],
    }
    demo_interp = {
        "indices": {
            "overload": {"value": 41.2, "level": "mid", "title": "Умеренная нагрузка",
                         "description": "Система работает вблизи комфортного диапазона, без признаков хронической перегрузки."},
            "recovery": {"value": 58.7, "level": "high", "title": "Хороший ресурс восстановления",
                         "description": "Способность к восстановлению выше среднего — сон и паузы работают эффективно."},
        },
        "gap_text": "Профиль основан только на пренатальной солнечной динамике. Добавьте когнитивные тесты, чтобы выявить разрыв между архитектурой и текущей функцией.",
        "top_priorities": ["Умеренная нагрузка", "Хороший ресурс восстановления"],
    }
    pdf_bytes = build_pdf(demo_profile, demo_interp, lang="RU")
    with open("/home/claude/demo_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("OK, bytes:", len(pdf_bytes))
