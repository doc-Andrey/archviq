"""
interpret_engine.py
Интерпретационный движок для psychotyp.com
Адаптирован для замороженного 43 NEW V3 / 254D; сохраняет связку prior → tests → questionnaires

Вход: словарь с параметрами движка 43 (no_lag)
Выход: полный интерпретационный профиль для отображения на сайте
"""

import numpy as np


# ─── 43 NEW V3 DISPLAY LAYER ────────────────────────────────────────────────
# The 254D geometry is different from legacy 43, so old LEMON percentile
# thresholds and the old linear transforms are not reused here.
# UI values below are deterministic 0..100 orientation coordinates only.

DISPLAY_BANDS = {"low": 35.0, "high": 65.0}


def _level(val, axis=None):
    if val < DISPLAY_BANDS["low"]:
        return "low"
    if val > DISPLAY_BANDS["high"]:
        return "high"
    return "mid"


def _disp(x, scale=1.0):
    try:
        x = float(x)
    except (TypeError, ValueError):
        x = 0.0
    return float(max(0.0, min(100.0, 50.0 + 50.0 * np.tanh(x / max(scale, 1e-9)))))


def compute_indices(raw):
    """Functional interpretation of frozen 43 NEW V3 native outputs.

    X1..X9 are primary.  RS1..RS4 remain summary macrocoordinates.  The
    returned 0..100 numbers are transparent display coordinates, not LEMON
    percentiles, clinical norms or calibrated probabilities.
    """
    def g(k, default=0.0):
        v = raw.get(k, default)
        try:
            return float(v)
        except (TypeError, ValueError):
            return float(default)

    x = {
        "EXC": _disp(g("X_EXC")),
        "SENS": _disp(g("X_SENS")),
        "STAB": _disp(g("X_STAB")),
        "INTEG": _disp(g("X_INTEG")),
        "FLEX": _disp(g("X_FLEX")),
        "LAB": _disp(g("X_LAB")),
        "SEGR": _disp(g("X_SEGR")),
        "HUB": _disp(g("X_HUB")),
        "MAT": _disp(g("X_MAT")),
    }

    arch = {
        "ARCH_RHYTHM_STABILITY": _disp(g("RS1_RHYTHM")),
        "ARCH_SYNCHRONY": _disp(g("RS2_SYNC")),
        "ARCH_SEGREGATION": x["SEGR"],
        "ARCH_INTEGRATION": x["INTEG"],
        "ARCH_EXCITABILITY": x["EXC"],
        "ARCH_SENSITIVITY": x["SENS"],
        "ARCH_STABILITY": x["STAB"],
        "ARCH_FLEXIBILITY": x["FLEX"],
        "ARCH_LABILITY": x["LAB"],
        "ARCH_HUBNESS": x["HUB"],
        "ARCH_MATURATION": x["MAT"],
    }

    arch["ARCH_POWER"] = np.mean([x["INTEG"], x["HUB"], x["MAT"]])
    arch["ARCH_OVERLOAD"] = np.mean([x["SENS"], x["LAB"], 100.0 - x["STAB"]])
    arch["ARCH_ADAPTIVE_RESERVE"] = np.mean([x["STAB"], x["FLEX"], x["MAT"], 100.0 - x["LAB"]])
    arch["ARCH_DECOMPENSATION_RISK"] = np.mean([x["SENS"], x["LAB"], 100.0-x["STAB"], 100.0-x["MAT"]])

    indices = {
        "overload": arch["ARCH_OVERLOAD"],
        "recovery": np.mean([arch["ARCH_ADAPTIVE_RESERVE"], 100.0-arch["ARCH_OVERLOAD"]]),
        "flexibility": np.mean([x["FLEX"], x["INTEG"], 100.0-x["LAB"]]),
        "rigidity": np.mean([x["SEGR"], x["STAB"], x["MAT"], 100.0-x["FLEX"]]),
        "transition_cost": np.mean([x["LAB"], x["SEGR"], 100.0-x["FLEX"]]),
        "emo_cost": np.mean([x["SENS"], x["LAB"], 100.0-x["STAB"]]),
        "bottleneck": np.mean([x["HUB"], x["SEGR"], 100.0-x["FLEX"], 100.0-x["STAB"]]),
        "autonomic": np.mean([x["SENS"], x["LAB"], 100.0-x["STAB"]]),
    }

    for k in arch:
        arch[k] = float(max(0.0, min(100.0, arch[k])))
    for k in indices:
        indices[k] = float(max(0.0, min(100.0, indices[k])))
    return arch, indices


