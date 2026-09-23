from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from profile_engine import compute_profile, export_flat
from interpret_engine import interpret, LABELS
from site_questionnaire import (
    AXES,
    AXIS_SCALE,
    COGNITIVE_FIELDS,
    architecture_gap,
    item_text,
    load_architecture_instrument,
    parse_cognitive_csv,
    scale_label,
    score_architecture_responses,
)

ROOT = Path(__file__).resolve().parent
APP_VERSION = "ARCHVIQ WEB 3.0 · ENGINE 43 v1.0"

PRODUCTS = {
    "compatibility": "https://osipoff.gumroad.com/l/tfmfiw",
    "burnout": "https://osipoff.gumroad.com/l/zfbje",
    "ai": "https://osipoff.gumroad.com/l/tspxvc",
    "full": "https://osipoff.gumroad.com/l/wsxcl",
}

st.set_page_config(
    page_title="ARCHVIQ",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = r"""
<style>
:root{
  --bg:#EAF3FB;--bg2:#E1EDF8;--panel:#FFFFFF;--panel2:#F4F8FC;
  --ink:#17324D;--muted:#4C647A;--cyan:#245D87;--teal:#0B756F;--gold:#A67525;
  --line:rgba(49,88,122,.20);--good:#8FE3A2;--danger:#F2A88E;
}
html, body, [class*="css"] {font-family:Arial, sans-serif;}
.stApp{background:radial-gradient(circle at 78% 6%,rgba(100,215,197,.10),transparent 31%),linear-gradient(180deg,var(--bg),#F6FAFD 72%);color:var(--ink)}
.block-container{max-width:1180px;padding-top:1.3rem;padding-bottom:4rem}
h1,h2,h3,.brand{font-family:Arial, sans-serif!important;letter-spacing:-.03em}
h1{font-size:clamp(2rem,4.4vw,3.8rem)!important;line-height:1.12!important;margin-bottom:1rem!important;overflow:visible!important;padding-bottom:.08em!important}
h2{font-size:clamp(1.8rem,4vw,3rem)!important;margin-top:1.4rem!important}
p,li{line-height:1.65}
.kicker{font-family:ui-monospace, monospace;color:var(--cyan);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;margin-bottom:.6rem}
.hero-copy{font-size:clamp(1.03rem,2vw,1.35rem);max-width:760px;color:#405C76;line-height:1.6}
.hero-accent{color:var(--teal)}
.card{background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(246,250,254,.96));border:1px solid var(--line);border-radius:18px;padding:1.25rem 1.35rem;height:100%;box-shadow:0 20px 70px rgba(0,0,0,.16)}
.card h3{font-size:1.05rem;margin:.1rem 0 .55rem}.card p{color:var(--muted);font-size:.93rem;margin:.1rem 0}
.metric-card{border-top:2px solid var(--cyan);background:#FFFFFF;border-radius:12px;padding:1rem 1.1rem;margin:.35rem 0}
.metric-number{font:600 1.8rem ui-monospace, monospace;color:var(--ink)}.metric-name{color:var(--cyan);font-weight:600}.metric-note{font-size:.8rem;color:var(--muted)}
.rule{height:1px;background:linear-gradient(90deg,transparent,var(--line),transparent);margin:3rem 0}
.formula{font:500 .9rem/1.75 ui-monospace, monospace;color:#795519;background:#F5F9FD;border-left:3px solid var(--cyan);padding:1rem 1.2rem;border-radius:4px 14px 14px 4px;margin:1rem 0}
.pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:.7rem;margin:1.2rem 0}.pipe div{border:1px solid var(--line);border-radius:14px;padding:1rem;text-align:center;background:#F7FAFD;color:var(--muted);font-size:.84rem}.pipe b{display:block;color:var(--gold);font:500 1.1rem ui-monospace, monospace;margin-bottom:.35rem}
.founder{display:grid;grid-template-columns:minmax(220px,320px) 1fr;gap:2rem;align-items:center}.founder img{width:100%;border-radius:24px;border:1px solid rgba(231,180,90,.35);box-shadow:0 30px 90px rgba(0,0,0,.4)}
.badge{display:inline-block;padding:.28rem .55rem;border:1px solid var(--line);border-radius:999px;color:var(--muted);font:500 .72rem ui-monospace, monospace;margin:.15rem .25rem .15rem 0}
.price-card{background:linear-gradient(145deg,rgba(255,255,255,.99),rgba(246,250,254,.98));border:1px solid var(--line);border-radius:18px;padding:1.25rem;box-sizing:border-box;min-height:0}.price-card.featured{border:2px solid rgba(11,117,111,.55);box-shadow:0 16px 45px rgba(23,50,77,.10)}.price{font:700 1.85rem Arial,sans-serif;color:var(--ink);margin:.55rem 0}.price-free{display:inline-block;font:700 .84rem Arial,sans-serif;color:#075D58;background:#D9F3EF;border-radius:999px;padding:.42rem .68rem;margin:.55rem 0}.price-card h3{font-size:1.08rem!important;line-height:1.4;margin:0}.price-card p{font-size:.88rem;color:var(--muted)}.offer-list{padding-left:1.1rem;margin:.65rem 0 0;color:var(--muted);font-size:.86rem}.offer-list li{margin:.25rem 0}.offer-tag{font:700 .68rem ui-monospace,monospace;letter-spacing:.08em;color:var(--teal);text-transform:uppercase;margin-bottom:.6rem}
.small{font-size:.78rem;color:var(--muted)}
[data-testid="stForm"]{background:#FFFFFF;border:1px solid var(--line);border-radius:18px;padding:1.1rem}
[data-testid="stMetric"]{background:#FFFFFF;border:1px solid var(--line);padding:1rem;border-radius:14px}
[data-testid="stExpander"]{background:#FFFFFF;border:1px solid var(--line);border-radius:14px}
.stButton>button{border-radius:12px;min-height:2.8rem;border:1px solid rgba(231,180,90,.4)}
.stButton>button[kind="primary"]{background:var(--teal);color:#FFFFFF;border:0;font-weight:700}
.stLinkButton>a{border-radius:12px!important}
@media(max-width:800px){.pipe{grid-template-columns:1fr 1fr}.founder{grid-template-columns:1fr}.founder img{max-width:280px}.block-container{padding-left:1rem;padding-right:1rem}}

/* Shared, explicit foregrounds prevent theme inheritance on nested button text. */
.stApp{background-color:var(--bg)}
[data-testid="stHeader"]{background:rgba(234,243,251,.96)}
h1,h2,h3,h4,label,[data-testid="stMetricValue"]{color:var(--ink)}
[data-testid="stButton"] button,[data-testid="stLinkButton"] a,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{box-sizing:border-box!important;min-height:54px!important;padding:12px 18px!important;border-radius:12px!important;background:#FFFFFF!important;color:#17324D!important;border:1px solid #7895AC!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important;white-space:normal!important}
[data-testid="stButton"] button p,[data-testid="stLinkButton"] a p,[data-testid="stFormSubmitButton"] button p,[data-testid="stDownloadButton"] button p{font:600 15px/1.35 Arial,sans-serif!important;color:inherit!important;margin:0!important;text-align:center!important;word-break:normal!important}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"]{background:#0B756F!important;color:#FFFFFF!important;border-color:#075D58!important}
[data-testid="stLinkButton"] a{background:#FFFFFF!important;color:#17324D!important;border-color:#7895AC!important}
[data-testid="stButton"] button:hover,[data-testid="stLinkButton"] a:hover{filter:brightness(.97);border-color:#17324D!important}
button:focus-visible,a:focus-visible{outline:3px solid #245D87!important;outline-offset:3px!important}
[data-testid="stRadio"] label{color:#17324D!important}
.formula{overflow-wrap:anywhere}
@media(max-width:800px){.price-card{height:auto;min-height:0}.price-card h3{min-height:0}h1{font-size:2.15rem!important}.hero-copy{font-size:1.05rem}.pipe{grid-template-columns:1fr 1fr}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state.lang = st.query_params.get("lang", "RU").upper()
    if st.session_state.lang not in {"RU", "EN"}:
        st.session_state.lang = "RU"
if "page" not in st.session_state:
    st.session_state.page = "home"
if "profile" not in st.session_state:
    st.session_state.profile = None
if "architecture_questionnaire" not in st.session_state:
    st.session_state.architecture_questionnaire = None
if "cognitive_result" not in st.session_state:
    st.session_state.cognitive_result = None


def tr(en: str, ru: str) -> str:
    return ru if st.session_state.lang == "RU" else en


def goto(page: str):
    st.session_state.page = page
    st.session_state.pending_page = page
    st.rerun()


def sync_language():
    st.query_params["lang"] = st.session_state.lang


def topbar():
    if "pending_page" in st.session_state:
        st.session_state.nav_radio = st.session_state.pop("pending_page")
    c1, c3 = st.columns([3.2, 1.8])
    with c1:
        st.markdown('<div class="brand" style="font-size:1.5rem;font-weight:800;line-height:1.35;padding:.15rem 0;overflow:visible">ARCHVIQ<span style="color:#0B756F">.</span></div>', unsafe_allow_html=True)
    with c3:
        st.radio("Language", ["RU", "EN"], format_func=lambda x: "Русский" if x == "RU" else "English", horizontal=True, key="lang", on_change=sync_language, label_visibility="collapsed")
    c2 = st.container()
    with c2:
        nav_labels = {
            "home": tr("Home", "Главная"),
            "profile": tr("Free analysis", "Бесплатный анализ"),
            "architecture": tr("Questionnaire", "Опросник"),
            "stage2": tr("Cognitive test", "Когнитивный тест"),
            "method": tr("How it works", "Как это работает"),
        }
        nav = st.radio(
            "nav",
            options=["home", "profile", "architecture", "stage2", "method"],
            format_func=nav_labels.get,
            horizontal=True,
            label_visibility="collapsed",
            index=0,
            key="nav_radio",
        )
        if nav != st.session_state.page:
            st.session_state.page = nav
            st.rerun()
    st.markdown('<div style="height:1px;background:rgba(160,190,205,.12);margin:.45rem 0 1.7rem"></div>', unsafe_allow_html=True)


def render_pipeline():
    labels = [
        ("01", tr("Birth date", "Дата рождения")),
        ("02", tr("15 development windows", "15 окон развития")),
        ("03", tr("Daily SILSO dynamics", "Суточная динамика SILSO")),
        ("04", tr("X9 nonlinear cascade", "Нелинейный каскад X9")),
        ("05", tr("Practical operating map", "Практическая карта работы")),
    ]
    html = '<div class="pipe">' + ''.join(f'<div><b>{n}</b>{label}</div>' for n,label in labels) + '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_prices():
    st.markdown(tr('<div class="kicker">ARCHVIQ products</div>', '<div class="kicker">Продукты ARCHVIQ</div>'), unsafe_allow_html=True)
    st.subheader(tr("Choose how deep you want to go", "Выберите глубину анализа"))
    offers = [
        {
            "name": tr("Your architecture: full free start", "Ваша архитектура: полный бесплатный старт"),
            "price": tr("FREE", "Бесплатно"),
            "tag": tr("START HERE", "НАЧНИТЕ ЗДЕСЬ"),
            "items": [
                tr("Engine 43 profile and seven axes", "Профиль модели 43 и семь осей"),
                tr("Architecture questionnaire", "Опросник архитектуры"),
                tr("Cognitive battery and GAP comparison", "Когнитивная батарея и сравнение GAP"),
            ],
            "url": None,
        },
        {"name": tr("Couple compatibility", "Совместимость в паре"), "price": "$19", "tag": tr("PAIR", "ПАРА"), "items": [tr("Interaction architecture", "Архитектура взаимодействия"), tr("Strengths and friction points", "Сильные стороны и зоны трения"), tr("Risk and favorable periods", "Периоды риска и благоприятного взаимодействия")], "url": PRODUCTS["compatibility"]},
        {"name": tr("Burnout", "Выгорание"), "price": "$19", "tag": tr("CURRENT LOAD", "ТЕКУЩАЯ НАГРУЗКА"), "items": [tr("Exhaustion and detachment", "Истощение и отстранение"), tr("Recovery deficit", "Дефицит восстановления"), tr("Architecture–state tension", "Напряжение архитектура–состояние")], "url": PRODUCTS["burnout"]},
        {"name": tr("Working with AI", "Работа с ИИ"), "price": "$19", "tag": tr("HUMAN + AI", "ЧЕЛОВЕК + ИИ"), "items": [tr("Delegation and verification style", "Стиль делегирования и проверки"), tr("Overtrust and passive-acceptance risks", "Риски сверхдоверия и пассивного принятия"), tr("Practical operating rules", "Практические правила работы")], "url": PRODUCTS["ai"]},
        {"name": tr("Complete Architecture Report", "Полный архитектурный отчёт"), "price": "$39", "tag": tr("ALL MODULES", "ВСЕ МОДУЛИ"), "items": [tr("Architecture and cognition", "Архитектура и когнитивные показатели"), tr("All thematic questionnaires", "Все тематические опросники"), tr("Integrated personal strategy", "Интегрированная личная стратегия")], "url": PRODUCTS["full"]},
    ]
    rows = (offers[:2], offers[2:])
    for row in rows:
        cols = st.columns(len(row))
        for col, offer in zip(cols, row):
            with col:
                free = offer["url"] is None
                price_html = f'<div class="price-free">{offer["price"]}</div>' if free else f'<div class="price">{offer["price"]}</div>'
                items_html = ''.join(f'<li>{item}</li>' for item in offer["items"])
                featured = " featured" if free or offer["price"] == "$39" else ""
                st.markdown(f'<div class="price-card{featured}"><div class="offer-tag">{offer["tag"]}</div><h3>{offer["name"]}</h3>{price_html}<ul class="offer-list">{items_html}</ul></div>', unsafe_allow_html=True)
                if offer["url"]:
                    st.link_button(tr(f"Choose · {offer['price']}", f"Выбрать · {offer['price']}"), offer["url"], use_container_width=True)
                else:
                    if st.button(tr("Start free analysis", "Начать бесплатный анализ"), key="free_profile", use_container_width=True, type="primary"):
                        goto("profile")
        st.write("")


def render_home():
    left, right = st.columns([1.45, .8], gap="large")
    with left:
        st.markdown(tr('<div class="kicker">DEVELOPMENTAL ARCHITECTURE · ENGINE 43</div>', '<div class="kicker">АРХИТЕКТУРА РАЗВИТИЯ · МОДЕЛЬ 43</div>'), unsafe_allow_html=True)
        st.markdown(tr(
            '<h1>How does <span class="hero-accent">your brain</span> work?</h1>',
            '<h1>Как работает именно <span class="hero-accent">ваш мозг?</span></h1>'
        ), unsafe_allow_html=True)
        st.markdown(f'<div class="hero-copy">{tr("ARCHVIQ converts the timing of your early developmental environment into a structured neurocognitive architecture profile: how the system allocates resource, switches, locks on a task, controls interference and pays for complex processing. Then the map can be refined with cognitive tests, questionnaires and optional EEG.", "ARCHVIQ превращает временную структуру раннего периода развития в структурированный нейрокогнитивный профиль: как система распределяет ресурс, переключается, фиксируется на задаче, удерживает контроль и какой ценой обрабатывает сложность. Затем карту можно уточнять когнитивными тестами, опросниками и при необходимости ЭЭГ.")}</div>', unsafe_allow_html=True)
        st.write("")
        b1, b2 = st.columns([1,1.1])
        with b1:
            if st.button(tr("Start free analysis", "Начать бесплатный анализ"), type="primary", use_container_width=True):
                goto("profile")
        with b2:
            if st.button(tr("See the calculation logic", "Посмотреть логику расчёта"), use_container_width=True):
                goto("method")
        st.markdown('<div style="margin-top:1.1rem">' + ''.join(f'<span class="badge">{text}</span>' for text in [tr("NO LAG SEARCH", "БЕЗ ПОДБОРА ЛАГОВ"), tr("DAILY SILSO DATA", "СУТОЧНЫЕ ДАННЫЕ SILSO"), tr("15 WINDOWS", "15 ОКОН"), tr("X9 CASCADE", "КАСКАД X9"), tr("TIMING SENSITIVITY", "ЧУВСТВИТЕЛЬНОСТЬ К СРОКУ")]) + '</div>', unsafe_allow_html=True)
    with right:
        st.markdown(f"""
        <div class="card" style="margin-top:1rem">
          <div class="kicker">{tr('What you receive','Что вы получаете')}</div>
          <h3>{tr('A map you can actually use','Карта, которую можно использовать')}</h3>
          <p>{tr('Seven practical axes instead of a one-word personality type. Each result includes sensitivity to conception-date uncertainty, so strong and unstable conclusions are not mixed together.', 'Семь практических осей вместо одного типа личности. Для каждого вывода показывается чувствительность к неопределённости даты зачатия — устойчивые и неустойчивые результаты не смешиваются.')}</p>
          <div class="formula">{tr('RESOURCE · SWITCHING · LOCK · NOVELTY · CONTROL · PROCESSING COST · MATURATION','РЕСУРС · ПЕРЕКЛЮЧЕНИЕ · ФИКСАЦИЯ · НОВИЗНА · КОНТРОЛЬ · ЦЕНА ОБРАБОТКИ · СОЗРЕВАНИЕ')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.markdown(tr('<div class="kicker">ONE SYSTEM · THREE LEVELS</div>', '<div class="kicker">ОДНА СИСТЕМА · ТРИ УРОВНЯ</div>'), unsafe_allow_html=True)
    st.subheader(tr("Start with architecture. Add measurements. Turn it into decisions.", "Начните с архитектуры. Добавьте измерения. Переведите их в решения."))
    cols = st.columns(3)
    blocks = [
        (tr("1 · Architecture", "1 · Архитектура"), tr("The date-linked layer reconstructs a developmental temporal signature from historical daily solar activity across fixed prenatal and early-postnatal windows.", "Слой по дате восстанавливает временную сигнатуру развития по исторической суточной солнечной активности в фиксированных пренатальных и ранних постнатальных окнах.")),
        (tr("2 · Measurement", "2 · Измерение"), tr("Cognitive tasks and questionnaires measure what the system does now: reaction speed, working memory, switching cost, interference control and self-reported load.", "Когнитивные задачи и опросники измеряют, как система работает сейчас: скорость реакции, рабочую память, цену переключения, контроль помех и субъективную нагрузку.")),
        (tr("3 · GAP", "3 · GAP"), tr("The difference between architecture and measured performance is useful information: compensation, training, overload and the operating conditions where you perform best.", "Разница между архитектурой и измеренной работой — полезная информация: компенсация, тренировка, перегрузка и условия, в которых вы работаете лучше всего.")),
    ]
    for col,(title,body) in zip(cols,blocks):
        with col: st.markdown(f'<div class="card"><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_pipeline()
    st.markdown(f'<div class="formula">{tr("DOB → conception ensemble → W0…W5 + N0…P8 → SSN dynamics → phase transitions → X9 cascade → operating axes → cognitive / questionnaire / EEG calibration", "дата рождения → ансамбль дат зачатия → W0…W5 + N0…P8 → динамика SSN → переходы фаз → каскад X9 → рабочие оси → калибровка тестами / опросниками / ЭЭГ")}</div>', unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_prices()

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_founder()


def render_founder():
    photo = ROOT / "assets" / "andrey_osipov.jpg"
    st.markdown(tr('<div class="kicker">FOUNDER</div>', '<div class="kicker">АВТОР ПРОЕКТА</div>'), unsafe_allow_html=True)
    
    c1, c2 = st.columns([.7,1.7], gap="large")
    with c1:
        if photo.exists():
            st.image(str(photo), use_container_width=True)
    with c2:
        st.subheader(tr("Andrey Osipov, MD, PhD", "Андрей Осипов, кандидат медицинских наук"))
        st.markdown(tr("Physician-scientist · Neurophysiology, EEG & AI", "Врач-исследователь · Нейрофизиология, ЭЭГ и ИИ"))
        st.markdown(tr(
            "Graduated from the First Leningrad Medical Institute. Twenty years of clinical practice: 15 years as an obstetrician-gynecologist and seven years as chief physician. Earned his PhD at the Military Medical Academy in Saint Petersburg.",
            "Окончил Первый Ленинградский медицинский институт. 20 лет клинической практики: 15 лет — акушер-гинеколог, 7 лет — главный врач. Защитил кандидатскую диссертацию в Военно-медицинской академии Санкт-Петербурга."
        ))
        st.markdown(tr(
            "His professional background also includes healthcare management and work in the pharmaceutical industry. Today his research lies at the intersection of developmental neurobiology, neurophysiology, EEG, artificial intelligence, cognitive measurement and computational modeling of individual brain architecture.",
            "Профессиональный опыт также включает управление в здравоохранении и работу в фармацевтической отрасли. Сегодня его исследования находятся на пересечении нейробиологии развития, нейрофизиологии, ЭЭГ, искусственного интеллекта, когнитивных измерений и вычислительного моделирования индивидуальной архитектуры мозга."
        ))



def score_chart(profile):
    labels = [LABELS[st.session_state.lang][k] for k in profile["scores"]]
    values = list(profile["scores"].values())
    fig = go.Figure(go.Scatterpolar(
        r=values+[values[0]], theta=labels+[labels[0]], fill="toself",
        line=dict(color="#245D87", width=3), fillcolor="rgba(36,93,135,.16)"
    ))
    fig.update_layout(
        template="plotly_white", height=460, margin=dict(l=40,r=40,t=40,b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(bgcolor="#F4F8FC", radialaxis=dict(range=[0,100],gridcolor="rgba(49,88,122,.20)")),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})


def x9_chart(profile):
    x = profile["x9"]
    names = [k.replace("X_","") for k in x]
    vals = list(x.values())
    fig=go.Figure(go.Bar(x=names,y=vals,marker_color="#A67525"))
    fig.update_layout(template="plotly_white",height=330,margin=dict(l=15,r=15,t=30,b=25),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#F4F8FC",yaxis=dict(range=[0,100],gridcolor="rgba(160,190,205,.12)"),xaxis_title="X9")
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})


def render_result(profile):
    interp = interpret(profile, st.session_state.lang)
    st.markdown(tr('<div class="kicker">YOUR ARCHVIQ PROFILE</div>', '<div class="kicker">ВАШ ПРОФИЛЬ ARCHVIQ</div>'), unsafe_allow_html=True)
    st.title(f"{profile['name']} · {interp['title']}")
    st.markdown(f'<div class="hero-copy">{interp["subtitle"]}</div>', unsafe_allow_html=True)
    st.caption(tr(f"Born {profile['dob']} · Estimated conception {profile['central_conception']}", f"Дата рождения {profile['dob']} · Оценка зачатия {profile['central_conception']}"))

    left,right=st.columns([1,1],gap="large")
    with left: score_chart(profile)
    with right:
        strongest=max(profile["scores"].items(),key=lambda kv:kv[1])
        highest_unc=max(profile["uncertainty"].items(),key=lambda kv:kv[1])
        st.metric(tr("Strongest axis","Самая сильная ось"),LABELS[st.session_state.lang][strongest[0]],f"{strongest[1]:.1f}/100")
        st.metric(tr("Largest timing range","Максимальная чувствительность ко времени"),LABELS[st.session_state.lang][highest_unc[0]],f"±{highest_unc[1]/2:.1f} " + tr("pts", "балла"))
        st.markdown(tr(
            "The timing range shows how much an axis changes across five fixed conception-to-birth assumptions: 252, 259, 266, 273 and 280 days. It is not a confidence trick: unstable timing is shown explicitly.",
            "Диапазон показывает, насколько меняется ось при пяти фиксированных предположениях о сроке от зачатия до рождения: 252, 259, 266, 273 и 280 дней. Неустойчивость не прячется — она показывается отдельно."
        ))

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("Your seven operating axes", "Семь рабочих осей"))
    rows=[interp["items"][i:i+2] for i in range(0,len(interp["items"]),2)]
    for pair in rows:
        cols=st.columns(2)
        for col,item in zip(cols,pair):
            with col:
                rng=item["timing_range"]
                st.markdown(f'<div class="metric-card"><div class="metric-name">{item["label"]}</div><div class="metric-number">{item["value"]:.1f}</div><div class="metric-note">{tr("timing range","диапазон по времени")}: {rng:.1f} {tr("pts", "балла")}</div><p>{item["text"]}</p></div>',unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    c1,c2=st.columns([1.2,.8],gap="large")
    with c1:
        st.subheader(tr("Continue the free analysis", "Продолжите бесплатный анализ"))
        st.markdown(tr(
            "The architecture layer is most useful when paired with actual performance. Stage 2 measures reaction time, choice control, working memory, Simon interference and complex-rule speed/accuracy. The difference between expected architecture and measured performance becomes the GAP layer.",
            "Архитектурный слой становится наиболее полезным в паре с реальной производительностью. Этап 2 измеряет простую реакцию, выбор, рабочую память, Саймон-интерференцию и скорость/точность сложного правила. Разница между архитектурой и фактической работой становится слоем GAP."
        ))
        q1, q2 = st.columns(2)
        with q1:
            if st.button(tr("Architecture questionnaire", "Опросник архитектуры"), type="primary", use_container_width=True):
                goto("architecture")
        with q2:
            if st.button(tr("Cognitive test", "Когнитивный тест"), use_container_width=True):
                goto("stage2")
    with c2:
        st.link_button(tr("Full Architecture Report · $39", "Полный отчёт · $39"), PRODUCTS["full"], use_container_width=True)

    with st.expander(tr("Advanced: X9 cascade", "Продвинутый уровень: каскад X9")):
        x9_chart(profile)
        st.markdown(tr(
            "X9 is the compact nonlinear layer between window dynamics and the practical seven-axis map. It is retained because compact cascade coordinates are useful for later matching with cognitive and EEG outcomes.",
            "X9 — компактный нелинейный слой между динамикой окон и практической картой из семи осей. Он сохраняется как промежуточное представление для последующего сопоставления с когнитивными и ЭЭГ-показателями."
        ))

    flat=pd.DataFrame([export_flat(profile)])
    c1,c2=st.columns(2)
    with c1:
        st.download_button(tr("Download profile CSV","Скачать профиль CSV"),flat.to_csv(index=False).encode("utf-8"),"archviq_profile.csv","text/csv",use_container_width=True)
    with c2:
        payload={k:v for k,v in profile.items() if k!="raw"}
        st.download_button(tr("Download profile JSON","Скачать профиль JSON"),json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8"),"archviq_profile.json","application/json",use_container_width=True)


def render_profile():
    st.markdown(tr('<div class="kicker">STEP 1 · ARCHITECTURE</div>', '<div class="kicker">ЭТАП 1 · АРХИТЕКТУРА</div>'), unsafe_allow_html=True)
    st.title(tr("Build your operating map", "Рассчитайте карту своей системы"))
    st.markdown(f'<div class="hero-copy">{tr("One input starts the calculation: your date of birth. ARCHVIQ reconstructs the relevant historical daily solar-activity sequence, maps it onto fixed developmental windows and runs it through Engine 43.", "Для старта нужен один вход — дата рождения. ARCHVIQ восстанавливает соответствующую историческую суточную последовательность солнечной активности, раскладывает её по фиксированным окнам развития и проводит через модель 43.")}</div>',unsafe_allow_html=True)
    with st.form("profile_form"):
        c1,c2=st.columns([1.3,1])
        with c1:
            name=st.text_input(tr("Name","Имя"),value=st.session_state.profile["name"] if st.session_state.profile else "")
        with c2:
            dob=st.date_input(tr("Date of birth","Дата рождения"),value=pd.Timestamp("1985-01-01").date(),min_value=pd.Timestamp("1819-01-01").date(),max_value=pd.Timestamp.today().date())
        accepted=st.checkbox(tr("I understand this is an analytical profile, not a medical diagnosis.","Я понимаю, что это аналитический профиль, а не медицинский диагноз."),value=True)
        submit=st.form_submit_button(tr("Calculate with Engine 43","Рассчитать модель 43"),type="primary",use_container_width=True)
    if submit:
        if not accepted:
            st.error(tr("Please confirm the notice above.","Подтвердите уведомление выше."))
        else:
            try:
                with st.spinner(tr("Reconstructing developmental windows…","Восстанавливаю окна развития…")):
                    st.session_state.profile=compute_profile(name or tr("Client","Клиент"),dob.isoformat())
            except Exception as e:
                st.error(str(e))
    if st.session_state.profile:
        st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
        render_result(st.session_state.profile)


def render_method():
    st.markdown(tr('<div class="kicker">ENGINE 43 · CALCULATION LOGIC</div>', '<div class="kicker">МОДЕЛЬ 43 · ЛОГИКА РАСЧЁТА</div>'), unsafe_allow_html=True)
    st.title(tr("The model is a chain, not a magic number", "Модель — это цепочка, а не магическое число"))
    st.markdown(f'<div class="hero-copy">{tr("Every client result can be traced back through fixed windows, measured daily solar-activity values, explicit dynamic descriptors and a compact nonlinear cascade. There is no per-client lag search.", "Каждый результат можно проследить назад до фиксированных окон, измеренных суточных значений солнечной активности, явных динамических признаков и компактного нелинейного каскада. Индивидуального подбора лагов нет.")}</div>',unsafe_allow_html=True)
    render_pipeline()

    st.subheader(tr("1. Timing anchor", "1. Временная привязка"))
    st.markdown(tr(
        "The central conception estimate is DOB − 266 days. Because actual gestation varies, ARCHVIQ also recalculates the same profile at 252, 259, 273 and 280 days. The central value stays fixed at 266; neighboring anchors quantify timing sensitivity.",
        "Центральная оценка зачатия — дата рождения − 266 дней. Поскольку реальная длительность беременности различается, ARCHVIQ повторяет тот же расчёт также для 252, 259, 273 и 280 дней. Центральное значение остаётся 266; соседние точки измеряют чувствительность к неопределённости времени."
    ))
    st.markdown(tr('<div class="formula">CTB = {252, 259, 266, 273, 280} days · central = 266 · no client-specific optimization</div>', '<div class="formula">CTB = {252, 259, 266, 273, 280} дней · центр = 266 · без индивидуальной оптимизации</div>'), unsafe_allow_html=True)

    st.subheader(tr("2. Fifteen developmental windows", "2. Пятнадцать окон развития"))
    st.markdown(tr(
        "Prenatal: W0 0–17, W1 18–45, W2 46–73, W3 74–100, W4 101–180, W5 181 days after conception to birth−1. Postnatal: N0 0–29 days, then P1…P8 through day 1095.",
        "Пренатально: W0 0–17, W1 18–45, W2 46–73, W3 74–100, W4 101–180, W5 от 181-го дня после зачатия до дня перед рождением. Постнатально: N0 0–29 дней, затем P1…P8 до 1095-го дня."
    ))

    st.subheader(tr("3. What is measured inside every window", "3. Что считается внутри каждого окна"))
    defs=[
        ("M",tr("mean SSN level","средний уровень SSN")),
        ("A",tr("mean absolute day-to-day activity","средняя абсолютная суточная динамика")),
        ("V",tr("volatility of daily changes","волатильность суточных изменений")),
        ("R",tr("reversal / flip rate","частота разворотов направления")),
        ("D",tr("directional persistence","направленная устойчивость")),
        ("B",tr("signed directional bias","знаковый направленный сдвиг")),
        ("ACC",tr("acceleration magnitude","модуль ускорения")),
        ("JERK",tr("third-order change / jerk","изменение ускорения")),
        ("E",tr("dynamic energy of first differences","динамическая энергия первых разностей")),
    ]
    cols=st.columns(3)
    for i,(code,body) in enumerate(defs):
        with cols[i%3]: st.markdown(f'<div class="card" style="margin:.35rem 0"><h3>{code}</h3><p>{body}</p></div>',unsafe_allow_html=True)

    st.subheader(tr("4. Historical normalization", "4. Историческая нормализация"))
    st.markdown(tr(
        "Raw window descriptors are converted into robust historical Z coordinates using a frozen reference distribution built from the same daily SILSO archive. This lets different windows and metrics enter one cascade on comparable scales.",
        "Сырые признаки окон переводятся в устойчивые исторические Z-координаты по замороженному распределению, построенному на том же суточном архиве SILSO. Это позволяет сравнивать разные окна и признаки в одном масштабе."
    ))

    st.subheader(tr("5. Phases, transitions and X9", "5. Фазы, переходы и X9"))
    st.markdown(tr(
        "Windows are summarized into early prenatal, late prenatal and postnatal phases. The engine also retains phase-to-phase deltas and key local transitions (W1→W2, W2→W3, W4→W5, W5→N0). These feed nine nonlinear coordinates: excitation, sensitivity, stability, integration, flexibility, lability, segregation, hub load and maturation.",
        "Окна сводятся в раннюю пренатальную, позднюю пренатальную и постнатальную фазы. Движок также сохраняет межфазные дельты и ключевые локальные переходы (W1→W2, W2→W3, W4→W5, W5→N0). Они поступают в девять нелинейных координат: возбуждение, чувствительность, стабильность, интеграция, гибкость, лабильность, сегрегация, узловая нагрузка и созревание."
    ))
    st.markdown(tr('<div class="formula">window physics → phase summaries + transitions → X_EXC · X_SENS · X_STAB · X_INTEG · X_FLEX · X_LAB · X_SEGR · X_HUB · X_MAT</div>', '<div class="formula">Динамика окон → фазы и переходы → X_EXC · X_SENS · X_STAB · X_INTEG · X_FLEX · X_LAB · X_SEGR · X_HUB · X_MAT</div>'), unsafe_allow_html=True)

    st.subheader(tr("6. The practical output layer", "6. Практический выход"))
    st.markdown(tr(
        "The X9 cascade is compressed into seven client-facing axes: Resource, Switching, Lock, Novelty, Control, Processing Cost and Maturation. This layer is designed to be compared directly with Stage 2 cognition, questionnaire scores and optional EEG metrics.",
        "Каскад X9 сжимается в семь клиентских осей: Ресурс, Переключение, Фиксация, Новизна, Контроль, Цена обработки и Созревание. Этот слой предназначен для прямого сопоставления со Этап 2, опросниками и при необходимости ЭЭГ."
    ))
    if st.button(tr("Calculate my profile", "Рассчитать мой профиль"),type="primary"):
        goto("profile")


def gap_chart(profile_scores, questionnaire_scores):
    labels = [LABELS[st.session_state.lang][axis] for axis in AXES]
    engine = [profile_scores[axis] for axis in AXES]
    observed = [questionnaire_scores[AXIS_SCALE[axis]] for axis in AXES]
    fig = go.Figure()
    fig.add_trace(go.Bar(name=tr("Engine 43", "Модель 43"), x=labels, y=engine, marker_color="#245D87"))
    fig.add_trace(go.Bar(name=tr("Questionnaire", "Опросник"), x=labels, y=observed, marker_color="#55AFA5"))
    fig.update_layout(
        barmode="group",
        template="plotly_white",
        height=410,
        margin=dict(l=20, r=15, t=25, b=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#F7FAFD",
        yaxis=dict(range=[0, 100], title=tr("Score", "Балл"), gridcolor="rgba(49,88,122,.14)"),
        legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_architecture_questionnaire():
    st.markdown(tr('<div class="kicker">FREE · ARCHITECTURE QUESTIONNAIRE</div>', '<div class="kicker">БЕСПЛАТНО · ОПРОСНИК АРХИТЕКТУРЫ</div>'), unsafe_allow_html=True)
    st.title(tr("How does your architecture show up now?", "Как ваша архитектура проявляется сейчас?"))
    st.markdown(f'<div class="hero-copy">{tr("The questionnaire measures your current expression and the effort used to maintain it. It does not replace Engine 43 or the cognitive test; it creates an independent layer for comparison.", "Опросник измеряет текущее проявление и усилия, которыми вы его поддерживаете. Он не заменяет модель 43 или когнитивный тест, а создаёт независимый слой для сравнения.")}</div>', unsafe_allow_html=True)
    st.info(tr(
        "Answer about your usual work over the last 30 days. The final three sections refer to effort, state and environment over the last 14 days.",
        "Первые шесть разделов описывают обычную работу за последние 30 дней. Последние три — усилия, состояние и среду за последние 14 дней."
    ))
    instrument = load_architecture_instrument()
    anchors = tr(
        ["Not at all like me", "Mostly unlike me", "Partly / sometimes", "Mostly like me", "Very much like me"],
        ["Совсем не похоже", "Скорее не похоже", "Иногда / частично", "Скорее похоже", "Очень похоже"],
    )
    responses = {}
    with st.form("architecture_questionnaire_form"):
        for scale_id, scale in instrument["scales"].items():
            st.subheader(scale_label(scale_id, st.session_state.lang))
            for item in scale["items"]:
                responses[item["id"]] = st.radio(
                    item_text(item, st.session_state.lang),
                    options=[1, 2, 3, 4, 5],
                    index=2,
                    format_func=lambda value, labels=anchors: f"{value} · {labels[value - 1]}",
                    horizontal=True,
                    key=f"arch_item_{item['id']}",
                )
        submitted = st.form_submit_button(tr("Calculate questionnaire profile", "Рассчитать профиль опросника"), type="primary", use_container_width=True)
    if submitted:
        st.session_state.architecture_questionnaire = score_architecture_responses(responses)

    scores = st.session_state.architecture_questionnaire
    if not scores:
        return
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader(tr("Questionnaire result", "Результат опросника"))
    cols = st.columns(3)
    for index, (scale_id, value) in enumerate(scores.items()):
        with cols[index % 3]:
            st.metric(scale_label(scale_id, st.session_state.lang), f"{value:.0f}/100")

    profile = st.session_state.profile
    integrated = {"architecture_questionnaire": scores}
    if profile:
        gaps = architecture_gap(profile["scores"], scores)
        integrated["engine43"] = {k: v for k, v in profile.items() if k != "raw"}
        integrated["architecture_gap"] = gaps
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.subheader(tr("Engine 43 ↔ questionnaire", "Модель 43 ↔ опросник"))
        gap_chart(profile["scores"], scores)
        for axis in AXES:
            row = gaps[axis]
            size = row["absolute_gap"]
            band = tr("close", "близко") if size < 15 else (tr("noticeable gap", "заметный разрыв") if size < 30 else tr("large gap", "большой разрыв"))
            direction = tr("questionnaire above model", "опросник выше модели") if row["signed_gap"] > 0 else tr("questionnaire below model", "опросник ниже модели")
            st.markdown(f"**{LABELS[st.session_state.lang][axis]}:** {row['engine43']:.0f} → {row['questionnaire']:.0f} · {band} ({direction}, {row['signed_gap']:+.0f})")

        effort = scores.get("compensatory_effort", 0)
        state = scores.get("state_interference", 0)
        support = scores.get("context_support", 0)
        if effort >= 65:
            st.warning(tr("Performance may be maintained through high compensatory effort. Interpret a close match with Engine 43 together with the cost of maintaining it.", "Результат может поддерживаться высокими компенсаторными усилиями. Даже близкое совпадение с моделью 43 нужно рассматривать вместе с ценой его поддержания."))
        if state >= 65:
            st.warning(tr("The current state may be suppressing usual performance. Repeat measurement after recovery before drawing stable conclusions.", "Текущее состояние может подавлять обычную производительность. До устойчивых выводов лучше повторить измерение после восстановления."))
        if support < 35:
            st.info(tr("The environment currently provides little support for your preferred operating mode.", "Текущая среда слабо поддерживает ваш предпочтительный режим работы."))
    else:
        st.info(tr("Build your free Engine 43 profile to see the GAP comparison.", "Рассчитайте бесплатный профиль модели 43, чтобы увидеть сравнение GAP."))
        if st.button(tr("Build Engine 43 profile", "Рассчитать профиль модели 43"), type="primary"):
            goto("profile")

    if st.session_state.cognitive_result:
        integrated["cognitive"] = st.session_state.cognitive_result
    st.caption(tr(
        "Pilot research instrument. A gap is not a deficit or diagnosis; it can reflect learning, context, state, compensation or measurement error.",
        "Исследовательская пилотная методика. Разрыв — не дефицит и не диагноз: он может отражать обучение, среду, состояние, компенсацию или ошибку измерения."
    ))
    st.download_button(
        tr("Download integrated free result", "Скачать объединённый бесплатный результат"),
        json.dumps(integrated, ensure_ascii=False, indent=2).encode("utf-8"),
        "archviq_free_integrated_result.json",
        "application/json",
        use_container_width=True,
    )


def render_stage2():
    st.markdown(tr('<div class="kicker">FREE · LIVE PERFORMANCE</div>', '<div class="kicker">БЕСПЛАТНО · ТЕКУЩИЕ ПОКАЗАТЕЛИ</div>'), unsafe_allow_html=True)
    st.title(tr("Measure how the system works now", "Измерьте, как система работает сейчас"))
    st.markdown(f'<div class="hero-copy">{tr("The date-linked layer gives the architecture map. Stage 2 measures current performance. The combination is more useful than either layer alone because it exposes the gap between expected architecture and learned compensation.", "Слой по дате даёт архитектурную карту. Этап 2 измеряет текущую работу. Их сочетание полезнее каждого слоя отдельно, потому что показывает разницу между исходной конфигурацией и сформированной компенсацией.")}</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    for col,title,body in [
        (c1,tr("Speed","Скорость"),tr("Simple reaction and forced choice.","Простая реакция и выбор.")),
        (c2,tr("Control","Контроль"),tr("Working memory and Simon interference.","Рабочая память и Саймон-интерференция.")),
        (c3,tr("Complexity","Сложность"),tr("Complex-rule accuracy and speed.","Точность и скорость сложного правила.")),
    ]:
        with col: st.markdown(f'<div class="card"><h3>{title}</h3><p>{body}</p></div>',unsafe_allow_html=True)
    html_path=ROOT/("cognitive_test_en.html" if st.session_state.lang == "EN" else "cognitive_test.html")
    if html_path.exists():
        st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
        st.info(tr("For best timing accuracy, run the battery on a desktop/laptop with minimal background load. The test downloads a CSV result at the end.","Для точности времени лучше проходить батарею на компьютере с минимальной фоновой нагрузкой. В конце тест скачивает CSV с результатами."))
        components.html(html_path.read_text(encoding="utf-8"),height=1100,scrolling=True)
    else:
        st.error(tr("Test file is missing", "Файл теста отсутствует"))
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("Add the result to your free architecture record", "Добавьте результат в бесплатный архитектурный профиль"))
    uploaded = st.file_uploader(
        tr("Upload the CSV downloaded by the test", "Загрузите CSV, который скачал тест"),
        type=["csv"],
        key="cognitive_upload",
    )
    if uploaded is not None:
        try:
            st.session_state.cognitive_result = parse_cognitive_csv(uploaded)
        except Exception as exc:
            st.error(str(exc))
    cognitive = st.session_state.cognitive_result
    if cognitive:
        st.success(tr("Cognitive result added to the integrated record.", "Когнитивный результат добавлен в объединённую запись."))
        metrics = cognitive["metrics"]
        cols = st.columns(3)
        for index, (field, value) in enumerate(metrics.items()):
            en, ru, unit = COGNITIVE_FIELDS[field]
            shown = f"{value:.0f} ms" if unit == "ms" else f"{value * 100:.0f}%"
            with cols[index % 3]:
                st.metric(ru if st.session_state.lang == "RU" else en, shown)
        st.caption(tr(
            "These are raw task metrics. Until external norms are validated, ARCHVIQ stores them but does not force them into 0–100 architecture axes.",
            "Это сырые показатели задач. До проверки внешних норм ARCHVIQ сохраняет их, но не превращает принудительно в архитектурные оси 0–100."
        ))
        if st.session_state.architecture_questionnaire:
            if st.button(tr("Open integrated GAP result", "Открыть объединённый результат GAP"), type="primary", use_container_width=True):
                goto("architecture")
        else:
            if st.button(tr("Complete the architecture questionnaire", "Пройти опросник архитектуры"), type="primary", use_container_width=True):
                goto("architecture")

    rdm_path = ROOT / "analysis_modules" / "cognitive_tools" / "rdm_perception_test.html"
    if rdm_path.exists() and st.session_state.lang == "RU":
        with st.expander(tr("Research extension: motion-perception RDM", "Исследовательское расширение: восприятие движения RDM")):
            st.markdown(tr(
                "This 8–10 minute task estimates perceptual decision dynamics for research. Its raw EZ-diffusion parameters are not client-facing architecture scores.",
                "Этот тест длительностью 8–10 минут оценивает динамику перцептивного решения для исследования. Его сырые параметры EZ-diffusion не являются клиентскими баллами архитектуры."
            ))
            components.html(rdm_path.read_text(encoding="utf-8"), height=1050, scrolling=True)


def footer():
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    c1,c2=st.columns([1.8,1])
    with c1:
        st.caption(tr(
            "ARCHVIQ is an analytical neurocognitive profiling platform. It is not a medical diagnostic service and does not replace medical or psychological care.",
            "ARCHVIQ — аналитическая платформа нейрокогнитивного профилирования. Это не медицинская диагностика и не замена медицинской или психологической помощи."
        ))
    with c2:
        st.caption(f"{APP_VERSION} · archviq.com")


topbar()
if st.session_state.page == "profile":
    render_profile()
elif st.session_state.page == "architecture":
    render_architecture_questionnaire()
elif st.session_state.page == "method":
    render_method()
elif st.session_state.page == "stage2":
    render_stage2()
else:
    render_home()
footer()
