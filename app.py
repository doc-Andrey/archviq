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

ROOT = Path(__file__).resolve().parent
APP_VERSION = "ARCHVIQ WEB 2.1 · ENGINE 43 v1.0"

PRODUCTS = {
    "gap": "https://osipoff.gumroad.com/l/kdjqsj",
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
  --ink:#17324D;--muted:#4C647A;--cyan:#245D87;--gold:#A67525;
  --line:rgba(49,88,122,.20);--good:#8FE3A2;--danger:#F2A88E;
}
html, body, [class*="css"] {font-family:Arial, sans-serif;}
.stApp{background:radial-gradient(circle at 78% 6%,rgba(100,215,197,.08),transparent 30%),radial-gradient(circle at 10% 20%,rgba(231,180,90,.06),transparent 25%),var(--bg);color:var(--ink)}
.block-container{max-width:1180px;padding-top:1.3rem;padding-bottom:4rem}
h1,h2,h3,.brand{font-family:Arial, sans-serif!important;letter-spacing:-.03em}
h1{font-size:clamp(2rem,4.4vw,3.8rem)!important;line-height:1.12!important;margin-bottom:1rem!important}
h2{font-size:clamp(1.8rem,4vw,3rem)!important;margin-top:1.4rem!important}
p,li{line-height:1.65}
.kicker{font-family:ui-monospace, monospace;color:var(--cyan);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;margin-bottom:.6rem}
.hero-copy{font-size:clamp(1.03rem,2vw,1.35rem);max-width:760px;color:#405C76;line-height:1.6}
.hero-accent{color:var(--gold)}
.card{background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(246,250,254,.96));border:1px solid var(--line);border-radius:18px;padding:1.25rem 1.35rem;height:100%;box-shadow:0 20px 70px rgba(0,0,0,.16)}
.card h3{font-size:1.05rem;margin:.1rem 0 .55rem}.card p{color:var(--muted);font-size:.93rem;margin:.1rem 0}
.metric-card{border-top:2px solid var(--cyan);background:#FFFFFF;border-radius:12px;padding:1rem 1.1rem;margin:.35rem 0}
.metric-number{font:600 1.8rem ui-monospace, monospace;color:var(--ink)}.metric-name{color:var(--cyan);font-weight:600}.metric-note{font-size:.8rem;color:var(--muted)}
.rule{height:1px;background:linear-gradient(90deg,transparent,var(--line),transparent);margin:3rem 0}
.formula{font:500 .9rem/1.75 ui-monospace, monospace;color:#795519;background:#F5F9FD;border-left:3px solid var(--cyan);padding:1rem 1.2rem;border-radius:4px 14px 14px 4px;margin:1rem 0}
.pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:.7rem;margin:1.2rem 0}.pipe div{border:1px solid var(--line);border-radius:14px;padding:1rem;text-align:center;background:#F7FAFD;color:var(--muted);font-size:.84rem}.pipe b{display:block;color:var(--gold);font:500 1.1rem ui-monospace, monospace;margin-bottom:.35rem}
.founder{display:grid;grid-template-columns:minmax(220px,320px) 1fr;gap:2rem;align-items:center}.founder img{width:100%;border-radius:24px;border:1px solid rgba(231,180,90,.35);box-shadow:0 30px 90px rgba(0,0,0,.4)}
.badge{display:inline-block;padding:.28rem .55rem;border:1px solid var(--line);border-radius:999px;color:var(--muted);font:500 .72rem ui-monospace, monospace;margin:.15rem .25rem .15rem 0}
.price-card{background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(246,250,254,.96));border:1px solid var(--line);border-radius:18px;padding:1.15rem;height:340px;box-sizing:border-box}.price{font:600 2rem ui-monospace, monospace;color:var(--gold);margin:.6rem 0}.price-card h3{font-size:1.08rem!important;line-height:1.4;min-height:3rem;margin:0}.price-card p{font-size:.86rem;color:var(--muted)}
.small{font-size:.78rem;color:var(--muted)}
[data-testid="stForm"]{background:#FFFFFF;border:1px solid var(--line);border-radius:18px;padding:1.1rem}
[data-testid="stMetric"]{background:#FFFFFF;border:1px solid var(--line);padding:1rem;border-radius:14px}
[data-testid="stExpander"]{background:#FFFFFF;border:1px solid var(--line);border-radius:14px}
.stButton>button{border-radius:12px;min-height:2.8rem;border:1px solid rgba(231,180,90,.4)}
.stButton>button[kind="primary"]{background:var(--gold);color:#15110A;border:0;font-weight:700}
.stLinkButton>a{border-radius:12px!important}
@media(max-width:800px){.pipe{grid-template-columns:1fr 1fr}.founder{grid-template-columns:1fr}.founder img{max-width:280px}.block-container{padding-left:1rem;padding-right:1rem}}

/* Shared, explicit foregrounds prevent theme inheritance on nested button text. */
.stApp{background-color:var(--bg);background-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI5NjAiIGhlaWdodD0iNzIwIiB2aWV3Qm94PSIwIDAgOTYwIDcyMCI+PGcgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjQUI3RTMyIiBzdHJva2Utd2lkdGg9IjEuMyIgb3BhY2l0eT0iLjE1Ij48cGF0aCBkPSJNMjAgMTMwSDM1ME00MCA0MFYxOTBNNDAgMTQ1QzkwIDE0NSA4MCA2NSAxMzAgOTVTMTg1IDE4MCAyMjUgOTVTMjgwIDE0MCAzNDAgNjAiLz48cGF0aCBkPSJNNjAwIDQ1MEg5MzBNNjIwIDM0MFY1MDBNNjIwIDQ1MEw2NTAgNDUwIDY2NiA0MTAgNjgyIDQ4MCA2OTggNDM1IDcyMCA0NTAgNzUwIDQ1MCA3NzUgMzkwIDc5OCA0ODAgODIwIDQ0NSA5MDAgNDUwIi8+PGNpcmNsZSBjeD0iODAwIiBjeT0iMTMwIiByPSI3NCIvPjxlbGxpcHNlIGN4PSI4MDAiIGN5PSIxMzAiIHJ4PSIxMTAiIHJ5PSIzMiIgdHJhbnNmb3JtPSJyb3RhdGUoLTMwIDgwMCAxMzApIi8+PC9nPjxnIGZpbGw9IiM5QTZDMjIiIG9wYWNpdHk9Ii4xNiIgZm9udC1mYW1pbHk9Ikdlb3JnaWEsc2VyaWYiIGZvbnQtc2l6ZT0iMjMiPjx0ZXh0IHg9IjYwIiB5PSIyNzAiPs6UeCA9IHgodCArIDEpIOKIkiB4KHQpPC90ZXh0Pjx0ZXh0IHg9IjU2NSIgeT0iNTcwIj7Pg8KyID0gzqMoeOG1oiDiiJIgzrwpwrIgLyBuPC90ZXh0Pjx0ZXh0IHg9Ijg1IiB5PSI2NTAiPmYodCkgPSBBIHNpbijPiXQgKyDPhik8L3RleHQ+PC9nPjwvc3ZnPg==");background-repeat:repeat;background-size:960px 720px}
[data-testid="stHeader"]{background:rgba(234,243,251,.96)}
h1,h2,h3,h4,label,[data-testid="stMetricValue"]{color:var(--ink)}
[data-testid="stButton"] button,[data-testid="stLinkButton"] a,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{box-sizing:border-box!important;min-height:54px!important;padding:12px 18px!important;border-radius:12px!important;background:#FFFFFF!important;color:#17324D!important;border:1px solid #7895AC!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important;white-space:normal!important}
[data-testid="stButton"] button p,[data-testid="stLinkButton"] a p,[data-testid="stFormSubmitButton"] button p,[data-testid="stDownloadButton"] button p{font:600 15px/1.35 Arial,sans-serif!important;color:inherit!important;margin:0!important;text-align:center!important;word-break:normal!important}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"],[data-testid="stLinkButton"] a{background:#E4BD72!important;color:#243348!important;border-color:#BD9145!important}
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
    c1, c3 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="brand" style="font-size:1.5rem;font-weight:700">ARCHVIQ<span style="color:#A67525">.</span></div>', unsafe_allow_html=True)
    with c3:
        st.radio("Язык / Language", ["RU", "EN"], format_func=lambda x: "Русский" if x == "RU" else "English", horizontal=True, key="lang", on_change=sync_language)
    c2 = st.container()
    with c2:
        nav_labels = {
            "home": tr("Home", "Главная"),
            "profile": tr("My profile", "Мой профиль"),
            "method": tr("How it works", "Как это работает"),
            "stage2": tr("Deep calibration", "Глубокая калибровка"),
        }
        nav = st.radio(
            "nav",
            options=["home", "profile", "method", "stage2"],
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
        (tr("Architecture snapshot", "Архитектурный профиль"), tr("FREE", "Бесплатно"), tr("Date-linked profile, seven operating axes and timing stability.", "Профиль по дате, семь рабочих осей и устойчивость к неопределённости времени зачатия."), None),
        (tr("Cognitive + GAP", "Когнитивный тест + GAP"), "$12", tr("Reaction, working memory, interference control and complex-rule performance compared with the architecture map.", "Реакция, рабочая память, контроль интерференции и сложные правила — в сравнении с архитектурным профилем."), PRODUCTS["gap"]),
        (tr("Couple compatibility", "Совместимость в паре"), "$19", tr("A questionnaire about your relationship: interaction, shared strengths and potential friction.", "Опросник об отношениях: взаимодействие в паре, общие сильные стороны и возможные разногласия."), PRODUCTS["compatibility"]),
        (tr("Burnout", "Выгорание"), "$19", tr("A questionnaire about current workload, fatigue and recovery.", "Опросник о текущей нагрузке, утомлении и восстановлении."), PRODUCTS["burnout"]),
        (tr("Working with AI", "Работа с ИИ"), "$19", tr("A questionnaire about your approach to working with artificial intelligence.", "Опросник об особенностях вашего взаимодействия с искусственным интеллектом."), PRODUCTS["ai"]),
        (tr("Full Architecture Report", "Полный архитектурный отчёт"), "$39", tr("Integrated profile, cognition, questionnaires and personalized operating strategy.", "Интегрированный профиль, когнитивные показатели, опросники и персональная стратегия работы."), PRODUCTS["full"]),
    ]
    for start in range(0, len(offers), 3):
        cols = st.columns(3)
        for col, (name, price, desc, url) in zip(cols, offers[start:start + 3]):
            with col:
                st.markdown(f'<div class="price-card"><h3>{name}</h3><div class="price">{price}</div><p>{desc}</p></div>', unsafe_allow_html=True)
                if url:
                    st.link_button(f"{name} · {price}", url, use_container_width=True)
                else:
                    if st.button(tr("Build now", "Рассчитать"), key="free_profile", use_container_width=True, type="primary"):
                        goto("profile")
        st.write("")


def render_home():
    left, right = st.columns([1.45, .8], gap="large")
    with left:
        st.markdown(tr('<div class="kicker">DEVELOPMENTAL ARCHITECTURE · ENGINE 43</div>', '<div class="kicker">АРХИТЕКТУРА РАЗВИТИЯ · МОДЕЛЬ 43</div>'), unsafe_allow_html=True)
        st.markdown(tr(
            '<h1>Your neurocognitive<br><span class="hero-accent">architecture.</span></h1>',
            '<h1>Ваша нейрокогнитивная<br><span class="hero-accent">архитектура.</span></h1>'
        ), unsafe_allow_html=True)
        st.markdown(f'<div class="hero-copy">{tr("ARCHVIQ converts the timing of your early developmental environment into a structured neurocognitive architecture profile: how the system allocates resource, switches, locks on a task, controls interference and pays for complex processing. Then the map can be refined with cognitive tests, questionnaires and optional EEG.", "ARCHVIQ превращает временную структуру раннего периода развития в структурированный нейрокогнитивный профиль: как система распределяет ресурс, переключается, фиксируется на задаче, удерживает контроль и какой ценой обрабатывает сложность. Затем карту можно уточнять когнитивными тестами, опросниками и при необходимости ЭЭГ.")}</div>', unsafe_allow_html=True)
        st.write("")
        b1, b2 = st.columns([1,1.1])
        with b1:
            if st.button(tr("Build my profile", "Рассчитать мой профиль"), type="primary", use_container_width=True):
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
            "Today his research lies at the intersection of neurophysiology, EEG, artificial intelligence and computational modeling of individual brain architecture.",
            "Сегодня его исследования находятся на пересечении нейрофизиологии, ЭЭГ, искусственного интеллекта и вычислительного моделирования индивидуальной архитектуры мозга."
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
        st.subheader(tr("Next step: measure the live system", "Следующий шаг: измерить систему сейчас"))
        st.markdown(tr(
            "The architecture layer is most useful when paired with actual performance. Stage 2 measures reaction time, choice control, working memory, Simon interference and complex-rule speed/accuracy. The difference between expected architecture and measured performance becomes the GAP layer.",
            "Архитектурный слой становится наиболее полезным в паре с реальной производительностью. Этап 2 измеряет простую реакцию, выбор, рабочую память, Саймон-интерференцию и скорость/точность сложного правила. Разница между архитектурой и фактической работой становится слоем GAP."
        ))
        if st.button(tr("Open cognitive calibration", "Открыть когнитивную калибровку"), type="primary", use_container_width=True):
            goto("stage2")
    with c2:
        st.link_button(tr("Full Architecture Report · $39", "Полный отчёт · $39"), PRODUCTS["full"], use_container_width=True)
        st.link_button(tr("Cognitive + GAP · $12", "Когнитивный + GAP · $12"), PRODUCTS["gap"], use_container_width=True)

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


def render_stage2():
    st.markdown(tr('<div class="kicker">STEP 2 · LIVE PERFORMANCE</div>', '<div class="kicker">ЭТАП 2 · ТЕКУЩИЕ ПОКАЗАТЕЛИ</div>'), unsafe_allow_html=True)
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
    st.link_button(tr("Get Cognitive + GAP report · $12","Получить Когнитивный тест + GAP · $12"),PRODUCTS["gap"],use_container_width=True)


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
elif st.session_state.page == "method":
    render_method()
elif st.session_state.page == "stage2":
    render_stage2()
else:
    render_home()
footer()