# ─── GAP-КЛАССИФИКАЦИЯ (из 245J) ──────────────────────────────────────────────

def classify_gap(ssn_eeg_gap, tests_eeg_gap, compensation_index):
    """Классификация по трёхисточниковому разрыву."""
    if ssn_eeg_gap is None or tests_eeg_gap is None:
        return "SINGLE_SOURCE"

    if ssn_eeg_gap <= 18 and tests_eeg_gap <= 18:
        return "FULL_MATCH"
    if tests_eeg_gap <= 18 and ssn_eeg_gap > 28:
        return "EEG_TESTS_MATCH_SSN_RUPTURE"
    if ssn_eeg_gap <= 18 and tests_eeg_gap > 28:
        return "SSN_EEG_MATCH_BEHAVIORAL_RUPTURE"
    if ssn_eeg_gap <= 25 and tests_eeg_gap <= 25:
        return "PARTIAL_MATCH"
    if compensation_index >= 65 and max(ssn_eeg_gap, tests_eeg_gap) >= 28:
        return "COMPENSATED_RUPTURE"
    if max(ssn_eeg_gap, tests_eeg_gap) >= 35:
        return "HIGH_RUPTURE"
    return "PARTIAL_MATCH"


# ─── ТЕКСТОВЫЕ ИНТЕРПРЕТАЦИИ ───────────────────────────────────────────────────

