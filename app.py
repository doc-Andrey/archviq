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

APP_VERSION = "ARCHVIQ WEB 4.1 · EXPLAINED PROCESSING SPIRAL / SILSO BASELINE A"
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
:root{
  --bg:#EAF3FB;--panel:#FFFFFF;--panel2:#F4F8FC;--ink:#17324D;--muted:#4C647A;
  --cyan:#245D87;--teal:#0B756F;--gold:#A67525;--orange:#D85C35;--line:rgba(49,88,122,.20);
  --green:#DDF3EC;--yellow:#FFF1CF;--red:#FCE8E1;--dark:#0D1721;
}
html,body,[class*="css"]{font-family:Arial,sans-serif}.stApp{background:radial-gradient(circle at 78% 6%,rgba(100,215,197,.10),transparent 31%),linear-gradient(180deg,var(--bg),#F7FBFE 72%);color:var(--ink)}
.block-container{max-width:1180px;padding-top:1.2rem;padding-bottom:4rem}h1,h2,h3,.brand{font-family:Arial,sans-serif!important;letter-spacing:-.03em}h1{font-size:clamp(2rem,4.3vw,3.7rem)!important;line-height:1.12!important}h2{font-size:clamp(1.7rem,3.7vw,2.8rem)!important}p,li{line-height:1.62}
.kicker{font-family:ui-monospace,monospace;color:var(--cyan);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;margin-bottom:.6rem}.hero-copy{font-size:clamp(1.03rem,2vw,1.31rem);max-width:820px;color:#405C76;line-height:1.62}.hero-accent{color:var(--teal)}
.card{background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(246,250,254,.98));border:1px solid var(--line);border-radius:18px;padding:1.2rem 1.3rem;height:100%;box-shadow:0 16px 55px rgba(23,50,77,.08)}.card h3{font-size:1.04rem;margin:.1rem 0 .55rem}.card p{color:var(--muted);font-size:.92rem;margin:.1rem 0}.card.dark{background:#111B24;color:#F2F6F8;border-color:rgba(255,255,255,.08)}.card.dark p,.card.dark .small{color:#B8C5CF}.card.dark h3{color:#fff}
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
        st.markdown('<div class="brand" style="font-size:1.55rem;font-weight:800">ARCHVIQ<span style="color:#0B756F">.</span></div>', unsafe_allow_html=True)
    with c2:
        st.radio("Language", ["RU", "EN"], format_func=lambda x: "Русский" if x == "RU" else "English", horizontal=True, key="lang", label_visibility="collapsed")
    labels = {
        "home": tr("Home", "Главная"),
        "profile": tr("Free SSN analysis", "Бесплатный SSN-анализ"),
        "method": tr("Processing spiral", "Спираль процессинга"),
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
    render_concept(compact=compact, key="home" if compact else "method")


def render_home():
    left, right = st.columns([1.45, .8], gap="large")
    with left:
        st.markdown(tr('<div class="kicker">DEVELOPMENTAL CYBERNETICS · FREE SSN ANALYTICS</div>', '<div class="kicker">КИБЕРНЕТИКА РАЗВИТИЯ · БЕСПЛАТНАЯ SSN-АНАЛИТИКА</div>'), unsafe_allow_html=True)
        st.markdown(tr('<h1>Not “what type are you?”<br><span class="hero-accent">How does your processing machine work?</span></h1>', '<h1>Не «какой вы тип?»<br><span class="hero-accent">Как работает ваша машина процессинга?</span></h1>'), unsafe_allow_html=True)
        st.markdown(f'<div class="hero-copy">{tr("How do you turn information into a choice, maintain a working rule and revise it after an error? ARCHVIQ explains these operations through a processing spiral. Its SSN analysis proposes model settings and shows what each parameter means and how to check it.", "Как информация превращается в выбор? Что удерживает рабочее правило и когда ошибка заставляет его пересмотреть? ARCHVIQ объясняет эти операции через спираль процессинга. Анализ по SSN предлагает модельные настройки и показывает, что означает каждый параметр и как его проверить.")}</div>', unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(tr("Run free SSN analysis", "Запустить бесплатный SSN-анализ"), type="primary", use_container_width=True): goto("profile")
        with c2:
            if st.button(tr("Understand the spiral first", "Сначала понять спираль"), use_container_width=True): goto("method")
        st.write("")
        evidence_badges()
    with right:
        st.markdown(f'''<div class="card"><div class="kicker">{tr("WHAT YOU RECEIVE", "ЧТО ВЫ ПОЛУЧАЕТЕ")}</div><h3>{tr("An explanation of your calculation", "Расшифровку своего расчёта")}</h3><p>{tr("Each parameter is linked to a spiral operation: its meaning, modeled direction, uncertainty and a question for testing. You can trace its contributing developmental windows.", "Каждый параметр связан с операцией спирали: его смысл, модельное направление, неопределённость и вопрос для проверки. Можно проследить вклад окон развития.")}</p><p><b>{tr("How to use it", "Как этим пользоваться")}</b><br>{tr("Choose one hypothesis, test it in a repeatable task and record whether it fits. The model and measured performance remain separate results.", "Выберите одну гипотезу, проверьте её повторяемой задачей и зафиксируйте совпадение или расхождение. Модель и измеренная работа остаются отдельными результатами.")}</p></div>''', unsafe_allow_html=True)

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
        st.markdown(f'''<div class="card"><div class="offer-tag">EXPERIMENTAL</div><h3>{tr("Somatic regulation", "Соматическая регуляция")}</h3><p>{tr("Research question: can the processing/regulatory architecture be associated with differential vulnerability or reserve in autonomic, metabolic, thyroid, immune-allergic, respiratory and visceral systems?", "Исследовательский вопрос: связана ли архитектура процессинга/регуляции с различиями уязвимости или резерва автономной, метаболической, тиреоидной, иммунно-аллергической, дыхательной и висцеральной систем?")}</p><p><b>{tr("Current status", "Статус")}: {som.get("mapping_status","NOT_CALIBRATED")}</b></p><p>{tr("No disease prediction or diagnosis is generated.", "Прогноз заболеваний и диагнозы не выдаются.")}</p></div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''<div class="card"><div class="offer-tag">EXPERIMENTAL</div><h3>{tr("Psychophysiology / psychosomatics", "Психофизиология / психосоматика")}</h3><p>{tr("Research question: how do salience, hysteresis, re-entry and recovery to H* translate into prolonged autonomic activation or recovery patterns under stress?", "Исследовательский вопрос: как salience, гистерезис, повторный вход и возврат к H* связаны с длительностью автономной активации и восстановлением при стрессе?")}</p><p><b>{tr("Current status", "Статус")}: {psy.get("mapping_status","NOT_CALIBRATED")}</b></p><p>{tr("This is a research branch, not a clinical conclusion.", "Это исследовательская ветка, а не клиническое заключение.")}</p></div>''', unsafe_allow_html=True)


def render_what_next(profile: Dict[str, Any]):
    render_use_cases(profile)
    st.write("")
    c1,c2,c3 = st.columns(3)
    with c1: st.link_button(tr("Cognitive tests / full report", "Когнитивные тесты / полный отчёт"), PRODUCTS["full"], use_container_width=True)
    with c2: st.link_button(tr("Compatibility", "Совместимость"), PRODUCTS["compatibility"], use_container_width=True)
    with c3: st.link_button(tr("Questionnaire work", "Работа с опросниками"), PRODUCTS["full"], use_container_width=True)


def render_result(profile: Dict[str, Any]):
    sub = profile["meta"]["subject"]
    st.markdown(tr('<div class="kicker">FREE · DEVELOPMENTAL SSN ARCHITECTURE</div>', '<div class="kicker">БЕСПЛАТНО · АРХИТЕКТУРА ПО SSN</div>'), unsafe_allow_html=True)
    st.title(f"{sub.get('label','Client')} · {tr('processing architecture', 'архитектура процессинга')}")
    st.markdown(f'<div class="hero-copy">{tr("The result below is a modeled configuration of one recurrent processing machine. It does not infer moral qualities, diagnosis or the content of your beliefs.", "Ниже — модельная конфигурация одной рекуррентной машины обработки информации. Она не выводит моральные качества, диагноз или содержание ваших убеждений.")}</div>', unsafe_allow_html=True)
    st.caption(tr(f"DOB {sub['dob']} · central conception {sub['central_conception']} · gestation {sub['central_conception_to_birth_days']} dpc · uncertainty ±{sub['uncertainty_days']} d", f"Дата рождения {sub['dob']} · центральное зачатие {sub['central_conception']} · срок {sub['central_conception_to_birth_days']} dpc · неопределённость ±{sub['uncertainty_days']} дн"))
    evidence_badges()

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_profile_story(profile)
    with st.expander(tr("Chart: directional shifts in model units", "График: направленные сдвиги в единицах модели")):
        processing_chart(profile)
    with st.expander(tr("Developmental windows and candidate circuits", "Окна развития и возможные нейронные контуры")):
        st.caption(tr("These are mapping hypotheses, not measurements of your brain.", "Это гипотезы привязки, а не измерения вашего мозга."))
        render_brain_map(profile)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    with st.expander(tr("SILSO context: level vs dynamics", "Контекст SILSO: уровень и динамика")):
        render_context_table(profile)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_what_next(profile)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_experimental(profile)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    render_explanation_downloads(profile)
    c1,c2 = st.columns(2)
    with c1:
        st.download_button(tr("Download profile JSON", "Скачать профиль JSON"), json.dumps(profile, ensure_ascii=False, indent=2).encode("utf-8"), "archviq_processing_profile.json", "application/json", use_container_width=True)
    with c2:
        rows = [{"parameter":p["parameter"],"mode":p["mode"],"state_median":p.get("state_median"),"state_min":p.get("state_min"),"state_max":p.get("state_max"),"pressure_median":p.get("pressure_median"),"robustness":p.get("robustness")} for p in profile["processing"]["parameters"]]
        st.download_button(tr("Download parameter CSV", "Скачать параметры CSV"), pd.DataFrame(rows).to_csv(index=False).encode("utf-8"), "archviq_processing_parameters.csv", "text/csv", use_container_width=True)


def render_profile():
    st.markdown(tr('<div class="kicker">FREE · SILSO ARCHITECTURE</div>', '<div class="kicker">БЕСПЛАТНО · АРХИТЕКТУРА ПО SILSO</div>'), unsafe_allow_html=True)
    st.title(tr("Build your processing architecture", "Постройте архитектуру своего процессинга"))
    st.markdown(f'<div class="hero-copy">{tr("Enter birth and gestation information. You will receive model hypotheses about spiral operations, explanations of all parameters and a concrete plan for checking them. Birth-date analysis does not measure your current brain function.", "Укажите дату рождения и сведения о сроке беременности. Вы получите модельные гипотезы об операциях спирали, расшифровку всех параметров и конкретный план их проверки. Анализ по дате не измеряет текущую работу мозга.")}</div>', unsafe_allow_html=True)

    with st.form("profile_form"):
        c1,c2,c3 = st.columns([1.3,1,1])
        with c1: name = st.text_input(tr("Name", "Имя"), value="")
        with c2: dob = st.date_input(tr("Date of birth", "Дата рождения"), value=pd.Timestamp("1985-01-01").date(), min_value=pd.Timestamp("1819-01-01").date(), max_value=pd.Timestamp.today().date())
        sex_labels = {"F": tr("Female", "Женский"), "M": tr("Male", "Мужской")}
        with c3: sex = st.selectbox(tr("Sex", "Пол"), ["F","M"], format_func=sex_labels.get)
        gestation_labels = {"unknown":tr("Unknown — use 266 dpc central estimate", "Неизвестен — центр 266 dpc"),"ctb_days":tr("Known conception-to-birth days", "Известны дни от зачатия до рождения"),"conception":tr("Exact/estimated conception date", "Известна/оценена дата зачатия")}
        mode_label = st.selectbox(tr("Gestation information", "Данные о сроке беременности"), ["unknown","ctb_days","conception"], format_func=gestation_labels.get)
        ctb_days = 266; conception = dob - pd.Timedelta(days=266); unc = 14
        if mode_label == "ctb_days":
            ctb_days = st.number_input(tr("Conception-to-birth days", "Дней от зачатия до рождения"), min_value=203, max_value=300, value=266, step=1)
            unc = st.number_input(tr("Uncertainty ± days", "Неопределённость ± дней"), min_value=0, max_value=30, value=7, step=1)
        elif mode_label == "conception":
            conception = st.date_input(tr("Conception date", "Дата зачатия"), value=dob-pd.Timedelta(days=266), min_value=pd.Timestamp("1818-01-01").date(), max_value=dob)
            unc = st.number_input(tr("Uncertainty ± days", "Неопределённость ± дней"), min_value=0, max_value=30, value=0, step=1)
        else:
            unc = st.number_input(tr("Research uncertainty ± days", "Исследовательская неопределённость ± дней"), min_value=0, max_value=30, value=14, step=1)
        accepted = st.checkbox(tr("I understand that natural EMF causality and brain-circuit mappings are research hypotheses, and this is not medical diagnosis.", "Я понимаю, что причинность естественного ЭМП и привязка к контурам мозга являются исследовательскими гипотезами, а результат не является медицинским диагнозом."), value=True)
        submit = st.form_submit_button(tr("Calculate free architecture", "Рассчитать бесплатную архитектуру"), type="primary", use_container_width=True)

    if submit:
        if not accepted:
            st.error(tr("Please confirm the research notice.", "Подтвердите исследовательское уведомление."))
        else:
            try:
                req_json = _request_json(name, dob, sex, mode_label, int(ctb_days), conception, int(unc))
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
