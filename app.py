from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from archviq import InputValidationError, UnsupportedGestationError, run_site_profile
from archviq.spiral_guide import finite
from archviq.spiral_ui import render_concept, render_profile_story, render_use_cases, render_explanation_downloads
from site_questionnaire import (
    COGNITIVE_FIELDS,
    item_text,
    load_architecture_instrument,
    parse_cognitive_csv,
    scale_label,
    score_architecture_responses,
)

APP_VERSION = "ARCHVIQ WEB 4.2 · SPIRAL / SILSO BASELINE A"
SILSO_PATH = ROOT / "data" / "SN_d_tot_V2.0.txt"
SPIRAL_IMAGE = ROOT / "assets" / "processing_spiral_v4.png"

PRODUCTS = {
    "compatibility": "https://osipoff.gumroad.com/l/tfmfiw",
    "burnout": "https://osipoff.gumroad.com/l/zfbje",
    "ai": "https://osipoff.gumroad.com/l/tspxvc",
    "full": "https://osipoff.gumroad.com/l/wsxcl",
}

st.set_page_config(page_title="ARCHVIQ", page_icon="◉", layout="wide", initial_sidebar_state="collapsed")

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');
:root{
  --bg:#0D1220;--panel:#121A30;--panel2:#17223C;--ink:#ECEEF3;--muted:#AAB3C5;
  --cyan:#6FD8C4;--teal:#6FD8C4;--gold:#E3A34E;--orange:#E3A34E;--line:#2A3655;
  --green:#163D39;--yellow:#443823;--red:#472728;--dark:#0D1220;
}
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif}.stApp{background:radial-gradient(circle at 78% 6%,rgba(111,216,196,.11),transparent 31%),linear-gradient(180deg,var(--bg),#10182B 72%);color:var(--ink)}
.block-container{max-width:1180px;padding-top:1.2rem;padding-bottom:4rem}h1,h2,h3,.brand{font-family:'Newsreader',serif!important;letter-spacing:-.03em}h1{font-size:clamp(2.2rem,4.7vw,4.4rem)!important;font-weight:500!important;line-height:1.05!important}h2{font-size:clamp(1.8rem,3.7vw,3rem)!important;font-weight:500!important}p,li{line-height:1.62}
.kicker{font-family:'IBM Plex Mono',monospace;color:var(--cyan);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;margin-bottom:.6rem}.hero-copy{font-size:clamp(1.03rem,2vw,1.31rem);max-width:820px;color:var(--muted);line-height:1.62}.hero-accent{color:var(--gold);font-style:italic}
.card{background:linear-gradient(145deg,rgba(22,32,58,.98),rgba(15,22,39,.98));border:1px solid var(--line);border-radius:18px;padding:1.2rem 1.3rem;height:100%;box-shadow:0 16px 55px rgba(0,0,0,.18)}.card h3{font-size:1.18rem;margin:.1rem 0 .55rem}.card p{color:var(--muted);font-size:.92rem;margin:.1rem 0}.card.dark{background:#111B24;color:#F2F6F8;border-color:rgba(255,255,255,.08)}.card.dark p,.card.dark .small{color:#B8C5CF}.card.dark h3{color:#fff}
.metric-card{border-top:2px solid var(--cyan);background:#FFFFFF;border-radius:12px;padding:1rem 1.1rem;margin:.35rem 0;border-left:1px solid var(--line);border-right:1px solid var(--line);border-bottom:1px solid var(--line)}.metric-number{font:700 1.65rem ui-monospace,monospace;color:var(--ink)}.metric-name{color:var(--cyan);font-weight:700}.metric-note{font-size:.79rem;color:var(--muted)}
.rule{height:1px;background:linear-gradient(90deg,transparent,var(--line),transparent);margin:2.6rem 0}.formula{font:500 .9rem/1.72 ui-monospace,monospace;color:#795519;background:#F5F9FD;border-left:3px solid var(--cyan);padding:1rem 1.2rem;border-radius:4px 14px 14px 4px;margin:1rem 0;overflow-wrap:anywhere}
.badge{display:inline-block;padding:.28rem .55rem;border:1px solid var(--line);border-radius:999px;color:var(--muted);font:600 .68rem ui-monospace,monospace;margin:.15rem .2rem}.badge.measured{background:#E1F2EA;color:#0B665A}.badge.modeled{background:#E2EDF8;color:#245D87}.badge.hyp{background:#FFF0CC;color:#856011}.badge.exp{background:#FCE8E1;color:#934329}
.pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:.7rem;margin:1.15rem 0}.pipe div{border:1px solid var(--line);border-radius:14px;padding:1rem;text-align:center;background:#F7FAFD;color:var(--muted);font-size:.84rem}.pipe b{display:block;color:var(--gold);font:700 1.05rem ui-monospace,monospace;margin-bottom:.35rem}
.spiral-mini{display:grid;grid-template-columns:1fr;gap:.42rem;margin:1rem 0}.spiral-step{display:flex;gap:.8rem;align-items:center;background:#fff;border:1px solid var(--line);border-radius:14px;padding:.7rem .85rem}.spiral-dot{width:28px;height:28px;border:3px solid var(--orange);border-radius:50%;flex:0 0 28px}.spiral-step b{color:var(--ink);font-size:.9rem}.spiral-step span{color:var(--muted);font-size:.79rem}.spiral-arrow{text-align:center;color:var(--orange);font-weight:800;line-height:.7}
.stage{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem 1.1rem;margin:.45rem 0}.stage h3{font-size:1rem!important;margin:.1rem 0 .35rem}.stage .value{font:700 1.25rem ui-monospace,monospace;color:var(--teal)}.stage .pressure{font:700 1.1rem ui-monospace,monospace;color:var(--gold)}
.window-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem;margin:.4rem 0}.window-card strong{color:var(--teal)}.small{font-size:.79rem;color:var(--muted)}
.price-card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:1.2rem;height:100%}.price-card.featured{border:2px solid rgba(11,117,111,.5)}.price{font:700 1.75rem Arial,sans-serif;color:var(--ink);margin:.45rem 0}.price-free{display:inline-block;font:700 .82rem Arial,sans-serif;color:#075D58;background:#D9F3EF;border-radius:999px;padding:.4rem .65rem;margin:.5rem 0}.offer-tag{font:700 .67rem ui-monospace,monospace;letter-spacing:.08em;color:var(--teal);text-transform:uppercase;margin-bottom:.55rem}.offer-list{padding-left:1.1rem;color:var(--muted);font-size:.86rem}.offer-list li{margin:.24rem 0}
[data-testid="stForm"]{background:#fff;border:1px solid var(--line);border-radius:18px;padding:1.1rem}[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);padding:1rem;border-radius:14px}[data-testid="stExpander"]{background:#fff;border:1px solid var(--line);border-radius:14px}
[data-testid="stButton"] button,[data-testid="stLinkButton"] a,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{box-sizing:border-box!important;min-height:52px!important;padding:11px 16px!important;border-radius:12px!important;background:#fff!important;color:#17324D!important;border:1px solid #7895AC!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important;white-space:normal!important}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"]{background:#0B756F!important;color:#fff!important;border-color:#075D58!important;font-weight:700!important}.founder{display:grid;grid-template-columns:minmax(220px,320px) 1fr;gap:2rem;align-items:center}
@media(max-width:800px){.pipe{grid-template-columns:1fr 1fr}.block-container{padding-left:1rem;padding-right:1rem}.founder{grid-template-columns:1fr}.price-card{height:auto}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

for key, default in {
    "lang": "RU", "page": "home", "profile": None,
    "architecture_questionnaire": None, "cognitive_result": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def tr(en: str, ru: str) -> str:
    return ru if st.session_state.lang == "RU" else en


def goto(page: str):
    st.session_state.page = page
    st.session_state.pending_page = page
    st.rerun()


def topbar():
    if "pending_page" in st.session_state:
        st.session_state.nav_radio = st.session_state.pop("pending_page")
    c1, c2 = st.columns([3.1, 1.2])
    with c1:
        st.markdown('<div class="brand" style="font-size:2.0rem;font-weight:600;letter-spacing:.04em">ARCH<span style="color:#E3A34E">VIQ</span></div><div class="small">developmental dynamics · processing spiral</div>', unsafe_allow_html=True)
    with c2:
        st.radio("Language", ["RU", "EN"], format_func=lambda x: "Русский" if x == "RU" else "English", horizontal=True, key="lang", label_visibility="collapsed")
    labels = {
        "home": tr("Home", "Главная"),
        "profile": tr("Free SSN analysis", "Бесплатный SSN-анализ"),
        "method": tr("The spiral", "Спираль"),
        "architecture": tr("Questionnaires · paid", "Опросники · платно"),
        "stage2": tr("Tests · paid", "Тесты · платно"),
    }
    nav = st.radio("nav", list(labels), format_func=labels.get, horizontal=True, label_visibility="collapsed", key="nav_radio")
    if nav != st.session_state.page:
        st.session_state.page = nav
        st.rerun()
    st.markdown('<div style="height:1px;background:rgba(49,88,122,.14);margin:.45rem 0 1.5rem"></div>', unsafe_allow_html=True)


def evidence_badges():
    st.markdown(
        '<span class="badge measured">MEASURED · SILSO</span>'
        '<span class="badge modeled">MODELED · CASCADE</span>'
        '<span class="badge hyp">HYPOTHESIZED · BRAIN MAP</span>'
        '<span class="badge exp">EXPERIMENTAL · MANIFESTATION</span>',
        unsafe_allow_html=True,
    )


def render_pipeline():
    labels = [
        ("01", tr("Birth / gestation", "Рождение / срок")),
        ("02", tr("5–7 d SSN packets", "5–7-дневные пакеты SSN")),
        ("03", tr("6 developmental windows", "6 окон развития")),
        ("04", tr("Brain → cyber cascade", "Мозг → киберкаскад")),
        ("05", tr("Processing spiral H*", "Спираль процессинга H*")),
    ]
    st.markdown('<div class="pipe">' + ''.join(f'<div><b>{n}</b>{label}</div>' for n, label in labels) + '</div>', unsafe_allow_html=True)


def render_spiral_explainer(compact: bool = False):
    st.markdown(f'<div class="kicker">{tr("THE CENTRAL MODEL", "ЦЕНТРАЛЬНАЯ МОДЕЛЬ")}</div>', unsafe_allow_html=True)
    st.subheader(tr("The processing spiral", "Спираль процессинга"))
    st.markdown(f'<div class="hero-copy">{tr("This is not a personality typology and not a decorative diagram. The spiral is a recurrent computational model of how a brain receives a signal, checks it against reality and memory, keeps or changes a working state, chooses an action, observes the consequence and changes the appropriate level of its internal model.", "Это не типология личности и не декоративная схема. Спираль — рекуррентная вычислительная модель того, как мозг принимает сигнал, сопоставляет его с реальностью и памятью, удерживает или меняет рабочее состояние, выбирает действие, получает его последствия и обновляет нужный уровень внутренней модели.")}</div>', unsafe_allow_html=True)
    steps = [
        ("01", tr("Admission", "Допуск"), tr("Which signals enter the working contour and with what initial weight.", "Какие сигналы входят в рабочий контур и с каким исходным весом.")),
        ("02", tr("Reality and provenance", "Реальность и источник"), tr("The signal is checked against evidence, context and the source; authority cannot override reality.", "Сигнал проверяется по данным, контексту и источнику; авторитет не может заменить реальность.")),
        ("03", tr("State and holding", "Состояние и удержание"), tr("The system compresses information into a workable configuration and decides what must remain stable.", "Система сжимает информацию в рабочую конфигурацию и определяет, что нужно удерживать.")),
        ("04", tr("Decision and action", "Решение и действие"), tr("Separate thresholds determine when to decide, act or wait.", "Отдельные пороги определяют, когда решать, действовать или ждать.")),
        ("05", tr("Error and update", "Ошибка и обновление"), tr("The consequence determines whether to correct the action, the rule or the model itself.", "Последствие определяет, что исправлять: действие, правило или саму модель.")),
        ("06", tr("Recovery and recalibration", "Возврат и перенастройка"), tr("H* is the individual return configuration; offline sleep/memory processes can recalibrate anchors and thresholds.", "H* — индивидуальная конфигурация возврата; сон и память могут перенастраивать якоря и пороги.")),
    ]
    shown = steps[:3] if compact else steps
    for n, title, body in shown:
        st.markdown(f'<div class="stage"><div class="kicker">{n}</div><h3>{title}</h3><div class="small">{body}</div></div>', unsafe_allow_html=True)
    if compact:
        st.caption(tr("The full model also includes separate decision/action/update thresholds, hysteresis, internal re-entry and offline recalibration.", "Полная модель также включает отдельные пороги решения/действия/обновления, гистерезис, внутренний повторный вход и офлайн-перенастройку."))


def render_home():
    left, right = st.columns([1.45, .8], gap="large")
    with left:
        st.markdown(tr('<div class="kicker">ARCHVIQ · DEVELOPMENTAL CYBERNETICS</div>', '<div class="kicker">ARCHVIQ · КИБЕРНЕТИКА РАЗВИТИЯ</div>'), unsafe_allow_html=True)
        st.markdown(tr('<h1>Your <span class="hero-accent">developmental map</span> of information processing</h1>', '<h1>Ваша <span class="hero-accent">карта развития</span> обработки информации</h1>'), unsafe_allow_html=True)
        st.markdown(f'<div class="hero-copy">{tr("ARCHVIQ follows the calendar of early development: raw daily SILSO activity, its percentiles and six developmental windows. The result is not a personality label. It is a model of the parameters through which the brain can admit, test, hold, choose and revise information.", "ARCHVIQ проходит по календарю раннего развития: сырым дневным данным SILSO, их перцентилям и шести окнам развития. Итог — не ярлык личности. Это модель параметров, через которые мозг может допускать, проверять, удерживать, выбирать и пересматривать информацию.")}</div>', unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(tr("Run free SSN analysis", "Запустить бесплатный SSN-анализ"), type="primary", use_container_width=True): goto("profile")
        with c2:
            if st.button(tr("What is the spiral?", "Что такое спираль?"), use_container_width=True): goto("method")
        st.write("")
        evidence_badges()
    with right:
        st.markdown(f'''<div class="card"><div class="kicker">{tr("WHAT THE FREE ANALYSIS SHOWS", "ЧТО ПОКАЖЕТ БЕСПЛАТНЫЙ АНАЛИЗ")}</div><h3>{tr("From developmental time to an explainable model", "От времени развития — к объяснимой модели")}</h3><p>{tr("You see the raw SSN row, its percentiles over your six windows and the resulting operations of the spiral. Every output is marked by its evidence level.", "Вы видите сырой ряд SSN, его перцентили на шести окнах и связанные с ними операции спирали. У каждого вывода указан уровень его доказательности.")}</p><p><b>{tr("Important", "Важно")}</b><br>{tr("The model describes a possible developmental prior. It does not measure your current EEG, predict illness or judge your character.", "Модель описывает возможный prior развития. Она не измеряет вашу текущую ЭЭГ, не предсказывает болезни и не оценивает характер.")}</p></div>''', unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_spiral_explainer(compact=True)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader(tr("What the analysis can and cannot say", "Что анализ может и чего не может сказать"))
    cols = st.columns(4)
    blocks = [
        (tr("Processing", "Процессинг"), tr("Thresholds, persistence, switching, hysteresis, update and recovery.", "Пороги, удержание, переключение, гистерезис, обновление и восстановление.")),
        (tr("Not morality", "Не мораль"), tr("No “killer”, “saint”, “genius” or social-value labels are inferred.", "Никаких ярлыков «убийца», «святой», «гений» или социальной ценности.")),
        (tr("Not diagnosis", "Не диагноз"), tr("Somatic and psychophysiological branches are shown only as experimental research directions.", "Соматика и психофизиология показываются только как экспериментальные исследовательские ветки.")),
        (tr("Testable", "Проверяемо"), tr("The model generates parameters that can be compared with cognitive tasks, questionnaires and biography.", "Модель выдаёт параметры, которые можно сопоставлять с когнитивными задачами, опросниками и биографией.")),
    ]
    for c,(h,b) in zip(cols, blocks):
        with c: st.markdown(f'<div class="card"><h3>{h}</h3><p>{b}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_pipeline()
    st.markdown(tr('<div class="formula">DOB / gestation → SILSO A·V·R·D·B·ACC·JERK·E → 5/7-day packet sequence → W1·W2·W3·F1·F2·F3 → candidate circuits → RS4/v4 spiral parameters → H*</div>', '<div class="formula">Дата рождения / срок → SILSO A·V·R·D·B·ACC·JERK·E → последовательность 5/7-дневных пакетов → W1·W2·W3·F1·F2·F3 → возможные контуры мозга → параметры спирали RS4/v4 → H*</div>'), unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_products()
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_founder()


def render_products():
    st.markdown(tr('<div class="kicker">FREE ARCHITECTURE · PAID MEASUREMENT</div>', '<div class="kicker">АРХИТЕКТУРА БЕСПЛАТНО · ИЗМЕРЕНИЯ ПЛАТНО</div>'), unsafe_allow_html=True)
    st.subheader(tr("SSN analytics are free. Tests and applied work are paid.", "SSN-аналитика бесплатна. Тесты и прикладная работа — платно."))
    offers = [
        {"name": tr("Developmental SSN architecture", "Архитектура по SSN"), "price": tr("FREE", "Бесплатно"), "tag": "SSN", "items": [tr("6 developmental windows", "6 окон развития"), tr("Processing spiral H*", "Спираль процессинга H*"), tr("Brain-circuit hypothesis map", "Карта гипотез по контурам мозга")], "url": None},
        {"name": tr("Cognitive tests + interpretation", "Когнитивные тесты + интерпретация"), "price": tr("PAID", "Платно"), "tag": tr("MEASUREMENT", "ИЗМЕРЕНИЕ"), "items": [tr("Current performance", "Текущая производительность"), tr("Decision / switching / control", "Решение / переключение / контроль"), tr("Architecture ↔ current-state GAP", "GAP архитектура ↔ текущее состояние")], "url": PRODUCTS["full"]},
        {"name": tr("Couple compatibility", "Совместимость в паре"), "price": "$19", "tag": tr("PAIR", "ПАРА"), "items": [tr("Two architectures", "Две архитектуры"), tr("Interaction loops", "Контуры взаимодействия"), tr("Friction and complementarity", "Трение и комплементарность")], "url": PRODUCTS["compatibility"]},
        {"name": tr("Questionnaire work", "Работа с опросниками"), "price": tr("PAID", "Платно"), "tag": tr("CONTEXT", "КОНТЕКСТ"), "items": [tr("Burnout / load", "Выгорание / нагрузка"), tr("Work with AI", "Работа с ИИ"), tr("State and compensation", "Состояние и компенсация")], "url": PRODUCTS["full"]},
    ]
    rows = (offers[:2], offers[2:])
    for row in rows:
        cols = st.columns(2)
        for col, o in zip(cols,row):
            with col:
                free = o["url"] is None
                price = f'<div class="price-free">{o["price"]}</div>' if free else f'<div class="price">{o["price"]}</div>'
                items = ''.join(f'<li>{x}</li>' for x in o["items"])
                st.markdown(f'<div class="price-card{" featured" if free else ""}"><div class="offer-tag">{o["tag"]}</div><h3>{o["name"]}</h3>{price}<ul class="offer-list">{items}</ul></div>', unsafe_allow_html=True)
                if free:
                    if st.button(tr("Start free", "Начать бесплатно"), key="start_free_product", type="primary", use_container_width=True): goto("profile")
                else:
                    st.link_button(tr("Open paid module", "Открыть платный модуль"), o["url"], use_container_width=True)
        st.write("")


def render_founder():
    photo = ROOT / "assets" / "andrey_osipov.jpg"
    st.markdown(tr('<div class="kicker">FOUNDER</div>', '<div class="kicker">АВТОР ПРОЕКТА</div>'), unsafe_allow_html=True)
    c1,c2 = st.columns([.7,1.7], gap="large")
    with c1:
        if photo.exists(): st.image(str(photo), use_container_width=True)
    with c2:
        st.subheader(tr("Andrey Osipov, MD, PhD", "Андрей Осипов, кандидат медицинских наук"))
        st.markdown(tr("Physician-scientist · Neurophysiology, EEG & AI", "Врач-исследователь · Нейрофизиология, ЭЭГ и ИИ"))
        st.markdown(tr("Clinical medicine, healthcare management and pharmaceutical experience; current work focuses on developmental neurobiology, neurophysiology, EEG, cognitive measurement, AI and computational brain architecture.", "Клиническая медицина, управление здравоохранением и фармацевтический опыт; текущая работа — нейробиология развития, нейрофизиология, ЭЭГ, когнитивные измерения, ИИ и вычислительная архитектура мозга."))


def _request_json(name: str, dob, sex: str, gest_mode: str, ctb_days: int, conception, uncertainty: int) -> str:
    gest: Dict[str, Any]
    if gest_mode == "unknown":
        gest = {"mode":"unknown", "uncertainty_days":int(uncertainty)}
    elif gest_mode == "ctb_days":
        gest = {"mode":"ctb_days", "conception_to_birth_days":int(ctb_days), "uncertainty_days":int(uncertainty)}
    else:
        gest = {"mode":"conception", "conception":conception.isoformat(), "uncertainty_days":int(uncertainty)}
    return json.dumps({"dob": dob.isoformat(), "sex": sex, "subject_label": name or "Client", "gestation": gest}, sort_keys=True)


@st.cache_data(show_spinner=False)
def cached_profile(request_json: str) -> Dict[str, Any]:
    request = json.loads(request_json)
    return run_site_profile(request, silso_path=SILSO_PATH)


def _param_map(profile: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {p["parameter"]: p for p in profile.get("processing",{}).get("parameters",[])}


def _direction_text(p: Dict[str, Any]) -> str:
    if p.get("mode") == "pressure_only":
        return tr(f"pressure {p.get('pressure_median',0):.3f}", f"pressure {p.get('pressure_median',0):.3f}")
    v = float(p.get("state_median") or 0.0)
    return f"{v:+.3f}"


def processing_chart(profile: Dict[str, Any]):
    ps = [p for p in profile["processing"]["parameters"] if p.get("mode") == "directional" and finite(p.get("state_median")) is not None]
    ps = sorted(ps, key=lambda p: abs(float(p["state_median"])), reverse=True)[:12]
    labels = [p.get("name_ru") if st.session_state.lang=="RU" else p.get("label_source") for p in ps]
    vals = [float(p["state_median"]) for p in ps]
    fig = go.Figure(go.Bar(x=vals[::-1], y=labels[::-1], orientation="h", marker_color="#245D87"))
    fig.update_layout(template="plotly_white", height=470, margin=dict(l=10,r=20,t=20,b=20), paper_bgcolor="rgba(0,0,0,0)", xaxis_title=tr("model shift (internal units)", "модельный сдвиг (внутренние единицы)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})


@st.cache_data(show_spinner=False)
def silso_daily() -> pd.DataFrame:
    df = pd.read_csv(SILSO_PATH, sep=r"\s+", header=None, usecols=[0, 1, 2, 4], names=["year", "month", "day", "ssn"], engine="python")
    df["date"] = pd.to_datetime(dict(year=df.year, month=df.month, day=df.day), errors="coerce")
    df.loc[df["ssn"] < 0, "ssn"] = float("nan")
    return df[["date", "ssn"]]


def render_ssn_timeline(profile: Dict[str, Any]):
    """Show the actual daily SILSO row and the packet percentiles used by the map."""
    sub = profile["meta"]["subject"]
    conception = pd.Timestamp(sub["central_conception"])
    birth = pd.Timestamp(sub["dob"])
    raw = silso_daily()
    raw = raw[(raw["date"] >= conception + pd.Timedelta(days=14)) & (raw["date"] <= birth)].copy()
    packets = pd.DataFrame(profile.get("physical", {}).get("central_packets", []))
    if packets.empty or raw.empty:
        st.info(tr("The SSN timeline is unavailable for this date range.", "Шкала SSN недоступна для этого диапазона дат."))
        return
    packets["date"] = pd.to_datetime(packets["date_start"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=raw["date"], y=raw["ssn"], mode="lines", name=tr("Daily SSN", "Суточный SSN"), line=dict(color="#E3A34E", width=1.4)))
    fig.add_trace(go.Scatter(x=packets["date"], y=packets["level_raw_pct"], mode="lines+markers", name=tr("SSN level percentile", "Перцентиль уровня SSN"), yaxis="y2", line=dict(color="#6FD8C4", width=2), marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=packets["date"], y=packets["dynamic_load_pct"], mode="lines+markers", name=tr("Dynamics percentile", "Перцентиль динамики"), yaxis="y2", line=dict(color="#AAB3C5", width=1.5, dash="dot"), marker=dict(size=4)))
    windows = [("W1",18,60,"#376D8A"),("W2",61,100,"#4C857D"),("W3",101,140,"#5C7499"),("F1",168,188,"#A67525"),("F2",189,202,"#A35E4E"),("F3",203,int(sub["central_conception_to_birth_days"]),"#7E6191")]
    for label, start, end, color in windows:
        x0=conception+pd.Timedelta(days=start); x1=conception+pd.Timedelta(days=end)
        fig.add_vrect(x0=x0, x1=x1, fillcolor=color, opacity=.18, line_width=0, annotation_text=label, annotation_position="top left", annotation_font_color="#ECEEF3")
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#121A30", legend=dict(orientation="h", y=1.15), yaxis=dict(title=tr("daily SILSO SSN", "суточный SILSO SSN"), gridcolor="#2A3655"), yaxis2=dict(title=tr("percentile", "перцентиль"), range=[0,100], overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"), xaxis=dict(gridcolor="#2A3655"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.caption(tr("Gold is the published daily SILSO number. Green and grey are packet percentiles: where the measured level and local dynamics fall in the historical reference distribution. Coloured bands are the six developmental windows used in this calculation.", "Золотая линия — опубликованный суточный показатель SILSO. Зелёная и серая — перцентили пакетов: место измеренного уровня и локальной динамики в историческом распределении. Цветные полосы — шесть окон развития, использованные в этом расчёте."))



def render_brain_map(profile: Dict[str, Any]):
    brain = profile.get("brain_map", {})
    order = ["W1","W2","W3","F1","F2","F3"]
    for w in order:
        item = brain.get(w)
        if not item: continue
        role = item.get("role_ru", "")
        dpc = item.get("dpc_observed_range", [])
        circuits = item.get("circuits", [])[:4]
        effects = item.get("top_parameter_effects", [])[:4]
        with st.expander(f"{w} · dpc {dpc[0] if dpc else '?'}–{dpc[1] if len(dpc)>1 else '?'} · {role}"):
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("**" + tr("Candidate circuits", "Возможные контуры") + "**")
                for c in circuits:
                    st.markdown(f"- {c.get('label_ru', c.get('circuit'))}: {float(c.get('mean_exposure_median') or 0):.3f}")
            with c2:
                st.markdown("**" + tr("Main modeled parameter effects", "Основные модельные эффекты") + "**")
                for e in effects:
                    st.markdown(f"- {e.get('name_ru',e.get('parameter'))}: Δ {float(e.get('net_delta_median') or 0):+.3f}")
            st.caption(tr("Circuit labels are functional/developmental hypotheses, not measured fetal brain exposure.", "Названия контуров — функциональные/развивающиеся гипотезы, а не измеренное воздействие на мозг плода."))


def render_context_table(profile: Dict[str, Any]):
    rows = profile.get("silso_context",{}).get("window_summary",[])
    if not rows: return
    df = pd.DataFrame(rows)
    keep = [c for c in ["sigma","window","level_raw_pct_median","dyn_cond_pct_median","dyn7_cond_pct_median","dyn_perp_z_median","dyn7_perp_z_median"] if c in df]
    if keep:
        st.dataframe(df[keep], use_container_width=True, hide_index=True)
    st.caption(tr("level is context only. dyn/dyn7 conditioned percentiles compare the local dynamics with historical periods at a similar activity level. This context layer is currently parallel and does not alter the frozen cascade.", "level — только контекст. Условные перцентили dyn/dyn7 сравнивают локальную динамику с историческими периодами при сходном уровне активности. Сейчас этот слой идёт параллельно и не меняет замороженный каскад."))


def render_experimental(profile: Dict[str, Any]):
    st.subheader(tr("Experimental branches: somatic and psychophysiology", "Экспериментальные ветки: соматика и психофизиология"))
    c1,c2 = st.columns(2)
    som = profile.get("experimental",{}).get("somatic",{})
    psy = profile.get("experimental",{}).get("psychophysiology",{})
    with c1:
        st.markdown(f'''<div class="card"><div class="offer-tag">EXPERIMENTAL</div><h3>{tr("Somatic regulation", "Соматическая регуляция")}</h3><p>{tr("Research question: can the processing/regulatory architecture be associated with differential vulnerability or reserve in autonomic, metabolic, thyroid, immune-allergic, respiratory and visceral systems?", "Исследовательский вопрос: связана ли архитектура процессинга/регуляции с различиями уязвимости или резерва автономной, метаболической, тиреоидной, иммунно-аллергической, дыхательной и висцеральной систем?")}</p><p><b>{tr("Research status", "Статус исследования")}: {tr("mapping is being developed; personal medical conclusions require independent clinical validation", "карта находится в разработке; для персональных медицинских выводов нужна независимая клиническая валидация")}</b></p><p>{tr("No disease prediction or diagnosis is generated.", "Прогноз заболеваний и диагнозы не выдаются.")}</p></div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''<div class="card"><div class="offer-tag">EXPERIMENTAL</div><h3>{tr("Psychophysiology / psychosomatics", "Психофизиология / психосоматика")}</h3><p>{tr("Research question: how do salience, hysteresis, re-entry and recovery to H* translate into prolonged autonomic activation or recovery patterns under stress?", "Исследовательский вопрос: как salience, гистерезис, повторный вход и возврат к H* связаны с длительностью автономной активации и восстановлением при стрессе?")}</p><p><b>{tr("Research status", "Статус исследования")}: {tr("a hypothesis for future measurement, not a personal psychosomatic conclusion", "гипотеза для будущих измерений, а не персональное психосоматическое заключение")}</b></p><p>{tr("This is a research branch, not a clinical conclusion.", "Это исследовательская ветка, а не клиническое заключение.")}</p></div>''', unsafe_allow_html=True)


def render_what_next(profile: Dict[str, Any]):
    render_use_cases(profile)
    st.write("")
    c1,c2,c3 = st.columns(3)
    with c1: st.link_button(tr("Cognitive tests / full report", "Когнитивные тесты / полный отчёт"), PRODUCTS["full"], use_container_width=True)
    with c2: st.link_button(tr("Compatibility", "Совместимость"), PRODUCTS["compatibility"], use_container_width=True)
    with c3: st.link_button(tr("Questionnaire work", "Работа с опросниками"), PRODUCTS["full"], use_container_width=True)


def render_result(profile: Dict[str, Any]):
    sub = profile["meta"]["subject"]
    st.markdown(tr('<div class="kicker">ARCHVIQ · YOUR DEVELOPMENTAL MAP</div>', '<div class="kicker">ARCHVIQ · ВАША КАРТА РАЗВИТИЯ</div>'), unsafe_allow_html=True)
    st.title(f"{sub.get('label','Клиент')} · {tr('your SSN development map', 'ваша SSN-карта развития')}")
    st.markdown(f'<div class="hero-copy">{tr("This page first shows the actual SSN row and its historical percentiles over your developmental windows. Only then does it translate this record into the model of the processing spiral. The model is not a personality verdict, diagnosis or measurement of current brain activity.", "Сначала эта страница показывает реальный ряд SSN и его исторические перцентили на ваших окнах развития. Затем переводит эту запись в модель спирали процессинга. Модель не является вердиктом о личности, диагнозом или измерением текущей работы мозга.")}</div>', unsafe_allow_html=True)
    gest = int(sub['central_conception_to_birth_days'])
    birth_note = tr("At term · 40 weeks", "Роды в срок · 40 недель") if gest == 266 else tr(f"Timeline: {gest} days from conception to birth", f"Расчётная шкала: {gest} дней от зачатия до рождения")
    st.caption(tr(f"Date of birth: {sub['dob']} · estimated conception: {sub['central_conception']} · {birth_note}", f"Дата рождения: {sub['dob']} · расчётное зачатие: {sub['central_conception']} · {birth_note}"))
    evidence_badges()

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader(tr("1 · SSN across your six developmental windows", "1 · SSN на шести окнах развития"))
    render_ssn_timeline(profile)
    with st.expander(tr("Window table and candidate circuits", "Таблица окон и возможных контуров")):
        render_context_table(profile)
        st.caption(tr("Candidate circuit labels are developmental hypotheses, not measurements of fetal brain exposure.", "Названия возможных контуров — гипотезы развития, а не измерение воздействия на мозг плода."))
        render_brain_map(profile)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader(tr("2 · What the spiral adds", "2 · Что добавляет спираль"))
    st.markdown(f'<div class="hero-copy">{tr("The spiral is the model that makes the calculation interpretable. It does not reduce the brain to a short sequence; it connects admission, reality testing, persistence, decision, action, error, memory and recalibration in one recurrent mechanism. The values below are modeled settings of that mechanism.", "Спираль — модель, которая делает расчёт интерпретируемым. Она не сводит мозг к короткой цепочке, а связывает допуск, проверку реальности, удержание, решение, действие, ошибку, память и перенастройку в одном рекуррентном механизме. Значения ниже — модельные настройки этого механизма.")}</div>', unsafe_allow_html=True)
    with st.expander(tr("Open the full spiral model", "Открыть полную модель спирали")):
        render_spiral_explainer(compact=False)
    st.subheader(tr("Modeled parameter map", "Карта модельных параметров"))
    processing_chart(profile)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader(tr("3 · Research extensions", "3 · Исследовательские продолжения"))
    render_experimental(profile)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.download_button(tr("Download profile JSON", "Скачать профиль JSON"), json.dumps(profile, ensure_ascii=False, indent=2).encode("utf-8"), "archviq_processing_profile.json", "application/json", use_container_width=True)
    with c2:
        rows = [{"parameter":p["parameter"],"mode":p["mode"],"state_median":p.get("state_median"),"state_min":p.get("state_min"),"state_max":p.get("state_max"),"pressure_median":p.get("pressure_median"),"robustness":p.get("robustness")} for p in profile["processing"]["parameters"]]
        st.download_button(tr("Download parameter CSV", "Скачать параметры CSV"), pd.DataFrame(rows).to_csv(index=False).encode("utf-8"), "archviq_processing_parameters.csv", "text/csv", use_container_width=True)


def render_profile():
    st.markdown(tr('<div class="kicker">FREE · SILSO DEVELOPMENTAL MAP</div>', '<div class="kicker">БЕСПЛАТНО · КАРТА РАЗВИТИЯ ПО SILSO</div>'), unsafe_allow_html=True)
    st.title(tr("Calculate your ARCHVIQ map", "Рассчитайте свою карту ARCHVIQ"))
    st.markdown(f'<div class="hero-copy">{tr("Date of birth anchors the developmental calendar. The term-of-birth answer sets the timeline from conception to birth. The result will show the raw SSN record and percentiles over six windows, then explain their modeled relation to the processing spiral.", "Дата рождения задаёт календарь развития. Ответ о сроке родов устанавливает путь от зачатия до рождения. Итог покажет сырой ряд SSN и перцентили на шести окнах, затем — их модельную связь со спиралью процессинга.")}</div>', unsafe_allow_html=True)

    with st.form("profile_form"):
        c1,c2,c3 = st.columns([1.3,1,1])
        with c1: name = st.text_input(tr("Name", "Имя"), value="")
        with c2: dob = st.date_input(tr("Date of birth", "Дата рождения"), value=pd.Timestamp("1985-01-01").date(), min_value=pd.Timestamp("1819-01-01").date(), max_value=pd.Timestamp.today().date())
        sex_labels = {"F": tr("Female", "Женский"), "M": tr("Male", "Мужской")}
        with c3: sex = st.selectbox(tr("Sex", "Пол"), ["F","M"], format_func=sex_labels.get)
        term_options = [tr("At term · 40 weeks", "В срок · 40 недель"), tr("Earlier than term", "Раньше срока"), tr("Later than term", "Позже срока")]
        term_label = st.radio(tr("Birth timing", "Роды"), term_options, horizontal=True)
        term = {term_options[0]: "term", term_options[1]: "earlier", term_options[2]: "later"}[term_label]
        weeks = 0
        if term != "term":
            weeks = int(st.number_input(tr("How many full weeks?", "На сколько полных недель?"), min_value=1, max_value=12, value=1, step=1))
        ctb_days = 266 - weeks * 7 if term == "earlier" else 266 + weeks * 7 if term == "later" else 266
        conception = dob - pd.Timedelta(days=ctb_days)
        unc = 0
        st.caption(tr(f"Calculation timeline: {ctb_days} days from conception to birth.", f"Расчётная шкала: {ctb_days} дней от зачатия до рождения."))
        accepted = st.checkbox(tr("I understand that natural EMF causality and brain-circuit mappings are research hypotheses, and this is not medical diagnosis.", "Я понимаю, что причинность естественного ЭМП и привязка к контурам мозга являются исследовательскими гипотезами, а результат не является медицинским диагнозом."), value=True)
        submit = st.form_submit_button(tr("Calculate free architecture", "Рассчитать бесплатную архитектуру"), type="primary", use_container_width=True)

    if submit:
        if not accepted:
            st.error(tr("Please confirm the research notice.", "Подтвердите исследовательское уведомление."))
        else:
            try:
                req_json = _request_json(name, dob, sex, "ctb_days", int(ctb_days), conception, int(unc))
                with st.spinner(tr("Running SILSO packets → six windows → brain/cyber cascade → processing spiral…", "Считаю SILSO-пакеты → шесть окон → brain/cyber cascade → спираль процессинга…")):
                    st.session_state.profile = cached_profile(req_json)
            except UnsupportedGestationError as exc:
                st.error(tr("This gestational estimate is too preterm for the current late-fetal cascade. A dedicated extrauterine-maturation layer is required.", "Этот срок слишком недоношенный для текущего позднефетального каскада. Нужен отдельный слой внеутробного созревания."))
                st.caption(str(exc))
            except (InputValidationError, ValueError, FileNotFoundError) as exc:
                st.error(str(exc))
            except Exception as exc:
                st.exception(exc)

    if st.session_state.profile:
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        render_result(st.session_state.profile)


def render_method():
    st.markdown(tr('<div class="kicker">RS4/v4 · GATED RECURRENT COMPRESSION SPIRAL</div>', '<div class="kicker">RS4/v4 · РЕКУРРЕНТНАЯ СПИРАЛЬ С ВОРОТАМИ И СЖАТИЕМ</div>'), unsafe_allow_html=True)
    st.title(tr("The concept behind the analysis", "Концепция, на которой построен анализ"))
    st.markdown(f'<div class="hero-copy">{tr("ARCHVIQ treats the brain as one recurrent information-processing machine, not as a list of personality traits. Each loop admits information, changes state, chooses a goal-dependent response, acts, observes error and updates the appropriate layer.", "ARCHVIQ рассматривает мозг как одну рекуррентную машину обработки информации, а не как список черт личности. Каждый виток допускает информацию, меняет состояние, выбирает зависящий от цели ответ, действует, получает ошибку и обновляет нужный уровень.")}</div>', unsafe_allow_html=True)
    render_spiral_explainer(compact=False)
    with st.expander(tr("Original processing-spiral diagram", "Исходная схема спирали процессинга")):
        if SPIRAL_IMAGE.exists():
            st.image(str(SPIRAL_IMAGE), use_container_width=True)
        st.caption(tr("Anatomical labels are hypotheses, not unique addresses.", "Анатомические подписи — гипотезы, а не однозначные адреса."))

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader(tr("How date-linked analysis enters the spiral", "Как анализ по дате входит в спираль"))
    st.write(tr("The six developmental windows describe when the model receives historical input. The six operation groups describe what the processing circuit does. A window is not a brain layer or a processing stage.", "Шесть окон развития описывают, когда модель получает исторический вход. Шесть групп операций описывают, что делает контур процессинга. Окно не является отделом мозга или этапом обработки информации."))
    render_pipeline()
    st.markdown(tr('<div class="formula">SSN dynamics do not “create a personality”. The working hypothesis is weaker: during sensitive developmental phases, weak environmental dynamics may contribute to functional calibration of gain, time constants, gating, persistence, switching, hysteresis, plasticity/update thresholds and recovery.</div>', '<div class="formula">Динамика SSN не «создаёт личность». Рабочая гипотеза слабее: в чувствительные фазы развития динамика среды может вносить вклад в функциональную калибровку gain, временных констант, gating, удержания, переключения, гистерезиса, порогов пластичности/обновления и восстановления.</div>'), unsafe_allow_html=True)
    evidence_badges()

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader(tr("Why the output is useful", "Зачем нужен итоговый профиль"))
    st.markdown(tr("The H* vector is a baseline hypothesis. It becomes useful when compared with measurements: cognitive tasks, questionnaires, repeated state checks, compatibility or biography. Agreement supports the mapping; disagreement is also informative because it can reflect training, compensation, current state or a wrong model.", "Вектор H* — базовая гипотеза. Он становится полезен при сравнении с измерениями: когнитивными задачами, опросниками, повторными проверками состояния, совместимостью или биографией. Совпадение поддерживает mapping; несовпадение тоже информативно — оно может отражать тренировку, компенсацию, текущее состояние или ошибку модели."))

    if st.button(tr("Calculate my free architecture", "Рассчитать мою бесплатную архитектуру"), type="primary"): goto("profile")


def paid_gate(kind: str):
    st.markdown(tr('<div class="kicker">PAID MEASUREMENT LAYER</div>', '<div class="kicker">ПЛАТНЫЙ СЛОЙ ИЗМЕРЕНИЙ</div>'), unsafe_allow_html=True)
    if kind == "test":
        st.title(tr("Cognitive tests", "Когнитивные тесты"))
        st.markdown(f'<div class="hero-copy">{tr("The SSN architecture is free. Cognitive tasks are a paid measurement layer because they measure the current system and require interpretation against the architecture.", "SSN-архитектура бесплатна. Когнитивные задачи — платный измерительный слой, потому что они измеряют текущую систему и требуют интерпретации относительно архитектуры.")}</div>', unsafe_allow_html=True)
    else:
        st.title(tr("Questionnaire work", "Работа с опросниками"))
        st.markdown(f'<div class="hero-copy">{tr("Questionnaires add current load, context, compensation and subjective state. They are not part of the free SSN calculation.", "Опросники добавляют текущую нагрузку, контекст, компенсацию и субъективное состояние. Они не входят в бесплатный расчёт по SSN.")}</div>', unsafe_allow_html=True)
    st.write("")
    c1,c2 = st.columns(2)
    with c1: st.link_button(tr("Open complete paid report", "Открыть полный платный отчёт"), PRODUCTS["full"], type="primary", use_container_width=True)
    with c2: st.link_button(tr("Compatibility · $19", "Совместимость · $19"), PRODUCTS["compatibility"], use_container_width=True)
    with st.expander(tr("Research / local preview (developer mode)", "Исследовательский / локальный режим разработчика")):
        st.caption(tr("Set ARCHVIQ_PAID_PREVIEW=1 in the server environment to expose the local instruments for development. This is not payment authorization.", "Установите ARCHVIQ_PAID_PREVIEW=1 в окружении сервера, чтобы открыть локальные инструменты для разработки. Это не авторизация оплаты."))


def render_questionnaires():
    paid_gate("questionnaire")
    if os.environ.get("ARCHVIQ_PAID_PREVIEW") != "1": return
    instrument = load_architecture_instrument()
    responses = {}
    anchors = instrument["response_anchors"]["ru" if st.session_state.lang=="RU" else "en"]
    with st.form("architecture_questionnaire_form"):
        for scale_id, scale in instrument["scales"].items():
            st.subheader(scale_label(scale_id, st.session_state.lang))
            for item in scale["items"]:
                responses[item["id"]] = st.radio(item_text(item, st.session_state.lang), options=[1,2,3,4,5], index=2, format_func=lambda value, labels=anchors: f"{value} · {labels[value-1]}", horizontal=True, key=f"arch_item_{item['id']}")
        submitted = st.form_submit_button(tr("Calculate questionnaire", "Рассчитать опросник"), type="primary", use_container_width=True)
    if submitted: st.session_state.architecture_questionnaire = score_architecture_responses(responses)
    if st.session_state.architecture_questionnaire:
        cols = st.columns(3)
        for i,(scale_id,value) in enumerate(st.session_state.architecture_questionnaire.items()):
            with cols[i%3]: st.metric(scale_label(scale_id, st.session_state.lang), f"{value:.0f}/100")
        st.info(tr("This questionnaire is not yet forced into the new RS4/v4 H* vector. A calibrated crosswalk is a separate validation task.", "Этот опросник пока не принудительно переводится в новый вектор H* RS4/v4. Калиброванный crosswalk — отдельная задача валидации."))


def render_tests():
    paid_gate("test")
    if os.environ.get("ARCHVIQ_PAID_PREVIEW") != "1": return
    html_path = ROOT / ("cognitive_test_en.html" if st.session_state.lang=="EN" else "cognitive_test.html")
    if html_path.exists(): components.html(html_path.read_text(encoding="utf-8"), height=1100, scrolling=True)
    uploaded = st.file_uploader(tr("Upload test CSV", "Загрузите CSV теста"), type=["csv"])
    if uploaded:
        try: st.session_state.cognitive_result = parse_cognitive_csv(uploaded)
        except Exception as exc: st.error(str(exc))
    if st.session_state.cognitive_result:
        cols=st.columns(3)
        for i,(field,value) in enumerate(st.session_state.cognitive_result["metrics"].items()):
            en,ru,unit=COGNITIVE_FIELDS[field]; shown=f"{value:.0f} ms" if unit=="ms" else f"{value*100:.0f}%"
            with cols[i%3]: st.metric(ru if st.session_state.lang=="RU" else en, shown)
        st.info(tr("Raw task metrics are preserved. They are not automatically mapped into H* until the measurement calibration is frozen.", "Сырые метрики сохраняются. Они не переводятся автоматически в H*, пока калибровка измерений не заморожена."))


def footer():
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    c1,c2 = st.columns([1.8,1])
    with c1: st.caption(tr("ARCHVIQ is a research/analytical platform. Natural EMF causality is unproven; brain mappings, somatic and psychophysiological branches are hypotheses and do not constitute diagnosis.", "ARCHVIQ — исследовательская/аналитическая платформа. Причинность естественного ЭМП не доказана; карты мозга, соматическая и психофизиологическая ветки являются гипотезами и не являются диагнозом."))
    with c2: st.caption(f"{APP_VERSION} · archviq.com")


topbar()
if st.session_state.page == "profile": render_profile()
elif st.session_state.page == "method": render_method()
elif st.session_state.page == "architecture": render_questionnaires()
elif st.session_state.page == "stage2": render_tests()
else: render_home()
footer()