INDEX_TEXTS = {
    "EN": {
        "overload": {
            "low":  ("Low System Load",
                     "The model indicates a low-load processing profile. "
                     "Stress response is efficient and resources are not depleted."),
            "mid":  ("Moderate System Load",
                     "The model indicates a noticeable but manageable processing load. "
                     "Performance is maintained but recovery time matters."),
            "high": ("High System Load",
                     "The model places the current prior near the high-load end of its display range. "
                     "This is often invisible externally — the system compensates. "
                     "But the cost is real: slower recovery, reduced flexibility under pressure."),
        },
        "recovery": {
            "low":  ("Limited Recovery Reserve",
                     "Your adaptive reserve is currently reduced. Recovery after stress "
                     "may take longer under comparable conditions."),
            "mid":  ("Adequate Recovery Capacity",
                     "Your system recovers reasonably well under normal conditions. "
                     "Extended pressure may reduce this."),
            "high": ("Strong Recovery Reserve",
                     "The model indicates substantial adaptive reserve. "
                     "You bounce back from stress relatively quickly."),
        },
        "flexibility": {
            "low":  ("Low Cognitive Flexibility",
                     "The profile favors depth over breadth. "
                     "Context switches and sudden changes of direction are costly."),
            "mid":  ("Moderate Cognitive Flexibility",
                     "You adapt to changing contexts at a normal pace. "
                     "Some transitions are smooth, others require effort."),
            "high": ("High Cognitive Flexibility",
                     "The profile is oriented toward efficient context shifts. "
                     "You generate options and adapt to new information quickly."),
        },
        "rigidity": {
            "low":  ("Fluid Pattern Maintenance",
                     "You hold patterns loosely — which supports creativity "
                     "but may challenge consistency."),
            "mid":  ("Balanced Structural Stability",
                     "You maintain useful patterns without being locked into them."),
            "high": ("Strong Structural Rigidity",
                     "The profile is oriented toward strong pattern maintenance. "
                     "This supports focus and depth but makes rapid pivots costly."),
        },
        "transition_cost": {
            "low":  ("Low Transition Cost",
                     "The profile suggests relatively low switching cost."),
            "mid":  ("Moderate Transition Cost",
                     "Task switching takes some effort — building in transition time helps."),
            "high": ("High Transition Cost",
                     "The profile suggests a relatively high switching cost. "
                     "Deep focus blocks work better than fragmented multitasking."),
        },
        "emo_cost": {
            "low":  ("Low Emotional Processing Cost",
                     "Emotional events are processed efficiently "
                     "without consuming disproportionate resources."),
            "mid":  ("Moderate Emotional Processing Cost",
                     "Emotionally significant events take a noticeable toll. "
                     "Self-regulation is active and functional."),
            "high": ("High Emotional Processing Cost",
                     "The profile suggests a higher processing cost around emotionally salient input. "
                     "Stress, conflict, and high-stakes situations drain more than average. "
                     "This is a model interpretation, not a judgment of ability."),
        },
        "bottleneck": {
            "low":  ("No Significant Bottleneck",
                     "Information flows efficiently through your network."),
            "mid":  ("Moderate Processing Bottleneck",
                     "Some information pathways are constrained — visible under high load."),
            "high": ("Active Processing Bottleneck",
                     "Your hub nodes are under pressure. Complex multi-thread tasks "
                     "create congestion. Prioritization and sequencing help significantly."),
        },
        "autonomic": {
            "low":  ("Low Autonomic Reactivity",
                     "Your nervous system responds to environmental signals moderately. "
                     "Any sensitivity to geomagnetic or electromagnetic conditions remains an individual hypothesis to test longitudinally."),
            "mid":  ("Moderate Autonomic Reactivity",
                     "The model suggests testing whether environmental conditions co-vary with your baseline state."),
            "high": ("High Autonomic Reactivity",
                     "Your nervous system is highly responsive to environmental signals — "
                     "including electromagnetic fluctuations, weather changes, and "
                     "social-emotional fields. This heightens both sensitivity and vulnerability."),
        },
    },
    "RU": {
        "overload": {
            "low":  ("Низкая нагрузка на систему",
                     "Модель указывает на профиль с невысокой расчётной нагрузкой. "
                     "Стрессовая реакция эффективна, ресурсы не истощены."),
            "mid":  ("Умеренная нагрузка на систему",
                     "Модель указывает на заметную, но управляемую расчётную нагрузку. "
                     "Производительность сохраняется, но время восстановления имеет значение."),
            "high": ("Высокая нагрузка на систему",
                     "Модель помещает текущий prior ближе к верхней части шкалы нагрузки. "
                     "Внешне это часто незаметно — система компенсирует. "
                     "Но цена реальна: замедленное восстановление, сниженная гибкость под давлением."),
        },
        "recovery": {
            "low":  ("Ограниченный адаптивный резерв",
                     "Ваш адаптивный резерв снижен. Восстановление после стресса "
                     "может занимать больше времени при сопоставимых условиях."),
            "mid":  ("Достаточный резерв восстановления",
                     "Система восстанавливается нормально в обычных условиях. "
                     "Длительное давление может снизить этот показатель."),
            "high": ("Сильный резерв восстановления",
                     "Модель указывает на значительный адаптивный резерв. "
                     "Вы достаточно быстро восстанавливаетесь после стресса."),
        },
        "flexibility": {
            "low":  ("Низкая когнитивная гибкость",
                     "Ваша архитектура предпочитает глубину, а не широту. "
                     "Переключение контекста и резкие смены направления обходятся дорого."),
            "mid":  ("Умеренная когнитивная гибкость",
                     "Вы адаптируетесь к меняющимся контекстам в нормальном темпе."),
            "high": ("Высокая когнитивная гибкость",
                     "Ваша архитектура эффективно обрабатывает переключения контекста. "
                     "Вы быстро генерируете варианты и адаптируетесь к новой информации."),
        },
        "rigidity": {
            "low":  ("Гибкое удержание паттернов",
                     "Вы удерживаете паттерны свободно — это поддерживает творчество, "
                     "но может затруднять последовательность."),
            "mid":  ("Сбалансированная структурная стабильность",
                     "Вы поддерживаете полезные паттерны, не будучи в них заперты."),
            "high": ("Высокая структурная ригидность",
                     "Ваша архитектура строит и поддерживает сильные паттерны. "
                     "Это поддерживает фокус и глубину, но делает быстрые развороты дорогостоящими."),
        },
        "transition_cost": {
            "low":  ("Низкая стоимость переходов",
                     "Переключение между задачами или режимами эффективно для вашей архитектуры."),
            "mid":  ("Умеренная стоимость переходов",
                     "Переключение задач требует некоторых усилий — планируйте время перехода."),
            "high": ("Высокая стоимость переходов",
                     "Профиль предполагает относительно высокую цену смены контекста. "
                     "Блоки глубокого фокуса работают лучше чем раздробленная многозадачность."),
        },
        "emo_cost": {
            "low":  ("Низкая стоимость эмоциональной обработки",
                     "Эмоциональные события обрабатываются эффективно "
                     "без непропорционального расхода ресурсов."),
            "mid":  ("Умеренная стоимость эмоциональной обработки",
                     "Значимые эмоциональные события ощутимо влияют на состояние. "
                     "Саморегуляция активна и функциональна."),
            "high": ("Высокая стоимость эмоциональной обработки",
                     "Ваша архитектура вкладывает значительные ресурсы в эмоциональную обработку. "
                     "Стресс, конфликты и ситуации высоких ставок истощают больше среднего. "
                     "Это интерпретация модели, а не оценка способности или слабости."),
        },
        "bottleneck": {
            "low":  ("Нет значимых узких мест",
                     "Информация эффективно проходит через вашу сеть."),
            "mid":  ("Умеренное узкое место обработки",
                     "Некоторые информационные пути ограничены — видно под высокой нагрузкой."),
            "high": ("Активное узкое место обработки",
                     "Ваши хаб-узлы находятся под давлением. Сложные многопоточные задачи "
                     "создают заторы. Приоритизация и последовательность значительно помогают."),
        },
        "autonomic": {
            "low":  ("Низкая автономная реактивность",
                     "Ваша нервная система умеренно реагирует на внешние сигналы. "
                     "Связь с геомагнитными или электромагнитными условиями остаётся индивидуальной гипотезой для продольной проверки."),
            "mid":  ("Умеренная автономная реактивность",
                     "Модель предлагает проверить, ковариируют ли внешние условия с вашим базовым состоянием."),
            "high": ("Высокая автономная реактивность",
                     "Ваша нервная система высоко чувствительна к внешним сигналам — "
                     "включая электромагнитные колебания, смену погоды и "
                     "социально-эмоциональный фон. Это повышает и чувствительность, и уязвимость."),
        },
    },
}

