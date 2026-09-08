import streamlit as st
import datetime
import base64
import gzip
import json
import os
import urllib.request
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from profile_engine import compute_profile, get_compatibility
from interpret_engine import interpret, compatibility_analysis


st.set_page_config(
    page_title="Archviq — Your brain's operating system",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Когнитивный тест встроен в app.py, чтобы приложение не зависело
# от отдельного cognitive_test.html.
COGNITIVE_HTML_GZ_B64 = """
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
"""



# V6.1: supplied landing and portrait embedded; no external HTML file needed.
LANDING_V6_HTML = "<style>\n  @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');\n\n  :root{\n    --bg: #0D1220;\n    --bg-alt: #121A30;\n    --ink: #ECEEF3;\n    --muted: #8C96AE;\n    --line: #262F4A;\n    --solar: #E3A34E;\n    --neural: #6FD8C4;\n    --serif: 'Newsreader', serif;\n    --sans: 'IBM Plex Sans', sans-serif;\n    --mono: 'IBM Plex Mono', monospace;\n  }\n\n  *{box-sizing:border-box; margin:0; padding:0;}\n  html,body{background:var(--bg) url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzNjAiIGhlaWdodD0iMzYwIiB2aWV3Qm94PSIwIDAgMzYwIDM2MCI+CiAgPGcgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNkZEOEM0IiBzdHJva2Utd2lkdGg9IjEuMyIgb3BhY2l0eT0iMC4yMCI+CiAgICA8cGF0aCBkPSJNMTAsNjAgTDMwLDYwIEwzOCw0MiBMNDYsNzggTDU0LDUwIEw2Miw2MCBMOTAsNjAiLz4KICAgIDxwYXRoIGQ9Ik0xODAsNDAgQzE5NSwyMCAyMTAsNjAgMjI1LDQwIEMyNDAsMjAgMjU1LDYwIDI3MCw0MCIvPgogIDwvZz4KICA8ZyBmaWxsPSJub25lIiBzdHJva2U9IiNFM0EzNEUiIHN0cm9rZS13aWR0aD0iMS4zIiBvcGFjaXR5PSIwLjIyIj4KICAgIDxjaXJjbGUgY3g9IjMwMCIgY3k9IjEyMCIgcj0iMjIiLz4KICAgIDxjaXJjbGUgY3g9IjI5NCIgY3k9IjExNSIgcj0iMi42IiBmaWxsPSIjRTNBMzRFIiBzdHJva2U9Im5vbmUiLz4KICAgIDxjaXJjbGUgY3g9IjMwOCIgY3k9IjEyNiIgcj0iMS44IiBmaWxsPSIjRTNBMzRFIiBzdHJva2U9Im5vbmUiLz4KICAgIDxsaW5lIHgxPSIzMDAiIHkxPSI5MCIgeDI9IjMwMCIgeTI9IjgwIi8+CiAgICA8bGluZSB4MT0iMzAwIiB5MT0iMTUwIiB4Mj0iMzAwIiB5Mj0iMTYwIi8+CiAgICA8bGluZSB4MT0iMjcwIiB5MT0iMTIwIiB4Mj0iMjYwIiB5Mj0iMTIwIi8+CiAgICA8bGluZSB4MT0iMzMwIiB5MT0iMTIwIiB4Mj0iMzQwIiB5Mj0iMTIwIi8+CiAgPC9nPgogIDxnIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0E3QjBDOCIgc3Ryb2tlLXdpZHRoPSIxLjIiIG9wYWNpdHk9IjAuMjAiPgogICAgPGVsbGlwc2UgY3g9IjcwIiBjeT0iMjIwIiByeD0iMzQiIHJ5PSIxNCIvPgogICAgPGVsbGlwc2UgY3g9IjcwIiBjeT0iMjIwIiByeD0iMzQiIHJ5PSIxNCIgdHJhbnNmb3JtPSJyb3RhdGUoNjAgNzAgMjIwKSIvPgogICAgPGVsbGlwc2UgY3g9IjcwIiBjeT0iMjIwIiByeD0iMzQiIHJ5PSIxNCIgdHJhbnNmb3JtPSJyb3RhdGUoMTIwIDcwIDIyMCkiLz4KICAgIDxjaXJjbGUgY3g9IjcwIiBjeT0iMjIwIiByPSIyLjgiIGZpbGw9IiNBN0IwQzgiIHN0cm9rZT0ibm9uZSIvPgogIDwvZz4KICA8ZyBmaWxsPSJub25lIiBzdHJva2U9IiM2RkQ4QzQiIHN0cm9rZS13aWR0aD0iMS4yIiBvcGFjaXR5PSIwLjIwIj4KICAgIDxjaXJjbGUgY3g9IjIzMCIgY3k9IjI2MCIgcj0iNyIvPgogICAgPGxpbmUgeDE9IjIzMCIgeTE9IjI1MyIgeDI9IjIxNSIgeTI9IjIzNSIvPgogICAgPGxpbmUgeDE9IjIzMCIgeTE9IjI1MyIgeDI9IjI0NSIgeTI9IjIzMiIvPgogICAgPGxpbmUgeDE9IjIzNyIgeTE9IjI2NCIgeDI9IjI2MCIgeTI9IjI3MCIvPgogICAgPGxpbmUgeDE9IjIyMyIgeTE9IjI2NiIgeDI9IjIwNSIgeTI9IjI4NSIvPgogIDwvZz4KICA8dGV4dCB4PSIxNTAiIHk9IjMzMCIgZm9udC1mYW1pbHk9InNlcmlmIiBmb250LXNpemU9IjIyIiBmaWxsPSIjQTdCMEM4IiBvcGFjaXR5PSIwLjIwIj7OozwvdGV4dD4KICA8dGV4dCB4PSIyMCIgeT0iMTUwIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNkZEOEM0IiBvcGFjaXR5PSIwLjIwIj7OlFNTTjwvdGV4dD4KPC9zdmc+Cg==') repeat; color:var(--ink); font-family:var(--sans); font-size:16px; line-height:1.6;}\n  img,svg{display:block; max-width:100%;}\n\n  .wrap{max-width:1180px; margin:0 auto; padding:0 40px;}\n\n  /* ===== NAV ===== */\n  nav{\n    display:flex; justify-content:space-between; align-items:center;\n    padding:28px 40px; max-width:1180px; margin:0 auto;\n  }\n  .logo{font-family:var(--serif); font-style:italic; font-size:22px; letter-spacing:0.3px;}\n  .logo b{font-style:normal; color:var(--solar); font-weight:500;}\n  .navcta{\n    font-family:var(--sans); font-size:14px; color:var(--ink);\n    border:1px solid var(--line); padding:9px 18px; border-radius:2px;\n    text-decoration:none;\n  }\n\n  /* ===== HERO ===== */\n  .hero{position:relative; padding:64px 0 48px; overflow:hidden;}\n  .hero-grid{display:grid; grid-template-columns:1.1fr 0.9fr; gap:40px; align-items:center; margin-bottom:48px;}\n  .hero h1{\n    font-family:var(--serif); font-weight:500; font-size:56px; line-height:1.12;\n    max-width:11ch; letter-spacing:-0.5px;\n  }\n  .hero h1 em{font-style:italic; color:var(--solar); font-weight:400;}\n  .hero p.sub{\n    margin-top:26px; max-width:46ch; color:var(--muted); font-size:17px; line-height:1.7;\n  }\n  .hero-actions{margin-top:36px; display:flex; align-items:center; gap:22px;}\n  .btn-primary{\n    background:var(--solar); color:#171106; font-family:var(--sans); font-weight:600;\n    font-size:15px; padding:14px 26px; border-radius:2px; text-decoration:none;\n  }\n  .btn-secondary{color:var(--ink); font-size:15px; text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:4px;}\n\n  .hero-visual{position:relative; height:420px;}\n  .hero-caption{\n    position:absolute; bottom:-6px; left:0; font-family:var(--mono); font-size:12px; color:var(--muted);\n  }\n\n  /* ===== TEST PANEL ===== */\n  .testpanel{\n    background:var(--bg-alt); border:1px solid var(--line); border-radius:2px;\n    padding:36px 40px; margin-top:8px;\n  }\n  .testpanel-head{display:flex; justify-content:space-between; align-items:baseline; margin-bottom:24px; flex-wrap:wrap; gap:12px;}\n  .testpanel-head .kicker{margin-bottom:0;}\n  .testpanel-head h3{font-family:var(--serif); font-style:italic; font-weight:500; font-size:20px;}\n  .test-main{\n    display:flex; justify-content:space-between; align-items:center; gap:20px;\n    background:var(--solar); color:#171106; padding:20px 26px; border-radius:2px; margin-bottom:22px;\n    text-decoration:none;\n  }\n  .test-main .t-name{font-family:var(--sans); font-weight:600; font-size:17px;}\n  .test-main .t-desc{font-family:var(--sans); font-size:13px; opacity:0.75; margin-top:4px;}\n  .test-main .t-arrow{font-family:var(--mono); font-size:20px;}\n  .test-grid{display:grid; grid-template-columns:repeat(4,1fr); gap:14px;}\n  .test-pill{\n    display:block; background:transparent; border:1px solid var(--line); border-radius:2px;\n    padding:16px 16px; text-decoration:none; transition:none;\n  }\n  .test-pill .p-name{font-family:var(--sans); font-weight:600; font-size:14px; color:var(--ink);}\n  .test-pill .p-tag{font-family:var(--mono); font-size:11px; color:var(--neural); display:block; margin-bottom:8px;}\n  @media (max-width:860px){\n    .test-grid{grid-template-columns:1fr 1fr;}\n  }\n  section{padding:96px 0; border-top:1px solid var(--line);}\n  .kicker{font-family:var(--mono); font-size:13px; color:var(--neural); margin-bottom:16px;}\n  h2{font-family:var(--serif); font-weight:500; font-size:34px; max-width:16ch; line-height:1.25; color:var(--ink);}\n  .hero h1{color:var(--ink);}\n  .lede{color:var(--muted); max-width:60ch; margin-top:18px; font-size:16px; line-height:1.75;}\n\n  /* ===== WHY IT MATTERS ===== */\n  .stages{margin-top:56px; display:grid; grid-template-columns:1fr 1fr; gap:56px;}\n  .stage-list{list-style:none; counter-reset:stage;}\n  .stage-list li{\n    counter-increment:stage; display:grid; grid-template-columns:34px 1fr; gap:16px;\n    padding:16px 0; border-bottom:1px solid var(--line); font-size:15px; color:var(--ink);\n  }\n  .stage-list li:first-child{padding-top:0;}\n  .stage-list li::before{\n    content:counter(stage);\n    font-family:var(--mono); color:var(--muted); font-size:13px; padding-top:2px;\n  }\n\n  .windows{display:flex; flex-direction:column; gap:0;}\n  .window-track{display:flex; height:10px; border-radius:1px; overflow:hidden; margin-bottom:22px;}\n  .w1{background:#3E4A78; flex:0.9;}\n  .w2{background:#5A6BA8; flex:0.9;}\n  .w3{background:var(--neural); flex:1.2;}\n  .window-item{display:flex; gap:16px; padding:12px 0; border-bottom:1px solid var(--line); font-size:14px;}\n  .window-tag{font-family:var(--mono); color:var(--solar); min-width:44px;}\n  .window-item .desc{color:var(--muted);}\n\n  /* ===== SIGNAL / FORMULAS ===== */\n  .signal-grid{display:grid; grid-template-columns:1fr 1fr; gap:56px; margin-top:56px; align-items:start;}\n  .formula-panel{\n    background:var(--bg-alt); border:1px solid var(--line); padding:32px; border-radius:2px;\n  }\n  .formula-row{\n    display:flex; justify-content:space-between; align-items:baseline;\n    padding:14px 0; border-bottom:1px solid var(--line); font-family:var(--mono); font-size:14px;\n  }\n  .formula-row:last-child{border-bottom:none;}\n  .formula-row .name{color:var(--muted); font-family:var(--sans); font-size:13px; max-width:20ch;}\n  .formula-row .expr{color:var(--neural);}\n\n  /* ===== AXES ===== */\n  .axes{margin-top:56px; display:flex; flex-direction:column;}\n  .axis-row{\n    display:grid; grid-template-columns:70px 200px 1fr 160px; gap:24px; align-items:center;\n    padding:22px 0; border-bottom:1px solid var(--line);\n  }\n  .axis-row:first-child{border-top:1px solid var(--line);}\n  .axis-code{font-family:var(--mono); color:var(--solar); font-size:14px;}\n  .axis-name{font-family:var(--serif); font-style:italic; font-size:19px;}\n  .axis-desc{color:var(--muted); font-size:14px; max-width:56ch;}\n  .axis-bar{height:6px; background:var(--line); border-radius:1px; position:relative;}\n  .axis-bar::after{content:''; position:absolute; left:0; top:0; height:100%; background:var(--neural); border-radius:1px;}\n  .axis-bar.b1::after{width:62%;}\n  .axis-bar.b2::after{width:74%;}\n  .axis-bar.b3::after{width:48%;}\n  .axis-bar.b4::after{width:83%; background:var(--solar);}\n\n  .rs4-formula{\n    margin-top:40px; font-family:var(--mono); font-size:14px; color:var(--muted);\n    background:var(--bg-alt); border:1px solid var(--line); padding:22px 28px; border-radius:2px;\n  }\n  .rs4-formula span{color:var(--ink);}\n\n  /* ===== ARCHETYPES ===== */\n  .types-grid{margin-top:56px; display:grid; grid-template-columns:repeat(2,1fr); gap:1px; background:var(--line);}\n  .type-card{background:var(--bg); padding:32px;}\n  .type-name{font-family:var(--serif); font-style:italic; font-weight:500; font-size:22px; margin-bottom:6px;}\n  .type-tag{font-family:var(--mono); font-size:12px; color:var(--muted); margin-bottom:16px; display:block;}\n  .type-card p{color:var(--muted); font-size:14px; line-height:1.7; margin-bottom:14px;}\n  .type-bio{font-size:13px; color:var(--ink); border-top:1px solid var(--line); padding-top:14px;}\n  .type-bio b{color:var(--solar); font-family:var(--mono); font-weight:500; font-size:11px; letter-spacing:0.3px;}\n  .type-card.accent-neural .type-name{color:var(--neural);}\n  .type-card.accent-solar .type-name{color:var(--solar);}\n\n  /* ===== VALIDATION ===== */\n  .val-grid{margin-top:48px; display:grid; grid-template-columns:repeat(3,1fr); gap:32px;}\n  .val-stat{border-top:1px solid var(--line); padding-top:18px;}\n  .val-num{font-family:var(--mono); font-size:28px; color:var(--neural);}\n  .val-label{color:var(--muted); font-size:13px; margin-top:6px;}\n  .val-note{color:var(--muted); font-size:13px; margin-top:32px; max-width:60ch; line-height:1.7;}\n\n  /* ===== COMPARISON TABLE ===== */\n  table{width:100%; border-collapse:collapse; margin-top:56px; font-size:14px;}\n  th{\n    text-align:left; font-family:var(--sans); font-weight:600; font-size:13px;\n    color:var(--muted); padding:14px 20px 14px 0; border-bottom:1px solid var(--line);\n  }\n  th:first-child{width:26%;}\n  td{padding:16px 20px 16px 0; border-bottom:1px solid var(--line); color:var(--ink); vertical-align:top;}\n  td:first-child{color:var(--muted); font-family:var(--mono); font-size:13px;}\n  td.arch{color:var(--neural);}\n\n  /* ===== THREE TIERS ===== */\n  .tiers{margin-top:56px; display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--line);}\n  .tier{background:var(--bg); padding:32px;}\n  .tier h3{font-family:var(--serif); font-style:italic; font-weight:500; font-size:19px; margin-bottom:16px;}\n  .tier ul{list-style:none;}\n  .tier li{\n    font-size:14px; color:var(--muted); padding:8px 0 8px 16px; position:relative; line-height:1.55;\n  }\n  .tier li::before{content:'—'; position:absolute; left:0; color:var(--line);}\n\n  /* ===== AUTHOR ===== */\n  .author{display:grid; grid-template-columns:200px 1fr; gap:48px; align-items:start;}\n  .author-portrait{\n    width:160px; height:160px; border-radius:50%; object-fit:cover;\n    border:1px solid var(--line);\n  }\n  .author-name{font-family:var(--serif); font-style:italic; font-size:24px; margin-bottom:6px;}\n  .author-role{color:var(--solar); font-size:14px; font-family:var(--mono); margin-bottom:22px;}\n  .author p{color:var(--muted); font-size:15px; max-width:64ch; margin-bottom:14px; line-height:1.75;}\n\n  /* ===== FOOTER CTA ===== */\n  .final{text-align:left; padding:110px 0 90px;}\n  .final h2{font-size:40px; max-width:14ch;}\n  .final .btn-primary{margin-top:36px; display:inline-block;}\n\n  footer{border-top:1px solid var(--line); padding:32px 0; }\n  .foot-row{display:flex; justify-content:space-between; color:var(--muted); font-size:13px; font-family:var(--mono);}\n\n  @media (max-width:860px){\n    .hero-grid, .stages, .signal-grid, .author{grid-template-columns:1fr;}\n    .hero h1{font-size:38px; max-width:none;}\n    h2{font-size:26px;}\n    .tiers{grid-template-columns:1fr;}\n    .axis-row{grid-template-columns:1fr; gap:8px;}\n    .types-grid{grid-template-columns:1fr;}\n    .val-grid{grid-template-columns:1fr; gap:20px;}\n  }\n\n/* Streamlit adaptation: landing only; retain the supplied visual composition. */\n.stApp {background:#0D1220!important;}\n.stApp::before {display:none!important}\n[data-testid=\"stMainBlockContainer\"],.block-container {max-width:1180px!important;padding:1rem 1rem 4rem!important;}\n.archviq-v6 {color:var(--ink);font-family:var(--sans);font-size:16px;}\n.archviq-v6 h1 {font-size:56px!important;line-height:1.12!important;}\n.archviq-v6 h2 {font-size:34px!important;}\n.archviq-v6 p {font-family:var(--sans);}\n.archviq-v6 .formula-row {gap:16px;flex-wrap:wrap;}\n.archviq-v6 .expr,.archviq-v6 .rs4-formula {overflow-wrap:anywhere;}\n.archviq-v6 .author-portrait {object-fit:cover;}\n.archviq-v6 a:focus-visible {outline:2px solid var(--neural);outline-offset:5px;}\n@media(max-width:860px){\n.archviq-v6 .hero h1 {font-size:38px!important;}\n.archviq-v6 h2 {font-size:26px!important;}\n.archviq-v6 .wrap,.archviq-v6 nav {padding-left:16px;padding-right:16px;}\n.archviq-v6 .hero-actions,.archviq-v6 .foot-row {flex-wrap:wrap;}\n.archviq-v6 .test-grid {grid-template-columns:1fr;}\n.archviq-v6 .formula-panel {padding:16px;}\n.archviq-v6 table {display:block;overflow-x:auto;}\n}</style><div class=\"archviq-v6\">\n\n<nav>\n  <div class=\"logo\">ARCH<b>VIQ</b></div>\n  <a class=\"navcta\" href=\"?archviq=profile\" target=\"_self\">Рассчитать профиль</a>\n</nav>\n\n<div class=\"wrap hero\">\n  <div class=\"hero-grid\">\n    <div>\n      <h1>Архитектура мозга <em>начинается</em> до рождения</h1>\n      <p class=\"sub\">Исследовательская система моделирования нейрофункциональной архитектуры на основе динамики солнечной активности в критические периоды нейрогенеза. Не астрология и не диагноз — вычислительная модель на датированных физических наблюдениях.</p>\n      <div class=\"hero-actions\">\n        <a class=\"btn-primary\" href=\"?archviq=profile\" target=\"_self\">Рассчитать архитектурный профиль</a>\n        <a class=\"btn-secondary\" href=\"#methodology\">Как это устроено</a>\n      </div>\n    </div>\n    <div class=\"hero-visual\">\n      <svg viewBox=\"0 0 420 420\" width=\"100%\" height=\"100%\">\n        <defs>\n          <linearGradient id=\"fade\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">\n            <stop offset=\"0%\" stop-color=\"#E3A34E\" stop-opacity=\"0.9\"/>\n            <stop offset=\"100%\" stop-color=\"#6FD8C4\" stop-opacity=\"0.9\"/>\n          </linearGradient>\n        </defs>\n        <!-- solar sunspot curve, upper -->\n        <path d=\"M10,120 C50,60 90,150 130,90 C170,40 210,130 250,80 C290,40 330,120 410,70\"\n              fill=\"none\" stroke=\"#E3A34E\" stroke-width=\"1.6\" opacity=\"0.85\"/>\n        <path d=\"M10,150 C50,110 90,170 130,130 C170,90 210,160 250,120 C290,90 330,150 410,110\"\n              fill=\"none\" stroke=\"#E3A34E\" stroke-width=\"1\" opacity=\"0.35\"/>\n        <!-- transition -->\n        <line x1=\"205\" y1=\"20\" x2=\"205\" y2=\"400\" stroke=\"#262F4A\" stroke-width=\"1\" stroke-dasharray=\"2 6\"/>\n        <!-- EEG-like signal, lower -->\n        <path d=\"M10,300 L40,300 L52,260 L64,330 L76,280 L88,300 L120,300 L132,240 L144,340 L156,290 L168,300 L200,300\"\n              fill=\"none\" stroke=\"#6FD8C4\" stroke-width=\"1.6\" opacity=\"0.9\"/>\n        <path d=\"M215,300 L235,300 L250,255 L266,345 L282,285 L298,300 L330,300 L346,235 L362,350 L378,290 L395,300 L412,300\"\n              fill=\"none\" stroke=\"#6FD8C4\" stroke-width=\"1.6\" opacity=\"0.9\"/>\n        <circle cx=\"205\" cy=\"210\" r=\"2\" fill=\"#ECEEF3\" opacity=\"0.6\"/>\n      </svg>\n      <div class=\"hero-caption\">Динамика SSN × окна развития → модель → проверка по EEG</div>\n    </div>\n  </div>\n\n  <div class=\"testpanel\">\n    <div class=\"testpanel-head\">\n      <div class=\"kicker\">Доступные инструменты</div>\n      <h3>Выберите тест или опросник</h3>\n    </div>\n\n    <a class=\"test-main\" href=\"?archviq=test\" target=\"_self\">\n      <div>\n        <div class=\"t-name\">Пройти когнитивный тест</div>\n        <div class=\"t-desc\">5 проб на реакцию, память и контроль — основа GAP-анализа</div>\n      </div>\n      <div class=\"t-arrow\">↗</div>\n    </a>\n\n    <div class=\"test-grid\">\n      <a class=\"test-pill\" href=\"https://osipoff.gumroad.com/l/kdjqsj\">\n        <span class=\"p-tag\">отчёт · $12</span>\n        <span class=\"p-name\">Тест + GAP Analysis</span>\n      </a>\n      <a class=\"test-pill\" href=\"https://osipoff.gumroad.com/l/tfmfiw\">\n        <span class=\"p-tag\">опросник · $19</span>\n        <span class=\"p-name\">Совместимость в паре</span>\n      </a>\n      <a class=\"test-pill\" href=\"https://osipoff.gumroad.com/l/zfbje\">\n        <span class=\"p-tag\">опросник · $19</span>\n        <span class=\"p-name\">Выгорание</span>\n      </a>\n      <a class=\"test-pill\" href=\"https://osipoff.gumroad.com/l/tspxvc\">\n        <span class=\"p-tag\">опросник · $19</span>\n        <span class=\"p-name\">Работа с ИИ</span>\n      </a>\n      <a class=\"test-pill\" href=\"https://osipoff.gumroad.com/l/wsxcl\">\n        <span class=\"p-tag\">полный отчёт · $39</span>\n        <span class=\"p-name\">Full Architecture Report</span>\n      </a>\n      <span class=\"test-pill\" style=\"opacity:0.45; cursor:default;\">\n        <span class=\"p-tag\">скоро</span>\n        <span class=\"p-name\">Подбор в команду</span>\n      </span>\n      <span class=\"test-pill\" style=\"opacity:0.45; cursor:default;\">\n        <span class=\"p-tag\">скоро</span>\n        <span class=\"p-name\">Профориентация</span>\n      </span>\n    </div>\n  </div>\n</div>\n\n<section id=\"methodology\">\n  <div class=\"wrap\">\n    <div class=\"kicker\">Почему период до рождения имеет значение</div>\n    <h2>Развитие мозга — последовательность взаимосвязанных этапов</h2>\n    <p class=\"lede\">Его развитие проходит через последовательность процессов, каждый со своим окном чувствительности. ARCHVIQ рассматривает три центральных пренатальных интервала и то, как динамика внешней среды могла пересекаться с каждым из них.</p>\n\n    <div class=\"stages\">\n      <ul class=\"stage-list\">\n        <li><span>Образование нервной трубки</span></li>\n        <li><span>Пролиферация и миграция нервных клеток</span></li>\n        <li><span>Специализация мозговых структур</span></li>\n        <li><span>Формирование сенсорных и регуляторных контуров</span></li>\n        <li><span>Развитие связей между областями мозга</span></li>\n        <li><span>Механизмы синхронизации, интеграции и контроля</span></li>\n      </ul>\n\n      <div class=\"windows\">\n        <p class=\"lede\">W1–W3 — расчётные интервалы кода 43; процессы развития перекрываются и не ограничены этими границами.</p><div class=\"window-track\">\n          <div class=\"w1\"></div><div class=\"w2\"></div><div class=\"w3\"></div>\n        </div>\n        <div class=\"window-item\">\n          <div class=\"window-tag\">W1</div>\n          <div><strong>18–45 день</strong> после зачатия — <span class=\"desc\">раннее формирование нервной системы</span></div>\n        </div>\n        <div class=\"window-item\">\n          <div class=\"window-tag\">W2</div>\n          <div><strong>46–73 день</strong> — <span class=\"desc\">лимбические, таламические и регуляторные контуры</span></div>\n        </div>\n        <div class=\"window-item\">\n          <div class=\"window-tag\">W3</div>\n          <div><strong>74–100 день</strong> — <span class=\"desc\">кортикальные интерфейсы, сетевая интеграция</span></div>\n        </div>\n      </div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"wrap\">\n    <div class=\"kicker\">Электромагнитная динамика</div>\n    <h2>Не дата — траектория изменения</h2>\n    <div class=\"signal-grid\">\n      <p class=\"lede\">В основе модели — временной ряд чисел Вольфа (SSN) из исторического архива SILSO. SSN — индекс солнечной активности, а не прямое измерение ЭМП. Модель учитывает не только уровень, но и то, как активность меняется во времени: скорость, ускорение, частота переломов направления.</p>\n      <div class=\"formula-panel\">\n        <div class=\"formula-row\"><span class=\"name\">Уровень активности</span><span class=\"expr\">SSN(t)</span></div>\n        <div class=\"formula-row\"><span class=\"name\">Скорость изменения</span><span class=\"expr\">ΔSSN(t) = SSN(t) − SSN(t−1)</span></div>\n        <div class=\"formula-row\"><span class=\"name\">Резкость изменения</span><span class=\"expr\">Δ²SSN(t) = ΔSSN(t) − ΔSSN(t−1)</span></div>\n        <div class=\"formula-row\"><span class=\"name\">Частота переломов</span><span class=\"expr\">FlipDensity = смены / окно</span></div>\n      </div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"wrap\">\n    <div class=\"kicker\">Четыре архитектурные оси</div>\n    <h2>Карта соотношений, а не ярлык</h2>\n    <p class=\"lede\">Девять скрытых состояний каскадной модели сводятся в четыре интегральные оси. Высокое значение не означает «лучше» — каждая ось описывает баланс, а не шкалу качества.</p>\n\n    <p class=\"lede\">Полосы ниже — иллюстрация, не результат расчёта человека.</p><div class=\"axes\">\n      <div class=\"axis-row\">\n        <div class=\"axis-code\">RS1</div>\n        <div class=\"axis-name\">Ритмическая организация</div>\n        <div class=\"axis-desc\">Баланс устойчивости, зрелости, возбуждения и лабильности</div>\n        <div class=\"axis-bar b1\"></div>\n      </div>\n      <div class=\"axis-row\">\n        <div class=\"axis-code\">RS2</div>\n        <div class=\"axis-name\">Синхронизация</div>\n        <div class=\"axis-desc\">Согласованность между функциональными областями и узлами сети</div>\n        <div class=\"axis-bar b2\"></div>\n      </div>\n      <div class=\"axis-row\">\n        <div class=\"axis-code\">RS3</div>\n        <div class=\"axis-name\">Сегрегация</div>\n        <div class=\"axis-desc\">Способность разделять процессы и ограничивать распространение помех</div>\n        <div class=\"axis-bar b3\"></div>\n      </div>\n      <div class=\"axis-row\">\n        <div class=\"axis-code\">RS4</div>\n        <div class=\"axis-name\">Интегральная согласованность</div>\n        <div class=\"axis-desc\">Объединяет синхронизацию, узлы сети, зрелость, стабильность и лабильность</div>\n        <div class=\"axis-bar b4\"></div>\n      </div>\n    </div>\n\n    <div class=\"rs4-formula\">\n      RS4 = 0.30·<span>X_INTEG</span> + 0.25·<span>X_HUB</span> + 0.20·<span>X_MAT</span> + 0.15·<span>X_STAB</span> − 0.20·<span>X_LAB</span>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"wrap\">\n    <div class=\"kicker\">Четыре архитектурных типа</div>\n    <h2>Не диагноз — рабочий режим системы</h2>\n    <p class=\"lede\">Комбинация осей и индексов сводится к одному из четырёх типов. Это не шкала «лучше/хуже» — у каждого свой ресурс и своя цена устойчивости.</p>\n\n    <div class=\"types-grid\">\n      <div class=\"type-card\">\n        <div class=\"type-name\">Fortress</div>\n        <span class=\"type-tag\">HIGH_LOAD_COMPENSATED</span>\n        <p>Высокая межсетевая синхронизация и хорошая топологическая организация. Обрабатывает сложные задачи глубоко, а не быстро, и удерживает структуру под нагрузкой. Цена — скрытое напряжение, компенсируемое контролем; когда контроль отключается, нагрузка выходит резко.</p>\n        <div class=\"type-bio\"><b>БИОХАКИНГ</b><br>Сон 7–8 ч, режим ±30 мин. Восстановление — одиночный глубокий фокус, не социальное.</div>\n      </div>\n      <div class=\"type-card accent-neural\">\n        <div class=\"type-name\">Antenna</div>\n        <span class=\"type-tag\">HIGH_POWER_TENSION_CONTROLLED</span>\n        <p>Сформирована в период высокой волатильности солнечной активности. Настроена улавливать сигналы среды, которые другие не замечают — творческая интуиция, быстрая реакция, эмпатия. Та же чувствительность впускает внешние возмущения прямо в систему.</p>\n        <div class=\"type-bio\"><b>БИОХАКИНГ</b><br>Сон 8–9 ч с цифровым ритуалом отключения за 2 часа. Важные решения — не в периоды геомагнитных бурь.</div>\n      </div>\n      <div class=\"type-card\">\n        <div class=\"type-name\">Fluid</div>\n        <span class=\"type-tag\">MIDDLE_COMPENSATED</span>\n        <p>Сформирована в период умеренной, ритмичной активности без экстремумов. Баланс между глубиной и широтой, устойчивостью и гибкостью. Реже даёт резкие творческие прорывы, но надёжно работает в широком диапазоне условий.</p>\n        <div class=\"type-bio\"><b>БИОХАКИНГ</b><br>Сон 7–8 ч, гибкий режим. Риск — недооценка собственной нагрузки из-за внешней стабильности.</div>\n      </div>\n      <div class=\"type-card accent-solar\">\n        <div class=\"type-name\">Collapse</div>\n        <span class=\"type-tag\">TENSION_DOMINANT</span>\n        <p>Не диагноз, а сигнал. Сформирована в период экстремальной нестабильности; часть ресурсов системы постоянно уходит на поддержание базового баланса. Поддаётся коррекции через целевые протоколы восстановления.</p>\n        <div class=\"type-bio\"><b>БИОХАКИНГ</b><br>Сон 8–9 ч строго. Структурированные паузы каждые 90 минут. Приоритет — снижение информационной нагрузки.</div>\n      </div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"wrap\">\n    <div class=\"kicker\">Валидация</div>\n    <h2>Сопоставление с данными LEMON</h2>\n    <p class=\"lede\">Модель тестировалась на датасете LEMON (Лейпциг, n=199) — сопоставление архитектурных индексов с независимо измеренными психометрическими показателями.</p>\n\n    <div class=\"val-grid\">\n      <div class=\"val-stat\">\n        <div class=\"val-num\">ρ = 0.20</div>\n        <div class=\"val-label\">Тревожность · p = 0.004</div>\n      </div>\n      <div class=\"val-stat\">\n        <div class=\"val-num\">ρ = 0.26</div>\n        <div class=\"val-label\">Импульсивность · p = 0.0002</div>\n      </div>\n      <div class=\"val-stat\">\n        <div class=\"val-num\">ρ = 0.23</div>\n        <div class=\"val-label\">Стресс · p = 0.001</div>\n      </div>\n    </div>\n\n    <p class=\"val-note\">Показатели приведены по материалам автора проекта; в этой версии страницы исходные расчёты не перепроверялись. Эти ассоциации сами по себе не доказывают причинность, индивидуальную точность или клиническую валидность. LEMON используется как отдельный исследовательский слой, а не как вход клиентского расчёта 43.</p>\n  </div>\n</section>\n\n<section>\n  <div class=\"wrap\">\n    <div class=\"kicker\">Почему это не астрология</div>\n    <h2>Различие в методе, не в теме Солнца</h2>\n    <table>\n      <tr><th>Критерий</th><th>Астрология</th><th>ARCHVIQ</th></tr>\n      <tr><td>Данные</td><td>Символическое положение объектов</td><td class=\"arch\">Измеренный ряд солнечной активности</td></tr>\n      <tr><td>Механизм</td><td>Символическая интерпретация</td><td class=\"arch\">Проверяемая нейродинамическая гипотеза</td></tr>\n      <tr><td>Расчёт</td><td>Качественное толкование</td><td class=\"arch\">Воспроизводимый алгоритм</td></tr>\n      <tr><td>Проверка</td><td>Обычно отсутствует</td><td class=\"arch\">Возможна на EEG и когнитивных данных</td></tr>\n      <tr><td>Отриц. результат</td><td>Не изменяет систему</td><td class=\"arch\">Приводит к пересмотру гипотезы</td></tr>\n    </table>\n  </div>\n</section>\n\n<section>\n  <div class=\"wrap\">\n    <div class=\"kicker\">Что установлено, а что остаётся гипотезой</div>\n    <h2>Три уровня, которые нельзя смешивать</h2>\n    <div class=\"tiers\">\n      <div class=\"tier\">\n        <h3>Установленные данные</h3>\n        <ul>\n          <li>Нервная система формируется последовательно, с чувствительными периодами</li>\n          <li>Солнечная активность измеряется инструментально</li>\n          <li>EEG и когнитивные тесты измеряют функциональные свойства мозга</li>\n        </ul>\n      </div>\n      <div class=\"tier\">\n        <h3>Результаты модели</h3>\n        <ul>\n          <li>Индивидуальные оконные сигнатуры</li>\n          <li>Девять скрытых состояний</li>\n          <li>Оси RS1–RS4</li>\n        </ul>\n      </div>\n      <div class=\"tier\">\n        <h3>Исследовательские гипотезы</h3>\n        <ul>\n          <li>Биологически значимое влияние ЭМП-динамики на нейрогенез</li>\n          <li>Соответствие параметров кода 43 EEG-фенотипам</li>\n          <li>Прогноз индивидуальной реакции на геомагнитную динамику</li>\n        </ul>\n      </div>\n    </div>\n  </div>\n</section>\n\n<section>\n  <div class=\"wrap\">\n    <div class=\"kicker\">Автор проекта</div>\n    <div class=\"author\">\n      <img class=\"author-portrait\" src=\"data:image/jpeg;base64,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\" alt=\"Andrey Osipov\">\n      <div>\n        <div class=\"author-name\">Andrey Osipov, MD, PhD</div>\n        <div class=\"author-role\">Physician-Scientist · Neurophysiology, EEG & AI</div>\n        <p>Окончил Первый Ленинградский медицинский институт. 20 лет клинической практики: 15 лет — акушер-гинеколог, 7 лет — главный врач. Защитил кандидатскую диссертацию в Военно-медицинской академии Санкт-Петербурга.</p>\n        <p>Сегодня его исследования находятся на пересечении нейрофизиологии, EEG, искусственного интеллекта и вычислительного моделирования индивидуальной архитектуры мозга.</p>\n      </div>\n    </div>\n  </div>\n</section>\n\n<div class=\"wrap final\">\n  <h2>Узнайте устройство своей системы, а не ярлык личности</h2>\n  <p class=\"lede\">Первый шаг — рассчитать архитектурный профиль по коду 43.</p>\n  <a class=\"btn-primary\" href=\"?archviq=profile\" target=\"_self\">Рассчитать профиль</a>\n</div>\n\n<footer>\n  <div class=\"wrap foot-row\">\n    <span>ARCHVIQ · LANDING V6.1</span>\n    <span>archviq.com</span>\n  </div>\n</footer>\n\n</div>"

def render_landing_v6():
    st.html(LANDING_V6_HTML)


def get_cognitive_html():
    return gzip.decompress(
        base64.b64decode(COGNITIVE_HTML_GZ_B64)
    ).decode("utf-8")


SCIENCE_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root {
  --ink:#ECEEF3; --muted:#8C96AE; --cyan:#6FD8C4; --gold:#E3A34E;
  --slate:#A7B0C8; --panel:rgba(18,26,48,.82); --line:rgba(180,190,214,.16);
}
.stApp, p, li, label, button, input {font-family:'IBM Plex Sans',sans-serif}.stApp {
  color:var(--ink);
  background:
    radial-gradient(circle at 12% 8%, rgba(227,163,78,.10), transparent 31rem),
    radial-gradient(circle at 88% 22%, rgba(111,216,196,.08), transparent 34rem),
    linear-gradient(145deg,#0A0E1A 0%,#0D1220 52%,#0B0F1C 100%);
}
.stApp::before {
  content:"ΔSSN(t)    ∂²S/∂t²    Xₖ₊₁ = DₖXₖ + GₖFₖ + C(Xₖ)\A\A RS₁ = rhythm · stability     RS₂ = synchrony · hubness\A\A W₀ → W₁ → W₂ → W₃ → W₄ → W₅ → N₀ → P₁ … P₈\A\A Fₖ = dynamic + instability + |direction|";
  white-space:pre-wrap; position:fixed; inset:7rem 2vw auto auto; width:38vw;
  color:rgba(227,163,78,.05); font:600 18px/2.3 'IBM Plex Mono',monospace;
  transform:rotate(-8deg); pointer-events:none; z-index:0;animation:neuralDrift 16s ease-in-out infinite alternate;
}
@keyframes neuralDrift{from{transform:translate3d(0,0,0) rotate(-8deg);opacity:.75}to{transform:translate3d(-24px,18px,0) rotate(-5deg);opacity:1}}
[data-testid="stAppViewContainer"] > .main {position:relative;z-index:1}
.block-container {max-width:1180px;padding-top:2.1rem;padding-bottom:5rem}
h1,h2,h3 {font-family:'Newsreader',serif;font-weight:500;letter-spacing:0;color:#F4F0E8}
h1 {font-size:clamp(2.2rem,5.5vw,4.3rem)!important;line-height:1.05!important}
p,li {line-height:1.65}
.hero-kicker {font:600 .76rem/1 'IBM Plex Mono',monospace;letter-spacing:.18em;color:var(--cyan);text-transform:uppercase;margin-bottom:1.1rem}
.hero-copy {font-size:1.18rem;color:var(--muted);max-width:800px;line-height:1.7;margin:1.2rem 0 1.5rem}
.science-card,.axis-card,.protocol-card,.pair-card {
  background:linear-gradient(145deg,rgba(18,26,48,.91),rgba(11,15,28,.82));
  border:1px solid var(--line);border-radius:18px;padding:1.2rem 1.35rem;margin:.55rem 0;
  box-shadow:0 14px 38px rgba(0,0,0,.18);
}
.science-card h3,.axis-card h3,.protocol-card h3,.pair-card h3 {font-family:'Newsreader',serif;font-style:italic;font-weight:500;font-size:1.08rem;margin:.1rem 0 .5rem;color:var(--ink)}
.science-card p,.axis-card p,.protocol-card p,.pair-card p {font-size:.94rem;color:var(--muted);margin:.25rem 0}
.formula {background:rgba(6,10,20,.7);border-left:3px solid var(--cyan);padding:1rem 1.2rem;border-radius:4px 14px 14px 4px;font:500 .92rem/1.7 'IBM Plex Mono',monospace;color:#CDEFE7;margin:1rem 0}
.pipeline {display:grid;grid-template-columns:repeat(5,1fr);gap:.55rem;margin:1.3rem 0}
.pipe-node {border:1px solid var(--line);border-radius:14px;padding:.9rem .7rem;text-align:center;background:rgba(18,26,48,.72);font-size:.8rem;color:var(--muted)}
.pipe-node b {display:block;color:var(--cyan);font-size:.78rem;margin-bottom:.35rem}
.eyebrow {font:600 .72rem/1 'IBM Plex Mono',monospace;letter-spacing:.14em;color:var(--cyan);text-transform:uppercase}
.score {font:500 2.15rem/1 'IBM Plex Mono',monospace;color:var(--ink)}
.level-low {color:#68e0b4}.level-mid {color:#ffd166}.level-high {color:#ff7e8d}
.micro {font-size:.78rem;color:var(--muted)}
.founder-photo{width:100%;border-radius:24px;border:1px solid rgba(227,163,78,.4);box-shadow:0 24px 70px rgba(0,0,0,.45);display:block}
.bio-role{color:var(--gold);font:600 .9rem/1.5 'IBM Plex Mono',monospace;margin:-.4rem 0 1.2rem}
.comparison-table{width:100%;border-collapse:collapse;margin:1rem 0 1.5rem;background:rgba(13,18,32,.72);border-radius:16px;overflow:hidden}
.comparison-table th,.comparison-table td{border-bottom:1px solid var(--line);padding:.8rem 1rem;text-align:left;font-size:.9rem}.comparison-table th{color:var(--cyan);background:rgba(111,216,196,.08)}
.price-card{min-height:185px;background:linear-gradient(145deg,rgba(18,26,48,.94),rgba(11,15,28,.9));border:1px solid var(--line);border-radius:18px;padding:1.2rem;margin:.4rem 0}.price-card b{font:600 1.05rem 'Newsreader',serif;color:#fff}.price{font:500 2rem 'IBM Plex Mono',monospace;color:var(--gold);margin:.7rem 0}.price-card p{color:var(--muted);font-size:.84rem}
.rule {height:1px;background:linear-gradient(90deg,var(--gold),transparent);margin:1.2rem 0}
[data-testid="stMetric"] {background:rgba(18,26,48,.78);border:1px solid var(--line);padding:1rem;border-radius:14px}
[data-testid="stExpander"] {background:rgba(13,18,32,.72);border-color:var(--line);border-radius:14px}
.stButton>button {border-radius:12px;border:1px solid rgba(227,163,78,.35);min-height:2.8rem}
.stButton>button[kind="primary"] {background:var(--gold);color:#171106;border:0}
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
    st.markdown('<div class="hero-kicker">FOUNDER · PHYSICIAN-SCIENTIST</div>',unsafe_allow_html=True)
    left,right=st.columns([.78,1.5],gap="large")
    with left:
        uri=founder_photo_uri()
        if uri:
            st.markdown(f'<img class="founder-photo" src="{uri}" alt="Andrey Osipov">',unsafe_allow_html=True)
    with right:
        st.header("Andrey Osipov, MD, PhD")
        st.markdown('<div class="bio-role">Physician-Scientist | Independent Researcher | Neurophysiology, EEG & AI</div>',unsafe_allow_html=True)
        if st.session_state.lang=="RU":
            st.markdown("""
**Образование и опыт**

- Окончил Первый Ленинградский медицинский институт.
- Прошёл интернатуру и ординатуру; более 15 лет работал в клинической медицине.
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
- Completed internship and residency training and worked in clinical medicine for more than 15 years.
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
        "Интеграция EEG, когнитивных тестов и ИИ для индивидуальной характеристики состояния мозга.",
        "EEG-биомаркеры когнитивной обработки, регуляции, стабильности, гибкости и функциональной организации.",
        "ИИ-ассистируемая нейрообратная связь и интерфейсы мозг–компьютер, адаптирующиеся к индивидуальным EEG-паттернам.",
        "Влияние пренатальных окон развития и электромагнитных факторов среды на последующую нейрофункциональную организацию.",
        "Биомиметические вычислительные методы для адаптивной обработки сигналов и интеллектуальных систем управления.",
    ]
    cols=st.columns(2)
    for i,item in enumerate(focus_ru if st.session_state.lang=="RU" else focus_en):
        with cols[i%2]: card(f"0{i+1}",item,"RESEARCH")
    st.info(tr(
        "Current objective: to build a scalable technology platform combining EEG, AI, individualized neurophysiological modeling, and adaptive feedback, with potential applications in digital health, cognitive assessment, neurotechnology, human performance, and intelligent human-machine interaction.",
        "Текущая цель: масштабируемая платформа, объединяющая EEG, ИИ, индивидуальное нейрофизиологическое моделирование и адаптивную обратную связь для цифрового здоровья, когнитивной оценки, нейротехнологий, работоспособности и интеллектуального взаимодействия человека с машиной."
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


def render_pricing():
    offers=[
        (tr("Architecture profile","Архитектурный профиль"),tr("RS axes and basic type","Оси RS и базовый тип"),"FREE"),
        (tr("Cognitive test + GAP","Когнитивный тест + GAP"),tr("Five measured tasks","Пять измерительных задач"),"$12"),
        (tr("Target questionnaire","Целевой опросник"),tr("Burnout, compatibility or AI","Выгорание, совместимость или ИИ"),"$19"),
        (tr("Full protocol","Полный протокол"),tr("Integrated report + biohacking","Интегрированный отчёт + биохакинг"),"$39"),
    ]
    cols=st.columns(4)
    for col,(name,desc,price) in zip(cols,offers):
        with col: st.markdown(f'<div class="price-card"><b>{name}</b><div class="price">{price}</div><p>{desc}</p></div>',unsafe_allow_html=True)


def purchase_button(label,product_key):
    url=os.getenv(f"GUMROAD_{product_key.upper()}_URL",os.getenv("GUMROAD_URL",""))
    if url:
        st.link_button(label,url,width="stretch")


def render_rs_radar(profile,title=""):
    labels=["RS1 · Rhythm","RS2 · Sync","RS3 · Topology","RS4 · Integral"]
    values=[max(0,min(100,safe_num(profile.get(k,50)))) for k in ("rs1","rs2","rs3","rs4")]
    fig=go.Figure(go.Scatterpolar(r=values+[values[0]],theta=labels+[labels[0]],fill="toself",line=dict(color="#6FD8C4",width=3),fillcolor="rgba(111,216,196,.25)",name=profile.get("name","Profile")))
    fig.update_layout(template="plotly_dark",height=410,margin=dict(l=40,r=40,t=55,b=35),paper_bgcolor="rgba(0,0,0,0)",polar=dict(bgcolor="rgba(13,18,32,.55)",radialaxis=dict(range=[0,100],showticklabels=True,gridcolor="rgba(180,190,214,.2)")),showlegend=False,title=title)
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})


def architecture_type(profile,interp=None):
    supplied=str(profile.get("type_name","")).lower()
    for key in ("fortress","antenna","fluid","collapse"):
        if key in supplied:return key
    idx=(interp or {}).get("indices",{})
    overload=idx.get("overload",{}).get("value",safe_num(profile.get("tension")))
    recovery=idx.get("recovery",{}).get("value",safe_num(profile.get("adaptive")))
    sensitivity=(profile.get("raw") or {}).get("X_SENS",0)
    rigidity=idx.get("rigidity",{}).get("value",50)
    flexibility=idx.get("flexibility",{}).get("value",50)
    if overload>=70 and recovery<38:return "collapse"
    if sensitivity>=16 or idx.get("autonomic",{}).get("value",50)>=67:return "antenna"
    if rigidity>=60:return "fortress"
    return "fluid" if flexibility>=50 else "fortress"


TYPE_CONTENT={
 "RU":{
  "fortress":("FORTRESS · Крепость","🛡️","Архитектура опирается на устойчивые внутренние модели, специализацию и сохранение структуры. Она хорошо удерживает долгие задачи и защищает фокус от внешнего шума.","В жизни это проявляется как потребность сначала понять систему, а затем действовать последовательно. Сильная сторона — глубина и надёжность; цена — более дорогая внезапная смена контекста.","Полезная стратегия: длинные блоки самостоятельной работы, заранее обозначенные переходы и восстановление без новых входящих сигналов."),
  "antenna":("ANTENNA · Антенна","📡","Архитектура обладает высоким входным усилением: быстро замечает изменения, несоответствия и эмоциональные сигналы. Она собирает больше контекста, чем требуется для простой реакции.","В жизни это даёт интуитивное распознавание обстановки и быстрый отклик, но увеличивает цену информационного и эмоционального шума.","Полезная стратегия: управлять числом входящих каналов, защищать сон и чередовать интенсивное взаимодействие с периодами сенсорного снижения."),
  "fluid":("FLUID · Поток","🌊","Архитектура легко перестраивает связи и меняет способ обработки по контексту. Её преимущество — адаптация и создание альтернатив.","В жизни это проявляется как способность быстро войти в новую тему и соединить удалённые идеи. Риск — распыление внимания и недостаточное закрепление результата.","Полезная стратегия: ограничивать число параллельных направлений и завершать цикл явной фиксацией решения."),
  "collapse":("COLLAPSE · Перегруженный режим","⚠️","Текущая конфигурация показывает высокую нагрузку при ограниченном резерве управления. Это описание режима системы, а не диагноз и не неизменный тип личности.","В жизни возможны фрагментация внимания, дорогие переключения и снижение качества решений после накопления усталости.","Полезная стратегия: сначала восстановить сон и снизить одновременную нагрузку, затем повторить когнитивные измерения и проверить, изменился ли профиль."),
 },
 "EN":{
  "fortress":("FORTRESS","🛡️","This architecture relies on stable internal models, specialization and structural persistence. It supports long tasks and protects focus from external noise.","In daily life it prefers understanding the system before acting consistently. Its strength is depth and reliability; abrupt context changes carry a higher cost.","Use long independent focus blocks, explicit transitions and recovery with reduced incoming stimulation."),
  "antenna":("ANTENNA","📡","This architecture has high input gain: it detects changes, mismatches and emotional signals quickly and collects more context than a simple response requires.","In daily life this supports intuitive situation reading and rapid response while increasing the cost of informational and emotional noise.","Control the number of input channels, protect sleep and alternate intensive contact with low-stimulation periods."),
  "fluid":("FLUID","🌊","This architecture reorganizes connections readily and changes processing strategy with context. Its advantage is adaptation and option generation.","In daily life it enters new topics quickly and links distant ideas. The risk is attention dispersion and insufficient consolidation.","Limit simultaneous directions and finish each cycle by explicitly recording the decision."),
  "collapse":("COLLAPSE · OVERLOADED MODE","⚠️","The current configuration indicates high load with limited control reserve. It describes a system mode, not a diagnosis or an immutable personality type.","Daily expression can include fragmented attention, costly switching and poorer decisions after fatigue accumulates.","Restore sleep and reduce simultaneous load first, then repeat cognitive measurement to test whether the profile changes."),
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
    st.markdown(f'<div class="science-card" style="border-color:{color}88;background:linear-gradient(135deg,{color}25,rgba(7,20,36,.88))"><div class="eyebrow">ARCHITECTURE TYPE</div><h3>{icon} {title}</h3></div>',unsafe_allow_html=True)
    for p in paras:st.write(p)
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
    'padding:6px 9px">ARCHVIQ · LANDING V6.1</div>',
    unsafe_allow_html=True,
)

# ── Состояние ──────────────────────────────────────────────────────────────
for k,v in {
    "step": "landing",
    "lang": "RU",
    "p1": None, "p2": None,
    "mode": "personal",
    "quiz": None,
    "quiz_answers": {},
    "cog_done": False,
    "cognitive_results": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# Consume only our navigation parameter; preserve unrelated query parameters.
route = st.query_params.get("archviq")
if route in ("profile", "test", "home"):
    del st.query_params["archviq"]
    if route == "profile":
        st.session_state.mode = "personal"
        st.session_state.step = "input"
    elif route == "home":
        st.session_state.step = "landing"
    else:
        st.session_state.step = "cognitive" if st.session_state.p1 else "test_preview"

if st.session_state.step == "test_preview":
    st.title("Когнитивный тест")
    st.info("Тест можно пройти без профиля. Для GAP-сопоставления сначала рассчитайте профиль 43, затем загрузите CSV результата на экране теста.")
    import streamlit.components.v1 as components
    components.html(get_cognitive_html(), height=1050, scrolling=True)
    if st.button("← На главную"):
        st.session_state.step = "landing"
        st.rerun()
    st.stop()

L = st.session_state.lang

# ── Переводы ───────────────────────────────────────────────────────────────
T = {
    "title": {"EN": "Archviq", "RU": "Archviq"},
    "subtitle": {
        "EN": "Your neural architecture — based on prenatal solar dynamics",
        "RU": "Ваша нейронная архитектура — на основе пренатальной солнечной динамики",
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
    "start_btn": {"EN": "Decode Your Brain →", "RU": "Расшифровать архитектуру мозга →"},
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
    render_landing_v6()
    st.caption("Главная страница — русский макет v6. Язык профиля и тестовых экранов выбирается вверху.")
    mode = st.radio(t("mode_label"), t("mode_opts"), horizontal=True)
    st.session_state.mode = "compat" if mode == t("mode_opts")[-1] else "personal"
    if st.button(t("start_btn"), key="v6_start", type="primary"):
        st.session_state.step = "input"
        st.rerun()

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
    st.markdown(f'<div class="hero-copy">{p.get("tagline","")}</div>',unsafe_allow_html=True)
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
    purchase_button(tr("Full report + biohacking protocol · $39","Полный отчёт + биохакинг-протокол · $39"),"full")

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
    import streamlit.components.v1 as components
    components.html(get_cognitive_html(), height=1050, scrolling=True)
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
    st.metric(t("compat_score"),f"{score:.0f}%",compat.get("summary",""))
    st.caption(tr(
        "The score is only a map of architectural distance. Relationship quality depends on the way two systems coordinate load, communication, recovery and decisions.",
        "Балл показывает только архитектурную дистанцию. Качество отношений зависит от того, как две системы согласуют нагрузку, общение, восстановление и решения."
    ))

    c1,c2=st.columns(2)
    for col,person in ((c1,p1),(c2,p2)):
        with col:
            st.markdown(f'<div class="pair-card"><div class="eyebrow">{person.get("type_name","")}</div><h3>{person.get("name","")}</h3><p>{person.get("tagline","")}</p></div>',unsafe_allow_html=True)
            a,b=st.columns(2)
            a.metric("RS4",f"{safe_num(person.get('rs4')):.1f}")
            b.metric(tr("Tension","Напряжение"),f"{safe_num(person.get('tension')):.1f}")

    architecture,dynamics,protocol,monitoring=st.tabs([
        tr("Pair architecture","Архитектура пары"),tr("Relationship dynamics","Динамика отношений"),
        tr("Behavior protocol","Протокол поведения"),tr("Control & forecast","Контроль и прогноз")])
    with architecture:
        r1,r2=st.columns(2)
        with r1: render_rs_radar(p1,p1.get("name","P1"))
        with r2: render_rs_radar(p2,p2.get("name","P2"))
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
        items=list(compat.get("dynamics",[]))
        if deep: items+=deep.get("dynamics",[])
        for d in dict.fromkeys(items): card(tr("Observed pair mechanism","Механизм пары"),d,"ARCHITECTURE → INTERACTION")
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
