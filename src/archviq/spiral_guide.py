"""Presentation of the existing cascade outputs. No new calculation or scores."""
from __future__ import annotations

import html
import math
from typing import Any

from .frozen.archviq_personal_interpreter_v0_1 import PARAM_RU, DIRECTIONAL_EPS

VERSION = "4.1-explained"


def tx(ru: str, en: str, lang: str) -> str:
    return ru if lang == "RU" else en


NAMES = {
    "GAIN": ("Сила отклика на вход", "Response to input"),
    "NOISE_SENSITIVITY": ("Обработка нерегулярного сигнала", "Irregular-input processing"),
    "RECOVERY_BASELINE": ("Возврат к опорному состоянию", "Return to reference state"),
    "THETA_W": ("Порог допуска информации", "Information admission threshold"),
    "THETA_C": ("Порог запроса проверки фактов", "Reality-check request threshold"),
    "TAU_INTEGRATION": ("Время накопления информации", "Evidence integration time"),
    "THETA_NU_TIME": ("Проверка временной структуры сигнала", "Signal timing checks"),
    "THETA_NU_CROSS": ("Проверка независимости источников", "Source independence checks"),
    "THETA_NU_PROVENANCE": ("Проверка происхождения информации", "Information provenance checks"),
    "M_C": ("Требование независимых подтверждений", "Independent confirmation requirement"),
    "COMPRESSION_STRENGTH": ("Сжатие деталей в общую схему", "Compression into a general representation"),
    "D_C": ("Закрепление подтверждённого представления", "Consolidation after confirmation"),
    "PERSISTENCE": ("Длительность удержания рабочего состояния", "Working-state persistence"),
    "HOLD_STABILITY": ("Устойчивость выбранного режима", "Active-state stability"),
    "THETA_D": ("Порог принятия решения", "Decision threshold"),
    "THETA_A": ("Порог перехода к действию", "Action threshold"),
    "SWITCH_THRESHOLD": ("Порог переключения режима", "State switching threshold"),
    "UPDATE_MAGNITUDE": ("Размер изменения после пересмотра", "Size of a model update"),
    "THETA_U": ("Порог пересмотра модели", "Model revision threshold"),
    "HYSTERESIS_W": ("Влияние предыстории на допуск", "History dependence at admission"),
    "HYSTERESIS_NU": ("Влияние предыстории на проверку", "History dependence in evidence checks"),
    "HYSTERESIS_D": ("Устойчивость выбора к обратному переключению", "Resistance to reverse switching"),
    "HYSTERESIS_U": ("Влияние прошлых пересмотров на новые", "History dependence in model revision"),
    "K_ASYMMETRY": ("Потеря и восстановление доверия", "Trust loss and recovery"),
    "SPAWN_THRESHOLD": ("Появление новой гипотезы", "Formation of a new hypothesis"),
    "REALITY_CALIBRATION": ("Сверка объяснения с наблюдением", "Checking explanations against observations"),
    "U_ROUTING_CAPACITY": ("Выбор уровня исправления ошибки", "Choosing the correction level"),
    "GAMMA_CAPACITY": ("Офлайн-перекалибровка", "Offline recalibration"),
    "ANCHOR_STABILITY": ("Устойчивость опорных представлений", "Reference representation stability"),
    "MEMORY_DUAL_TIMESCALE_CAPACITY": ("Память о факте и готовность им пользоваться", "Remembering a fact versus using it"),
}


