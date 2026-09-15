import streamlit as st
import datetime
import base64
import json
import os
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from profile_engine import compute_profile, get_compatibility
from interpret_engine import interpret, compatibility_analysis
from pdf_report import build_pdf
APP_BUILD = "FINAL-9 · OLD43 NO-LAG · UI/TEXT REVISION"

st.set_page_config(
    page_title="Archviq — Your brain's operating system",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# Когнитивный тест встроен в app.py, чтобы приложение не зависело
# от отдельного cognitive_test.html.
COGNITIVE_HTML_PATH = Path(__file__).with_name("cognitive_test.html")

def get_cognitive_html():
    return COGNITIVE_HTML_PATH.read_text(encoding="utf-8")


SCIENCE_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root {
  --ink:#F4F6FA; --muted:#C8D0DE; --cyan:#6FD8C4; --gold:#E9B15D;
  --slate:#A7B0C8; --panel:rgba(18,26,48,.82); --line:rgba(180,190,214,.16);
}
.stApp, p, li, label, button, input {font-family:'IBM Plex Sans',sans-serif}.stApp {
  color:var(--ink);
  background:
    radial-gradient(circle at 12% 8%, rgba(227,163,78,.16), transparent 31rem),
    radial-gradient(circle at 88% 22%, rgba(111,216,196,.13), transparent 34rem),
    linear-gradient(145deg,#161C36 0%,#1B2340 52%,#161C36 100%)
    ,url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzNjAiIGhlaWdodD0iMzYwIiB2aWV3Qm94PSIwIDAgMzYwIDM2MCI+CiAgPGcgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNkZEOEM0IiBzdHJva2Utd2lkdGg9IjEuMyIgb3BhY2l0eT0iMC4yMCI+CiAgICA8cGF0aCBkPSJNMTAsNjAgTDMwLDYwIEwzOCw0MiBMNDYsNzggTDU0LDUwIEw2Miw2MCBMOTAsNjAiLz4KICAgIDxwYXRoIGQ9Ik0xODAsNDAgQzE5NSwyMCAyMTAsNjAgMjI1LDQwIEMyNDAsMjAgMjU1LDYwIDI3MCw0MCIvPgogIDwvZz4KICA8ZyBmaWxsPSJub25lIiBzdHJva2U9IiNFM0EzNEUiIHN0cm9rZS13aWR0aD0iMS4zIiBvcGFjaXR5PSIwLjIyIj4KICAgIDxjaXJjbGUgY3g9IjMwMCIgY3k9IjEyMCIgcj0iMjIiLz4KICAgIDxjaXJjbGUgY3g9IjI5NCIgY3k9IjExNSIgcj0iMi42IiBmaWxsPSIjRTNBMzRFIiBzdHJva2U9Im5vbmUiLz4KICAgIDxjaXJjbGUgY3g9IjMwOCIgY3k9IjEyNiIgcj0iMS44IiBmaWxsPSIjRTNBMzRFIiBzdHJva2U9Im5vbmUiLz4KICAgIDxsaW5lIHgxPSIzMDAiIHkxPSI5MCIgeDI9IjMwMCIgeTI9IjgwIi8+CiAgICA8bGluZSB4MT0iMzAwIiB5MT0iMTUwIiB4Mj0iMzAwIiB5Mj0iMTYwIi8+CiAgICA8bGluZSB4MT0iMjcwIiB5MT0iMTIwIiB4Mj0iMjYwIiB5Mj0iMTIwIi8+CiAgICA8bGluZSB4MT0iMzMwIiB5MT0iMTIwIiB4Mj0iMzQwIiB5Mj0iMTIwIi8+CiAgPC9nPgogIDxnIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0E3QjBDOCIgc3Ryb2tlLXdpZHRoPSIxLjIiIG9wYWNpdHk9IjAuMjAiPgogICAgPGVsbGlwc2UgY3g9IjcwIiBjeT0iMjIwIiByeD0iMzQiIHJ5PSIxNCIvPgogICAgPGVsbGlwc2UgY3g9IjcwIiBjeT0iMjIwIiByeD0iMzQiIHJ5PSIxNCIgdHJhbnNmb3JtPSJyb3RhdGUoNjAgNzAgMjIwKSIvPgogICAgPGVsbGlwc2UgY3g9IjcwIiBjeT0iMjIwIiByeD0iMzQiIHJ5PSIxNCIgdHJhbnNmb3JtPSJyb3RhdGUoMTIwIDcwIDIyMCkiLz4KICAgIDxjaXJjbGUgY3g9IjcwIiBjeT0iMjIwIiByPSIyLjgiIGZpbGw9IiNBN0IwQzgiIHN0cm9rZT0ibm9uZSIvPgogIDwvZz4KICA8ZyBmaWxsPSJub25lIiBzdHJva2U9IiM2RkQ4QzQiIHN0cm9rZS13aWR0aD0iMS4yIiBvcGFjaXR5PSIwLjIwIj4KICAgIDxjaXJjbGUgY3g9IjIzMCIgY3k9IjI2MCIgcj0iNyIvPgogICAgPGxpbmUgeDE9IjIzMCIgeTE9IjI1MyIgeDI9IjIxNSIgeTI9IjIzNSIvPgogICAgPGxpbmUgeDE9IjIzMCIgeTE9IjI1MyIgeDI9IjI0NSIgeTI9IjIzMiIvPgogICAgPGxpbmUgeDE9IjIzNyIgeTE9IjI2NCIgeDI9IjI2MCIgeTI9IjI3MCIvPgogICAgPGxpbmUgeDE9IjIyMyIgeTE9IjI2NiIgeDI9IjIwNSIgeTI9IjI4NSIvPgogIDwvZz4KICA8dGV4dCB4PSIxNTAiIHk9IjMzMCIgZm9udC1mYW1pbHk9InNlcmlmIiBmb250LXNpemU9IjIyIiBmaWxsPSIjQTdCMEM4IiBvcGFjaXR5PSIwLjIwIj7OozwvdGV4dD4KICA8dGV4dCB4PSIyMCIgeT0iMTUwIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNkZEOEM0IiBvcGFjaXR5PSIwLjIwIj7OlFNTTjwvdGV4dD4KPC9zdmc+Cg==') repeat;
}
.stApp::before {
  content:"ΔSSN(t)    ∂²S/∂t²    Xₖ₊₁ = DₖXₖ + GₖFₖ + C(Xₖ)\A\A RS₁ = rhythm · stability     RS₂ = synchrony · hubness\A\A W₀ → W₁ → W₂ → W₃ → W₄ → W₅ → N₀ → P₁ … P₈\A\A Fₖ = dynamic + instability + |direction|";
  white-space:pre-wrap; position:fixed; inset:7rem 2vw auto auto; width:38vw;
  color:rgba(227,163,78,.09); font:600 18px/2.3 'IBM Plex Mono',monospace;
  transform:rotate(-8deg); pointer-events:none; z-index:0;animation:neuralDrift 16s ease-in-out infinite alternate;
}
@keyframes neuralDrift{from{transform:translate3d(0,0,0) rotate(-8deg);opacity:.75}to{transform:translate3d(-24px,18px,0) rotate(-5deg);opacity:1}}
[data-testid="stAppViewContainer"] > .main {position:relative;z-index:1}
.block-container {max-width:1180px;padding-top:2.1rem;padding-bottom:5rem}
h1,h2,h3 {font-family:'Newsreader',serif;font-weight:500;letter-spacing:0;color:#F4F0E8}
h1 {font-size:clamp(2.2rem,5.5vw,4.3rem)!important;line-height:1.05!important}
p,li {line-height:1.65}
.hero-kicker {font:600 .76rem/1 'IBM Plex Mono',monospace;letter-spacing:.18em;color:var(--cyan);text-transform:uppercase;margin-bottom:1.1rem}
.hero-copy {font-size:1.18rem;color:#D6DCE8;max-width:800px;line-height:1.7;margin:1.2rem 0 1.5rem}
.science-card,.axis-card,.protocol-card,.pair-card {
  background:linear-gradient(145deg,rgba(18,26,48,.91),rgba(11,15,28,.82));
  border:1px solid var(--line);border-radius:18px;padding:1.2rem 1.35rem;margin:.55rem 0;
  box-shadow:0 14px 38px rgba(0,0,0,.18);
}
.science-card h3,.axis-card h3,.protocol-card h3,.pair-card h3 {font-family:'Newsreader',serif;font-style:italic;font-weight:500;font-size:1.08rem;margin:.1rem 0 .5rem;color:var(--ink)}
.science-card p,.axis-card p,.protocol-card p,.pair-card p {font-size:1rem;color:#C7CEDE;margin:.25rem 0}
.formula {background:rgba(6,10,20,.7);border-left:3px solid var(--cyan);padding:1rem 1.2rem;border-radius:4px 14px 14px 4px;font:500 .92rem/1.7 'IBM Plex Mono',monospace;color:#CDEFE7;margin:1rem 0}
.pipeline {display:grid;grid-template-columns:repeat(5,1fr);gap:.55rem;margin:1.3rem 0}
.pipe-node {border:1px solid var(--line);border-radius:14px;padding:.9rem .7rem;text-align:center;background:rgba(18,26,48,.72);font-size:.8rem;color:var(--muted)}
.pipe-node b {display:block;color:var(--cyan);font-size:.78rem;margin-bottom:.35rem}
.eyebrow {font:600 .78rem/1 'IBM Plex Mono',monospace;letter-spacing:.14em;color:var(--cyan);text-transform:uppercase}
.score {font:500 2.15rem/1 'IBM Plex Mono',monospace;color:var(--ink)}
.level-low {color:#68e0b4}.level-mid {color:#ffd166}.level-high {color:#ff7e8d}
.micro {font-size:.80rem;color:#C8D0DE}
.founder-photo{width:100%;border-radius:24px;border:1px solid rgba(227,163,78,.4);box-shadow:0 24px 70px rgba(0,0,0,.45);display:block}
.bio-role{color:var(--gold);font:600 .9rem/1.5 'IBM Plex Mono',monospace;margin:-.4rem 0 1.2rem}
.comparison-table{width:100%;border-collapse:collapse;margin:1rem 0 1.5rem;background:rgba(13,18,32,.72);border-radius:16px;overflow:hidden}
.comparison-table th,.comparison-table td{border-bottom:1px solid var(--line);padding:.8rem 1rem;text-align:left;font-size:.9rem}.comparison-table th{color:var(--cyan);background:rgba(111,216,196,.08)}
.price-card{height:295px;box-sizing:border-box;background:linear-gradient(145deg,rgba(22,31,55,.98),rgba(12,18,34,.96));border:1px solid rgba(111,216,196,.28);border-radius:18px;padding:1.2rem;margin:.4rem 0;box-shadow:0 12px 32px rgba(0,0,0,.20);display:flex;flex-direction:column}.price-card-title{font:600 1.08rem/1.25 'Newsreader',serif;color:#FFFFFF;min-height:2.7rem}.price{font:700 2.15rem/1 'IBM Plex Mono',monospace;color:#F3BB63;margin:.68rem 0 .72rem}.price-card-desc{color:#D8DEEA;font-size:.90rem;line-height:1.48;margin:0;flex:1}.price-cta{display:flex;align-items:center;justify-content:center;width:100%;min-height:3.0rem;box-sizing:border-box;border:1.5px solid #6FD8C4;border-radius:12px;background:#17233F;color:#F7FAFF!important;font-family:'IBM Plex Sans',sans-serif;font-size:.98rem;font-weight:800;text-decoration:none!important;margin-top:.85rem;box-shadow:0 5px 18px rgba(0,0,0,.20)}.price-cta:hover{background:#203150;color:#FFFFFF!important;border-color:#8CEAD9}.price-cta-included{border-color:rgba(227,163,78,.82);background:rgba(227,163,78,.16);color:#FFE0A5!important}.price-note{font-size:.78rem;color:#BFC8D8;margin-top:.55rem}
.rule {height:1px;background:linear-gradient(90deg,var(--gold),transparent);margin:1.2rem 0}
[data-testid="stMetric"] {background:rgba(18,26,48,.78);border:1px solid var(--line);padding:1rem;border-radius:14px}
[data-testid="stMetricValue"] {color:var(--ink)!important;font-size:1.9rem!important}
[data-testid="stMetricLabel"] p {color:#B8C0D4!important;font-size:.95rem!important}
.stTabs [data-baseweb="tab"] {font-size:1.02rem;color:#B8C0D4;padding:.6rem 1rem}
.stTabs [aria-selected="true"] {color:var(--gold)!important}
.stTabs [data-baseweb="tab-highlight"] {background-color:var(--gold)!important}
p,li,.stMarkdown {color:#DCE1EC}
[data-testid="stExpander"] {background:rgba(13,18,32,.72);border-color:var(--line);border-radius:14px}

/* HIGH-CONTRAST ACTION CONTROLS — fixes pale/white unreadable buttons */
.stButton > button,
[data-testid="stButton"] > button,
.stDownloadButton > button,
[data-testid="stDownloadButton"] > button,
[data-testid="stLinkButton"] > a,
.stLinkButton > a,
a[kind="secondary"],
button[kind="secondary"],
[data-testid="stBaseButton-secondary"] {
  background:#17233F !important;
  color:#F7FAFF !important;
  border:1.5px solid #6FD8C4 !important;
  border-radius:12px !important;
  min-height:2.9rem !important;
  font-family:'IBM Plex Sans',sans-serif !important;
  font-size:1.00rem !important;
  font-weight:700 !important;
  letter-spacing:.005em !important;
  opacity:1 !important;
  box-shadow:0 5px 18px rgba(0,0,0,.20) !important;
  text-decoration:none !important;
}
.stButton > button:hover,
[data-testid="stButton"] > button:hover,
.stDownloadButton > button:hover,
[data-testid="stDownloadButton"] > button:hover,
[data-testid="stLinkButton"] > a:hover,
.stLinkButton > a:hover,
a[kind="secondary"]:hover,
button[kind="secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {
  background:#203150 !important;
  color:#FFFFFF !important;
  border-color:#8CEAD9 !important;
  box-shadow:0 7px 22px rgba(111,216,196,.20) !important;
}

/* Primary actions: gold/orange, dark readable text */
.stButton > button[kind="primary"],
[data-testid="stButton"] > button[kind="primary"],
button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background:linear-gradient(135deg,#F5C66B,#E3A34E) !important;
  color:#111827 !important;
  border:1px solid #F6D18A !important;
  font-family:'IBM Plex Sans',sans-serif !important;
  font-size:1.08rem !important;
  font-weight:800 !important;
  letter-spacing:.005em !important;
  min-height:3.15rem !important;
  opacity:1 !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stButton"] > button[kind="primary"]:hover,
button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  background:linear-gradient(135deg,#FFD987,#EFB253) !important;
  color:#0A0F18 !important;
  border-color:#FFE1A3 !important;
}

/* Force child text/icon to inherit button color; Streamlit sometimes paints <p> separately */
.stButton button *,
[data-testid="stButton"] button *,
.stDownloadButton button *,
[data-testid="stDownloadButton"] button *,
[data-testid="stLinkButton"] a *,
.stLinkButton a *,
[data-testid="stBaseButton-secondary"] *,
[data-testid="stBaseButton-primary"] * {
  color:inherit !important;
  font-family:'IBM Plex Sans',sans-serif !important;
  font-weight:inherit !important;
  opacity:1 !important;
}

/* Disabled controls remain obviously disabled, but text is still legible */
.stButton button:disabled,
[data-testid="stButton"] button:disabled,
.stDownloadButton button:disabled,
[data-testid="stDownloadButton"] button:disabled,
[data-testid="stLinkButton"] a[aria-disabled="true"] {
  background:#263047 !important;
  color:#BFC8DA !important;
  border-color:#536078 !important;
  opacity:.72 !important;
  cursor:not-allowed !important;
}

/* Pricing / action links should not inherit global pale anchor styles */
[data-testid="stLinkButton"] a:visited,
.stLinkButton a:visited {
  color:#F7FAFF !important;
}

[data-testid="stAlert"],[data-testid^="stAlertContent"] {
  background:rgba(18,26,48,.94)!important;border:1px solid var(--line)!important;border-radius:14px!important;
}
[data-testid="stAlert"] p,[data-testid="stAlert"] div,[data-testid="stAlert"] span,
[data-testid^="stAlertContent"] p,[data-testid^="stAlertContent"] div,[data-testid^="stAlertContent"] span {
  color:var(--ink)!important;font-size:1rem!important;
}
[data-testid="stAlertContentInfo"] {border-left:4px solid var(--cyan)!important}
[data-testid="stAlertContentSuccess"] {border-left:4px solid var(--cyan)!important}
[data-testid="stAlertContentWarning"] {border-left:4px solid var(--gold)!important}
[data-testid="stAlertContentError"] {border-left:4px solid #ff7e8d!important}

/* High-contrast form text: no pale labels, values or placeholders */
.stTextInput label p, .stDateInput label p, .stSelectbox label p,
.stRadio label p, [data-testid="stWidgetLabel"] p {
  color:#F2F5FA !important; font-weight:650 !important; opacity:1 !important;
}
.stTextInput input, .stDateInput input,
[data-baseweb="select"] input, [data-baseweb="select"] div {
  color:#F7FAFF !important; opacity:1 !important;
}
.stTextInput input::placeholder, .stDateInput input::placeholder {
  color:#AEB8CA !important; opacity:1 !important;
}
[data-baseweb="select"] > div {
  background:#111B31 !important; border-color:#53637F !important;
}
.stCaption, [data-testid="stCaptionContainer"] {color:#C3CBD9 !important;}
.stRadio label p {font-size:1.05rem!important;color:var(--ink)!important}
.stRadio [role="radiogroup"] label {padding:.3rem .8rem}
@media(max-width:760px){.pipeline{grid-template-columns:1fr 1fr}.stApp::before{display:none}.block-container{padding-top:1rem}}
</style>
"""


def tr(en, ru):
    return ru if st.session_state.get("lang", "EN") == "RU" else en


def card(title, body, meta=""):
    meta_html = f'<div class="eyebrow">{meta}</div>' if meta else ""
    st.markdown(f'<div class="science-card">{meta_html}<h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)


def safe_num(value, default=50.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def get_interp(profile):
    raw = (profile or {}).get("raw", {})
    return interpret(raw, st.session_state.lang) if raw else None


def level_word(level):
    words = {
        "EN":{"low":"low","mid":"moderate","high":"high"},
        "RU":{"low":"низкий","mid":"умеренный","high":"высокий"},
    }
    return words[st.session_state.lang].get(level, level)


def render_science_pipeline():
    labels = [
        ("01", tr("Birth date", "Дата рождения")),
        ("02", tr("SILSO daily SSN", "Суточные SSN SILSO")),
        ("03", tr("15 developmental windows", "15 окон развития")),
        ("04", tr("9-state cascade", "Каскад 9 состояний")),
        ("05", tr("Function + feedback", "Функция + обратная связь")),
    ]
    nodes = "".join(f'<div class="pipe-node"><b>{n}</b>{label}</div>' for n,label in labels)
    st.markdown(f'<div class="pipeline">{nodes}</div>', unsafe_allow_html=True)


def founder_photo_uri():
    path = os.path.join(os.path.dirname(__file__), "assets", "andrey_osipov.jpg")
    try:
        with open(path,"rb") as source:
            return "data:image/jpeg;base64," + base64.b64encode(source.read()).decode("ascii")
    except OSError:
        return ""


def render_founder():
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-kicker">' + tr('FOUNDER · PHYSICIAN-SCIENTIST','ОСНОВАТЕЛЬ · ВРАЧ-ИССЛЕДОВАТЕЛЬ') + '</div>',
        unsafe_allow_html=True
    )
    left,right=st.columns([.78,1.5],gap="large")
    with left:
        uri=founder_photo_uri()
        if uri:
            st.markdown(f'<img class="founder-photo" src="{uri}" alt="Andrey Osipov">',unsafe_allow_html=True)
    with right:
        st.header(tr("Andrey Osipov, MD, PhD", "Андрей Осипов, врач, к.м.н."))
        st.markdown(
            '<div class="bio-role">' + tr(
                'Physician-Scientist | Independent Researcher | Neurophysiology, EEG & AI',
                'Врач-исследователь | Независимый исследователь | Нейрофизиология, ЭЭГ и ИИ'
            ) + '</div>',
            unsafe_allow_html=True
        )
        if st.session_state.lang=="RU":
            st.markdown("""
**Образование и опыт**

- Окончил Первый Ленинградский медицинский институт.
- Прошёл интернатуру и ординатуру; **23 года профессионального опыта в медицине**, включая клиническую практику, исследования и медицинское управление.
- Проводил диссертационные исследования в Санкт-Петербургской государственной педиатрической медицинской академии.
- Защитил кандидатскую диссертацию в Военно-медицинской академии Санкт-Петербурга.
- Работал на управленческих должностях в фармацевтической отрасли.
- Получил экономическое образование в Санкт-Петербургском политехническом университете и дополнительное управленческое образование в Москве.
- Разработал и руководил медицинским проектом в области диабетологической помощи.
""")
        else:
            st.markdown("""
**Background**

- Graduated from the First Leningrad Medical Institute.
- Completed internship and residency training; **23 years of professional experience in medicine**, including clinical practice, research, and medical management.
- Conducted doctoral research at the St. Petersburg State Pediatric Medical Academy.
- Defended his PhD dissertation at the Military Medical Academy in St. Petersburg.
- Later worked in the pharmaceutical industry in management roles.
- Received an economics degree from St. Petersburg Polytechnic University.
- Subsequently completed additional management education in Moscow.
- Later developed and managed a medical project focused on diabetes care.
""")
    st.subheader(tr("Current research focus", "Текущие направления исследований"))
    focus_en=[
        "Computational modeling of individual brain architecture based on developmental and neurophysiological parameters.",
        "Development of methods for extracting stable neurophysiological phenotypes from heterogeneous biological data.",
        "Integration of EEG, cognitive testing, and AI-based analysis for individualized brain-state characterization.",
        "Research into EEG biomarkers associated with cognitive processing, regulation, stability, flexibility, and functional brain organization.",
        "Development of AI-assisted neurofeedback and brain-computer interface concepts, including adaptive systems that respond to individual EEG patterns.",
        "Investigation of how prenatal developmental windows and environmental electromagnetic factors may influence later neurofunctional organization.",
        "Development of biomimetic computational approaches in which principles derived from neural systems are applied to adaptive signal processing and intelligent control systems.",
    ]
    focus_ru=[
        "Вычислительное моделирование индивидуальной архитектуры мозга по параметрам развития и нейрофизиологии.",
        "Выделение устойчивых нейрофизиологических фенотипов из разнородных биологических данных.",
        "Интеграция ЭЭГ, когнитивных тестов и ИИ для индивидуальной характеристики состояния мозга.",
        "ЭЭГ-биомаркеры когнитивной обработки, регуляции, стабильности, гибкости и функциональной организации.",
        "ИИ-ассистируемая нейрообратная связь и интерфейсы мозг–компьютер, адаптирующиеся к индивидуальным ЭЭГ-паттернам.",
        "Влияние пренатальных окон развития и электромагнитных факторов среды на последующую нейрофункциональную организацию.",
        "Биомиметические вычислительные методы для адаптивной обработки сигналов и интеллектуальных систем управления.",
    ]
    cols=st.columns(2)
    for i,item in enumerate(focus_ru if st.session_state.lang=="RU" else focus_en):
        with cols[i%2]: card(f"0{i+1}",item,tr("RESEARCH","ИССЛЕДОВАНИЕ"))
    st.info(tr(
        "Current objective: to build a scalable technology platform combining EEG, AI, individualized neurophysiological modeling, and adaptive feedback, with potential applications in digital health, cognitive assessment, neurotechnology, human performance, and intelligent human-machine interaction.",
        "Текущая цель: масштабируемая платформа, объединяющая ЭЭГ, ИИ, индивидуальное нейрофизиологическое моделирование и адаптивную обратную связь для цифрового здоровья, когнитивной оценки, нейротехнологий, работоспособности и интеллектуального взаимодействия человека с машиной."
    ))


def render_ssn_windows_chart():
    x=np.linspace(0,110,260)
    y=52+18*np.sin(x/8.5)+8*np.sin(x/2.9)+.12*x
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=x,y=y,mode="lines",name="SSN dynamics",line=dict(color="#6FD8C4",width=3),fill="tozeroy",fillcolor="rgba(111,216,196,.08)"))
    windows=[("W1",18,45,"#6FD8C4"),("W2",46,73,"#E3A34E"),("W3",74,100,"#A7B0C8")]
    for name,a,b,color in windows:
        fig.add_vrect(x0=a,x1=b,fillcolor=color,opacity=.13,line_width=0,annotation_text=name,annotation_position="top left")
    fig.update_layout(template="plotly_dark",height=340,margin=dict(l=10,r=10,t=35,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(13,18,32,.72)",xaxis_title=tr("Days after conception","Дни после зачатия"),yaxis_title="SSN / dynamic signal",legend=dict(orientation="h"))
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    st.caption(tr("Conceptual visualization of the calculation. The personal profile uses actual daily SILSO values for the corresponding historical dates.","Схематическая визуализация расчёта. Персональный профиль использует реальные суточные значения SILSO для соответствующих исторических дат."))


def render_validation_chart():
    names=[tr("Anxiety","Тревога"),tr("Impulsivity","Импульсивность"),tr("Stress","Стресс")]
    rho=[.20,.26,.23];p=[.004,.0002,.001]
    fig=go.Figure(go.Bar(x=names,y=rho,text=[f"ρ={r:.2f}<br>p={pv:g}" for r,pv in zip(rho,p)],textposition="outside",marker=dict(color=["#6FD8C4","#E3A34E","#A7B0C8"])))
    fig.update_layout(template="plotly_dark",height=330,margin=dict(l=10,r=10,t=35,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(13,18,32,.72)",yaxis=dict(title="Spearman ρ",range=[0,.32]))
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})


def render_not_astrology():
    rows=[
        (tr("Mechanism","Механизм"),tr("Symbolic positions","Символические положения"),tr("Measured temporal environmental dynamics","Измеренная временная динамика среды")),
        (tr("Input","Вход"),tr("Calendar symbolism","Календарная символика"),tr("Daily SILSO Wolf numbers since 1818","Суточные числа Вольфа SILSO с 1818 года")),
        (tr("Model","Модель"),tr("Interpretive tradition","Интерпретационная традиция"),tr("Fixed windows, features and equations","Фиксированные окна, признаки и уравнения")),
        (tr("External test","Внешняя проверка"),tr("Not required","Не требуется"),tr("EEG, cognition and questionnaires","EEG, когнитивные тесты и опросники")),
        (tr("Failure possible","Возможность опровержения"),tr("No","Нет"),tr("Yes — including negative results","Да, включая отрицательные результаты")),
    ]
    body="".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a,b,c in rows)
    st.markdown(f'<table class="comparison-table"><thead><tr><th>{tr("Criterion","Критерий")}</th><th>{tr("Astrology","Астрология")}</th><th>Archviq</th></tr></thead><tbody>{body}</tbody></table>',unsafe_allow_html=True)


PRICES = {
    "architecture": "FREE",
    "cognitive": "$12",
    "burnout": "$19",
    "compatibility": "$19",
    "full": "$39",
}


def render_pricing():
    offers=[
        (tr("Architecture profile","Архитектурный профиль"),tr("RS axes, architecture type and functional interpretation","Оси RS, тип архитектуры и функциональная интерпретация"),PRICES["architecture"],None),
        (tr("Cognitive test + GAP","Когнитивный тест + GAP"),tr("Five measured tasks and architecture–function comparison","Пять измерительных задач и сравнение архитектуры с текущей функцией"),PRICES["cognitive"],"cognitive"),
        (tr("Target questionnaire","Целевой опросник"),tr("Burnout, compatibility or AI behavior profile","Выгорание, совместимость или поведенческий профиль ИИ"),PRICES["burnout"],"burnout"),
        (tr("Compatibility profile","Профиль совместимости"),tr("Two architectures, pair asymmetries and coordination protocol","Две архитектуры, асимметрии пары и протокол согласования"),PRICES["compatibility"],"compatibility"),
    ]
    cols=st.columns(4)
    for col,(name,desc,price,key) in zip(cols,offers):
        with col:
            if key:
                url = purchase_url(key)
                cta = tr(f"Buy · {price}",f"Купить · {price}")
                action = f'<a class="price-cta" href="{url}" target="_blank" rel="noopener noreferrer">{cta}</a>' if url else ''
            else:
                action = ''
            st.markdown(
                f'<div class="price-card">'
                f'<div class="price-card-title">{name}</div>'
                f'<div class="price">{price}</div>'
                f'<p class="price-card-desc">{desc}</p>'
                f'{action}</div>',
                unsafe_allow_html=True
            )
            if key is None:
                if st.button(tr("Start FREE analysis →","Начать БЕСПЛАТНЫЙ анализ →"), key="free_architecture_cta", width="stretch", type="primary"):
                    st.session_state.mode = "personal"
                    st.session_state.step = "input"
                    st.rerun()


GUMROAD_LINKS = {
    "COGNITIVE": "https://archviq.gumroad.com/l/kdjqsj",
    "COMPATIBILITY": "https://archviq.gumroad.com/l/tfmfiw",
    "BURNOUT": "https://archviq.gumroad.com/l/zfbje",
    "AI": "https://archviq.gumroad.com/l/tspxvc",
    "FULL": "https://archviq.gumroad.com/l/wsxcl",
}


def purchase_url(product_key):
    key=product_key.upper()
    url = ""
    try:
        url = st.secrets.get(f"GUMROAD_{key}_URL","")
    except Exception:
        pass
    if not url:
        url = os.getenv(f"GUMROAD_{key}_URL", GUMROAD_LINKS.get(key,""))
    return url


def purchase_button(label,product_key):
    url = purchase_url(product_key)
    if url:
        st.link_button(label,url,width="stretch")


def get_gumroad_product_id(product_key):
    """Product ID (не permalink!) — берётся из Streamlit secrets:
    GUMROAD_COGNITIVE_PRODUCT_ID, GUMROAD_COMPATIBILITY_PRODUCT_ID и т.д.
    Найти его: Gumroad → товар → Content → License key → включить —
    там появится Product ID для копирования."""
    key = product_key.upper()
    try:
        return st.secrets.get(f"GUMROAD_{key}_PRODUCT_ID","")
    except Exception:
        return os.getenv(f"GUMROAD_{key}_PRODUCT_ID","")


def verify_gumroad_license(product_key, license_key):
    """Проверяет ключ через официальный публичный endpoint Gumroad.
    Возвращает (ok: bool, message: str)."""
    product_id = get_gumroad_product_id(product_key)
    if not product_id:
        return False, tr(
            "This product's license verification is not configured yet (missing Product ID).",
            "Проверка лицензии для этого товара ещё не настроена (нет Product ID)."
        )
    if not license_key or not license_key.strip():
        return False, tr("Enter your license key.","Введите лицензионный ключ.")
    try:
        data = urllib.parse.urlencode({
            "product_id": product_id,
            "license_key": license_key.strip(),
            "increment_uses_count": "false",
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.gumroad.com/v2/licenses/verify",
            data=data, method="POST",
            headers={"User-Agent":"Archviq/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, tr("License key not found.","Лицензионный ключ не найден.")
        return False, tr(f"Verification error: {e}", f"Ошибка проверки: {e}")
    except Exception as e:
        return False, tr(f"Verification error: {e}", f"Ошибка проверки: {e}")

    if not payload.get("success"):
        return False, payload.get("message") or tr("Invalid license key.","Неверный лицензионный ключ.")
    purchase = payload.get("purchase",{})
    if purchase.get("refunded") or purchase.get("chargebacked"):
        return False, tr("This purchase was refunded and is no longer valid.","Эта покупка была возвращена и больше недействительна.")
    return True, tr("Unlocked!","Открыто!")


def paywall_gate(product_key, session_flag, price_label):
    """Рендерит блок «купить / ввести ключ». Возвращает True, если контент уже разблокирован."""
    if st.session_state.get(session_flag):
        return True
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.info(tr(
        f"Full analysis is part of the paid report ({price_label}). Buy it, then enter your license key below to unlock it here.",
        f"Полный разбор — часть платного отчёта ({price_label}). Купите его, затем введите лицензионный ключ ниже, чтобы открыть здесь."
    ))
    c1,c2 = st.columns([1,1.4])
    with c1:
        purchase_button(tr(f"Buy · {price_label}",f"Купить · {price_label}"),product_key)
    with c2:
        lic = st.text_input(tr("License key","Лицензионный ключ"),key=f"lic_input_{product_key}",placeholder="XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX")
        if st.button(tr("Unlock","Открыть"),key=f"lic_btn_{product_key}",width="stretch"):
            ok,msg = verify_gumroad_license(product_key, lic)
            if ok:
                st.session_state[session_flag]=True
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    return False


def render_rs_radar(profile,title=""):
    labels=["RS1 · Rhythm","RS2 · Sync","RS3 · Topology","RS4 · Integral"]
    values=[max(0,min(100,safe_num(profile.get(k,50)))) for k in ("rs1","rs2","rs3","rs4")]
    fig=go.Figure(go.Scatterpolar(r=values+[values[0]],theta=labels+[labels[0]],fill="toself",line=dict(color="#6FD8C4",width=3),fillcolor="rgba(111,216,196,.25)",name=profile.get("name","Profile")))
    fig.update_layout(template="plotly_dark",height=410,margin=dict(l=40,r=40,t=55,b=35),paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(bgcolor="rgba(13,18,32,.55)",
            radialaxis=dict(range=[0,100],showticklabels=True,gridcolor="rgba(180,190,214,.28)",tickfont=dict(size=12,color="#B8C0D4")),
            angularaxis=dict(tickfont=dict(size=14,color="#ECEEF3"),gridcolor="rgba(180,190,214,.28)")),
        showlegend=False,title=title,font=dict(color="#ECEEF3"))
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})


def architecture_type(profile,interp=None):
    """Return only a structural architecture type.

    Load/overload is a separate state indicator and must never redefine the
    person's psychotype.  In particular, the legacy adapter may still carry
    a legacy overload-state label; we deliberately ignore it
    here and classify the stable architecture from structural indices.
    """
    supplied=str(profile.get("type_name","")).lower()
    for key in ("fortress","antenna","fluid"):
        if key in supplied:return key

    idx=(interp or {}).get("indices",{})
    sensitivity=safe_num((profile.get("raw") or {}).get("X_SENS",0),0)
    rigidity=safe_num(idx.get("rigidity",{}).get("value",50),50)
    flexibility=safe_num(idx.get("flexibility",{}).get("value",50),50)
    autonomic=safe_num(idx.get("autonomic",{}).get("value",50),50)

    if sensitivity>=16 or autonomic>=67:
        return "antenna"
    if rigidity>=60:
        return "fortress"
    return "fluid" if flexibility>=50 else "fortress"


def architecture_short_tagline(profile,interp=None):
    key=architecture_type(profile,interp)
    ru={
        "fortress":"Устойчивая структурная архитектура: сильное удержание курса, фокуса и правил.",
        "antenna":"Чувствительная архитектура: быстро замечает изменения и собирает много контекста.",
        "fluid":"Гибкая архитектура: легче перестраивает способ обработки под ситуацию.",
    }
    en={
        "fortress":"Stable structural architecture: strong persistence, focus and rule maintenance.",
        "antenna":"Sensitive architecture: detects change quickly and gathers broad context.",
        "fluid":"Flexible architecture: reconfigures processing more readily with context.",
    }
    return (ru if st.session_state.lang=="RU" else en)[key]


def _band(value, low=38.0, high=62.0):
    value=safe_num(value,50)
    if value < low:return "low"
    if value > high:return "high"
    return "mid"


def _idx_value(interp, key, default=50.0):
    try:
        return safe_num((interp or {}).get("indices",{}).get(key,{}).get("value"),default)
    except Exception:
        return safe_num(default)


def profile_modifier(profile, interp):
    """Data-dependent modifier so two people of the same broad type do not get the same text."""
    rs2=safe_num(profile.get("rs2"),50)
    rs3=safe_num(profile.get("rs3"),50)
    rs4=safe_num(profile.get("rs4"),50)
    flex=_idx_value(interp,"flexibility",50)
    load=_idx_value(interp,"overload",50)
    rec=_idx_value(interp,"recovery",50)

    if load>=68 and rec<45:
        return tr("high-load compensated contour","компенсированный контур высокой нагрузки")
    if rs4>=65 and rs3>=60:
        return tr("integrative-structured contour","интегративно-структурный контур")
    if rs4>=65 and flex>=60:
        return tr("integrative-flexible contour","интегративно-гибкий контур")
    if rs3>=65:
        return tr("focus-protective contour","контур с выраженной защитой фокуса")
    if rs2>=65:
        return tr("coordination-dominant contour","контур с доминированием сетевой координации")
    if flex>=62:
        return tr("rapid-reconfiguration contour","контур быстрой перестройки")
    return tr("balanced mixed contour","смешанный сбалансированный контур")


def individualized_profile_notes(profile, interp):
    """Functional notes derived only from already displayed 0–100 profile/index values."""
    rs1=safe_num(profile.get("rs1"),50)
    rs2=safe_num(profile.get("rs2"),50)
    rs3=safe_num(profile.get("rs3"),50)
    rs4=safe_num(profile.get("rs4"),50)
    load=_idx_value(interp,"overload",safe_num(profile.get("tension"),50))
    rec=_idx_value(interp,"recovery",safe_num(profile.get("adaptive"),50))
    flex=_idx_value(interp,"flexibility",50)
    switch=_idx_value(interp,"transition_cost",50)
    emo=_idx_value(interp,"emo_cost",50)

    out=[]
    # Information assembly
    if rs4>=62:
        out.append((tr("Decision assembly","Сборка решения"),tr(
            "You tend to integrate several streams before committing. Complex decisions can be strong once the internal model is assembled.",
            "Вы склонны собирать несколько потоков информации до фиксации решения. Сложные решения становятся сильной стороной после того, как внутренняя модель собрана.")))
    elif rs4<=38:
        out.append((tr("Decision assembly","Сборка решения"),tr(
            "You benefit from decomposing complex decisions into short sequential steps rather than holding the entire structure at once.",
            "Сложные решения лучше разбирать на короткие последовательные шаги, а не удерживать всю конструкцию одновременно.")))
    else:
        out.append((tr("Decision assembly","Сборка решения"),tr(
            "Your integration level is balanced: you can combine context without needing maximal complexity in every decision.",
            "Интеграция сбалансирована: вы можете учитывать контекст, не превращая каждое решение в максимально сложную конструкцию.")))

    # Focus boundary
    if rs3>=62:
        out.append((tr("Focus boundary","Граница фокуса"),tr(
            "Strong segregation supports protected focus and specialization. Interruptions are usually more expensive than the task itself.",
            "Выраженная сегрегация поддерживает защищённый фокус и специализацию. Прерывания часто обходятся дороже самой задачи.")))
    elif rs3<=38:
        out.append((tr("Focus boundary","Граница фокуса"),tr(
            "Information channels remain relatively open to each other. This helps cross-domain associations but increases interference under overload.",
            "Информационные каналы остаются относительно открытыми друг к другу. Это помогает междисциплинарным ассоциациям, но повышает интерференцию при перегрузке.")))
    else:
        out.append((tr("Focus boundary","Граница фокуса"),tr(
            "You can separate tasks when needed without becoming rigidly locked into one channel.",
            "Вы способны разделять задачи при необходимости, не фиксируясь жёстко на одном канале.")))

    # Tempo + switching
    if switch>=62 or rs1<=38:
        out.append((tr("Tempo and switching","Темп и переключение"),tr(
            "The main cost appears at transitions. Fewer context switches and explicit finish/start rituals should improve output more than simply working faster.",
            "Основная цена возникает на переходах. Меньшее число переключений и явное завершение/начало блоков полезнее, чем попытка просто работать быстрее.")))
    elif flex>=62 and switch<=45:
        out.append((tr("Tempo and switching","Темп и переключение"),tr(
            "Reconfiguration is relatively inexpensive. The risk is not slowness but too many simultaneous directions.",
            "Перестройка относительно дешева. Риск не в медлительности, а в избытке одновременно открытых направлений.")))
    else:
        out.append((tr("Tempo and switching","Темп и переключение"),tr(
            "Your optimal tempo is stable rather than extreme: enough continuity for depth, with planned transitions when context changes.",
            "Оптимальный темп скорее устойчивый, чем экстремальный: достаточно непрерывности для глубины и запланированные переходы при смене контекста.")))

    # Load/recovery
    if load>=65 and rec<50:
        out.append((tr("Under pressure","Под нагрузкой"),tr(
            "Compensation can preserve outward performance while internal cost rises. Recovery should be treated as part of performance, not as time left over after it.",
            "Компенсация может сохранять внешнюю производительность при росте внутренней цены. Восстановление стоит считать частью работоспособности, а не остатком времени после неё.")))
    elif load>=65 and rec>=50:
        out.append((tr("Under pressure","Под нагрузкой"),tr(
            "You can carry high load for a while because reserve remains available, but prolonged pressure may still narrow flexibility.",
            "Вы способны некоторое время нести высокую нагрузку за счёт сохранного резерва, но длительное давление всё равно может сужать гибкость.")))
    else:
        out.append((tr("Under pressure","Под нагрузкой"),tr(
            "The architecture does not show a dominant overload pattern at baseline; performance is more likely to depend on task fit and transition management.",
            "На базовом уровне нет доминирующего паттерна перегрузки; работоспособность сильнее зависит от соответствия задачи и управления переходами.")))

    # Emotional processing
    if emo>=65:
        out.append((tr("Emotional processing","Эмоциональная обработка"),tr(
            "Emotionally significant events consume a larger share of processing capacity. Difficult conversations are best separated from immediately subsequent complex decisions.",
            "Эмоционально значимые события занимают большую долю вычислительного ресурса. Трудные разговоры лучше не ставить непосредственно перед сложными решениями.")))
    elif emo<=35:
        out.append((tr("Emotional processing","Эмоциональная обработка"),tr(
            "Emotional events are comparatively inexpensive for the system, so the blind spot may be underestimating how costly the same event is for another person.",
            "Эмоциональные события сравнительно недороги для системы; слепая зона — недооценка того, насколько дорого то же событие может обходиться другому человеку.")))
    else:
        out.append((tr("Emotional processing","Эмоциональная обработка"),tr(
            "Emotional load is noticeable but usually manageable when conflict, fatigue and multitasking do not accumulate simultaneously.",
            "Эмоциональная нагрузка заметна, но обычно управляемая, если конфликт, усталость и многозадачность не накапливаются одновременно.")))
    return out


def render_pair_rs_radar(p1, p2, title=""):
    labels=["RS1 · Rhythm","RS2 · Sync","RS3 · Topology","RS4 · Integral"]
    keys=("rs1","rs2","rs3","rs4")
    v1=[max(0,min(100,safe_num(p1.get(k,50)))) for k in keys]
    v2=[max(0,min(100,safe_num(p2.get(k,50)))) for k in keys]
    fig=go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=v1+[v1[0]],theta=labels+[labels[0]],mode="lines+markers",fill="toself",
        line=dict(color="#6FD8C4",width=3),fillcolor="rgba(111,216,196,.16)",
        marker=dict(size=7),name=p1.get("name","P1")))
    fig.add_trace(go.Scatterpolar(
        r=v2+[v2[0]],theta=labels+[labels[0]],mode="lines+markers",fill="toself",
        line=dict(color="#E9B15D",width=3),fillcolor="rgba(233,177,93,.12)",
        marker=dict(size=7),name=p2.get("name","P2")))
    fig.update_layout(
        template="plotly_dark",height=480,margin=dict(l=45,r=45,t=65,b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(bgcolor="rgba(13,18,32,.55)",
                   radialaxis=dict(range=[0,100],showticklabels=True,gridcolor="rgba(180,190,214,.28)",tickfont=dict(size=12,color="#D7DEEA")),
                   angularaxis=dict(tickfont=dict(size=14,color="#F3F6FA"),gridcolor="rgba(180,190,214,.28)")),
        showlegend=True,legend=dict(orientation="h",y=-.12,x=.5,xanchor="center"),
        title=title,font=dict(color="#F3F6FA"))
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})


def compatibility_story(p1, p2, deep, score):
    n1,n2=p1.get("name","P1"),p2.get("name","P2")
    notes=[]
    rs_keys=("rs1","rs2","rs3","rs4")
    rs_names={"rs1":tr("rhythm/pace","ритм/темп"),"rs2":tr("network coordination","сетевая координация"),"rs3":tr("focus boundaries","границы фокуса"),"rs4":tr("integration style","стиль интеграции")}
    gaps={k:abs(safe_num(p1.get(k),50)-safe_num(p2.get(k),50)) for k in rs_keys}
    biggest=max(gaps,key=gaps.get)

    if score>=82:
        notes.append((tr("Core fit","Базовое совпадение"),tr(
            "The pair has low architectural translation cost: many default thresholds are similar. The main risk is assuming similarity means identical needs.",
            "У пары низкая цена архитектурного перевода: многие базовые пороги похожи. Главный риск — принять сходство за полное совпадение потребностей.")))
    elif score>=65:
        notes.append((tr("Core fit","Базовое совпадение"),tr(
            "The pair is moderately complementary: enough common ground for coordination, with several differences that can become strengths when roles are explicit.",
            "Пара умеренно комплементарна: общей базы достаточно для согласования, а несколько различий могут стать сильной стороной при ясном распределении ролей.")))
    else:
        notes.append((tr("Core fit","Базовое совпадение"),tr(
            "The pair has a higher translation cost. This is not a verdict on relationship quality; it means expectations about pace, conflict and recovery should be made explicit rather than assumed.",
            "У пары выше цена взаимного перевода. Это не оценка качества отношений; темп, конфликт и восстановление лучше проговаривать явно, а не считать очевидными.")))

    notes.append((tr("Largest architecture gap","Главное архитектурное различие"),tr(
        f"The largest RS difference is {rs_names[biggest]} ({gaps[biggest]:.1f} points). This is the first place to look when the same situation feels 'obvious' to one partner and costly to the other.",
        f"Наибольший разрыв по RS — {rs_names[biggest]} ({gaps[biggest]:.1f} пункта). Именно здесь чаще всего одна и та же ситуация кажется одному партнёру «очевидной», а другому — дорогой.")))

    if deep:
        i1,i2=deep["idx1"],deep["idx2"]
        # recovery
        rgap=abs(i1["recovery"]-i2["recovery"])
        if rgap>=15:
            faster=n1 if i1["recovery"]>i2["recovery"] else n2
            slower=n2 if faster==n1 else n1
            notes.append((tr("Recovery asymmetry","Асимметрия восстановления"),tr(
                f"{faster} has the larger recovery reserve. After conflict or overload, {slower} may need more time before a productive second conversation is possible.",
                f"У {faster} выше резерв восстановления. После конфликта или перегрузки {slower} может требоваться больше времени до продуктивного второго разговора.")))
        else:
            notes.append((tr("Recovery rhythm","Ритм восстановления"),tr(
                "Recovery capacity is relatively similar, which makes shared routines easier — provided both partners are actually at comparable load levels.",
                "Резерв восстановления относительно похож, поэтому совместные режимы проще — если текущая нагрузка у обоих действительно сопоставима.")))

        # emotional processing
        egap=abs(i1["emo_cost"]-i2["emo_cost"])
        if egap>=15:
            higher=n1 if i1["emo_cost"]>i2["emo_cost"] else n2
            lower=n2 if higher==n1 else n1
            notes.append((tr("Conflict processing","Обработка конфликта"),tr(
                f"Emotional processing costs more for {higher}. {lower} may be ready to move on earlier; pushing that pace onto {higher} can prolong rather than resolve the conflict.",
                f"Эмоциональная обработка дороже для {higher}. {lower} может быть готов двигаться дальше раньше; навязывание этого темпа {higher} способно не сократить, а продлить конфликт.")))
        else:
            notes.append((tr("Conflict processing","Обработка конфликта"),tr(
                "The emotional-processing cost is close enough that escalation is more likely to come from timing or topic overload than from radically different sensitivity.",
                "Цена эмоциональной обработки достаточно близка; эскалация скорее будет связана со временем и перегрузкой темами, чем с радикально разной чувствительностью.")))

        # flexibility
        fgap=abs(i1["flexibility"]-i2["flexibility"])
        if fgap>=15:
            fast=n1 if i1["flexibility"]>i2["flexibility"] else n2
            deep_name=n2 if fast==n1 else n1
            notes.append((tr("Change and decisions","Изменения и решения"),tr(
                f"{fast} reconfigures faster; {deep_name} is more likely to preserve the existing model until it is internally coherent. Agree on a decision deadline instead of arguing about who is 'too fast' or 'too slow'.",
                f"{fast} перестраивается быстрее; {deep_name} вероятнее сохраняет текущую модель, пока она не станет внутренне согласованной. Лучше согласовать срок решения, чем спорить, кто «слишком быстрый» или «слишком медленный».")))
        else:
            notes.append((tr("Change and decisions","Изменения и решения"),tr(
                "The pair changes strategy at a similar pace. The advantage is easy coordination; the risk is jointly rushing or jointly postponing the same decision.",
                "Пара меняет стратегию в похожем темпе. Плюс — лёгкое согласование; риск — синхронно поспешить или синхронно откладывать одно и то же решение.")))
    return notes


TYPE_CONTENT={
 "RU":{
  "fortress":("FORTRESS · Крепость","🛡️","Архитектура опирается на устойчивые внутренние модели, специализацию и сохранение структуры. Она хорошо удерживает долгие задачи и защищает фокус от внешнего шума.","В жизни это проявляется как потребность сначала понять систему, а затем действовать последовательно. Сильная сторона — глубина и надёжность; цена — более дорогая внезапная смена контекста.","Полезная стратегия: длинные блоки самостоятельной работы, заранее обозначенные переходы и восстановление без новых входящих сигналов."),
  "antenna":("ANTENNA · Антенна","📡","Архитектура обладает высоким входным усилением: быстро замечает изменения, несоответствия и эмоциональные сигналы. Она собирает больше контекста, чем требуется для простой реакции.","В жизни это даёт интуитивное распознавание обстановки и быстрый отклик, но увеличивает цену информационного и эмоционального шума.","Полезная стратегия: управлять числом входящих каналов, защищать сон и чередовать интенсивное взаимодействие с периодами сенсорного снижения."),
  "fluid":("FLUID · Поток","🌊","Архитектура легко перестраивает связи и меняет способ обработки по контексту. Её преимущество — адаптация и создание альтернатив.","В жизни это проявляется как способность быстро войти в новую тему и соединить удалённые идеи. Риск — распыление внимания и недостаточное закрепление результата.","Полезная стратегия: ограничивать число параллельных направлений и завершать цикл явной фиксацией решения."),
  "collapse":("ПОВЫШЕННАЯ НАГРУЗКА · текущее состояние","⚠️","Текущая конфигурация показывает повышенную нагрузку при ограниченном резерве управления. Это состояние системы, а не психотип и не диагноз.","При накоплении усталости могут расти цена переключений и число ошибок.","Полезная стратегия: снизить одновременную нагрузку, восстановить сон и затем повторить функциональные измерения."),
 },
 "EN":{
  "fortress":("FORTRESS","🛡️","This architecture relies on stable internal models, specialization and structural persistence. It supports long tasks and protects focus from external noise.","In daily life it prefers understanding the system before acting consistently. Its strength is depth and reliability; abrupt context changes carry a higher cost.","Use long independent focus blocks, explicit transitions and recovery with reduced incoming stimulation."),
  "antenna":("ANTENNA","📡","This architecture has high input gain: it detects changes, mismatches and emotional signals quickly and collects more context than a simple response requires.","In daily life this supports intuitive situation reading and rapid response while increasing the cost of informational and emotional noise.","Control the number of input channels, protect sleep and alternate intensive contact with low-stimulation periods."),
  "fluid":("FLUID","🌊","This architecture reorganizes connections readily and changes processing strategy with context. Its advantage is adaptation and option generation.","In daily life it enters new topics quickly and links distant ideas. The risk is attention dispersion and insufficient consolidation.","Limit simultaneous directions and finish each cycle by explicitly recording the decision."),
  "collapse":("HIGH LOAD · current state","⚠️","The current configuration indicates elevated load with limited control reserve. This is a system state, not a psychotype or diagnosis.","With accumulated fatigue, switching cost and avoidable errors may rise.","Reduce simultaneous load, restore sleep, then repeat functional measurements."),
 }
}

FAMOUS_REFERENCE={
 "Thomas Edison":[-2.20,38.06,17.10,27.10,36.11,29.62,-29.82,33.84,50.00],
 "Nikola Tesla":[-1.44,35.96,14.80,25.85,31.43,26.77,-27.30,26.40,50.00],
 "Sigmund Freud":[-1.40,35.26,14.30,25.40,29.91,25.95,-26.42,25.11,50.00],
 "Marie Curie":[-1.98,38.17,16.25,27.29,35.94,28.87,-29.58,32.23,50.00],
 "Mahatma Gandhi":[-5.11,37.75,16.89,25.65,38.39,31.64,-36.82,35.01,50.00],
 "Winston Churchill":[1.18,26.44,10.07,20.06,16.55,11.20,-16.38,16.81,38.72],
 "Albert Einstein":[-.94,27.39,10.07,19.88,20.29,16.47,-21.04,16.69,41.13],
 "Pablo Picasso":[-2.62,28.11,9.23,19.85,21.66,17.87,-24.38,16.79,43.74],
 "Coco Chanel":[-3.41,22.97,6.83,15.80,17.77,14.27,-22.56,13.23,35.55],
 "Alan Turing":[3.04,30.96,13.30,23.92,18.92,14.63,-16.70,19.70,43.49],
}


def famous_analogies(profile):
    keys=("RS1_RHYTHM","RS2_SYNC","RS3_SEGR","RS4_INTEGRAL","X_SENS","X_LAB","X_STAB","X_FLEX","X_HUB")
    raw=profile.get("raw",{})
    if not raw or any(k not in raw for k in keys):return []
    matrix=np.array(list(FAMOUS_REFERENCE.values()),dtype=float)
    target=np.array([safe_num(raw[k],0) for k in keys],dtype=float)
    scale=np.std(matrix,axis=0);scale[scale<1e-6]=1
    dist=np.sqrt(np.mean(((matrix-target)/scale)**2,axis=1))
    order=np.argsort(dist)[:3]
    names=list(FAMOUS_REFERENCE)
    return [(names[i],float(dist[i])) for i in order]


def render_type_profile(profile,interp):
    key=architecture_type(profile,interp);title,icon,*paras=TYPE_CONTENT[st.session_state.lang][key]
    color={"fortress":"#6FD8C4","antenna":"#E3A34E","fluid":"#A7B0C8","collapse":"#D9714B"}[key]
    modifier=profile_modifier(profile,interp)
    st.markdown(
        f'<div class="science-card" style="border-color:{color}88;background:linear-gradient(135deg,{color}25,rgba(7,20,36,.88))">'
        f'<div class="eyebrow">ARCHITECTURE TYPE</div><h3>{icon} {title}</h3>'
        f'<p><b>{tr("Individual contour","Индивидуальный контур")}:</b> {modifier}</p></div>',
        unsafe_allow_html=True
    )
    for p in paras:st.write(p)

    st.markdown("**"+tr("How this type is expressed in your numbers","Как этот тип выражается именно в ваших цифрах")+"**")
    for note_title,note_text in individualized_profile_notes(profile,interp):
        card(note_title,note_text,"INDIVIDUAL SIGNATURE")

    analogies=famous_analogies(profile)
    if analogies:
        st.markdown("**"+tr("Closest reference profiles","Ближайшие референсные профили")+"**")
        st.write(" · ".join(name for name,_ in analogies))
        st.caption(tr("Mathematical proximity within an exploratory zero-lag 43 reference set; it does not imply identical personality, biography or ability.","Математическая близость в исследовательской zero-lag выборке 43; она не означает одинаковую личность, биографию или способности."))
    st.caption(tr("Type assignment is a functional summary of continuous scores; the full profile is defined by the RS and X parameters.","Тип — функциональное резюме непрерывных показателей; полный профиль определяется параметрами RS и X."))


AXIS_EXPLAIN = {
    "rs1": ("RS1 · Rhythm", "Ритм, энергетическая устойчивость и цена удержания темпа.", "Rhythm, energetic stability, and the cost of maintaining pace."),
    "rs2": ("RS2 · Synchrony", "Согласование сетей и способность объединять параллельные сигналы.", "Network coordination and the ability to combine parallel signals."),
    "rs3": ("RS3 · Segregation", "Разделение функций, специализация и защита фокуса от помех.", "Functional separation, specialization, and protection of focus from interference."),
    "rs4": ("RS4 · Integration", "Сборка распределённых процессов в целостное решение.", "Integration of distributed processes into a coherent decision."),
}


def render_axes(profile):
    cols = st.columns(4)
    for col,(key,(title,ru,en)) in zip(cols,AXIS_EXPLAIN.items()):
        val = safe_num(profile.get(key,50))
        with col:
            st.markdown(
                f'<div class="axis-card"><div class="eyebrow">{title}</div>'
                f'<div class="score">{val:.1f}</div><p>{ru if st.session_state.lang=="RU" else en}</p></div>',
                unsafe_allow_html=True,
            )


def render_rs_bars(profile):
    for key,(title,ru,en) in AXIS_EXPLAIN.items():
        value=max(0,min(100,safe_num(profile.get(key,50))))
        st.progress(value/100,text=f"{title} · {value:.1f}/100 · {ru if st.session_state.lang=='RU' else en}")


def render_architecture_interpretation(profile, interp):
    st.subheader(tr("From numbers to function", "От чисел к функции"))
    if not interp:
        for insight in profile.get("insights", []):
            card(tr("Functional observation", "Функциональный вывод"), insight, "43 → FUNCTION")
        return
    for key,data in interp["indices"].items():
        with st.expander(f"{data['title']} · {data['value']:.1f}/100 · {level_word(data['level'])}"):
            st.write(data["description"])
            actions = action_for_index(key, data["level"])
            st.markdown("**" + tr("What to do", "Как использовать") + "**")
            for item in actions:
                st.markdown(f"- {item}")


def action_for_index(key, level):
    ru = {
        "overload": ["Планируйте сложные решения до накопления усталости.", "Сравнивайте утреннюю энергию и вечернее истощение раз в неделю."],
        "recovery": ["Зафиксируйте постоянное время подъёма.", "После перегрузки планируйте отдельное окно восстановления, а не только отсутствие работы."],
        "flexibility": ["При высокой гибкости ограничивайте число параллельных задач; при низкой заранее готовьте переходы.", "Используйте один контекст на рабочий блок."],
        "rigidity": ["Сильные устойчивые паттерны направляйте на глубокую работу.", "Перед изменением плана формулируйте, что сохраняется неизменным."],
        "transition_cost": ["Оставляйте 10–20 минут между разными типами задач.", "Группируйте звонки, переписку и аналитическую работу."],
        "emo_cost": ["После эмоционально значимых разговоров снижайте следующую когнитивную нагрузку.", "Разделяйте событие, телесную реакцию и решение."],
        "bottleneck": ["Декомпозируйте многоэтапные задачи и фиксируйте следующий шаг письменно.", "Не держите несколько незавершённых решений одновременно."],
        "autonomic": ["Ведите журнал сна, пульса и самочувствия рядом с данными космической погоды.", "Вывод делайте по повторяющемуся личному паттерну, а не по одному дню."],
    }
    en = {
        "overload": ["Schedule complex decisions before fatigue accumulates.", "Compare morning energy with evening depletion once a week."],
        "recovery": ["Anchor a consistent wake time.", "After overload, schedule active recovery rather than merely stopping work."],
        "flexibility": ["With high flexibility, limit parallel tasks; with low flexibility, prepare transitions.", "Keep one context per work block."],
        "rigidity": ["Use stable patterns for deep work.", "Before changing plans, state what will remain stable."],
        "transition_cost": ["Leave 10–20 minutes between task types.", "Batch calls, messages, and analytical work."],
        "emo_cost": ["Reduce the next cognitive load after emotionally significant conversations.", "Separate the event, body response, and decision."],
        "bottleneck": ["Break multi-stage tasks down and write the next action.", "Avoid holding several unresolved decisions at once."],
        "autonomic": ["Track sleep, pulse, and symptoms beside space-weather data.", "Infer a personal pattern from repetitions, not one day."],
    }
    items = (ru if st.session_state.lang=="RU" else en).get(key, [])
    if level == "low" and key in ("overload","transition_cost","emo_cost","bottleneck","autonomic"):
        return [tr("This is currently a relative strength; protect it under prolonged load.", "Сейчас это относительная сильная сторона; контролируйте её при длительной нагрузке.")] + items[:1]
    return items


def sleep_protocol(interp):
    levels = interp.get("index_levels", {}) if interp else {}
    high_load = levels.get("overload") == "high"
    high_lab = levels.get("transition_cost") == "high" or levels.get("autonomic") == "high"
    low_rec = levels.get("recovery") == "low"
    wind = "90" if high_lab else "60"
    caffeine = "8–10" if high_lab else "6–8"
    return [
        tr("Fix one wake time seven days a week; vary it by no more than 30–45 minutes.", "Зафиксируйте одно время подъёма на всю неделю; отклонение не более 30–45 минут."),
        tr(f"Begin a {wind}-minute low-stimulation transition before bed.", f"Начинайте {wind}-минутный переход к сну со снижением стимуляции."),
        tr(f"Stop caffeine {caffeine} hours before planned sleep and test the effect for 14 days.", f"Прекращайте кофеин за {caffeine} часов до сна и проверяйте эффект 14 дней."),
        tr("Record bedtime, sleep latency, awakenings, wake time and morning energy (0–10).", "Записывайте время отбоя, засыпания, пробуждения, подъёма и утреннюю энергию 0–10."),
        tr("On high-load days, reduce late cognitive and conflict load.", "В дни высокой нагрузки снижайте позднюю когнитивную нагрузку и конфликтные разговоры.") if high_load else tr("Keep the same protocol during calm weeks to establish your baseline.", "Сохраняйте протокол и в спокойные недели, чтобы определить личный базовый уровень."),
        tr("Plan an additional recovery block after two poor nights.", "После двух плохих ночей планируйте отдельный блок восстановления.") if low_rec else tr("Use the recovery reserve deliberately; do not wait for exhaustion.", "Используйте резерв восстановления заранее, не дожидаясь истощения."),
    ]


@st.cache_data(ttl=1800, show_spinner=False)
def load_kp_forecast():
    url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
    if os.getenv("PSYCHOTYP_OFFLINE") == "1":
        return {"max_kp":None,"rows":[],"source":url}
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Archviq/1.0"})
        with urllib.request.urlopen(req, timeout=7) as response:
            rows = json.loads(response.read().decode("utf-8"))
        if rows and isinstance(rows[0], dict):
            data = rows
        else:
            header = rows[0]
            data = [dict(zip(header,row)) for row in rows[1:]]
        forecast_rows = [row for row in data if str(row.get("observed","")).lower() == "predicted"]
        window = forecast_rows[:24] or data[-24:]
        vals = []
        for row in window:
            for key,val in row.items():
                if "kp" in key.lower():
                    try: vals.append(float(val))
                    except (TypeError, ValueError): pass
                    break
        return {"max_kp":max(vals) if vals else None,"rows":data,"source":url}
    except Exception:
        return {"max_kp":None,"rows":[],"source":url}


def render_space_weather(interp):
    st.subheader(tr("Solar environment: personal monitoring", "Солнечная среда: персональный мониторинг"))
    forecast = load_kp_forecast()
    kp = forecast.get("max_kp")
    autonomic = (interp or {}).get("indices",{}).get("autonomic",{}).get("value",50)
    c1,c2,c3 = st.columns(3)
    c1.metric(tr("Forecast Kp maximum", "Максимум Kp по прогнозу"), f"{kp:.1f}" if kp is not None else "—")
    c2.metric(tr("Architectural reactivity", "Архитектурная реактивность"), f"{autonomic:.1f}/100")
    state = tr("heightened observation", "усиленное наблюдение") if (kp or 0) >= 5 and autonomic >= 60 else tr("baseline observation", "базовое наблюдение")
    c3.metric(tr("Personal protocol", "Личный протокол"), state)
    st.caption(tr(
        "Kp is an official geomagnetic activity index, not a measurement of your nervous system. The app uses it to schedule an N-of-1 observation: sleep, pulse, symptoms, and performance are compared across repeated quiet and active periods.",
        "Kp — официальный индекс геомагнитной активности, а не измерение вашей нервной системы. Приложение использует его для персонального N-of-1 наблюдения: сон, пульс, симптомы и работоспособность сравниваются в повторяющиеся спокойные и активные периоды."
    ))
    if kp is None:
        st.info(tr("Live NOAA data are temporarily unavailable; the personal architecture report remains valid.", "Онлайн-данные NOAA временно недоступны; персональный архитектурный отчёт остаётся доступным."))
    else:
        predicted=[r for r in forecast.get("rows",[]) if str(r.get("observed","")).lower()=="predicted"]
        if predicted:
            times=[r.get("time_tag") for r in predicted]
            vals=[safe_num(r.get("kp"),0) for r in predicted]
            colors=["#D9714B" if v>=5 else "#6FD8C4" for v in vals]
            fig=go.Figure(go.Scatter(x=times,y=vals,mode="lines+markers",line=dict(color="#6FD8C4",width=3),marker=dict(color=colors,size=7),fill="tozeroy",fillcolor="rgba(111,216,196,.1)"))
            fig.add_hline(y=5,line_dash="dash",line_color="#D9714B",annotation_text="Kp 5")
            fig.update_layout(template="plotly_dark",height=310,margin=dict(l=10,r=10,t=25,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(13,18,32,.72)",xaxis_title=tr("Forecast time","Время прогноза"),yaxis=dict(title="Kp",range=[0,max(6,max(vals)+.5)]))
            st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
        if kp >= 5 and autonomic >= 60:
            st.warning(tr("Active period for this architecture: protect sleep timing, avoid stacking high-stakes decisions late in the day, reduce conflict load and record the response.", "Активный период для этой архитектуры: защитите режим сна, не накапливайте важные решения к вечеру, снизьте конфликтную нагрузку и зафиксируйте реакцию."))
        elif kp >= 5:
            st.warning(tr("Geomagnetically active period: maintain the normal schedule and record whether your state departs from baseline.","Геомагнитно активный период: сохраняйте обычный режим и отмечайте, отклоняется ли состояние от вашего базового уровня."))
        else:
            st.success(tr("Forecast quiet-to-moderate period: use it to record your baseline. Personal usefulness requires repeated comparison with active windows.", "По прогнозу спокойный или умеренный период: используйте его для записи базового состояния. Персональная полезность определяется повторным сравнением с активными окнами."))


def render_sleep_and_work(interp):
    tab1,tab2,tab3 = st.tabs([tr("Sleep", "Сон"),tr("Work rhythm", "Рабочий ритм"),tr("14-day control", "Контроль 14 дней")])
    with tab1:
        levels=(interp or {}).get("index_levels",{})
        extended=levels.get("autonomic")=="high" or levels.get("overload")=="high" or levels.get("recovery")=="low"
        wake=st.time_input(tr("Required wake time","Необходимое время подъёма"),value=datetime.time(7,0),key=f"wake_{st.session_state.get('step','screen')}")
        sleep_hours=8.5 if extended else 8.0
        wake_dt=datetime.datetime.combine(datetime.date.today(),wake)
        bed_dt=wake_dt-datetime.timedelta(hours=sleep_hours)
        st.metric(tr("Target sleep window","Целевое окно сна"),f"{bed_dt:%H:%M} → {wake_dt:%H:%M}",tr(f"{sleep_hours:.1f} h initial test window",f"{sleep_hours:.1f} ч — стартовое окно проверки"))
        st.caption(tr("This is an initial behavioral experiment derived from load and recovery indices, not a clinical prescription. Adjust after 14 days using sleep latency, awakenings and morning function.","Это начальный поведенческий эксперимент по индексам нагрузки и восстановления, а не клиническое назначение. Корректируйте его через 14 дней по времени засыпания, пробуждениям и утренней функции."))
        for i,item in enumerate(sleep_protocol(interp),1):
            card(f"{i:02d}",item,"SLEEP PROTOCOL")
    with tab2:
        transition = (interp or {}).get("indices",{}).get("transition_cost",{}).get("value",50)
        block = "75–100" if transition >= 60 else "45–75"
        card(tr("Focus block", "Блок фокуса"),tr(f"Use {block}-minute single-context blocks followed by a real transition.",f"Используйте блоки одного контекста по {block} минут с отдельным переходом."),"LOAD DESIGN")
        card(tr("Decision timing", "Время решений"),tr("Place strategic decisions in the first stable energy window of your day.","Ставьте стратегические решения в первое устойчивое энергетическое окно дня."),"CONTROL")
        card(tr("Recovery", "Восстановление"),tr("Treat recovery as an input to performance and reserve it in the calendar.","Считайте восстановление входным параметром работоспособности и резервируйте его в календаре."),"FEEDBACK")
    with tab3:
        st.markdown(tr(
            "1. Keep wake time stable.  2. Record five sleep variables daily.  3. Add Kp and subjective load.  4. Review medians after 14 days.  5. Change one variable for the next cycle.",
            "1. Стабилизируйте подъём.  2. Ежедневно записывайте пять параметров сна.  3. Добавляйте Kp и субъективную нагрузку.  4. Через 14 дней сравните медианы.  5. В следующем цикле меняйте только одну переменную."
        ))


def render_method_detail():
    tabs = st.tabs([tr("Neurogenesis", "Нейрогенез"),tr("Engine 43", "Движок 43"),tr("Cybernetics", "Кибернетика"),tr("Evidence", "Проверка")])
    with tabs[0]:
        st.markdown(tr(
            "During prenatal and early postnatal development, proliferation, migration, differentiation, synaptogenesis, pruning, myelination and network synchronization unfold in partially ordered windows. Archviq tests whether temporal structure in the solar-activity environment can act as a weak background modulator of these developing control systems. The date of birth anchors the developmental timeline; it does not assign a symbolic sign or character.",
            "Во время пренатального и раннего постнатального развития последовательно и частично перекрываясь идут пролиферация, миграция, дифференцировка, синаптогенез, прунинг, миелинизация и синхронизация сетей. Archviq проверяет гипотезу, может ли временная структура солнечной активности быть слабым фоновым модулятором формирующихся систем управления. Дата рождения фиксирует шкалу развития; она не присваивает человеку символический знак или характер."
        ))
        st.markdown('<div class="formula">developmental state = intrinsic program + environment(t) + adaptation + experience</div>',unsafe_allow_html=True)
        st.latex(r"RS_k=f\!\left(SSN(t)\otimes W_k(t)\right)")
    with tabs[1]:
        st.markdown(tr(
            "The production v1 engine loads measured daily SILSO Wolf numbers, derives first and second differences, sign reversals, 7/14/21-day volatility and ranges, and robustly standardizes them. It aggregates impulse, jerk, volatility, directional asymmetry and instability in 15 developmental windows: W0–W5, N0 and P1–P8. Each window updates nine coupled latent states. The final state is projected into RS1–RS4 and load/control indices.",
            "Production v1 загружает измеренные суточные числа Вольфа SILSO, вычисляет первую и вторую разности, смены знака, волатильность и диапазоны за 7/14/21 день, затем выполняет робастную стандартизацию. Импульс, рывок, волатильность, направленная асимметрия и нестабильность собираются в 15 окнах развития: W0–W5, N0 и P1–P8. Каждое окно обновляет девять связанных скрытых состояний. Финальное состояние проецируется в RS1–RS4 и индексы нагрузки/контроля."
        ))
        st.markdown('<div class="formula">dynamic = .35·impulse + .30·jerk + .20·volatility + .15·range<br>Xₖ₊₁ = clip(DₖXₖ + GₖFₖ + coupling)</div>',unsafe_allow_html=True)
        st.latex(r"X_{k+1}=\operatorname{clip}\left(D_kX_k+G_kF_k+C(X_k)\right)")
        st.latex(r"RS_4=.30X_{integ}+.25X_{hub}+.20X_{mat}+.15X_{stab}-.20X_{lab}")
    with tabs[2]:
        st.markdown(tr(
            "The architecture is represented as a control system: excitation and sensitivity provide input gain; stability and maturation constrain the response; flexibility and segregation allocate processing; hubness and integration combine signals; lability describes switching cost. The useful output is not a label but a control policy: when to load the system, how to switch, how much recovery it needs, and how to measure adaptation.",
            "Архитектура представлена как система управления: возбуждение и чувствительность задают усиление входа; стабильность и зрелость ограничивают реакцию; гибкость и сегрегация распределяют обработку; хабовость и интеграция объединяют сигналы; лабильность описывает цену переключения. Полезный результат — не ярлык, а политика управления: когда нагружать систему, как переключаться, сколько восстановления ей нужно и как измерять адаптацию."
        ))
        st.markdown('<div class="formula">input → state transition → output → measurement → correction</div>',unsafe_allow_html=True)
    with tabs[3]:
        st.markdown(tr(
            "Unlike astrology, the model uses a public measured time series, explicit windows and reproducible equations. Its claims can be tested against EEG, cognitive measures and questionnaires, and can fail. The LEMON n=199 layer is used for research calibration and percentile interpretation; a date-only result remains a prior hypothesis until checked against the person's measured function.",
            "В отличие от астрологии модель использует публичный измеренный временной ряд, явные окна и воспроизводимые уравнения. Её выводы можно проверять по EEG, когнитивным измерениям и опросникам, и проверка может их опровергнуть. Слой LEMON n=199 используется для исследовательской калибровки и перцентильной интерпретации; результат только по дате остаётся априорной гипотезой до сопоставления с измеренной функцией человека."
        ))


st.markdown(SCIENCE_CSS, unsafe_allow_html=True)
st.markdown(
    '<div style="position:fixed;left:14px;bottom:10px;z-index:9999;'
    'font:700 10px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#6FD8C4;'
    'background:#0B0F1C;border:1px solid rgba(111,216,196,.35);border-radius:8px;'
    'padding:6px 9px">ARCHVIQ · PRODUCT R3</div>',
    unsafe_allow_html=True,
)

# ── Состояние ──────────────────────────────────────────────────────────────
for k,v in {
    "step": "landing",
    "lang": "EN",
    "p1": None, "p2": None,
    "mode": "personal",
    "quiz": None,
    "quiz_answers": {},
    "cog_done": False,
    "cognitive_results": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

L = st.session_state.lang

# ── Переводы ───────────────────────────────────────────────────────────────
T = {
    "title": {"EN": "Archviq", "RU": "Archviq"},
    "subtitle": {
        "EN": "A computational profile of information processing",
        "RU": "Расчётный профиль обработки информации",
    },
    "landing_h1": {
        "EN": "What is your brain actually built for?",
        "RU": "Для чего реально построен ваш мозг?",
    },
    "landing_p1": {
        "EN": """Standard personality tests measure *behaviour*.  
Archviq measures the **architecture** behind it — the neural structure formed 
during your critical developmental windows, shaped by electromagnetic solar dynamics.  

This is not astrology. The mechanism is biophysical. The data is measured.  
The results are falsifiable.""",
        "RU": """Стандартные тесты личности измеряют *поведение*.  
Archviq измеряет **архитектуру** за ним — нейронную структуру, сформированную  
в критические окна развития под влиянием электромагнитной солнечной динамики.  

Это не астрология. Механизм биофизический. Данные измерены.  
Результаты фальсифицируемы.""",
    },
    "how_title": {
        "EN": "How it works",
        "RU": "Как это работает",
    },
    "how_steps": {
        "EN": [
            "**Step 1 — Neural Architecture Profile**  \nYour date of birth → prenatal solar dynamics → RS1-RS4 axes → 8 functional indices",
            "**Step 2 — Cognitive Test** *(optional)*  \nReaction time, working memory, interference control → measured performance vs. predicted baseline",
            "**Step 3 — Targeted Questionnaire** *(optional)*  \nBurnout / Compatibility / AI collaboration → behavioral layer on top of architecture",
            "**Step 4 — Integrated Report**  \nGAP analysis: where architecture and behavior diverge — and what to do about it",
        ],
        "RU": [
            "**Шаг 1 — Профиль нейронной архитектуры**  \nДата рождения → солнечная динамика → оси RS1-RS4 → 8 функциональных индексов",
            "**Шаг 2 — Когнитивный тест** *(опционально)*  \nВремя реакции, рабочая память, контроль интерференции → измеренные показатели vs. предсказанный базовый уровень",
            "**Шаг 3 — Целевой опросник** *(опционально)*  \nВыгорание / Совместимость / Работа с ИИ → поведенческий слой поверх архитектуры",
            "**Шаг 4 — Интегрированный отчёт**  \nGAP-анализ: где архитектура и поведение расходятся — и что с этим делать",
        ],
    },
    "start_btn": {"EN": "Calculate my profile →", "RU": "Рассчитать мой профиль →"},
    "name_label": {"EN": "Name (optional)", "RU": "Имя (опционально)"},
    "sex_label": {"EN": "Sex", "RU": "Пол"},
    "sex_opts": {"EN": ["Male", "Female"], "RU": ["Мужской", "Женский"]},
    "dob_label": {"EN": "Date of Birth", "RU": "Дата рождения"},
    "compute_btn": {"EN": "Compute My Profile →", "RU": "Вычислить профиль →"},
    "computing": {"EN": "Analyzing solar dynamics...", "RU": "Анализ солнечной динамики..."},
    "mode_label": {"EN": "Mode", "RU": "Режим"},
    "mode_opts": {"EN": ["Personal Profile", "Compatibility"], "RU": ["Личный профиль", "Совместимость"]},
    "p1_label": {"EN": "Partner 1", "RU": "Партнёр 1"},
    "p2_label": {"EN": "Partner 2", "RU": "Партнёр 2"},
    "compat_btn": {"EN": "Analyze Compatibility →", "RU": "Анализировать совместимость →"},
    "key_insights": {"EN": "Key Insights", "RU": "Ключевые инсайты"},
    "recommendations": {"EN": "Recommendations", "RU": "Рекомендации"},
    "next_cog": {"EN": "→ Take Cognitive Test", "RU": "→ Пройти когнитивный тест"},
    "next_quiz": {"EN": "→ Choose Questionnaire", "RU": "→ Выбрать опросник"},
    "back": {"EN": "← Back", "RU": "← Назад"},
    "restart": {"EN": "Start Over", "RU": "Начать заново"},
    "cog_title": {"EN": "Cognitive Assessment", "RU": "Когнитивная оценка"},
    "cog_desc": {
        "EN": "5 short tests (15 min). Measures your actual reaction time, working memory, and cognitive control — compared against your architectural prediction.",
        "RU": "5 коротких тестов (15 минут). Измеряет ваше реальное время реакции, рабочую память и когнитивный контроль — в сравнении с архитектурным предсказанием.",
    },
    "cog_done_btn": {"EN": "Tests Complete → View Results", "RU": "Тесты пройдены → Смотреть результаты"},
    "quiz_title": {"EN": "Choose Your Questionnaire", "RU": "Выберите опросник"},
    "quiz_opts": {
        "EN": {
            "compatibility": "💞 Compatibility — understand relationship dynamics",
            "burnout": "🔥 Burnout Audit — measure your current resource load",
            "ai": "🤖 AI Collaboration — how your architecture interacts with AI",
        },
        "RU": {
            "compatibility": "💞 Совместимость — понять динамику отношений",
            "burnout": "🔥 Аудит выгорания — измерить текущую ресурсную нагрузку",
            "ai": "🤖 Работа с ИИ — как ваша архитектура взаимодействует с ИИ",
        },
    },
    "submit_quiz": {"EN": "Submit Answers →", "RU": "Отправить ответы →"},
    "scale_label": {"EN": "1 = Never / Strongly disagree  |  5 = Always / Strongly agree",
                    "RU": "1 = Никогда / Совершенно не согласен  |  5 = Всегда / Полностью согласен"},
    "compat_score": {"EN": "Compatibility Index", "RU": "Индекс совместимости"},
    "pair_dynamics": {"EN": "Pair Dynamics", "RU": "Динамика пары"},
    "validation_note": {
        "EN": "Validated on LEMON dataset (n=199). Significant associations with anxiety (ρ=0.20), impulsivity (ρ=0.26), stress (ρ=0.23).",
        "RU": "Валидировано на датасете LEMON (n=199). Значимые связи с тревогой (ρ=0.20), импульсивностью (ρ=0.26), стрессом (ρ=0.23).",
    },
}

def t(key):
    return T.get(key, {}).get(L, T.get(key, {}).get("EN", key))

# ── Опросники ──────────────────────────────────────────────────────────────
QUESTIONS = {
    "compatibility": {
        "EN": [
            "When we disagree, I feel heard and understood.",
            "I find it easy to express what I need from my partner.",
            "After a difficult conversation, I feel relief rather than tension.",
            "I can raise an uncomfortable topic without fearing a negative reaction.",
            "We talk about important things before they become problems.",
            "Our arguments end with a resolution, not just exhaustion.",
            "After conflict, we return to closeness fairly quickly.",
            "I feel safe being wrong or admitting a mistake with my partner.",
            "We have compatible needs for alone time and togetherness.",
            "We want the same things from life in the next 5 years.",
            "We support each other's individual goals, not just shared ones.",
            "Being with my partner restores my energy rather than draining it.",
        ],
        "RU": [
            "Когда мы не соглашаемся, я чувствую что меня слышат и понимают.",
            "Мне легко сказать партнёру чего я хочу или в чём нуждаюсь.",
            "После трудного разговора я чувствую облегчение, а не напряжение.",
            "Я могу поднять неудобную тему не опасаясь негативной реакции.",
            "Мы говорим о важных вещах до того, как они становятся проблемами.",
            "Наши ссоры заканчиваются решением, а не просто истощением.",
            "После конфликта мы довольно быстро возвращаемся к близости.",
            "Я чувствую безопасность признавая ошибку перед партнёром.",
            "У нас совместимые потребности в одиночестве и близости.",
            "Мы хотим одного и того же от жизни в следующие 5 лет.",
            "Мы поддерживаем индивидуальные цели друг друга.",
            "Пребывание с партнёром восстанавливает мою энергию.",
        ],
    },
    "burnout": {
        "EN": [
            "By end of day I feel completely drained, even if nothing major happened.",
            "I wake up tired, before the day has even started.",
            "Small tasks require effort that feels disproportionate.",
            "My body carries tension that doesn't go away even after rest.",
            "I feel emotionally distant from people I used to care about at work.",
            "I find myself going through the motions rather than being genuinely engaged.",
            "I have become more cynical or irritable about things that used to matter.",
            "My work no longer has the meaning it once did.",
            "I still produce good work but it costs me much more than it used to.",
            "I struggle to concentrate on one thing for more than 20-30 minutes.",
            "My sleep doesn't feel restorative — I still wake up tired.",
            "Activities that used to recharge me no longer work the same way.",
        ],
        "RU": [
            "К концу дня я чувствую себя полностью опустошённым.",
            "Я просыпаюсь усталым ещё до начала дня.",
            "Небольшие задачи требуют несоразмерных усилий.",
            "Моё тело несёт напряжение которое не уходит даже после отдыха.",
            "Я чувствую эмоциональную дистанцию от людей на работе.",
            "Я замечаю что просто делаю движения, а не реально включён.",
            "Я стал более циничным по отношению к вещам которые раньше имели значение.",
            "Моя работа больше не имеет того смысла что был раньше.",
            "Я ещё могу делать хорошую работу, но это стоит значительно больше.",
            "Мне трудно сосредоточиться дольше 20-30 минут.",
            "Мой сон не восстанавливает — я всё равно просыпаюсь усталым.",
            "Занятия которые раньше восстанавливали меня больше не работают.",
        ],
    },
    "ai": {
        "EN": [
            "I tend to accept AI outputs without extensively checking them.",
            "When AI gives a confident answer, I feel uncomfortable doubting it.",
            "I can tell when an AI response is plausible but wrong.",
            "I actively look for errors or gaps in what AI produces.",
            "Using AI leaves me feeling mentally clearer and more productive.",
            "I sometimes feel more confused after using AI than before.",
            "I notice when I am delegating thinking to AI that I should do myself.",
            "My decisions improved after I started using AI regularly.",
            "I use AI to challenge my thinking, not just confirm it.",
            "I trust my own judgment more than AI when they conflict.",
            "I am aware of how my emotional state affects my AI prompts.",
            "I can clearly explain why I accepted or rejected an AI suggestion.",
        ],
        "RU": [
            "Я склонен принимать результаты ИИ без тщательной проверки.",
            "Когда ИИ даёт уверенный ответ, мне некомфортно сомневаться.",
            "Я могу определить когда ответ ИИ правдоподобен, но неверен.",
            "Я активно ищу ошибки или пробелы в том что производит ИИ.",
            "Использование ИИ оставляет меня ментально более ясным.",
            "Иногда после ИИ я чувствую себя более запутанным чем до.",
            "Я замечаю когда делегирую ИИ мышление которое должен делать сам.",
            "Мои решения улучшились после того как я начал регулярно использовать ИИ.",
            "Я использую ИИ чтобы оспорить своё мышление, а не просто подтвердить.",
            "Я доверяю своему суждению больше чем ИИ когда они конфликтуют.",
            "Я осознаю как моё эмоциональное состояние влияет на запросы к ИИ.",
            "Я могу объяснить почему принял или отклонил предложение ИИ.",
        ],
    },
}

# Product questionnaires from the Archviq specification.
QUESTIONS["compatibility"]["EN"] = [
    "My partner listens without preparing a counterargument.", "I can state a need directly.",
    "We clarify what the other person meant.", "Important information is not withheld.",
    "We can discuss vulnerable topics safely.", "We notice when tone changes the meaning.",
    "We discuss one issue rather than many past issues.", "A pause in conflict has an agreed return time.",
    "We can acknowledge our own contribution to a conflict.", "Repair includes a concrete agreement.",
    "We return to emotional contact after disagreement.", "The same conflict does not repeat without analysis.",
    "Our priorities for the next five years are compatible.", "We agree on money and responsibility principles.",
    "We support each other's independent goals.", "We can negotiate different social needs.",
    "We share a realistic picture of family obligations.", "Major decisions are made jointly.",
    "Time together usually restores rather than depletes me.", "Our needs for solitude are respected.",
    "We notice overload before it becomes conflict.", "We allow different recovery speeds.",
    "Sleep and work schedules do not chronically damage the relationship.", "We deliberately create positive shared experiences.",
]
QUESTIONS["compatibility"]["RU"] = [
    "Партнёр слушает меня, не готовя встречный аргумент.", "Я могу прямо сказать о своей потребности.",
    "Мы уточняем, что другой действительно имел в виду.", "Важная информация не скрывается.",
    "Мы безопасно обсуждаем уязвимые темы.", "Мы замечаем, когда тон меняет смысл сказанного.",
    "В конфликте мы обсуждаем один вопрос, а не весь архив претензий.", "Пауза в конфликте включает согласованное время возврата.",
    "Каждый может признать собственный вклад в конфликт.", "Восстановление заканчивается конкретной договорённостью.",
    "После разногласия мы возвращаем эмоциональный контакт.", "Повторяющийся конфликт становится предметом анализа.",
    "Наши приоритеты на ближайшие пять лет совместимы.", "Мы согласны в принципах денег и ответственности.",
    "Мы поддерживаем самостоятельные цели друг друга.", "Мы можем согласовать разные социальные потребности.",
    "У нас общее реалистичное представление о семейных обязанностях.", "Важные решения принимаются совместно.",
    "Совместное время обычно восстанавливает, а не истощает меня.", "Наша потребность в уединении уважается.",
    "Мы замечаем перегрузку до того, как она становится конфликтом.", "Мы допускаем разную скорость восстановления.",
    "Режим сна и работы не разрушает отношения хронически.", "Мы намеренно создаём положительный совместный опыт.",
]
QUESTIONS["burnout"]["EN"] = [
    "I wake up tired.", "My energy drops sharply before the day ends.", "Small tasks require disproportionate effort.", "Rest no longer restores me quickly.",
    "I feel emotionally detached from work or people.", "I operate on autopilot.", "I have become more cynical or irritable.", "My activity has lost meaning.",
    "Concentration is harder than before.", "I make more avoidable errors.", "Good work costs much more effort.", "I postpone decisions because processing feels overloaded.",
    "My sleep is not restorative.", "My body carries persistent tension.", "My pulse or autonomic state stays activated after work.", "Activities that used to recharge me work less effectively.",
]
QUESTIONS["burnout"]["RU"] = [
    "Я просыпаюсь усталым.", "Энергия резко падает до окончания дня.", "Малые задачи требуют несоразмерных усилий.", "Отдых перестал быстро восстанавливать меня.",
    "Я эмоционально отстраняюсь от работы или людей.", "Я действую на автопилоте.", "Я стал более циничным или раздражительным.", "Моя деятельность потеряла смысл.",
    "Концентрироваться стало труднее.", "Я допускаю больше предотвратимых ошибок.", "Хорошая работа требует намного больше усилий.", "Я откладываю решения из-за ощущения перегрузки обработки.",
    "Мой сон не восстанавливает.", "В теле сохраняется постоянное напряжение.", "Пульс или автономное возбуждение долго не снижаются после работы.", "Привычные способы восстановления работают хуже.",
]


def score_quiz(answers, quiz_type):
    vals = [answers[k] for k in sorted(answers)]
    if not vals:
        return 0, "—"
    if quiz_type == "ai":
        vals = [6-v if i in {0,1,5,6} else v for i,v in enumerate(vals)]
    avg = sum(vals) / len(vals)
    pct = int((avg - 1) / 4 * 100)
    if quiz_type == "burnout":
        if pct < 35:
            label = {"EN": "Low risk", "RU": "Низкий риск"}[L]
        elif pct < 60:
            label = {"EN": "Moderate — monitor", "RU": "Умеренный — наблюдайте"}[L]
        else:
            label = {"EN": "High — action needed", "RU": "Высокий — нужны действия"}[L]
    elif quiz_type == "compatibility":
        if pct > 65:
            label = {"EN": "Strong connection", "RU": "Сильная связь"}[L]
        elif pct > 40:
            label = {"EN": "Moderate — growth areas visible", "RU": "Умеренная — видны зоны роста"}[L]
        else:
            label = {"EN": "Challenging — conscious work needed", "RU": "Сложная — нужна осознанная работа"}[L]
    else:
        if pct > 65:
            label = {"EN": "Optimal AI collaborator", "RU": "Оптимальное взаимодействие с ИИ"}[L]
        elif pct > 40:
            label = {"EN": "Moderate — calibration needed", "RU": "Умеренное — нужна калибровка"}[L]
        else:
            label = {"EN": "Risk of over-delegation", "RU": "Риск избыточного делегирования"}[L]
    return pct, label


def quiz_domain_scores(answers, quiz_type):
    vals = [answers[k] for k in sorted(answers)]
    if quiz_type == "ai":
        vals = [6-v if i in {0,1,5,6} else v for i,v in enumerate(vals)]
    names = {
        "burnout": [tr("Energy depletion","Истощение энергии"),tr("Detachment and meaning","Дистанция и смысл"),tr("Functional efficiency","Функциональная эффективность"),tr("Body and recovery","Тело и восстановление")],
        "compatibility": [tr("Communication","Коммуникация"),tr("Conflict repair","Восстановление после конфликта"),tr("Values and direction","Ценности и направление"),tr("Energy and recovery","Энергия и восстановление")],
        "ai": [tr("Verification","Проверка ИИ"),tr("Cognitive agency","Собственное мышление"),tr("Metacognitive control","Метакогнитивный контроль")],
    }[quiz_type]
    out=[]
    block_size={"compatibility":6,"burnout":4,"ai":4}[quiz_type]
    for i,name in enumerate(names):
        block=vals[i*block_size:(i+1)*block_size]
        pct=round((sum(block)/len(block)-1)/4*100) if block else 0
        out.append((name,pct))
    return out


def questionnaire_actions(quiz_type, domains, interp):
    strongest=max(domains,key=lambda x:x[1])
    weakest=min(domains,key=lambda x:x[1])
    overload=(interp or {}).get("indices",{}).get("overload",{}).get("value",50)
    if quiz_type=="burnout":
        return [
            tr(f"Highest current burden: {strongest[0]} ({strongest[1]}%).","Наибольшая текущая нагрузка: "+f"{strongest[0]} ({strongest[1]}%)."),
            tr("Reduce one recurring demand for 14 days and track morning energy.","На 14 дней уберите одну повторяющуюся нагрузку и отслеживайте утреннюю энергию."),
            tr("Architecture also indicates elevated baseline load; recovery should be scheduled before symptoms peak.","Архитектура также показывает повышенную базовую нагрузку; восстановление нужно планировать до пика симптомов.") if overload>=60 else tr("The behavioral load exceeds the architectural baseline if symptoms remain high; inspect work, sleep and recent stressors.","Если симптомы остаются высокими, поведенческая нагрузка превышает архитектурный фон; проверьте работу, сон и недавние стрессоры."),
        ]
    if quiz_type=="compatibility":
        return [
            tr(f"Primary growth area: {weakest[0]} ({weakest[1]}%).",f"Главная зона роста: {weakest[0]} ({weakest[1]}%)."),
            tr("Choose one weekly 25-minute conversation with a fixed structure: facts → feelings → request → agreement.","Проводите один 25-минутный разговор в неделю по структуре: факты → чувства → просьба → договорённость."),
            tr("After conflict, record how long each partner needs before constructive dialogue becomes possible.","После конфликта отмечайте, сколько времени каждому нужно до конструктивного разговора."),
        ]
    return [
        tr(f"Best calibrated domain: {strongest[0]} ({strongest[1]}%).",f"Лучше всего откалибрована область: {strongest[0]} ({strongest[1]}%)."),
        tr(f"Priority for improvement: {weakest[0]} ({weakest[1]}%).",f"Приоритет улучшения: {weakest[0]} ({weakest[1]}%)."),
        tr("For high-stakes outputs use a three-step rule: independent hypothesis → AI answer → explicit contradiction check.","Для важных задач используйте три шага: собственная гипотеза → ответ ИИ → явная проверка противоречий."),
    ]


def render_seven_day_recovery(profile,interp):
    kind=architecture_type(profile,interp)
    type_action={
        "fortress":tr("Use protected solitary focus as recovery; avoid fragmented rest filled with messages.","Используйте защищённый одиночный фокус как восстановление; избегайте фрагментированного отдыха с перепиской."),
        "antenna":tr("Reduce incoming channels and alternate social contact with sensory quiet.","Сократите число входящих каналов и чередуйте общение с сенсорной тишиной."),
        "fluid":tr("Reduce simultaneous projects and close one cycle each day.","Сократите число параллельных проектов и ежедневно завершайте один цикл."),
        "collapse":tr("Reduce obligations first; stabilize wake time before adding performance goals.","Сначала снизьте обязательства; стабилизируйте подъём до добавления целей производительности."),
    }[kind]
    days=[
        tr("Baseline: record sleep, morning energy, workload and evening depletion.","Базовая линия: запишите сон, утреннюю энергию, нагрузку и вечернее истощение."),
        tr("Remove one recurring nonessential demand.","Уберите одну повторяющуюся необязательную нагрузку."),
        type_action,
        tr("Place the hardest task in the first stable energy window; stop before exhaustion.","Поставьте самую сложную задачу в первое устойчивое энергетическое окно; остановитесь до истощения."),
        tr("Create a 60–90 minute low-stimulation pre-sleep transition.","Создайте 60–90-минутный переход ко сну со снижением стимуляции."),
        tr("Use active physical recovery at comfortable intensity and compare the next morning.","Используйте комфортную физическую активность и сравните состояние следующим утром."),
        tr("Review medians, keep the one intervention that improved both sleep and function.","Сравните медианы и сохраните одно вмешательство, улучшившее и сон, и функцию."),
    ]
    st.subheader(tr("Seven-day correction protocol","Семидневный протокол коррекции"))
    for i,item in enumerate(days,1):card(tr(f"Day {i}",f"День {i}"),item,"RECOVERY")


def _clamp(value, low=0.0, high=100.0):
    return max(low, min(high, safe_num(value, low)))


def _accuracy_pct(value):
    value = safe_num(value, 0)
    return _clamp(value * 100 if value <= 1.0001 else value)


def _rt_score(value, best=180.0, worst=900.0):
    """Convert latency to a transparent 0–100 orientation score."""
    return _clamp(100.0 * (worst - safe_num(value, worst)) / (worst - best))


def cognitive_gap_rows(profile, results):
    """Return prediction-versus-measurement rows without diagnosing the user."""
    interp = get_interp(profile)
    indices = (interp or {}).get("indices", {})

    def iv(key, default=50):
        return safe_num((indices.get(key) or {}).get("value"), default)

    rs3 = _clamp(profile.get("rs3", 50))
    rs4 = _clamp(profile.get("rs4", 50))
    predicted = {
        "reaction": .55 * iv("recovery") + .45 * (100 - iv("overload")),
        "choice": .55 * rs3 + .45 * (100 - iv("transition_cost")),
        "memory": .55 * rs4 + .45 * (100 - iv("bottleneck")),
        "inhibition": .50 * rs3 + .50 * (100 - iv("transition_cost")),
        "integration": .65 * rs4 + .35 * iv("flexibility"),
    }
    complex_accuracy = _accuracy_pct(results.get("COMPLEX_ACC_accuracy"))
    complex_hard = _accuracy_pct(results.get("COMPLEX_ACC_hard_accuracy"))
    measured = {
        "reaction": _rt_score(results.get("SRT_median_rt")),
        "choice": _accuracy_pct(results.get("CHOICE_accuracy")),
        "memory": _accuracy_pct(results.get("NBACK_accuracy")),
        "inhibition": _clamp(100 - safe_num(results.get("SIMON_interference_cost"), 350) / 3.5),
        "integration": .65 * complex_accuracy + .35 * complex_hard,
    }
    titles = {
        "reaction": tr("Reaction stability", "Стабильность реакции"),
        "choice": tr("Choice accuracy", "Точность выбора"),
        "memory": tr("Working memory", "Рабочая память"),
        "inhibition": tr("Interference control", "Контроль интерференции"),
        "integration": tr("Complex rule integration", "Интеграция сложного правила"),
    }
    rows = []
    for key in titles:
        gap = measured[key] - predicted[key]
        agap = abs(gap)
        status = (tr("aligned", "согласовано") if agap <= 12 else
                  tr("compensated / context-sensitive", "компенсация / зависимость от контекста") if agap <= 25 else
                  tr("marked divergence — repeat", "выраженное расхождение — повторить"))
        rows.append({
            tr("Function", "Функция"): titles[key],
            tr("43 prior", "Прогноз 43"): round(predicted[key], 1),
            tr("Measured", "Измерено"): round(measured[key], 1),
            "GAP": round(gap, 1),
            tr("Interpretation", "Интерпретация"): status,
        })
    return rows


def render_cognitive_gap(profile, results):
    rows = cognitive_gap_rows(profile, results)
    st.subheader(tr("Architecture × measured cognition", "Архитектура × измеренная когниция"))
    st.dataframe(rows, width="stretch", hide_index=True)
    gaps = [abs(safe_num(row["GAP"])) for row in rows]
    mean_gap = float(np.mean(gaps)) if gaps else 0.0
    signed = [safe_num(row["GAP"]) for row in rows]
    c1, c2, c3 = st.columns(3)
    c1.metric(tr("Mean absolute GAP", "Средний абсолютный GAP"), f"{mean_gap:.1f}")
    c2.metric(tr("Above prior", "Выше прогноза"), sum(g > 12 for g in signed))
    c3.metric(tr("Below prior", "Ниже прогноза"), sum(g < -12 for g in signed))
    if mean_gap <= 12:
        st.success(tr(
            "The measured functional pattern is close to the architectural prior. Repeat once to estimate test–retest stability.",
            "Измеренный функциональный паттерн близок к архитектурному прогнозу. Повторите тест один раз для оценки ретестовой стабильности."
        ))
    elif mean_gap <= 25:
        st.info(tr(
            "The architecture is partly compensated or state-dependent. Compare the same test after two weeks of stable sleep and workload.",
            "Архитектура частично компенсирована или зависит от состояния. Повторите тот же тест после двух недель стабильного сна и нагрузки."
        ))
    else:
        st.warning(tr(
            "The measurement diverges from the prior. Check device conditions, sleep and interruptions, then repeat before interpreting the difference.",
            "Измерение расходится с прогнозом. Проверьте устройство, сон и помехи, затем повторите тест до интерпретации различия."
        ))
    st.caption(tr(
        "Scores are orientation scales derived from reaction time, accuracy and interference cost. They are research feedback metrics, not clinical norms or diagnoses.",
        "Баллы — ориентировочные шкалы, рассчитанные из времени реакции, точности и цены интерференции. Это исследовательские метрики обратной связи, а не клинические нормы или диагноз."
    ))
    export = pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        tr("Download cognitive GAP report", "Скачать отчёт cognitive GAP"),
        data=export,
        file_name="archviq_cognitive_gap.csv",
        mime="text/csv",
        width="stretch",
    )


def ai_profile_name(score,domains,interp):
    overload=(interp or {}).get("indices",{}).get("overload",{}).get("value",50)
    if overload>=67 and score<65:return tr("OVERLOADED USER","ПЕРЕГРУЖЕННЫЙ ПОЛЬЗОВАТЕЛЬ")
    if score<38:return tr("OVER-DELEGATOR","ИЗБЫТОЧНОЕ ДЕЛЕГИРОВАНИЕ")
    if score<55:return tr("UNDER-CALIBRATED USER","НЕДОСТАТОЧНАЯ КАЛИБРОВКА")
    return tr("OPTIMAL COLLABORATOR","ОПТИМАЛЬНЫЙ ПАРТНЁР ИИ")

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 0: Выбор языка (всегда вверху)
# ═══════════════════════════════════════════════════════════════════════════
col_lang = st.columns([4,1])[1]
new_lang = col_lang.selectbox("🌐", ["EN","RU"],
    index=0 if st.session_state.lang=="EN" else 1,
    label_visibility="collapsed")
if new_lang != st.session_state.lang:
    st.session_state.lang = new_lang
    L = new_lang
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 1: Лендинг
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.step == "landing":
    st.markdown('<div class="hero-kicker">ARCHVIQ · NEURAL ARCHITECTURE INTELLIGENCE</div>', unsafe_allow_html=True)
    st.title(tr("Why does your brain process information this way?", "Почему ваш мозг обрабатывает информацию именно так?"))
    st.markdown(
        '<div class="hero-copy">' + tr(
            "A computational developmental profile that is compared with how you actually perform cognitive tasks and answer questionnaires.",
            "Расчётный профиль развития, который сопоставляется с тем, как вы реально выполняете когнитивные задачи и отвечаете на опросники."
        ) + '</div>', unsafe_allow_html=True)
    render_science_pipeline()
    c1,c2,c3 = st.columns(3)
    with c1: card(tr("Measured input", "Измеряемый вход"),tr("Daily SILSO Wolf numbers; derivatives, volatility, ranges and reversals.","Суточные числа Вольфа SILSO; производные, волатильность, диапазоны и смены направления."),"DATA")
    with c2: card(tr("Computational architecture", "Расчётная архитектура"),tr("15 developmental windows, nine coupled states and four RS axes.","15 окон развития, девять связанных состояний и четыре оси RS."),"MODEL 43")
    with c3: card(tr("Feedback loop", "Контур обратной связи"),tr("Cognitive tests, questionnaires, sleep and repeated personal measurements.","Когнитивные тесты, опросники, сон и повторные персональные измерения."),"CONTROL")
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("The problem", "Проблема"))
    st.markdown('<div class="formula">ARCHITECTURE → COGNITION → BEHAVIOUR</div>',unsafe_allow_html=True)
    st.write(tr(
        "Standard tests measure behavior after it has already been shaped by education, stress, culture and adaptation. Archviq estimates the architecture beneath that behavior, then measures how it is expressed now.",
        "Стандартные тесты измеряют поведение после того, как его сформировали образование, стресс, культура и адаптация. Archviq оценивает лежащую под ним архитектуру, а затем измеряет, как она проявляется сейчас."
    ))
    st.subheader(tr("What the model is testing", "Что проверяет модель"))
    st.write(tr(
        "The working hypothesis is that weak environmental dynamics may interact with sensitive periods of neurodevelopment and leave a statistical prior in the organization of rhythm, synchrony, specialization and integration. The system does not infer personality from a calendar symbol. It reconstructs a physical time series around development, applies fixed numerical transformations, and exposes the result to external tests.",
        "Рабочая гипотеза состоит в том, что слабая динамика внешней среды может взаимодействовать с чувствительными периодами нейроразвития и оставлять статистический след в организации ритма, синхронизации, специализации и интеграции. Система не выводит личность из календарного символа. Она реконструирует физический временной ряд вокруг развития, применяет фиксированные численные преобразования и передаёт результат на внешнюю проверку."
    ))
    render_ssn_windows_chart()
    render_method_detail()
    st.subheader(tr("Why this is not astrology", "Почему это не астрология"))
    render_not_astrology()
    st.subheader(tr("Research calibration · LEMON n=199", "Исследовательская калибровка · LEMON n=199"))
    render_validation_chart()
    st.caption(tr(
        "Reported Spearman associations in the project analysis: anxiety ρ=.20, p=.004; impulsivity ρ=.26, p=.0002; stress ρ=.23, p=.001. These are statistical associations and do not by themselves establish causality.",
        "Связи Спирмена в анализе проекта: тревога ρ=.20, p=.004; импульсивность ρ=.26, p=.0002; стресс ρ=.23, p=.001. Это статистические связи; сами по себе они не устанавливают причинность."
    ))
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("From profile to an individual protocol", "От профиля к индивидуальному протоколу"))
    for title,body in [
        (tr("1 · Architecture", "1 · Архитектура"),tr("Estimate rhythm, synchrony, segregation, integration and nine control states.","Оценка ритма, синхронизации, сегрегации, интеграции и девяти управляющих состояний.")),
        (tr("2 · Function", "2 · Функция"),tr("Translate every score into load, recovery, flexibility, switching and emotional-processing cost.","Перевод каждого показателя в нагрузку, восстановление, гибкость, переключение и цену эмоциональной обработки.")),
        (tr("3 · Measurement", "3 · Измерение"),tr("Compare the prior with reaction time, working memory, interference control and questionnaires.","Сопоставление прогноза со временем реакции, рабочей памятью, контролем интерференции и опросниками.")),
        (tr("4 · Correction", "4 · Коррекция"),tr("Build sleep, work, recovery and relationship protocols; repeat measurement after 14 days.","Построение протоколов сна, работы, восстановления и отношений; повторное измерение через 14 дней.")),
    ]:
        card(title,body)
    st.subheader(tr("Choose the depth of analysis", "Выберите глубину анализа"))
    render_pricing()
    purchase_button(tr(f"Get the complete Archviq package · {PRICES['full']}",f"Получить полный пакет Archviq · {PRICES['full']}"),"full")
    st.caption("Patent Pending — Israel Application No. 322588 (2025)")
    render_founder()
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    mode = st.radio(t("mode_label"), t("mode_opts"), horizontal=True)
    st.session_state.mode = "compat" if mode == t("mode_opts")[-1] else "personal"
    if st.button(t("start_btn"), width="stretch", type="primary"):
        st.session_state.step = "input"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 2: Ввод данных
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "input":
    st.title(t("title") + " 🧠")
    if st.session_state.mode == "personal":
        col1, col2 = st.columns(2)
        name = col1.text_input(t("name_label"), placeholder="...")
        sex  = col2.selectbox(t("sex_label"), t("sex_opts"))
        dob  = st.date_input(t("dob_label"),
               value=datetime.date(1985,6,15),
               min_value=datetime.date(1920,1,1),
               max_value=datetime.date.today()-datetime.timedelta(days=365*16))
        if st.button(t("compute_btn"), width="stretch", type="primary"):
            with st.spinner(t("computing")):
                st.session_state.p1 = compute_profile(dob, sex, name or "—", L)
            st.session_state.step = "result"
            st.rerun()
    else:
        st.subheader(t("p1_label"))
        c1, c2 = st.columns(2)
        n1 = c1.text_input(t("name_label"), key="n1", placeholder="...")
        s1 = c1.selectbox(t("sex_label"), t("sex_opts"), key="s1")
        d1 = c2.date_input(t("dob_label"), value=datetime.date(1985,3,10),
             min_value=datetime.date(1920,1,1),
             max_value=datetime.date.today(), key="d1")
        st.subheader(t("p2_label"))
        c3, c4 = st.columns(2)
        n2 = c3.text_input(t("name_label"), key="n2", placeholder="...")
        s2 = c3.selectbox(t("sex_label"), t("sex_opts"), key="s2")
        d2 = c4.date_input(t("dob_label"), value=datetime.date(1988,9,22),
             min_value=datetime.date(1920,1,1),
             max_value=datetime.date.today(), key="d2")
        if st.button(t("compat_btn"), width="stretch", type="primary"):
            with st.spinner(t("computing")):
                st.session_state.p1 = compute_profile(d1, s1, n1 or "P1", L)
                st.session_state.p2 = compute_profile(d2, s2, n2 or "P2", L)
            st.session_state.step = "compat"
            st.rerun()
    if st.button(t("back")):
        st.session_state.step = "landing"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 3: Результат — личный профиль
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "result":
    p = st.session_state.p1
    interp = get_interp(p)
    st.markdown('<div class="hero-kicker">PERSONAL CONTROL ARCHITECTURE · MODEL 43</div>',unsafe_allow_html=True)
    st.title(p.get("name","") + " · " + tr("Neural Architecture", "Нейронная архитектура"))
    st.markdown(f'<div class="hero-copy">{architecture_short_tagline(p,interp)}</div>',unsafe_allow_html=True)
    engine_source = str(p.get("engine_source", "ENGINE 43"))
    if "FALLBACK" in engine_source.upper():
        st.warning(tr(
            "Demo fallback is active: the production engine file was not found. Place 43_universal_full_cascade_engine.py beside app.py or set PSYCHOTYP_ENGINE_PATH, then calculate again.",
            "Включён демонстрационный резервный режим: файл промышленного движка не найден. Поместите 43_universal_full_cascade_engine.py рядом с app.py или задайте PSYCHOTYP_ENGINE_PATH и выполните расчёт повторно."
        ))
    else:
        st.caption("✓ " + engine_source + " · pre_lag=0 · post_lag=0")
    radar_col,type_col=st.columns([1,1.15],gap="large")
    with radar_col: render_rs_radar(p,tr("RS1–RS4 architecture","Архитектура RS1–RS4"))
    with type_col: render_type_profile(p,interp)
    render_axes(p)
    st.markdown('<div class="formula">SSN dynamics → developmental signatures → 9 coupled X states → RS architecture → functional protocol</div>',unsafe_allow_html=True)

    overview,mechanics,protocol,weather = st.tabs([
        tr("Interpretation", "Интерпретация"),
        tr("How 43 produced it", "Как это получил 43"),
        tr("Sleep & performance", "Сон и работоспособность"),
        tr("Solar monitoring", "Солнечный мониторинг"),
    ])
    with overview:
        render_rs_bars(p)
        render_architecture_interpretation(p,interp)
        if interp:
            st.info(interp.get("gap_text",""))
            if interp.get("top_priorities"):
                st.markdown("**"+tr("Current control priorities", "Текущие приоритеты управления")+"**")
                st.write(" · ".join(interp["top_priorities"]))
        if p.get("recommendations"):
            st.subheader(tr("Immediate use", "Немедленное применение"))
            for rec in p.get("recommendations",[]):
                st.success("✓ "+rec)
    with mechanics:
        render_science_pipeline()
        render_method_detail()
        raw = p.get("raw",{})
        if raw:
            with st.expander(tr("Open the numerical output of engine 43", "Открыть численный выход движка 43")):
                keys = ["RS1_RHYTHM","RS2_SYNC","RS3_SEGR","RS4_INTEGRAL",
                        "X_EXC","X_SENS","X_STAB","X_INTEG","X_FLEX","X_LAB","X_SEGR","X_HUB","X_MAT",
                        "hidden_tension_index","architecture_power_score","pathology_load_score",
                        "adaptive_control_score","adaptive_stability_score","decompensation_risk_score",
                        "high_load_compensation_score","tension_control_ratio"]
                rows = [{tr("Parameter","Параметр"):k,tr("Value","Значение"):round(safe_num(raw.get(k)),4)} for k in keys if k in raw]
                st.dataframe(rows,width="stretch",hide_index=True)
    with protocol:
        render_sleep_and_work(interp)
    with weather:
        render_space_weather(interp)

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button(t("next_cog"), width="stretch"):
        st.session_state.step = "cognitive"
        st.rerun()
    if c2.button(t("next_quiz"), width="stretch"):
        st.session_state.step = "quiz_select"
        st.rerun()
    if c3.button(t("restart")):
        for k in ["p1","p2","quiz","quiz_answers","cog_done","cognitive_results"]:
            st.session_state[k] = None if k in ["p1","p2","quiz","cognitive_results"] else {} if k=="quiz_answers" else False
        st.session_state.step = "landing"
        st.rerun()
    purchase_button(tr(f"Full report + biohacking protocol · {PRICES['full']}",f"Полный отчёт + биохакинг-протокол · {PRICES['full']}"),"full")

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("Get your report as PDF","Получить отчёт в PDF"))
    pdf_bytes = build_pdf(p, interp, lang=L)
    st.download_button(
        tr("Download PDF","Скачать PDF"),
        data=pdf_bytes,
        file_name="archviq_report.pdf",
        mime="application/pdf",
        width="stretch",
    )
    st.caption(tr(
        "Email delivery of the PDF will be connected in the next step; it is intentionally hidden until the backend is ready.",
        "Отправку PDF на email подключим следующим этапом; до готовности backend эта кнопка намеренно не показывается."
    ))

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 4: Когнитивный тест
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "cognitive":
    st.markdown('<div class="hero-kicker">MEASURED FUNCTION · STAGE 2</div>',unsafe_allow_html=True)
    st.title(t("cog_title"))
    st.markdown('<div class="hero-copy">'+t("cog_desc")+'</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1: card(tr("Reaction","Реакция"),tr("Response latency and stability.","Время и стабильность ответа."),"TEST 1–2")
    with c2: card(tr("Working memory","Рабочая память"),tr("Updating and holding information.","Обновление и удержание информации."),"TEST 3")
    with c3: card(tr("Control","Контроль"),tr("Interference and rule switching.","Интерференция и смена правил."),"TEST 4–5")
    st.info(tr("The test is embedded in this app. Press its internal Start button, complete all five blocks, then download the CSV and press the button below.","Тест встроен в приложение. Нажмите внутреннюю кнопку старта, завершите пять блоков, скачайте CSV и затем нажмите кнопку под тестом."))
    st.iframe(get_cognitive_html(), height=1050)
    st.subheader(tr("Load the measured result", "Загрузите измеренный результат"))
    st.write(tr(
        "After the test downloads its CSV, upload that file here. Archviq will compare the measured functions with the engine 43 prior.",
        "После того как тест скачает CSV, загрузите этот файл сюда. Archviq сопоставит измеренные функции с прогнозом движка 43."
    ))
    uploaded = st.file_uploader(
        tr("Cognitive-test CSV", "CSV когнитивного теста"),
        type=["csv"], key="cognitive_csv"
    )
    if uploaded is not None:
        try:
            cognitive_df = pd.read_csv(uploaded)
            if cognitive_df.empty:
                raise ValueError(tr("The CSV contains no result row.", "В CSV нет строки результата."))
            cognitive_result = cognitive_df.iloc[0].to_dict()
            required_metrics = ["SRT_median_rt", "CHOICE_accuracy", "NBACK_accuracy", "SIMON_interference_cost", "COMPLEX_ACC_accuracy"]
            missing_metrics = [k for k in required_metrics if k not in cognitive_result]
            if missing_metrics:
                raise ValueError(tr("Missing test fields: ", "Нет полей теста: ") + ", ".join(missing_metrics))
            st.session_state.cognitive_results = cognitive_result
            render_cognitive_gap(st.session_state.p1, cognitive_result)
        except Exception as exc:
            st.error(tr("Cannot read this cognitive CSV: ", "Не удалось прочитать cognitive CSV: ") + str(exc))
    elif st.session_state.cognitive_results:
        render_cognitive_gap(st.session_state.p1, st.session_state.cognitive_results)
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button(t("cog_done_btn"), type="primary"):
        st.session_state.cog_done = True
        st.session_state.step = "quiz_select"
        st.rerun()
    if c2.button(t("back")):
        st.session_state.step = "result"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 5: Выбор опросника
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz_select":
    st.title(t("quiz_title") + " 📋")
    st.divider()
    quiz_opts = t("quiz_opts")
    for qkey, qlabel in quiz_opts.items():
        if st.button(qlabel, width="stretch"):
            st.session_state.quiz = qkey
            st.session_state.quiz_answers = {}
            st.session_state.step = "quiz"
            st.rerun()
    st.divider()
    if st.button(t("back")):
        st.session_state.step = "result" if not st.session_state.cog_done else "cognitive"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 6: Опросник
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz":
    quiz_type = st.session_state.quiz
    quiz_name = t("quiz_opts").get(quiz_type, quiz_type)
    st.title(quiz_name)
    st.caption(t("scale_label"))
    st.divider()

    questions = QUESTIONS.get(quiz_type, {}).get(L, QUESTIONS.get(quiz_type,{}).get("EN",[]))
    answers = {}
    for i, q in enumerate(questions):
        answers[i] = st.slider(
            f"{i+1}. {q}",
            min_value=1, max_value=5, value=3,
            key=f"q_{quiz_type}_{i}"
        )

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button(t("submit_quiz"), type="primary", width="stretch"):
        st.session_state.quiz_answers = answers
        st.session_state.step = "quiz_result"
        st.rerun()
    if c2.button(t("back")):
        st.session_state.step = "quiz_select"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 7: Результат опросника + финальный отчёт
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz_result":
    p = st.session_state.p1
    quiz_type = st.session_state.quiz
    answers = st.session_state.quiz_answers
    score_pct, score_label = score_quiz(answers, quiz_type)
    domains = quiz_domain_scores(answers, quiz_type)
    interp = get_interp(p)

    quiz_name = t("quiz_opts").get(quiz_type, quiz_type)
    st.markdown('<div class="hero-kicker">BEHAVIOR × ARCHITECTURE · GAP ANALYSIS</div>',unsafe_allow_html=True)
    st.title({"EN":"Your measured behavioral layer","RU":"Измеренный поведенческий слой"}[L])
    st.subheader(quiz_name)
    if quiz_type=="ai":
        st.markdown(f'<div class="formula">AI PROFILE · {ai_profile_name(score_pct,domains,interp)}</div>',unsafe_allow_html=True)
    result_cols = st.columns(len(domains)+1)
    result_cols[0].metric(tr("Total score","Общий результат"),f"{score_pct}%",score_label)
    for col,(name,value) in zip(result_cols[1:],domains):
        col.metric(name,f"{value}%")
    st.caption(tr(
        "The questionnaire measures the current behavioral layer. Engine 43 estimates a prior architecture. Their difference is information: it may reflect adaptation, compensation, context or current load.",
        "Опросник измеряет текущий поведенческий слой. Движок 43 оценивает априорную архитектуру. Разница между ними информативна: она может отражать адаптацию, компенсацию, контекст или текущую нагрузку."
    ))

    # GAP: архитектура vs поведение
    st.subheader({"EN":"Architecture × Behavior GAP","RU":"GAP: Архитектура × Поведение"}[L])
    try:
        if interp:
            overload_level = interp["index_levels"].get("overload","mid")
            emo_level = interp["index_levels"].get("emo_cost","mid")

            if quiz_type == "burnout":
                if score_pct > 60 and overload_level == "high":
                    st.error({"EN":"⚠️ High architectural load + high behavioral burnout. Immediate recovery protocol recommended.",
                              "RU":"⚠️ Высокая архитектурная нагрузка + высокое поведенческое выгорание. Рекомендован немедленный протокол восстановления."}[L])
                elif score_pct > 60 and overload_level == "low":
                    st.warning({"EN":"Burnout symptoms above architectural baseline. Situational overload — not structural.",
                                "RU":"Симптомы выгорания выше архитектурного базового уровня. Ситуационная перегрузка — не структурная."}[L])
                elif score_pct < 40 and overload_level == "high":
                    st.info({"EN":"Architecture carries high load but behavior is compensated. Hidden tension — monitor.",
                             "RU":"Архитектура несёт высокую нагрузку, но поведение компенсировано. Скрытое напряжение — наблюдайте."}[L])
                else:
                    st.success({"EN":"Architecture and burnout levels are aligned. System is functioning within expected range.",
                                "RU":"Архитектура и уровень выгорания согласованы. Система функционирует в ожидаемом диапазоне."}[L])

            elif quiz_type == "compatibility":
                if score_pct > 65:
                    st.success({"EN":"Strong behavioral connection. Your architecture supports this.",
                                "RU":"Сильная поведенческая связь. Ваша архитектура это поддерживает."}[L])
                else:
                    st.info({"EN":"Growth areas visible. Your architectural profile suggests specific strategies.",
                             "RU":"Видны зоны роста. Ваш архитектурный профиль предполагает конкретные стратегии."}[L])

            elif quiz_type == "ai":
                if score_pct > 65 and emo_level == "high":
                    st.warning({"EN":"Good AI calibration but high emotional cost. Stress may reduce critical evaluation of AI outputs.",
                                "RU":"Хорошая калибровка ИИ, но высокая эмоциональная стоимость. Стресс может снизить критическую оценку вывода ИИ."}[L])
                elif score_pct < 40:
                    st.error({"EN":"Risk of over-delegation. Your architecture may amplify this under load.",
                              "RU":"Риск избыточного делегирования. Ваша архитектура может усилить это под нагрузкой."}[L])
                else:
                    st.success({"EN":"Balanced AI collaboration profile.",
                                "RU":"Сбалансированный профиль взаимодействия с ИИ."}[L])
    except Exception:
        pass

    st.subheader(tr("Detailed conclusions and next action", "Подробные выводы и следующий шаг"))
    for action in questionnaire_actions(quiz_type,domains,interp):
        card(tr("Control decision","Управляющее решение"),action,"FEEDBACK LOOP")
    if quiz_type=="burnout":
        render_sleep_and_work(interp)
        render_seven_day_recovery(p,interp)
    elif quiz_type=="compatibility":
        card(tr("Measurement","Измерение"),tr("Repeat the same questionnaire after two weeks and compare each domain, not only the total score.","Повторите тот же опросник через две недели и сравните каждую область, а не только общий балл."),"14 DAYS")
    else:
        card(tr("Measurement","Измерение"),tr("Repeat three real tasks with and without AI; compare time, error rate, confidence and ability to explain the final decision.","Повторите три реальные задачи с ИИ и без него; сравните время, ошибки, уверенность и способность объяснить итоговое решение."),"A/B CONTROL")

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button({"EN":"← Another Questionnaire","RU":"← Другой опросник"}[L]):
        st.session_state.step = "quiz_select"
        st.rerun()
    if c2.button(t("restart")):
        for k in ["p1","p2","quiz","quiz_answers","cog_done","cognitive_results"]:
            st.session_state[k] = None if k in ["p1","p2","quiz","cognitive_results"] else {} if k=="quiz_answers" else False
        st.session_state.step = "landing"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 8: Совместимость пары
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "compat":
    p1 = st.session_state.p1
    p2 = st.session_state.p2
    compat = get_compatibility(p1, p2)
    score = safe_num(compat.get("score"),50)
    raw1,raw2=p1.get("raw",{}),p2.get("raw",{})
    deep = compatibility_analysis(p1,p2,raw1,raw2,L) if raw1 and raw2 else None

    st.markdown('<div class="hero-kicker">TWO CONTROL SYSTEMS · ONE RELATIONSHIP</div>',unsafe_allow_html=True)
    st.title(f"{p1.get('name','P1')} × {p2.get('name','P2')}")
    st.metric(t("compat_score"),f"{score:.0f}%")
    pair_level=(
        tr("low translation cost","низкая цена взаимного перевода") if score>=82 else
        tr("moderate complementarity","умеренная комплементарность") if score>=65 else
        tr("explicit coordination required","нужно явное согласование")
    )
    st.markdown(f'**{tr("Pair pattern","Паттерн пары")}:** {pair_level}')
    st.caption(tr(
        "The score is only a map of architectural distance. Relationship quality depends on the way two systems coordinate load, communication, recovery and decisions.",
        "Балл показывает только архитектурную дистанцию. Качество отношений зависит от того, как две системы согласуют нагрузку, общение, восстановление и решения."
    ))

    if paywall_gate("compatibility","compat_unlocked",PRICES["compatibility"]):
        c1,c2=st.columns(2)
        for col,person in ((c1,p1),(c2,p2)):
            with col:
                person_interp=get_interp(person)
                st.markdown(
                    f'<div class="pair-card"><div class="eyebrow">{TYPE_CONTENT[st.session_state.lang][architecture_type(person,person_interp)][0]}</div>'
                    f'<h3>{person.get("name","")}</h3>'
                    f'<p>{profile_modifier(person,person_interp)}</p></div>',
                    unsafe_allow_html=True
                )
                a,b=st.columns(2)
                a.metric("RS4",f"{safe_num(person.get('rs4')):.1f}")
                b.metric(tr("Tension","Напряжение"),f"{safe_num(person.get('tension')):.1f}")

        architecture,dynamics,protocol,monitoring=st.tabs([
            tr("Pair architecture","Архитектура пары"),tr("Relationship dynamics","Динамика отношений"),
            tr("Behavior protocol","Протокол поведения"),tr("Control & forecast","Контроль и прогноз")])
        with architecture:
            render_pair_rs_radar(p1,p2,tr("Overlaid RS architecture","Совмещённая архитектура RS"))
            st.caption(tr(
                "Both profiles are shown on one scale to make shared structure and real pair asymmetries visible at once.",
                "Оба профиля показаны на одной шкале, чтобы одновременно видеть общую структуру и реальные асимметрии пары."
            ))
            if deep:
                labels={
                    "overload":tr("System load","Нагрузка"),"recovery":tr("Recovery","Восстановление"),
                    "flexibility":tr("Flexibility","Гибкость"),"rigidity":tr("Rigidity","Ригидность"),
                    "transition_cost":tr("Switching cost","Цена переключения"),"emo_cost":tr("Emotional cost","Эмоциональная цена"),
                    "bottleneck":tr("Processing bottleneck","Узкое место"),"autonomic":tr("Autonomic reactivity","Автономная реактивность")}
                rows=[]
                for key,label in labels.items():
                    v1,v2=deep["idx1"][key],deep["idx2"][key]
                    rows.append({tr("Function","Функция"):label,p1.get("name","P1"):round(v1,1),p2.get("name","P2"):round(v2,1),tr("Gap","Разрыв"):round(abs(v1-v2),1)})
                st.dataframe(rows,width="stretch",hide_index=True)
            else:
                render_axes(p1);render_axes(p2)
        with dynamics:
            st.markdown("**"+tr("Individualized pair reading","Индивидуальный разбор пары")+"**")
            for note_title,note_text in compatibility_story(p1,p2,deep,score):
                card(note_title,note_text,"PAIR SIGNATURE")

            items=list(compat.get("dynamics",[]))
            if deep: items+=deep.get("dynamics",[])
            for d in dict.fromkeys(items):
                card(tr("Additional pair mechanism","Дополнительный механизм пары"),d,"ARCHITECTURE → INTERACTION")
            if deep:
                gaps={k:abs(deep["idx1"][k]-deep["idx2"][k]) for k in deep["idx1"]}
                largest=max(gaps,key=gaps.get)
                n1,n2=p1.get("name","P1"),p2.get("name","P2")
                high=n1 if deep["idx1"][largest]>deep["idx2"][largest] else n2
                low=n2 if high==n1 else n1
                card(tr("Largest asymmetry","Главная асимметрия"),tr(
                    f"{labels[largest]} differs by {gaps[largest]:.1f} points. {high} carries the higher value; {low} should not use their own threshold as the norm for both.",
                    f"{labels[largest]} различается на {gaps[largest]:.1f} пункта. Более высокий уровень у {high}; {low} не следует считать собственный порог нормой для обоих."
                ),"PAIR GAP")
        with protocol:
            steps=[
                tr("Before a difficult conversation, each partner states current load from 0 to 10.","Перед трудным разговором каждый называет текущую нагрузку от 0 до 10."),
                tr("Use one issue per conversation: fact → interpretation → feeling → concrete request.","Обсуждайте один вопрос за разговор: факт → интерпретация → чувство → конкретная просьба."),
                tr("Agree on a pause signal and an exact return time; a pause without return increases uncertainty.","Согласуйте сигнал паузы и точное время возврата; пауза без возврата усиливает неопределённость."),
                tr("Do not demand identical recovery speed. Record the time each partner needs after conflict.","Не требуйте одинаковой скорости восстановления. Фиксируйте время, нужное каждому после конфликта."),
                tr("Hold one weekly 25-minute review: what restored us, what overloaded us, what one rule changes next week.","Раз в неделю проводите 25-минутный разбор: что восстановило, что перегрузило, какое одно правило меняем на следующую неделю."),
            ]
            for i,s in enumerate(steps,1): card(f"{i:02d}",s,"PAIR CONTROL")
        with monitoring:
            card(tr("Two-week baseline","Двухнедельный базовый цикл"),tr(
                "Each evening record individual load, relationship tension, sleep quality and recovery. Compare the median of week 1 and week 2.",
                "Каждый вечер записывайте индивидуальную нагрузку, напряжение в паре, качество сна и восстановление. Сравните медианы первой и второй недели."
            ),"FEEDBACK")
            render_space_weather(get_interp(p1))
            st.caption(tr(
                "During forecast active periods, treat any change as a hypothesis: compare both partners with their own quiet-period baseline before changing behavior.",
                "В периоды прогнозируемой активности рассматривайте любое изменение как гипотезу: сравнивайте каждого партнёра с его собственным базовым состоянием в спокойные периоды до изменения поведения."
            ))

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    if st.button(t("restart")):
        for k in ["p1","p2"]:
            st.session_state[k] = None
        st.session_state.step = "landing"
        st.rerun()
