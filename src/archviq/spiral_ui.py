"""Streamlit concept and interpretation views; calculation stays in the runner."""
from __future__ import annotations

import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from .spiral_guide import (
    GUIDE_CSS, STAGES, build_guide, concept_html, guide_markdown,
    parameter_html, spiral_svg, tx,
)


def language():
    return st.session_state.get("lang", "RU")


def say(ru, en):
    return tx(ru, en, language())


def diagram(stage="admission"):
    components.html(
        '<style>html,body{margin:0;background:transparent}svg{width:100%;height:100vh}</style>'
        + spiral_svg(language(), stage), height=460, scrolling=False,
    )
    st.caption(say("Каждый виток повторяет полный цикл. Уровни спирали — способы представления информации, а не отделы мозга.",
                   "Each loop repeats the full cycle. Spiral levels describe information representations, not brain regions."))


def render_concept(compact=False, key="concept"):
    st.markdown(GUIDE_CSS, unsafe_allow_html=True)
    left, right = st.columns([1, 1.1], gap="large")
    with left:
        st.markdown(say('<div class="kicker">ОДИН КОНТУР · МНОГО ВИТОКОВ</div>',
                        '<div class="kicker">ONE CIRCUIT · MANY LOOPS</div>'), unsafe_allow_html=True)
        st.subheader(say("От наблюдения — к объяснению, действию и пересмотру", "From observation to explanation, action and revision"))
        st.write(say("Спираль описывает, как система снова и снова принимает информацию, проверяет её, удерживает рабочее объяснение, выбирает действие и учится на последствиях.",
                     "The spiral describes how a system repeatedly admits information, checks it, retains a working explanation, chooses an action and learns from consequences."))
        st.write(say("Почему спираль сужается? Множество деталей собирается в более короткое представление: наблюдения → проверенная картина → правило → модель. Это сжатие сохраняет связь с источниками. Каждый новый уровень снова проходит полный цикл.",
                     "Why does the spiral narrow? Many details become a shorter representation: observations → checked picture → rule → model. Compression retains provenance. Each new level repeats the full cycle."))
        st.write(say("Чем отличаются люди в этой модели? Настройками допуска, накопления, удержания, переключения и обновления. У одного контура может быть много моделей; в данный момент работает выбранная конфигурация.",
                     "How do people differ in this model? Admission, accumulation, retention, switching and revision settings. One circuit can hold many models; a selected configuration is active at a given moment."))
    with right:
        diagram(st.session_state.get(f"spiral_operation_{key}", "admission"))
    st.info(say("Анализ по SSN предлагает гипотезу о настройках этого контура. Он не измеряет работу мозга сейчас. Для проверки нужны отдельные наблюдения и задачи.",
                "SSN analysis proposes a hypothesis about these settings. It does not measure current brain function. Testing requires separate observations and tasks."))
    if not compact:
        render_thresholds()
        st.subheader(say("Пример: вы получили совет изменить рабочий план", "Example: you receive advice to change a work plan"))
        examples = [
            ("01", say("Допустить сигнал", "Admit the input"), say("Вы замечаете совет. История источника влияет на внимание, но не делает совет истинным.", "You notice the advice. Source history affects attention without making the advice true.")),
            ("02", say("Проверить и собрать объяснение", "Check and build an explanation"), say("Вы отличаете независимые факты от пересказов, сверяете их с наблюдением и формулируете рабочее правило.", "You distinguish independent facts from retellings, check observations and form a working rule.")),
            ("03", say("Решить, затем действовать", "Decide, then act"), say("Данных хватает для выбора. Начать выполнение — отдельный переход; решение не означает, что действие уже состоялось.", "Evidence becomes sufficient for a choice. Starting execution is a separate transition; choosing is not already acting.")),
            ("04", say("Исправить подходящий уровень", "Correct the appropriate level"), say("Если результат не совпал с ожиданием, можно изменить исполнение, правило или объяснение. Не каждая ошибка требует новой модели.", "If outcomes differ from expectations, execution, the rule or the explanation can change. Not every error requires a new model.")),
        ]
        cols = st.columns(2)
        for i, (num, title, body) in enumerate(examples):
            with cols[i % 2]:
                st.markdown(f'<div class="sg-card"><span class="sg-code">{num}</span><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
        st.write(say("Память возвращает материал на вход с меткой «изнутри»; якоря дают опору для проверки. Γ обозначает офлайн-перекалибровку, связанную в концепции со сном. Это функциональные гипотезы, а не доказанная карта анатомии.",
                     "Memory returns material with an internal-source tag; anchors provide references for checks. Γ denotes offline recalibration, linked to sleep in the concept. These are functional hypotheses, not an established anatomical map."))
        render_walkthrough(None, key)


def render_thresholds(profile=None):
    st.subheader(say("«Решил», «сделал» и «изменил модель» — три разных перехода", "Choosing, acting and revising a model are three different transitions"))
    guide = build_guide(profile, language()) if profile else None
    by_code = {p["code"]: p for p in guide["parameters"]} if guide else {}
    items = [
        ("THETA_D", "Θ_D", say("Порог решения", "Decision threshold"), say("Сколько свидетельств достаточно, чтобы зафиксировать выбор.", "How much evidence is sufficient to commit to a choice.")),
        ("THETA_A", "Θ_A", say("Порог действия", "Action threshold"), say("Когда выбранное решение переходит в выполнение.", "When a chosen decision proceeds to execution.")),
        ("THETA_U", "Θ_U", say("Порог пересмотра", "Revision threshold"), say("Сколько противоречия требуется, чтобы изменить само объяснение.", "How much contradiction is needed to change the explanation itself.")),
    ]
    for col, (code, symbol, title, body) in zip(st.columns(3), items):
        with col:
            p = by_code.get(code)
            detail = f'<p class="sg-small"><b>{html.escape(p["label"])}</b><br>{html.escape(p["meaning"])}</p>' if p else ""
            st.markdown(f'<div class="sg-card"><span class="sg-code">{symbol}</span><h3>{title}</h3><p>{body}</p>{detail}</div>', unsafe_allow_html=True)
    st.caption(say("Порог — условие перехода. Уровень представления — то, над чем система работает. Эти две вещи не объединяются в одну шкалу.",
                   "A threshold is a transition condition. A representation level is what the system works on. They are separate variables."))


def render_walkthrough(profile, key="result"):
    st.subheader(say("Разберите спираль по операциям", "Explore the spiral by operation"))
    stage_labels = {s[0]: s[1 if language() == "RU" else 2] for s in STAGES}
    chosen = st.radio(say("Выберите операцию", "Choose an operation"), [s[0] for s in STAGES],
                      format_func=stage_labels.get,
                      horizontal=True, key=f"spiral_operation_{key}")
    stage = next(s for s in STAGES if s[0] == chosen)
    st.markdown(f'**{stage[3 if language() == "RU" else 4]}**')
    st.write(stage[5 if language() == "RU" else 6])
    if profile:
        params = [p for p in build_guide(profile, language())["parameters"] if p["stage"] == chosen]
        if not params:
            st.info(say("Для этой операции параметры в результате отсутствуют.", "No parameters for this operation are present in the result."))
        cols = st.columns(2)
        for i, p in enumerate(params):
            with cols[i % 2]:
                st.markdown(parameter_html(p, language()), unsafe_allow_html=True)
    else:
        st.caption(say("После расчёта здесь появятся ваши параметры, их направление, диапазон вариантов и способ проверки.",
                       "After calculation, this view shows your parameters, direction, range across variants and a way to check each one."))


def render_profile_story(profile):
    st.markdown(GUIDE_CSS, unsafe_allow_html=True)
    guide = build_guide(profile, language())
    st.subheader(say("Как читать вашу модель процессинга", "How to read your processing model"))
    st.write(say("Ниже расчёт переведён в операции спирали. Числа показывают сдвиги внутри модели, а описания объясняют их возможный функциональный смысл. Это отправная точка для проверки, а не установленный портрет человека.",
                 "The calculation is translated into spiral operations below. Numbers describe model shifts; explanations describe their possible functional meaning. This is a starting point for testing, not an established portrait of a person."))
    for col, label, value in zip(st.columns(3),
                                [say("Устойчивое направление", "Stable model direction"), say("Направление неустойчиво / мало", "Uncertain / small direction"), say("Только нагрузка узла", "Node load only")],
                                [len(guide["stable"]), len(guide["unresolved"]), len(guide["pressure_only"])]):
        col.metric(label, value)
    st.caption(say("Устойчивость означает согласие вариантов расчёта. Она не подтверждает связь с реальным поведением или физиологией.",
                   "Stability means agreement across calculation variants. It does not confirm an association with actual behavior or physiology."))
    if guide["stable"]:
        st.markdown(say("**На какие гипотезы сначала обратить внимание**", "**Hypotheses to examine first**"))
        highlights, used = [], set()
        for p in guide["stable"]:
            if p["stage"] not in used:
                highlights.append(p)
                used.add(p["stage"])
            if len(highlights) == 3:
                break
        for p in highlights:
            st.markdown(f'**{p["name"]}.** {p["meaning"]}')
    else:
        st.info(say("В этом результате нет направлений, устойчивых по заданным критериям модели. Персональную стратегию по таким числам назначать нельзя.",
                    "No directions meet the model's stability criteria in this result. These numbers cannot prescribe a personal strategy."))
    with st.expander(say("Что означают число, диапазон и H*", "What the value, range and H* mean")):
        st.write(say("Знак «+» или «−» — направление относительно исходного состояния модели, не оценка «лучше / хуже». Значение не является процентом, нормой или процентилем.",
                     "A plus or minus sign indicates direction from the model's initial state, not better or worse. Values are not percentages, norms or percentiles."))
        st.write(say("Диапазон — разброс вариантов расчёта при выбранной неопределённости даты и двух размерах пакета. Это не статистический доверительный интервал. Пересечение нуля делает направление неопределённым.",
                     "The range describes calculation variants for the chosen date uncertainty and two packet sizes. It is not a statistical confidence interval. Crossing zero makes direction uncertain."))
        st.write(say("H* — вектор параметров модели, условная опорная конфигурация. Он не показывает текущее состояние мозга. Узлы «только нагрузка» не сообщают, высока или низка соответствующая функция.",
                     "H* is a model parameter vector, a conditional reference configuration. It does not show current brain state. Load-only nodes do not indicate high or low functional capacity."))
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")
    with left:
        diagram(st.session_state.get("spiral_operation_result", "admission"))
    with right:
        st.markdown(say("**Ваш расчёт внутри спирали**", "**Your calculation within the spiral**"))
        for stage in STAGES:
            params = [p for p in guide["stable"] if p["stage"] == stage[0]]
            body = params[0]["meaning"] if params else say("Устойчивое направление в этой операции не выделено. Параметры можно посмотреть ниже.", "No stable direction is identified for this operation. Its parameters are available below.")
            st.markdown(f'<div class="sg-compact"><b>{html.escape(stage[1 if language() == "RU" else 2])}</b><p>{html.escape(body)}</p></div>', unsafe_allow_html=True)
    render_thresholds(profile)
    render_walkthrough(profile)
    with st.expander(say("Все параметры с расшифровкой и способом проверки", "All parameters with explanations and checks")):
        rows = [{say("Параметр", "Parameter"): p["name"], say("Код", "Code"): p["code"], say("Статус", "Status"): p["label"],
                 say("Смысл", "Meaning"): p["meaning"], say("Как проверить", "How to check"): p["check"]} for p in guide["parameters"]]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_use_cases(profile):
    st.subheader(say("Что этот анализ даёт дальше", "What this analysis helps you do next"))
    st.write(say("Полезный итог — конкретный вопрос для проверки. Выберите одну операцию, запишите ожидаемое поведение и сравните его с результатами повторяемой задачи. Сохраните и совпадения, и расхождения.",
                 "A useful outcome is a specific testable question. Choose one operation, record the expected behavior and compare it with a repeatable task. Retain both agreements and disagreements."))
    cases = [
        (say("Решения", "Decisions"), say("Разделить «данных достаточно», «выбор сделан» и «действие началось». Записать условия, время и ошибки для каждого перехода.", "Separate sufficient evidence, committed choice and action onset. Record conditions, timing and errors for each transition.")),
        (say("Работа и обучение", "Work and learning"), say("Проверить удержание правила, переключение и пересмотр после ошибки. Изменять по одному условию, сохраняя одинаковую задачу.", "Check rule retention, switching and revision after error. Change one condition at a time while keeping the task comparable.")),
        (say("Взаимодействие с ИИ", "Working with AI"), say("Сохранять источники, отделять наблюдение от вывода и заранее задавать, какой факт потребует пересмотра ответа.", "Retain sources, separate observations from inferences and specify which fact would require revising an answer.")),
        (say("Состояние во времени", "State over time"), say("Повторять короткую задачу при сопоставимых условиях, отмечая сон и нагрузку. Не считать модельную нагрузку измерением выгорания.", "Repeat a short task under comparable conditions, recording sleep and workload. Do not treat model load as a burnout measurement.")),
    ]
    cols = st.columns(2)
    for i, (title, body) in enumerate(cases):
        with cols[i % 2]:
            st.markdown(f'<div class="sg-card"><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
    guide = build_guide(profile, language())
    if guide["stable"]:
        first = guide["stable"][0]
        st.success(say("Первый вопрос из вашего расчёта: ", "First question from your calculation: ") + first["name"] + ". " + first["check"])
    st.caption(say("Это план наблюдения, а не валидированная рекомендация. Несовпадение не списывается автоматически на компенсацию: неверная модель тоже возможна. Готового перевода тестовых баллов в H* пока нет.",
                   "This is an observation plan, not a validated recommendation. Disagreement is not automatically attributed to compensation: the model may be wrong. A calibrated conversion from task scores to H* is not yet available."))


def render_explanation_downloads(profile):
    left, right = st.columns(2)
    with left:
        st.download_button(say("Скачать понятный отчёт HTML", "Download the explained HTML report"),
                           concept_html(language(), profile).encode("utf-8"), "archviq_spiral_explained.html", "text/html", use_container_width=True)
    with right:
        st.download_button(say("Скачать расшифровку Markdown", "Download explanations as Markdown"),
                           guide_markdown(profile, language()).encode("utf-8"), "archviq_spiral_explained.md", "text/markdown", use_container_width=True)
