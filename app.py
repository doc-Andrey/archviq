from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from profile_engine import compute_profile, export_flat, UnsupportedGestationError, InputValidationError
from site_questionnaire import (
    COGNITIVE_FIELDS,
    item_text,
    load_architecture_instrument,
    parse_cognitive_csv,
    scale_label,
    score_architecture_responses,
)

ROOT = Path(__file__).resolve().parent
APP_VERSION = "ARCHVIQ WEB 4.0 · SPIRAL v4 / SILSO CASCADE"

PRODUCTS = {
    "compatibility": "https://osipoff.gumroad.com/l/tfmfiw",
    "burnout": "https://osipoff.gumroad.com/l/zfbje",
    "ai": "https://osipoff.gumroad.com/l/tspxvc",
    "full": "https://osipoff.gumroad.com/l/wsxcl",
}

# The public site keeps SSN-linked analytics free. Cognitive tests, compatibility
# and questionnaire-based work remain paid modules. Set this only in a private/local
# research deployment if you need to inspect the embedded paid instruments directly.
PAID_RESEARCH_MODE = os.getenv("ARCHVIQ_PAID_RESEARCH_MODE", "0") == "1"

st.set_page_config(page_title="ARCHVIQ", page_icon="◉", layout="wide", initial_sidebar_state="collapsed")