# The six groups are functions, not six anatomical layers or prenatal windows.
STAGES = [
    ("admission", "Допуск и накопление", "Admission and accumulation",
     "Какой сигнал проходит и сколько времени система его собирает?",
     "Which signal gets through, and how long is it accumulated?",
     "Не каждый вход становится рабочим свидетельством. Ворота учитывают силу сигнала, его историю и вес источника. Затем информация накапливается во времени.",
     "Not every input becomes usable evidence. The gate considers signal strength, its history and the source weight. Information then accumulates over time.",
     ["GAIN", "NOISE_SENSITIVITY", "THETA_W", "THETA_C", "TAU_INTEGRATION", "HYSTERESIS_W"]),
    ("evidence", "Проверка и сжатие", "Checks and compression",
     "Что подтверждено независимо, а что повторяет один источник?",
     "What is independently supported, and what repeats one source?",
     "Проверяется структура и происхождение свидетельств. Детали сворачиваются в более общую схему, но связь с исходными наблюдениями должна сохраняться.",
     "Evidence structure and provenance are checked. Details are compressed into a more general representation while retaining links to the original observations.",
     ["THETA_NU_TIME", "THETA_NU_CROSS", "THETA_NU_PROVENANCE", "M_C", "COMPRESSION_STRENGTH", "HYSTERESIS_NU"]),
    ("reality", "Реальность и доверие", "Reality and trust",
     "Совпадает ли объяснение с фактами и как меняется доверие?",
     "Does the explanation match observations, and how does trust change?",
     "Reality сверяет представление с наблюдением и эталонами. RS4_T меняет доверие после этой проверки. Вес авторитетного источника на входе не заменяет проверку фактов.",
     "Reality compares a representation with observations and anchors. RS4_T changes trust after this check. A source's authority at admission does not replace checking observations.",
     ["REALITY_CALIBRATION", "K_ASYMMETRY"]),
    ("decision", "Удержание, решение и действие", "Holding, decision and action",
     "Когда достаточно данных, когда действовать и когда переключиться?",
     "When is evidence sufficient, when do we act, and when do we switch?",
     "HOLD удерживает выбранный рабочий режим. Θ_D отвечает за фиксацию выбора, Θ_A — за переход к действию. Переключение режима и изменение самой модели — разные события.",
     "HOLD maintains the active working state. Θ_D governs committing to a choice; Θ_A governs acting on it. Switching a state and changing a model are different events.",
     ["D_C", "PERSISTENCE", "HOLD_STABILITY", "THETA_D", "THETA_A", "SWITCH_THRESHOLD", "HYSTERESIS_D"]),
    ("update", "Ошибка и обновление модели", "Error and model update",
     "Исправить действие, правило или само объяснение?",
     "Should we correct an action, a rule, or the explanation itself?",
     "После обратной связи U выбирает уровень исправления. Θ_U задаёт порог пересмотра модели; величина обновления — размер изменения после порога. Якоря сохраняют опорные схемы.",
     "After feedback, U chooses the correction level. Θ_U is the threshold for revising a model; update magnitude is the size of change after that threshold. Anchors retain reference representations.",
     ["UPDATE_MAGNITUDE", "THETA_U", "U_ROUTING_CAPACITY", "SPAWN_THRESHOLD", "HYSTERESIS_U", "ANCHOR_STABILITY"]),
    ("recovery", "Память и возврат", "Memory and recovery",
     "Что остаётся после опыта и как система возвращается к работе?",
     "What remains after experience, and how does the system return to work?",
     "Вспомненное снова входит в контур с меткой «изнутри». Γ обозначает офлайн-перекалибровку. Возврат к H* — отдельная модельная функция, а не прямое измерение сна или восстановления.",
     "Recalled material re-enters the circuit with an internal-source tag. Γ denotes offline recalibration. Return to H* is a separate model function, not a direct measure of sleep or recovery.",
     ["GAMMA_CAPACITY", "MEMORY_DUAL_TIMESCALE_CAPACITY", "RECOVERY_BASELINE"]),
]