GAP_CLASS_TEXTS = {
    "EN": {
        "FULL_MATCH": "The developmental prior and measured behavioral layers align well within the current comparison scheme.",
        "PARTIAL_MATCH": "Moderate alignment across sources. The developmental prior and measured layers differ in some dimensions.",
        "COMPENSATED_RUPTURE": "The developmental prior and current behavior differ substantially. This may reflect adaptation, current state, measurement conditions, or model error.",
        "HIGH_RUPTURE": "A large discrepancy is present between the developmental prior and measured function. Repeat measurement before interpreting its source.",
        "SSN_EEG_MATCH_BEHAVIORAL_RUPTURE": "The model prior and neural measurements align more closely than the behavioral layer. The source of the difference requires independent follow-up.",
        "EEG_TESTS_MATCH_SSN_RUPTURE": "Current neural and behavioral measurements align more closely with each other than with the developmental prior.",
        "SINGLE_SOURCE": "Profile currently contains only the developmental prior. Add cognitive tests and questionnaires to compare it with measured function.",
    },
    "RU": {
        "FULL_MATCH": "Developmental prior и измеренные поведенческие слои хорошо согласованы в рамках текущей схемы сравнения.",
        "PARTIAL_MATCH": "Умеренное согласование источников. Developmental prior и измеренные слои различаются по части параметров.",
        "COMPENSATED_RUPTURE": "Developmental prior и текущее поведение существенно различаются. Причиной могут быть адаптация, текущее состояние, условия измерения или ошибка модели.",
        "HIGH_RUPTURE": "Есть крупное расхождение между developmental prior и измеренной функцией. До интерпретации причины измерение следует повторить.",
        "SSN_EEG_MATCH_BEHAVIORAL_RUPTURE": "Модельный prior и нейронные измерения согласуются лучше, чем поведенческий слой. Источник различия требует отдельной проверки.",
        "EEG_TESTS_MATCH_SSN_RUPTURE": "Текущие нейронные и поведенческие измерения согласуются между собой лучше, чем с developmental prior.",
        "SINGLE_SOURCE": "Сейчас профиль содержит только developmental prior. Добавьте когнитивный тест и опросники для сравнения с измеренной функцией.",
    },
}


# ─── ГЛАВНАЯ ФУНКЦИЯ ───────────────────────────────────────────────────────────