CSS = r"""
<style>
:root{--bg:#EAF3FB;--panel:#FFFFFF;--panel2:#F4F8FC;--ink:#17324D;--muted:#4C647A;--cyan:#245D87;--teal:#0B756F;--gold:#A67525;--line:rgba(49,88,122,.20);--warn:#A9681D}
html,body,[class*="css"]{font-family:Arial,sans-serif}.stApp{background:radial-gradient(circle at 78% 6%,rgba(100,215,197,.10),transparent 31%),linear-gradient(180deg,var(--bg),#F6FAFD 72%);color:var(--ink)}
.block-container{max-width:1180px;padding-top:1.3rem;padding-bottom:4rem}h1,h2,h3,.brand{font-family:Arial,sans-serif!important;letter-spacing:-.03em}h1{font-size:clamp(2rem,4.4vw,3.8rem)!important;line-height:1.12!important}h2{font-size:clamp(1.7rem,3.8vw,2.8rem)!important}p,li{line-height:1.62}
.kicker{font-family:ui-monospace,monospace;color:var(--cyan);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;margin-bottom:.6rem}.hero-copy{font-size:clamp(1.03rem,2vw,1.32rem);max-width:790px;color:#405C76;line-height:1.6}.hero-accent{color:var(--teal)}
.card{background:linear-gradient(145deg,rgba(255,255,255,.97),rgba(246,250,254,.97));border:1px solid var(--line);border-radius:18px;padding:1.25rem 1.35rem;height:100%;box-shadow:0 12px 42px rgba(23,50,77,.08)}.card h3{font-size:1.06rem;margin:.1rem 0 .55rem}.card p{color:var(--muted);font-size:.93rem;margin:.1rem 0}.rule{height:1px;background:linear-gradient(90deg,transparent,var(--line),transparent);margin:2.6rem 0}
.badge{display:inline-block;padding:.28rem .55rem;border:1px solid var(--line);border-radius:999px;color:var(--muted);font:500 .72rem ui-monospace,monospace;margin:.15rem .25rem .15rem 0}.badge.measured{background:#E7F6EF;color:#126645}.badge.modeled{background:#EAF1FB;color:#245D87}.badge.hyp{background:#FFF3DF;color:#865C17}.badge.exp{background:#F7EAF9;color:#6E3579}
.pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:.7rem;margin:1.2rem 0}.pipe div{border:1px solid var(--line);border-radius:14px;padding:1rem;text-align:center;background:#F7FAFD;color:var(--muted);font-size:.84rem}.pipe b{display:block;color:var(--gold);font:500 1.1rem ui-monospace,monospace;margin-bottom:.35rem}
.price-card{background:#FFF;border:1px solid var(--line);border-radius:18px;padding:1.25rem;min-height:0}.price-card.featured{border:2px solid rgba(11,117,111,.55);box-shadow:0 16px 45px rgba(23,50,77,.10)}.price{font:700 1.85rem Arial,sans-serif;color:var(--ink);margin:.55rem 0}.price-free{display:inline-block;font:700 .84rem Arial,sans-serif;color:#075D58;background:#D9F3EF;border-radius:999px;padding:.42rem .68rem;margin:.55rem 0}.offer-list{padding-left:1.1rem;color:var(--muted);font-size:.86rem}.offer-tag{font:700 .68rem ui-monospace,monospace;letter-spacing:.08em;color:var(--teal);text-transform:uppercase;margin-bottom:.6rem}
.formula{font:500 .9rem/1.75 ui-monospace,monospace;color:#795519;background:#F5F9FD;border-left:3px solid var(--cyan);padding:1rem 1.2rem;border-radius:4px 14px 14px 4px;margin:1rem 0;overflow-wrap:anywhere}
[data-testid="stForm"]{background:#FFF;border:1px solid var(--line);border-radius:18px;padding:1.1rem}[data-testid="stMetric"]{background:#FFF;border:1px solid var(--line);padding:1rem;border-radius:14px}[data-testid="stExpander"]{background:#FFF;border:1px solid var(--line);border-radius:14px}
[data-testid="stButton"] button,[data-testid="stLinkButton"] a,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{box-sizing:border-box!important;min-height:52px!important;padding:11px 18px!important;border-radius:12px!important;background:#FFF!important;color:#17324D!important;border:1px solid #7895AC!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important;white-space:normal!important}[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"]{background:#0B756F!important;color:#FFF!important;border-color:#075D58!important}
@media(max-width:800px){.pipe{grid-template-columns:1fr 1fr}.block-container{padding-left:1rem;padding-right:1rem}h1{font-size:2.15rem!important}.hero-copy{font-size:1.05rem}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

for key, value in {"lang":"RU","page":"home","profile":None,"architecture_questionnaire":None,"cognitive_result":None}.items():
    if key not in st.session_state:
        st.session_state[key] = value


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
        st.markdown('<div class="brand" style="font-size:1.5rem;font-weight:800">ARCHVIQ<span style="color:#0B756F">.</span></div>', unsafe_allow_html=True)
    with c3:
        st.radio("Language", ["RU", "EN"], format_func=lambda x: "Русский" if x == "RU" else "English", horizontal=True, key="lang", on_change=sync_language, label_visibility="collapsed")
    nav_labels = {
        "home": tr("Home", "Главная"),
        "profile": tr("Free SSN analysis", "Бесплатный SSN-анализ"),
        "architecture": tr("Questionnaires · paid", "Опросники · платно"),
        "stage2": tr("Tests · paid", "Тесты · платно"),
        "method": tr("How it works", "Как это работает"),
    }
    nav = st.radio("nav", options=list(nav_labels), format_func=nav_labels.get, horizontal=True, label_visibility="collapsed", key="nav_radio")
    if nav != st.session_state.page:
        st.session_state.page = nav
        st.rerun()
    st.markdown('<div style="height:1px;background:rgba(160,190,205,.12);margin:.45rem 0 1.7rem"></div>', unsafe_allow_html=True)


def evidence_badges():
    st.markdown(
        '<span class="badge measured">MEASURED · SILSO</span>'
        '<span class="badge modeled">MODELED · CASCADE</span>'
        '<span class="badge hyp">HYPOTHESIZED · BRAIN MAP</span>'
        '<span class="badge exp">EXPERIMENTAL · SOMATIC / PSYCHOPHYSIOLOGY</span>',
        unsafe_allow_html=True,
    )


def render_pipeline():
    labels = [
        ("01", tr("Birth date + gestation", "Дата рождения + срок")),
        ("02", tr("W1–W3 + F1–F3", "W1–W3 + F1–F3")),
        ("03", tr("5/7-day SILSO dynamics", "5/7-дневная динамика SILSO")),
        ("04", tr("Brain → Spiral cascade", "Мозг → каскад Спирали")),
        ("05", tr("Explainable profile", "Объяснимый профиль")),
    ]
    st.markdown('<div class="pipe">'+''.join(f'<div><b>{n}</b>{label}</div>' for n,label in labels)+'</div>', unsafe_allow_html=True)


def render_prices():
    st.markdown(tr('<div class="kicker">ARCHVIQ products</div>', '<div class="kicker">Продукты ARCHVIQ</div>'), unsafe_allow_html=True)
    st.subheader(tr("SSN analytics are free. Measurements and applied work are paid.", "SSN-аналитика бесплатна. Измерения и прикладная работа — платные."))
    offers = [
        {
            "name": tr("Developmental SSN / cyber-architecture analysis", "Анализ SSN / кибер-архитектуры развития"),
            "price": tr("FREE", "Бесплатно"), "tag": tr("CORE ANALYTICS", "БАЗОВАЯ АНАЛИТИКА"),
            "items": [
                tr("Six developmental windows and 5/7-day packets", "Шесть окон развития и пакеты 5/7 дней"),
                tr("SILSO percentiles, cascade and hysteresis", "Перцентили SILSO, каскад и гистерезис"),
                tr("Brain/spiral map + experimental somatic branches", "Карта мозга/спирали + экспериментальные соматические ветки"),
            ], "url": None,
        },
        {"name":tr("Couple compatibility", "Совместимость в паре"),"price":"$19","tag":tr("PAID", "ПЛАТНО"),"items":[tr("Interaction architecture", "Архитектура взаимодействия"),tr("Strengths and friction", "Сильные стороны и зоны трения"),tr("Pair interpretation", "Интерпретация пары")],"url":PRODUCTS["compatibility"]},
        {"name":tr("Tests and questionnaires", "Тесты и опросники"),"price":tr("PAID", "Платно"),"tag":tr("MEASUREMENT", "ИЗМЕРЕНИЕ"),"items":[tr("Cognitive tasks", "Когнитивные тесты"),tr("Architecture / state questionnaires", "Опросники архитектуры / состояния"),tr("GAP interpretation", "Интерпретация GAP")],"url":PRODUCTS["full"]},
        {"name":tr("Complete applied report", "Полный прикладной отчёт"),"price":"$39","tag":tr("ALL MODULES", "ВСЕ МОДУЛИ"),"items":[tr("Free SSN architecture + paid measurements", "Бесплатная SSN-архитектура + платные измерения"),tr("Integrated interpretation", "Интегрированная интерпретация"),tr("Personal operating strategy", "Персональная стратегия работы")],"url":PRODUCTS["full"]},
    ]
    for row in (offers[:2], offers[2:]):
        cols = st.columns(len(row))
        for col, offer in zip(cols,row):
            with col:
                free = offer["url"] is None
                price_html = f'<div class="price-free">{offer["price"]}</div>' if free else f'<div class="price">{offer["price"]}</div>'
                st.markdown(f'<div class="price-card{" featured" if free else ""}"><div class="offer-tag">{offer["tag"]}</div><h3>{offer["name"]}</h3>{price_html}<ul class="offer-list">'+''.join(f'<li>{x}</li>' for x in offer["items"])+"</ul></div>", unsafe_allow_html=True)
                if free:
                    if st.button(tr("Start free SSN analysis", "Начать бесплатный SSN-анализ"), key="free_ssn", use_container_width=True, type="primary"):
                        goto("profile")
                else:
                    st.link_button(tr("Open paid module", "Открыть платный модуль"), offer["url"], use_container_width=True)
        st.write("")


def render_home():
    left,right=st.columns([1.45,.8],gap="large")
    with left:
        st.markdown(tr('<div class="kicker">DEVELOPMENTAL CYBER-ARCHITECTURE · SILSO</div>','<div class="kicker">КИБЕР-АРХИТЕКТУРА РАЗВИТИЯ · SILSO</div>'),unsafe_allow_html=True)
        st.markdown(tr('<h1>How does <span class="hero-accent">your processing loop</span> work?</h1>','<h1>Как работает <span class="hero-accent">ваш вычислительный контур?</span></h1>'),unsafe_allow_html=True)
        st.markdown(f'<div class="hero-copy">{tr("ARCHVIQ uses the frozen daily SILSO archive bundled with the site. It reconstructs 5/7-day solar-dynamics packets across six prenatal windows, propagates them through an experimental developmental brain map, and expresses the result as parameters of the Processing Spiral. The SSN-linked analysis is free.","ARCHVIQ использует замороженный ежедневный архив SILSO, который лежит прямо в репозитории сайта. Он восстанавливает 5/7-дневные пакеты солнечной динамики в шести пренатальных окнах, проводит их через экспериментальную карту развивающихся контуров мозга и переводит в параметры Спирали процессинга. Аналитика по SSN бесплатна.")}</div>',unsafe_allow_html=True)
        st.write("")
        c1,c2=st.columns(2)
        with c1:
            if st.button(tr("Start free analysis", "Начать бесплатный анализ"), type="primary", use_container_width=True): goto("profile")
        with c2:
            if st.button(tr("See calculation logic", "Посмотреть логику расчёта"), use_container_width=True): goto("method")
        st.write(""); evidence_badges()
    with right:
        st.markdown(f'<div class="card"><div class="kicker">{tr("What is free","Что бесплатно")}</div><h3>{tr("Full SSN-linked developmental analysis","Полный анализ развития по SSN")}</h3><p>{tr("Physical packets, percentiles, six windows, brain/circuit hypotheses, Processing Spiral parameters, uncertainty, and explicitly experimental somatic / psychophysiological branches.","Физические пакеты, перцентили, шесть окон, гипотезы по контурам мозга, параметры Спирали процессинга, неопределённость и явно экспериментальные ветки соматики / психофизиологии.")}</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.markdown(tr('<div class="kicker">ONE SYSTEM · THREE LEVELS</div>','<div class="kicker">ОДНА СИСТЕМА · ТРИ УРОВНЯ</div>'),unsafe_allow_html=True)
    st.subheader(tr("Architecture first. Measurements second. Applied interpretation third.","Сначала архитектура. Затем измерения. Затем прикладная интерпретация."))
    cols=st.columns(3)
    blocks=[
        (tr("1 · Free architecture","1 · Бесплатная архитектура"),tr("Date-linked SILSO dynamics and the developmental Processing Spiral profile.","Динамика SILSO по дате и профиль Спирали процессинга развития.")),
        (tr("2 · Paid measurements","2 · Платные измерения"),tr("Cognitive tests and questionnaires measure current performance and self-reported state.","Когнитивные тесты и опросники измеряют текущую работу и самоописание состояния.")),
        (tr("3 · Paid applied work","3 · Платная прикладная работа"),tr("Compatibility, GAP and integrated reports connect architecture with measured behavior.","Совместимость, GAP и интегрированные отчёты связывают архитектуру с измеренным поведением.")),
    ]
    for col,(title,body) in zip(cols,blocks):
        with col: st.markdown(f'<div class="card"><h3>{title}</h3><p>{body}</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    render_pipeline(); st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    render_prices(); st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    render_founder()


def render_founder():
    photo=ROOT/"assets"/"andrey_osipov.jpg"
    st.markdown(tr('<div class="kicker">FOUNDER</div>','<div class="kicker">АВТОР ПРОЕКТА</div>'),unsafe_allow_html=True)
    c1,c2=st.columns([.7,1.7],gap="large")
    with c1:
        if photo.exists(): st.image(str(photo),use_container_width=True)
    with c2:
        st.subheader(tr("Andrey Osipov, MD, PhD","Андрей Осипов, кандидат медицинских наук"))
        st.markdown(tr("Physician-scientist · developmental neurophysiology, computational modeling & AI","Врач-исследователь · нейрофизиология развития, вычислительное моделирование и ИИ"))
        st.markdown(tr("Graduated from the First Leningrad Medical Institute. Clinical and management experience includes obstetrics and gynecology, chief-physician work, research and pharmaceutical management.","Окончил Первый Ленинградский медицинский институт. Клинический и управленческий опыт включает акушерство и гинекологию, работу главным врачом, исследования и фармацевтический менеджмент."))
        st.markdown(tr("ARCHVIQ is an independent experimental research project. The current site separates measured SILSO data, modeled cascade outputs, hypothesized brain mappings and experimental downstream interpretations.","ARCHVIQ — независимый экспериментальный исследовательский проект. Текущий сайт разделяет измеренные данные SILSO, модельные результаты каскада, гипотезы по мозговым контурам и экспериментальные нисходящие интерпретации."))


def _param_chart(parameters):
    rows=[p for p in parameters if p.get("mode")=="directional" and p.get("state_median") is not None]
    rows=sorted(rows,key=lambda p:abs(float(p.get("state_median") or 0)),reverse=True)[:14]
    if not rows: return
    rows=list(reversed(rows))
    fig=go.Figure(go.Bar(x=[float(p["state_median"]) for p in rows],y=[p.get("name_ru") or p["parameter"] for p in rows],orientation="h"))
    fig.add_vline(x=0,line_width=1,line_dash="dash")
    fig.update_layout(height=520,margin=dict(l=10,r=10,t=30,b=20),xaxis_title=tr("Internal model calibration (0 = neutral)","Внутренняя калибровка модели (0 = нейтрально)"),yaxis_title="")
    st.plotly_chart(fig,use_container_width=True)


def _pressure_table(parameters):
    rows=[]
    for p in parameters:
        if p.get("mode") != "pressure_only": continue
        rows.append({tr("Mechanism","Механизм"):p.get("name_ru") or p.get("parameter"),tr("Calibration pressure","Калибровочное давление"):round(float(p.get("pressure_median") or 0),3),tr("Status","Статус"):"NO DIRECTION"})
    if rows:
        st.dataframe(pd.DataFrame(rows).sort_values(tr("Calibration pressure","Калибровочное давление"),ascending=False),hide_index=True,use_container_width=True)


def render_result(profile):
    meta=profile["meta"]; subject=meta["subject"]
    params=profile.get("processing",{}).get("parameters",[])
    st.title(f"{subject.get('label','Client')} · {tr('Processing Spiral profile','Профиль Спирали процессинга')}")
    st.caption(tr(
        f"Born {subject['dob']} · central conception {subject['central_conception']} · gestation {subject['central_conception_to_birth_days']} dpc",
        f"Дата рождения {subject['dob']} · центральная оценка зачатия {subject['central_conception']} · срок от зачатия {subject['central_conception_to_birth_days']} дней",
    ))
    evidence_badges()
    st.info(tr("This is an experimental developmental model, not a medical or psychological diagnosis. Natural EMF causality has not been established.","Это экспериментальная модель развития, а не медицинская или психологическая диагностика. Причинное влияние естественного ЭМП не установлено."))

    st.subheader(tr("Processing architecture", "Архитектура процессинга"))
    _param_chart(params)
    directional=[p for p in params if p.get("mode")=="directional"]
    top=sorted(directional,key=lambda p:abs(float(p.get("state_median") or 0)),reverse=True)[:8]
    cols=st.columns(2)
    for i,p in enumerate(top):
        with cols[i%2]:
            val=float(p.get("state_median") or 0); lo=p.get("state_min"); hi=p.get("state_max")
            st.markdown(f'<div class="card"><div class="kicker">{p.get("family_ru",p.get("family",""))}</div><h3>{p.get("name_ru",p["parameter"])}</h3><p><b>{val:+.3f}</b> · {p.get("robustness","")}</p><p>{p.get("summary","")}</p><p>{tr("Range","Диапазон")}: {lo:+.3f} … {hi:+.3f}</p></div>',unsafe_allow_html=True)

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("Pressure-only mechanisms", "Механизмы только с калибровочным давлением"))
    st.caption(tr("For these mechanisms the current engine estimates how strongly the developmental trajectory loads the mechanism, but does not assign a functional direction.","Для этих механизмов текущий движок оценивает силу калибровочной нагрузки, но не назначает функциональное направление."))
    _pressure_table(params)

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("Six developmental windows", "Шесть окон развития"))
    windows=profile.get("windows",[])
    if windows:
        st.dataframe(pd.DataFrame(windows),hide_index=True,use_container_width=True)

    st.subheader(tr("Candidate developing circuits", "Возможные развивающиеся контуры"))
    bm=profile.get("brain_map",[])
    if bm:
        frame=pd.DataFrame(bm)
        show=[c for c in ["window","circuit","exposure_median","exposure_min","exposure_max","top_parameters"] if c in frame.columns]
        st.dataframe(frame[show] if show else frame,hide_index=True,use_container_width=True)
    st.caption(tr("Circuit labels are developmental/functional hypotheses, not unique anatomical addresses.","Названия контуров — функционально-развивающиеся гипотезы, а не однозначные анатомические адреса."))

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    st.subheader(tr("Experimental somatic branch", "Экспериментальная соматическая ветка"))
    som=profile.get("experimental",{}).get("somatic",{})
    st.warning(tr("Research direction only: no disease prediction or diagnosis. The downstream somatic mapping is not calibrated yet.","Только исследовательское направление: без прогноза заболеваний и диагностики. Нисходящее соматическое соответствие пока не откалибровано."))
    st.write(", ".join(som.get("domains",[])))

    st.subheader(tr("Experimental psychophysiology / psychosomatics", "Экспериментальная психофизиология / психосоматика"))
    psy=profile.get("experimental",{}).get("psychophysiology",{})
    st.warning(tr("Research direction only. These outputs describe candidate routes from processing architecture to physiological expression; they are not clinical conclusions.","Только исследовательское направление. Здесь рассматриваются возможные пути от архитектуры процессинга к физиологическому проявлению; это не клинические выводы."))
    st.write(", ".join(psy.get("domains",[])))

    with st.expander(tr("SILSO packet context and uncertainty", "Контекст пакетов SILSO и неопределённость")):
        st.markdown(tr("SILSO context v2 is shown in parallel and does not yet change the frozen cascade weights.","SILSO context v2 показывается параллельно и пока не меняет замороженные веса каскада."))
        csum=profile.get("silso_context",{}).get("window_summary",[])
        if csum: st.dataframe(pd.DataFrame(csum),hide_index=True,use_container_width=True)
        unc=profile.get("uncertainty",[])
        if unc: st.dataframe(pd.DataFrame(unc),hide_index=True,use_container_width=True)

    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    flat=pd.DataFrame([export_flat(profile)])
    c1,c2=st.columns(2)
    with c1: st.download_button(tr("Download profile CSV","Скачать профиль CSV"),flat.to_csv(index=False).encode("utf-8"),"archviq_spiral_profile.csv","text/csv",use_container_width=True)
    with c2: st.download_button(tr("Download full profile JSON","Скачать полный профиль JSON"),json.dumps(profile,ensure_ascii=False,indent=2).encode("utf-8"),"archviq_spiral_profile.json","application/json",use_container_width=True)


def render_profile():
    st.markdown(tr('<div class="kicker">FREE · BUNDLED SILSO ANALYTICS</div>','<div class="kicker">БЕСПЛАТНО · SILSO ВНУТРИ РЕПОЗИТОРИЯ</div>'),unsafe_allow_html=True)
    st.title(tr("Developmental SSN / Processing Spiral analysis", "Анализ развития по SSN / Спираль процессинга"))
    st.markdown(f'<div class="hero-copy">{tr("The calculation uses the frozen WDC-SILSO Daily Total Sunspot Number V2.0 file stored with this GitHub repository. Nothing is downloaded during a profile calculation.","Расчёт использует замороженный файл WDC-SILSO Daily Total Sunspot Number V2.0, который хранится вместе с репозиторием GitHub. Во время расчёта ничего не скачивается.")}</div>',unsafe_allow_html=True)
    with st.form("profile_form"):
        c1,c2,c3=st.columns([1.2,1,1])
        with c1: name=st.text_input(tr("Name / label","Имя / метка"),value="")
        with c2: dob=st.date_input(tr("Date of birth","Дата рождения"),value=pd.Timestamp("1990-01-01").date(),min_value=pd.Timestamp("1819-01-01").date(),max_value=pd.Timestamp.today().date())
        with c3: sex=st.selectbox(tr("Sex","Пол"),options=["F","M"],format_func=lambda x: tr("Female" if x=="F" else "Male","Женский" if x=="F" else "Мужской"))
        mode_label=st.radio(tr("Gestation information","Данные о сроке беременности"),["unknown","ctb_days","conception"],format_func=lambda x:{"unknown":tr("Unknown — use 266 dpc ±14 d","Неизвестен — 266 дней ±14"),"ctb_days":tr("Known conception-to-birth duration","Известно число дней от зачатия до родов"),"conception":tr("Known conception date","Известна дата зачатия")}[x],horizontal=False)
        ctb=None; conception=None
        if mode_label=="ctb_days":
            ctb=int(st.number_input(tr("Days from conception to birth","Дней от зачатия до рождения"),min_value=140,max_value=300,value=266,step=1))
            unc=int(st.number_input(tr("Timing uncertainty, days","Неопределённость, дней"),min_value=0,max_value=60,value=7,step=1))
        elif mode_label=="conception":
            conception=st.date_input(tr("Conception date","Дата зачатия"),value=(pd.Timestamp(dob)-pd.Timedelta(days=266)).date()).isoformat()
            unc=int(st.number_input(tr("Timing uncertainty, days","Неопределённость, дней"),min_value=0,max_value=60,value=0,step=1))
        else:
            unc=14
        accepted=st.checkbox(tr("I understand this is a research analytical model, not a medical diagnosis.","Я понимаю, что это исследовательская аналитическая модель, а не медицинская диагностика."),value=True)
        submit=st.form_submit_button(tr("Calculate free SSN profile","Рассчитать бесплатный SSN-профиль"),type="primary",use_container_width=True)
    if submit:
        if not accepted:
            st.error(tr("Please confirm the research-use statement.","Подтвердите исследовательский характер расчёта."))
        else:
            try:
                with st.spinner(tr("Building 5/7-day packets and cascade…","Строю 5/7-дневные пакеты и каскад…")):
                    st.session_state.profile=compute_profile(name or tr("Client","Клиент"),dob.isoformat(),sex,mode_label,ctb,conception,unc)
            except UnsupportedGestationError as exc:
                st.error(tr("This strongly preterm case requires the PRETERM_EXTRAUTERINE_MATURATION layer, which is not yet part of the public engine.","Этот случай выраженной недоношенности требует слоя PRETERM_EXTRAUTERINE_MATURATION, который пока не включён в публичный движок.")); st.caption(str(exc))
            except (InputValidationError,ValueError,FileNotFoundError) as exc:
                st.error(str(exc))
            except Exception as exc:
                st.exception(exc)
    if st.session_state.profile:
        st.markdown('<div class="rule"></div>',unsafe_allow_html=True); render_result(st.session_state.profile)


def paid_intro(title_en,title_ru,body_en,body_ru):
    st.markdown(tr('<div class="kicker">PAID MEASUREMENT MODULE</div>','<div class="kicker">ПЛАТНЫЙ МОДУЛЬ ИЗМЕРЕНИЙ</div>'),unsafe_allow_html=True)
    st.title(tr(title_en,title_ru)); st.markdown(f'<div class="hero-copy">{tr(body_en,body_ru)}</div>',unsafe_allow_html=True)
    st.info(tr("The SSN-linked developmental analysis remains free. Payment applies only to tests, compatibility work, questionnaires and their interpretation.","Аналитика развития по SSN остаётся бесплатной. Оплата относится только к тестам, совместимости, работе с опросниками и их интерпретации."))
    st.link_button(tr("Open paid module / full report","Открыть платный модуль / полный отчёт"),PRODUCTS["full"],use_container_width=True)


def render_architecture_questionnaire():
    paid_intro("Questionnaires and GAP work","Опросники и работа с GAP","Questionnaires measure current self-reported expression and compensatory effort. They are a paid measurement layer and are not part of the free SSN calculation.","Опросники измеряют текущее самоописание и компенсаторные усилия. Это платный измерительный слой, он не входит в бесплатный расчёт по SSN.")
    if not PAID_RESEARCH_MODE:
        st.caption(tr("The questionnaire engine is kept in the repository for paid/private workflows, but is hidden on the public free site.","Движок опросников сохранён в репозитории для платного/частного использования, но скрыт на публичной бесплатной странице.")); return
    instrument=load_architecture_instrument(); responses={}; anchors=[tr("Strongly disagree","Совсем не согласен"),tr("Rather disagree","Скорее не согласен"),tr("Neutral","Нейтрально"),tr("Rather agree","Скорее согласен"),tr("Strongly agree","Полностью согласен")]
    with st.form("architecture_questionnaire_form"):
        for scale_id,scale in instrument["scales"].items():
            st.subheader(scale_label(scale_id,st.session_state.lang))
            for item in scale["items"]:
                responses[item["id"]]=st.radio(item_text(item,st.session_state.lang),[1,2,3,4,5],index=2,format_func=lambda v,labels=anchors:f"{v} · {labels[v-1]}",horizontal=True,key=f"arch_item_{item['id']}")
        submitted=st.form_submit_button(tr("Calculate questionnaire profile","Рассчитать профиль опросника"),type="primary",use_container_width=True)
    if submitted: st.session_state.architecture_questionnaire=score_architecture_responses(responses)
    if st.session_state.architecture_questionnaire:
        st.json(st.session_state.architecture_questionnaire)


def render_stage2():
    paid_intro("Cognitive tests","Когнитивные тесты","Reaction, working-memory, switching and interference tasks are a paid measurement layer. Raw tests are kept separate from the free developmental SSN model.","Реакция, рабочая память, переключение и интерференция — платный измерительный слой. Сырые тесты отделены от бесплатной модели развития по SSN.")
    if not PAID_RESEARCH_MODE:
        st.caption(tr("The cognitive battery files remain in the repository for paid/private workflows, but are hidden on the public free site.","Файлы когнитивной батареи остаются в репозитории для платного/частного использования, но скрыты на публичной бесплатной странице.")); return
    html_path=ROOT/("cognitive_test_en.html" if st.session_state.lang=="EN" else "cognitive_test.html")
    if html_path.exists(): components.html(html_path.read_text(encoding="utf-8"),height=1100,scrolling=True)
    uploaded=st.file_uploader(tr("Upload the test CSV","Загрузите CSV теста"),type=["csv"])
    if uploaded is not None:
        try: st.session_state.cognitive_result=parse_cognitive_csv(uploaded); st.json(st.session_state.cognitive_result)
        except Exception as exc: st.error(str(exc))


def render_method():
    st.markdown(tr('<div class="kicker">METHOD · FROZEN BASELINE A</div>','<div class="kicker">МЕТОД · ЗАМОРОЖЕННЫЙ BASELINE A</div>'),unsafe_allow_html=True)
    st.title(tr("How the current engine works", "Как работает текущий движок"))
    render_pipeline(); evidence_badges()
    st.markdown(tr("""