# Practical hypotheses are offered as observations/tasks, never as trait scores.
CHECKS = {
    "GAIN": ("Сравнить изменение точности и темпа при одинаковом задании с тихим и отвлекающим входом.", "Compare accuracy and pace on the same task with quiet and distracting input."),
    "NOISE_SENSITIVITY": ("Повторить одинаковую задачу с регулярным и нерегулярным потоком; сохранить ошибки и время ответа.", "Repeat the same task with regular and irregular input; record errors and response times."),
    "THETA_W": ("Менять силу и достоверность сигнала; отмечать, какой информации достаточно для допуска к рассмотрению.", "Vary signal strength and reliability; record what is sufficient for considering evidence."),
    "THETA_C": ("Отмечать, после какого нового свидетельства появляется запрос перепроверить исходную версию.", "Record which new evidence triggers an explicit check of the initial explanation."),
    "TAU_INTEGRATION": ("Сравнить выбор после одного сигнала и после последовательности; менять интервалы между сигналами.", "Compare a choice after one signal versus a sequence, varying intervals between signals."),
    "THETA_NU_TIME": ("Сравнить оценку регулярных и нерегулярных последовательностей с одинаковой средней интенсивностью.", "Compare judgments of regular and irregular sequences with equal mean intensity."),
    "THETA_NU_CROSS": ("Сравнить независимые подтверждения и несколько пересказов одного сообщения.", "Compare independent confirmations with several retellings of one message."),
    "THETA_NU_PROVENANCE": ("Отдельно фиксировать «видел», «вспомнил» и «предположил», затем проверять происхождение ответа.", "Tag observed, recalled and inferred information separately, then check answer provenance."),
    "M_C": ("В задаче менять число действительно независимых источников при неизменном числе сообщений.", "Vary the number of genuinely independent sources while holding message count fixed."),
    "COMPRESSION_STRENGTH": ("Объяснить одну задачу подробно и коротким правилом; проверить, какие важные детали потерялись.", "Explain a task in detail and as a short rule; check which essential details were lost."),
    "D_C": ("Проверять, сколько последовательных подтверждений нужно для закрепления нового правила.", "Check how many consecutive confirmations are needed to retain a new rule."),
    "PERSISTENCE": ("После перерыва проверить, сохраняется ли выбранная стратегия без новых подсказок.", "After a break, check whether the selected strategy persists without new cues."),
    "HOLD_STABILITY": ("Добавить одинаковое отвлечение к задаче и проверить сохранение активного правила.", "Add the same distraction to a task and check whether the active rule is maintained."),
    "THETA_D": ("В задаче выбора менять количество свидетельств и цену ошибки; сравнивать точность и время вместе.", "Vary evidence quantity and error cost in a choice task; compare accuracy and timing together."),
    "THETA_A": ("Отдельно записать момент выбора и начало действия; различать задержку исполнения и отмену действия.", "Record choice and action onset separately; distinguish execution delay from cancellation."),
    "SWITCH_THRESHOLD": ("Изменять правило задачи; отмечать, после какого сигнала происходит смена стратегии.", "Change a task rule and record which signal produces a strategy switch."),
    "UPDATE_MAGNITUDE": ("После одинаковой ошибки сравнить размер изменения прогноза или правила, а не только факт изменения.", "After comparable errors, measure the size of a prediction or rule change, not just whether it changed."),
    "THETA_U": ("Заранее задать критерий пересмотра правила; в задаче со сменой правил измерить накопление ошибки до пересмотра.", "Set a rule-revision criterion in advance; in a reversal task measure accumulated error before revision."),
    "HYSTERESIS_W": ("Повышать, затем снижать силу сигнала; сравнить пороги допуска в двух направлениях.", "Increase and then decrease signal strength; compare admission thresholds in both directions."),
    "HYSTERESIS_NU": ("Предъявлять одинаковое свидетельство после надёжного и ненадёжного контекста; сравнить оценки.", "Present identical evidence after reliable versus unreliable contexts and compare judgments."),
    "HYSTERESIS_D": ("После закрепления выбора постепенно вводить противоположные данные; измерить порог обратного переключения.", "After a choice is retained, introduce opposing evidence gradually and measure reverse switching."),
    "HYSTERESIS_U": ("Поменять правило, затем вернуть прежние условия; сравнить пороги первого и обратного пересмотра.", "Change a rule and then restore the original conditions; compare initial and reverse revision thresholds."),
    "K_ASYMMETRY": ("Раздельно измерить изменение доверия после ошибки источника и после восстановления его надёжности.", "Measure trust loss after a source error separately from recovery after reliable evidence."),
    "SPAWN_THRESHOLD": ("Сравнить локальное исправление старого объяснения с созданием отдельной новой гипотезы.", "Compare a local correction to an old explanation with forming a separate new hypothesis."),
    "REALITY_CALIBRATION": ("Сверить вывод с независимым наблюдением; не использовать повтор собственного вывода как подтверждение.", "Check a conclusion against independent observations; do not count repeating it as confirmation."),
    "U_ROUTING_CAPACITY": ("После ошибки попросить указать, что меняется: исполнение, правило или исходное предположение.", "After an error, ask what changes: execution, the rule, or the initial assumption."),
    "GAMMA_CAPACITY": ("Сравнить выполнение одной задачи до и после ночного сна, сохранив условия и отметив качество сна.", "Compare the same task before and after sleep, retaining task conditions and recording sleep quality."),
    "ANCHOR_STABILITY": ("Проверить сохранение выученного правила через отсрочку и после противоречащего примера.", "Check retention of a learned rule after a delay and a contradictory example."),
    "MEMORY_DUAL_TIMESCALE_CAPACITY": ("Раздельно проверить узнавание факта и готовность пользоваться им после опровержения.", "Test recognition of a fact separately from willingness to use it after disconfirmation."),
    "RECOVERY_BASELINE": ("Повторить короткую задачу до нагрузки, сразу после и после одинаковой паузы; сравнить возвращение показателей.", "Repeat a short task before load, immediately after and after a fixed break; compare metric recovery."),
}