def interpret(raw, lang="EN",
              cognitive_gap=None,
              questionnaire_gap=None):
    """
    Создаёт полный интерпретационный профиль.

    raw: dict из движка 43 (no_lag результат)
    lang: "EN" или "RU"
    cognitive_gap: разрыв SSN↔тесты (опционально, для GAP-классификации)
    questionnaire_gap: разрыв тесты↔опросник (опционально)

    Возвращает dict с полным профилем для отображения
    """
    arch, indices = compute_indices(raw)

    # Уровни каждого индекса
    index_levels = {}
    for idx_name, val in indices.items():
        if idx_name == "overload":
            level = _level(val, "ARCH_OVERLOAD")
        elif idx_name == "recovery":
            level = _level(val, "ARCH_ADAPTIVE_RESERVE")
        elif idx_name == "flexibility":
            level = _level(val, "ARCH_FLEXIBILITY")
        elif idx_name in ("rigidity", "transition_cost", "bottleneck"):
            level = "low" if val < 35 else "high" if val > 60 else "mid"
        else:
            level = "low" if val < 33 else "high" if val > 67 else "mid"
        index_levels[idx_name] = level

    # Тексты
    texts = INDEX_TEXTS.get(lang, INDEX_TEXTS["EN"])
    interpreted_indices = {}
    for idx_name in indices:
        level = index_levels[idx_name]
        title, desc = texts[idx_name][level]
        interpreted_indices[idx_name] = {
            "value":  round(indices[idx_name], 1),
            "level":  level,
            "title":  title,
            "description": desc,
        }

    # GAP-классификация
    comp_idx = arch.get("ARCH_ADAPTIVE_RESERVE", 50)
    gap_class = classify_gap(cognitive_gap, questionnaire_gap, comp_idx)
    gap_text  = GAP_CLASS_TEXTS.get(lang, GAP_CLASS_TEXTS["EN"])[gap_class]

    # Топ-3 приоритета (самые высокие перегрузки)
    priority_indices = ["overload", "emo_cost", "bottleneck",
                        "transition_cost", "autonomic"]
    priorities = sorted(
        [(k, indices[k]) for k in priority_indices],
        key=lambda x: x[1], reverse=True
    )[:3]

    priority_texts = []
    for pkey, pval in priorities:
        if index_levels[pkey] in ("mid", "high"):
            title, _ = texts[pkey][index_levels[pkey]]
            priority_texts.append(title)

    return {
        "arch":               arch,
        "indices":            interpreted_indices,
        "gap_class":          gap_class,
        "gap_text":           gap_text,
        "top_priorities":     priority_texts,
        "index_levels":       index_levels,
    }


# ─── СОВМЕСТИМОСТЬ (расширенная) ──────────────────────────────────────────────

def compatibility_analysis(profile1, profile2, raw1, raw2, lang="EN"):
    """
    Расширенный анализ совместимости на основе реальных параметров.

    profile1, profile2: результаты compute_profile()
    raw1, raw2: сырые параметры движка 43
    """
    _, idx1 = compute_indices(raw1)
    _, idx2 = compute_indices(raw2)

    # Ключевые разрывы
    overload_diff    = abs(idx1["overload"] - idx2["overload"])
    flexibility_diff = abs(idx1["flexibility"] - idx2["flexibility"])
    emo_diff         = abs(idx1["emo_cost"] - idx2["emo_cost"])
    recovery_diff    = abs(idx1["recovery"] - idx2["recovery"])

    # Суммарный индекс совместимости
    compatibility_score = max(20, min(95, 75
        - overload_diff * 0.3
        - flexibility_diff * 0.2
        - emo_diff * 0.2
        - recovery_diff * 0.15
    ))

    if lang == "RU":
        dynamics = []
        if overload_diff < 10:
            dynamics.append("Близкий уровень системной нагрузки — вы синхронно чувствуете усталость и восстанавливаетесь.")
        elif overload_diff > 25:
            dynamics.append(f"Значительная разница в уровне нагрузки ({overload_diff:.0f} пунктов) — один партнёр может выглядеть менее уставшим, но внутренне несёт больше.")

        if flexibility_diff < 10:
            dynamics.append("Похожая когнитивная гибкость — вы одинаково реагируете на изменения и неопределённость.")
        elif flexibility_diff > 25:
            dynamics.append("Разные уровни гибкости — один адаптируется быстрее, другой глубже. Это может дополнять, но требует осознанности.")

        if emo_diff > 20:
            dynamics.append("Разная стоимость эмоциональной обработки — один партнёр эмоционально 'дороже' реагирует на конфликты. Это не слабость, это архитектура.")

        if recovery_diff > 20:
            dynamics.append("Разный адаптивный резерв — одному нужно больше времени на восстановление. Учёт этого снижает напряжение пары.")
    else:
        dynamics = []
        if overload_diff < 10:
            dynamics.append("Similar system load — you experience fatigue and recovery in sync.")
        elif overload_diff > 25:
            dynamics.append(f"Significant load difference ({overload_diff:.0f} points) — one partner may appear less tired but internally carries more.")

        if flexibility_diff < 10:
            dynamics.append("Similar cognitive flexibility — you respond to change and uncertainty alike.")
        elif flexibility_diff > 25:
            dynamics.append("Different flexibility levels — one adapts faster, the other goes deeper. Complementary but requires awareness.")

        if emo_diff > 20:
            dynamics.append("Different emotional processing cost — one partner 'pays more' emotionally in conflict. This is a model interpretation, not a judgment of ability.")

        if recovery_diff > 20:
            dynamics.append("Different recovery capacity — one needs more restoration time. Accounting for this reduces pair tension.")

    return {
        "score":    round(compatibility_score),
        "dynamics": dynamics,
        "idx1":     idx1,
        "idx2":     idx2,
    }