### 1. Physical layer
The repository contains a frozen WDC-SILSO Daily Total Sunspot Number V2.0 archive. No runtime download is used. The engine calculates 5- and 7-day packets across W1 18–60, W2 61–100, W3 101–140, F1 168–188, F2 189–202 and F3 203→birth.

### 2. Dynamic geometry
The physical layer uses daily dynamics such as A, V, reversal/persistence, directional bias, acceleration, jerk and energy. Activity level is used as a nuisance/context variable for level-conditioned normalization, not as a direct explanatory target.

### 3. Developmental brain map
Each window has a frozen sensitivity map to candidate developing circuits. These labels are hypotheses about functional calibration, not claims that natural EMF changes gross anatomy.

### 4. Processing Spiral
The cascade updates parameters of one processing machine: gating, ν, persistence, decision/action/model-update thresholds, hysteresis, recovery, compression and related variables. Previous packets affect later packets; trajectory is retained.

### 5. Experimental downstream branches
Somatic and psychophysiological/psychosomatic branches remain visible as experimental research directions. They do not currently predict disease and are not diagnostic.
""","""
### 1. Физический слой
В репозитории лежит замороженный архив WDC-SILSO Daily Total Sunspot Number V2.0. Во время расчёта ничего не скачивается. Движок строит 5- и 7-дневные пакеты в W1 18–60, W2 61–100, W3 101–140, F1 168–188, F2 189–202 и F3 203→роды.