POS_EN = {
    "GAIN": "a larger response to input changes", "RECOVERY_BASELINE": "a faster modeled return after disturbance",
    "THETA_W": "stronger or more sustained evidence required at admission", "THETA_C": "more evidence accumulated before an explicit Reality check",
    "TAU_INTEGRATION": "a longer evidence-integration horizon", "COMPRESSION_STRENGTH": "stronger compression of details into general representations",
    "D_C": "a longer sequence of confirmations before consolidation", "PERSISTENCE": "longer retention of the active state",
    "HOLD_STABILITY": "greater retention of the active configuration under ordinary disturbances", "THETA_D": "more evidence before committing to a choice",
    "SWITCH_THRESHOLD": "a larger disturbance required to switch the active configuration", "UPDATE_MAGNITUDE": "larger updates after the revision threshold",
    "THETA_U": "more accumulated contradiction before revising a model", "HYSTERESIS_W": "stronger history dependence at admission",
    "HYSTERESIS_NU": "stronger history dependence when checking evidence structure", "HYSTERESIS_D": "more opposing evidence required to reverse a committed state",
    "HYSTERESIS_U": "more contradiction required for reverse model revision", "ANCHOR_STABILITY": "more persistent reference representations",
}
NEG_EN = {
    "GAIN": "a smaller response to input changes", "RECOVERY_BASELINE": "a longer modeled carry-over after disturbance",
    "THETA_W": "easier admission of evidence", "THETA_C": "earlier explicit Reality checks", "TAU_INTEGRATION": "a shorter evidence-integration horizon",
    "COMPRESSION_STRENGTH": "more detail retained at each representation level", "D_C": "a shorter confirmation sequence before consolidation",
    "PERSISTENCE": "easier change of the active state", "HOLD_STABILITY": "easier disturbance of the active configuration",
    "THETA_D": "less evidence before committing to a choice", "SWITCH_THRESHOLD": "easier switching of the active configuration",
    "UPDATE_MAGNITUDE": "smaller, incremental updates after the revision threshold", "THETA_U": "model revision after less accumulated contradiction",
    "HYSTERESIS_W": "less history dependence at admission", "HYSTERESIS_NU": "faster adjustment of evidence checks to current input",
    "HYSTERESIS_D": "a closer boundary for reverse switching", "HYSTERESIS_U": "less history dependence in model revision",
    "ANCHOR_STABILITY": "easier revision of retained reference representations",
}


def finite(value: Any) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def explain_parameter(p: dict, lang: str = "RU") -> dict:
    """Translate existing direction/uncertainty; never substitute missing data by 0."""
    code = str(p.get("parameter", ""))
    meta = PARAM_RU.get(code, {})
    stage = next((s for s in STAGES if code in s[7]), None)
    pressure = p.get("mode") == "pressure_only"
    value = finite(p.get("pressure_median" if pressure else "state_median"))
    lo = finite(p.get("pressure_min" if pressure else "state_min"))
    hi = finite(p.get("pressure_max" if pressure else "state_max"))
    robustness = p.get("robustness")
    stable = (p.get("mode") == "directional" and value is not None and abs(value) > DIRECTIONAL_EPS
              and robustness == "robust_direction" and lo is not None and hi is not None
              and lo <= value <= hi and lo * hi > 0)
    if pressure:
        label = tx("Направление не рассчитано", "Direction not modeled", lang)
        meaning = tx("Для этого узла рассчитана только условная калибровочная нагрузка. Она не сообщает, насколько функция сильна или слаба у человека.",
                     "Only conditional calibration load is modeled for this node. It does not indicate a person's functional strength or weakness.", lang)
    elif value is None:
        label = tx("Недостаточно данных", "Data unavailable", lang)
        meaning = tx("Численный результат отсутствует; направление не присваивается.", "The numeric result is unavailable; no direction is assigned.", lang)
    elif abs(value) <= DIRECTIONAL_EPS:
        label = tx("Близко к модельному нулю", "Near the model's zero", lang)
        meaning = tx("Выраженного направленного сдвига относительно исходного состояния модели нет. Это не доказательство средних показателей человека.",
                     "No directional shift is apparent from the model's initial state. This does not establish average human performance.", lang)
    else:
        label = (tx("Знак устойчив в расчёте", "Stable sign within the calculation", lang) if stable else
                 tx("Направление требует проверки", "Direction needs checking", lang))
        candidate = meta.get("pos" if value > 0 else "neg", "направленный сдвиг") if lang == "RU" else (POS_EN if value > 0 else NEG_EN).get(code, "a directional shift")
        if lang == "RU":
            candidate = candidate.replace("серия PASS", "серия подтверждений").replace("серии PASS", "серии подтверждений")
            candidate = candidate.replace("carry-over", "последействию").replace("commit решения возможен при меньшем объёме evidence", "решение фиксируется при меньшем объёме свидетельств").replace("evidence", "свидетельств")
        meaning = tx("Модель предполагает: " + candidate + ".", "The model suggests " + candidate + ".", lang)
        if not stable:
            meaning += tx(" Варианты даты зачатия и ширины пакета не дают достаточного основания закрепить эту характеристику.",
                          "Conception-date and packet-width variants do not justify treating this as an established characteristic.", lang)
    return {
        "code": code, "stage": stage[0] if stage else "other",
        "name": NAMES.get(code, (p.get("name_ru", meta.get("name", code)), p.get("label_source", code)))[0 if lang == "RU" else 1],
        "label": label, "meaning": meaning, "stable": stable, "pressure_only": pressure,
        "value": value, "range": [lo, hi],
        "process": meta.get("process", p.get("process", "")) if lang == "RU" else (stage[6] if stage else ""),
        "check": CHECKS.get(code, ("Нужна отдельная задача для проверки.", "A separate measurement task is needed."))[0 if lang == "RU" else 1],
        "windows": list(p.get("top_windows") or [])[:3],
        "sign_consistency": finite(p.get("sign_consistency")),
    }