### 2. Геометрия динамики
Физический слой использует A, V, reversal/persistence, направленный bias, acceleration, jerk, energy и другие параметры. Уровень солнечной активности служит контекстной/nuisance-переменной для нормировки, а не прямым объясняющим признаком.

### 3. Карта развивающихся контуров
Для каждого окна заморожена карта чувствительности возможных развивающихся контуров. Это гипотезы функциональной калибровки, а не утверждение о том, что естественное ЭМП меняет грубую анатомию мозга.

### 4. Спираль процессинга
Каскад обновляет параметры одной машины обработки: gating, ν, persistence, пороги решения/действия/обновления модели, гистерезис, recovery, compression и связанные переменные. Предыдущие пакеты меняют реакцию на последующие; траектория сохраняется.

### 5. Экспериментальные нисходящие ветки
Соматика и психофизиология/психосоматика остаются видимыми как экспериментальные исследовательские направления. Сейчас они не предсказывают заболевание и не являются диагностикой.
"""))
    st.markdown('<div class="formula">SSN daily archive → 5/7-day packets → W1–W3 + F1–F3 → candidate circuits → RS4/v4 Processing Spiral cascade → explainable profile → experimental downstream branches</div>',unsafe_allow_html=True)


def footer():
    st.markdown('<div class="rule"></div>',unsafe_allow_html=True)
    c1,c2=st.columns([1.8,1])
    with c1: st.caption(tr("ARCHVIQ is an experimental analytical platform. It is not a medical diagnostic service and does not replace medical or psychological care.","ARCHVIQ — экспериментальная аналитическая платформа. Это не медицинская диагностика и не замена медицинской или психологической помощи."))
    with c2: st.caption(f"{APP_VERSION} · archviq.com")


topbar()
if st.session_state.page=="profile": render_profile()
elif st.session_state.page=="architecture": render_architecture_questionnaire()
elif st.session_state.page=="stage2": render_stage2()
elif st.session_state.page=="method": render_method()
else: render_home()
footer()