def build_guide(profile: dict, lang: str = "RU") -> dict:
    parameters = [explain_parameter(p, lang) for p in profile.get("processing", {}).get("parameters", [])]
    stable = sorted([p for p in parameters if p["stable"]], key=lambda p: abs(p["value"]), reverse=True)
    return {"version": VERSION, "language": lang, "parameters": parameters,
            "stable": stable, "unresolved": [p for p in parameters if not p["stable"] and not p["pressure_only"]],
            "pressure_only": [p for p in parameters if p["pressure_only"]]}


def fnum(value: Any, signed: bool = False) -> str:
    number = finite(value)
    return "—" if number is None else (f"{number:+.3f}" if signed else f"{number:.3f}")


def spiral_svg(lang: str = "RU", stage: str = "admission") -> str:
    """Readable vector metaphor. Each loop repeats operations; levels are representations."""
    esc = html.escape
    names = [tx("Вход: увидел / вспомнил", "Input: observed / recalled", lang),
             tx("Наблюдения и детали", "Observations and details", lang),
             tx("Проверенные представления", "Checked representations", lang),
             tx("Рабочее объяснение", "Working explanation", lang),
             tx("Модели и якоря", "Models and anchors", lang)]
    active = next((s for s in STAGES if s[0] == stage), STAGES[0])
    loops = ""
    for i, (y, rx) in enumerate([(488,192),(385,166),(282,137),(179,106)]):
        loops += f'<ellipse cx="274" cy="{y}" rx="{rx}" ry="31" fill="#edf5fa" stroke="#9eb8cc" stroke-width="1.5"/>'
        loops += f'<path d="M {274-rx} {y} A {rx} 31 0 0 0 {274+rx} {y}" fill="none" stroke="#d85c35" stroke-width="5"/>'
        loops += f'<rect x="{274+rx-6}" y="{y-8}" width="12" height="16" rx="3" fill="#0b756f"/>'
        loops += f'<text x="505" y="{y+5}" fill="#17324d" font-size="17">{esc(names[i+1])}</text>'
        if i < 3:
            next_y, next_rx = [(385,166),(282,137),(179,106)][i]
            loops += f'<path d="M {274+rx} {y} C {274+rx-15} {y-32}, {274-next_rx+10} {next_y+36}, {274-next_rx} {next_y}" fill="none" stroke="#d85c35" stroke-width="2.5" stroke-dasharray="7 5" marker-end="url(#arrow)"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 670" role="img" aria-label="{esc(tx('Спираль: каждый виток повторяет операции, сужение означает сжатие представления.', 'Spiral: each loop repeats operations; narrowing denotes representation compression.',lang))}">
    <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="none" stroke="#d85c35"/></marker></defs>
    <rect width="900" height="670" rx="24" fill="#f4f8fc"/>
    <text x="38" y="45" font-family="Arial" font-size="15" fill="#0b756f">{esc(tx('ОТ ДЕТАЛЕЙ К ОБЪЯСНЕНИЮ', 'FROM DETAILS TO EXPLANATIONS', lang))}</text>
    <g font-family="Arial">{loops}
    <path d="M274 565 L274 523" stroke="#d85c35" stroke-width="3" marker-end="url(#arrow)"/>
    <text x="38" y="595" fill="#17324d" font-size="18">{esc(names[0])}</text>
    <path d="M167 179 H40 V535 H240" fill="none" stroke="#0b756f" stroke-width="2" stroke-dasharray="6 5"/>
    <text x="44" y="126" fill="#0b756f" font-size="15">{esc(tx('Память → на вход', 'Memory → input', lang))}</text>
    <text x="44" y="148" fill="#4c647a" font-size="13">{esc(tx('с меткой «изнутри»', 'with an internal-source tag', lang))}</text>
    <rect x="505" y="325" width="352" height="52" rx="12" fill="#e1f2ea"/>
    <text x="521" y="357" fill="#075d58" font-size="18">Θ_D → {esc(tx('выбор', 'choice', lang))} · Θ_A → {esc(tx('действие', 'action',lang))}</text>
    <path d="M410 294 H480 V351 H505" fill="none" stroke="#d85c35" stroke-width="2"/>
    <rect x="505" y="531" width="352" height="52" rx="12" fill="#fff1cf"/>
    <text x="521" y="563" fill="#795519" font-size="17">{esc(tx('Ошибка → U / Θ_U → пересмотр', 'Error → U / Θ_U → revision',lang))}</text>
    <path d="M855 381 V518 M505 557 H469 V400" fill="none" stroke="#a67525" stroke-width="2" stroke-dasharray="5 4"/>
    <text x="505" y="623" fill="#0b756f" font-size="16">{esc(tx('Γ: офлайн-перекалибровка', 'Γ: offline recalibration', lang))}</text>
    <text x="38" y="83" fill="#4c647a" font-size="14">{esc(tx('Каждый виток: допуск · проверка · состояние · цель · ответ · ошибка', 'Every loop: admission · check · state · goal · response · error',lang))}</text>
    <text x="38" y="647" fill="#17324d" font-size="15">{esc(tx('Сейчас читаем: ', 'Now reading: ', lang) + active[1 if lang=='RU' else 2])}</text>
    </g></svg>'''


GUIDE_CSS = """<style>
.sg-code{font:600 18px ui-monospace,monospace;color:#0b756f}.sg-compact{border-left:3px solid #d85c35;padding:4px 12px;margin:10px 0}.sg-compact p{margin:5px 0;color:#4c647a;font-size:14px;line-height:1.55}
.sg-card{background:#fff;border:1px solid #cbdbe7;border-radius:18px;padding:22px;margin:12px 0;color:#17324d;break-inside:avoid}.sg-card h3{font-size:19px;margin:8px 0 12px}.sg-card p{line-height:1.65}.sg-eyebrow{color:#0b756f;font-size:12px;letter-spacing:.07em;text-transform:uppercase}.sg-small{color:#4c647a;font-size:14px;line-height:1.6}.sg-value{font:600 19px ui-monospace,monospace}.sg-check{border-left:3px solid #0b756f;padding-left:13px;margin-top:17px}.sg-number{display:inline-block;color:#a67525;font:600 14px ui-monospace,monospace;margin-right:12px}.sg-columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.sg-caution{background:#fff1cf;padding:16px;border-radius:12px;line-height:1.6}.sg-lead{font-size:20px;line-height:1.7}.sg-wrap{max-width:1120px;margin:auto;padding:24px}.sg-wrap h1{font-size:clamp(30px,5vw,52px);line-height:1.14;letter-spacing:-.035em}.sg-wrap h2{font-size:27px;margin-top:40px}.sg-wrap a{color:#0b756f}.sg-wrap svg{display:block;width:100%;height:auto}.sg-steps{display:flex;flex-wrap:wrap;gap:8px}.sg-steps a{padding:10px 14px;border:1px solid #bdd2e2;border-radius:999px;text-decoration:none;background:white}@media(max-width:720px){.sg-columns{grid-template-columns:1fr}.sg-wrap{padding:16px}.sg-card{padding:17px}}@media print{.sg-steps{display:none}}
</style>"""


def parameter_html(p: dict, lang: str = "RU") -> str:
    e = html.escape
    value = fnum(p["value"], not p["pressure_only"])
    range_text = f'{fnum(p["range"][0], not p["pressure_only"])} … {fnum(p["range"][1], not p["pressure_only"])}'
    wtext = ", ".join(str(w.get("window", "")) for w in p["windows"])
    number_label = tx("Условная нагрузка", "Conditional load", lang) if p["pressure_only"] else tx("Сдвиг модели", "Model shift", lang)
    return f'''<article class="sg-card"><div class="sg-eyebrow">{e(p['label'])}</div><h3>{e(p['name'])}</h3>
    <div class="sg-value">{e(number_label)} {value}</div><p class="sg-small">{e(tx('Диапазон вариантов', 'Variant range',lang))}: {range_text}</p>
    <p>{e(p['meaning'])}</p><p class="sg-small">{e(p['process'])}</p>
    <div class="sg-check"><b>{e(tx('Как проверить в своей работе', 'How to check in practice',lang))}</b><p>{e(p['check'])}</p></div>
    <p class="sg-small">{e(tx('Основные окна расчёта', 'Main contributing windows',lang))}: {e(wtext) if wtext else '—'} · <code>{e(p['code'])}</code></p></article>'''


def guide_markdown(profile: dict, lang: str = "RU") -> str:
    g = build_guide(profile, lang)
    sub = profile.get("meta", {}).get("subject", {})
    lines = ["# " + tx("ARCHVIQ — расшифровка спирали процессинга", "ARCHVIQ — processing spiral explained", lang),
             str(sub.get("label", "")), tx("Дата рождения: ", "Birth date: ", lang) + str(sub.get("dob", "")),
             tx("Это гипотезы существующей модели. Знак устойчивости относится к вариантам расчёта, а не к установленной достоверности характеристики человека.",
                "These are hypotheses of the existing model. Sign stability refers to calculation variants, not established validity of a human characteristic.", lang),
             "## " + tx("Как читать числа", "How to read the numbers", lang),
             tx("Сдвиг — внутренняя единица модели, не процент и не балл качества. Диапазон — минимум и максимум вариантов даты/пакета, не доверительный интервал. Pressure-only — нагрузка на узел без заданного направления функции.",
                "A shift uses internal model units, not percentiles or quality scores. The range is the minimum and maximum over date/packet variants, not a confidence interval. Pressure-only is load without a modeled functional direction.", lang),
             tx("H* — вектор условных опорных параметров модели. Он не является измерением текущего состояния мозга. Согласие вариантов расчёта не доказывает достоверность признака у человека.",
                "H* is a vector of conditional model reference parameters. It is not a measurement of current brain state. Agreement across calculation variants does not establish human-trait validity.",lang)]
    for stage in STAGES:
        lines += ["## " + stage[1 if lang == "RU" else 2], stage[5 if lang == "RU" else 6]]
        for p in [p for p in g["parameters"] if p["stage"] == stage[0]]:
            lines += ["### " + p["name"], p["label"], p["meaning"],
                      f"{p['code']}: {fnum(p['value'], not p['pressure_only'])}; " + tx("диапазон ", "range ",lang) + " … ".join(fnum(v, not p['pressure_only']) for v in p["range"]),
                      tx("Проверка: ", "Check: ",lang) + p["check"]]
    lines += ["## " + tx("Что делать дальше", "What to do next", lang),
              tx("Выберите одну устойчивую гипотезу. Зафиксируйте одинаковую задачу, ожидаемый результат и условия до наблюдения. Повторите измерение в нескольких сессиях, сохраняя и несовпадения. Тестовые метрики не переводятся автоматически в параметры спирали без отдельной калибровки.",
                 "Choose one stable hypothesis. Record the same task, expected result and conditions before observing outcomes. Repeat across sessions and retain mismatches. Task metrics are not automatically converted into spiral parameters without separate calibration.", lang)]
    return "\n\n".join(lines) + "\n"


def concept_html(lang: str = "RU", profile: dict | None = None) -> str:
    e = html.escape
    title = tx("Как информация становится решением", "How information becomes a decision",lang)
    intro = tx("Спираль описывает повторяющийся цикл: мы допускаем информацию, сверяем её, собираем объяснение, выбираем ответ и возвращаемся к нему после ошибки. Каждый виток сохраняет эту логику; сужение означает переход от множества деталей к более компактной модели.",
               "The spiral describes a repeating cycle: we admit information, check it, form an explanation, choose a response and revisit it after error. Every loop repeats this logic; narrowing denotes a move from many details to a more compact model.",lang)
    nav = ''.join(f'<a href="#{s[0]}">{e(s[1 if lang=="RU" else 2])}</a>' for s in STAGES)
    body = f'<header><div class="sg-eyebrow">ARCHVIQ · {VERSION}</div><h1>{e(title)}</h1><p class="sg-lead">{e(intro)}</p></header><div class="sg-columns"><div>{spiral_svg(lang)}</div><div class="sg-card"><h2>{e(tx("Три разных порога", "Three different thresholds",lang))}</h2>'
    for code, ru, en in [("Θ_D","Решение: достаточно ли свидетельств, чтобы выбрать?","Decision: is there enough evidence to choose?"),("Θ_A","Действие: когда выбранное становится исполненным?","Action: when is a choice executed?"),("Θ_U","Обновление: достаточно ли противоречия, чтобы пересмотреть правило?","Update: is there enough contradiction to revise a rule?")]:
        body += f'<p><b>{code}</b> · {e(tx(ru,en,lang))}</p>'
    body += f'<p class="sg-small">{e(tx("Высота представления, порог решения и порог пересмотра не сводятся друг к другу.", "Representation level, decision threshold and revision threshold are separate coordinates.",lang))}</p></div></div><nav class="sg-steps">{nav}</nav>'
    g = build_guide(profile, lang) if profile else None
    if g:
        body += f'<h2>{e(tx("Ваш модельный профиль", "Your model profile",lang))}</h2><p class="sg-caution">{e(tx("Числа — сдвиги во внутренних единицах модели. Диапазон отражает варианты расчёта, а не вероятность того, что характеристика верна для человека. Страницы ниже показывают рассчитанные гипотезы и способы их проверки.", "Numbers are shifts in internal model units. Ranges reflect calculation variants, not probabilities of human traits. The sections below show modeled hypotheses and ways to check them.",lang))}</p>'
        sub = profile.get("meta", {}).get("subject", {})
        body += f'<p class="sg-small">{e(str(sub.get("label", "")))} · {e(str(sub.get("dob", "")))} · {e(tx("неопределённость даты ±", "date uncertainty ±",lang))}{e(str(sub.get("uncertainty_days", "—")))} {e(tx("дн", "days",lang))}</p>'
        body += f'<p>{e(tx("Устойчивых модельных направлений: ", "Stable model directions: ",lang))}{len(g["stable"])} · {e(tx("невыделенных направлений: ", "unresolved directions: ",lang))}{len(g["unresolved"])} · {e(tx("узлов только с нагрузкой: ", "load-only nodes: ",lang))}{len(g["pressure_only"])}</p>'
        if g["stable"]:
            first = g["stable"][0]
            body += f'<div class="sg-card"><h3>{e(tx("С чего начать проверку", "Where to start testing",lang))}</h3><p><b>{e(first["name"])}</b> · {e(first["meaning"])}</p><p>{e(first["check"])}</p></div>'
    for s in STAGES:
        body += f'<section id="{s[0]}"><h2>{e(s[1 if lang=="RU" else 2])}</h2><p><b>{e(s[3 if lang=="RU" else 4])}</b></p><p>{e(s[5 if lang=="RU" else 6])}</p>'
        if g:
            body += '<div class="sg-columns">' + ''.join(parameter_html(p, lang) for p in g["parameters"] if p["stage"]==s[0]) + '</div>'
        body += '</section>'
    body += f'<h2>{e(tx("От анализа к пользе", "From analysis to practical use",lang))}</h2><p>{e(tx("Результат помогает сформулировать конкретные вопросы: какие данные нужны для решения, что удерживает рабочее правило, какая ошибка заставляет его пересмотреть и как меняются показатели после нагрузки. Выберите один вопрос и сравните гипотезу с повторными наблюдениями. Результаты задач, опыт и текущее состояние учитываются отдельно.", "The result helps formulate concrete questions: what evidence is needed for a decision, what maintains a working rule, which error leads to revision, and how performance changes after load. Choose one question and compare the hypothesis with repeated observations. Task results, experience and current state are considered separately.",lang))}</p><footer class="sg-small">{e(tx("SSN-модель экспериментальна. Связь солнечной динамики с индивидуальным процессингом и нейронными контурами пока не установлена. Операции схемы — функциональные гипотезы.", "The SSN model is experimental. Links from solar dynamics to individual processing and neural circuits are not established. Diagram operations are functional hypotheses.",lang))}</footer>'
    return f'<!doctype html><html lang="{"ru" if lang=="RU" else "en"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ARCHVIQ — {e(title)}</title>{GUIDE_CSS}<style>body{{margin:0;background:#eaf3fb;font-family:Arial,sans-serif;color:#17324d}}p{{line-height:1.7}}</style></head><body><main class="sg-wrap">{body}</main></body></html>'
