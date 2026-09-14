"""
interpret_engine.py
Интерпретационный движок для psychotyp.com
Основан на реальных формулах из 245H/245J анализа LEMON (n=199)

Вход: словарь с параметрами движка 43 (no_lag)
Выход: полный интерпретационный профиль для отображения на сайте
"""

import numpy as np


# ─── НОРМЫ ПО LEMON (n=199, перцентильные границы) ───────────────────────────
# low < 33-й перцентиль, mid = 33-67, high > 67-й перцентиль
# Значения получены из 01_UNIVERSAL_CARD_V1_FROM_SSN_43_LEMON199_245G.csv

LEMON_NORMS = {
    "ARCH_OVERLOAD":          {"low": 30, "high": 55},
    "ARCH_ADAPTIVE_RESERVE":  {"low": 35, "high": 60},
    "ARCH_POWER":             {"low": 30, "high": 55},
    "ARCH_INTEGRATION":       {"low": 35, "high": 60},
    "ARCH_EXCITABILITY":      {"low": 30, "high": 55},
    "ARCH_SENSITIVITY":       {"low": 35, "high": 60},
    "ARCH_LABILITY":          {"low": 30, "high": 55},
    "ARCH_FLEXIBILITY":       {"low": 35, "high": 60},
    "ARCH_STABILITY":         {"low": 30, "high": 55},
    "ARCH_HUBNESS":           {"low": 35, "high": 60},
    "ARCH_MATURATION":        {"low": 35, "high": 60},
    "ARCH_SYNCHRONY":         {"low": 35, "high": 60},
    "ARCH_SEGREGATION":       {"low": 30, "high": 55},
    "ARCH_RHYTHM_STABILITY":  {"low": 30, "high": 55},
    "ARCH_DECOMPENSATION_RISK": {"low": 25, "high": 50},
}


def _level(val, axis):
    """Определяет уровень параметра: low/mid/high"""
    norms = LEMON_NORMS.get(axis, {"low": 33, "high": 67})
    if val < norms["low"]:
        return "low"
    elif val > norms["high"]:
        return "high"
    return "mid"


# ─── ВЫЧИСЛЕНИЕ ИНДЕКСОВ (из 245H формул) ─────────────────────────────────────

def compute_indices(raw):
    """
    Вычисляет 8 интерпретационных индексов из сырых параметров движка 43.

    raw: dict с ключами RS1_RHYTHM, RS2_SYNC, RS3_SEGR, RS4_INTEGRAL,
         X_EXC, X_SENS, X_STAB, X_INTEG, X_FLEX, X_LAB, X_SEGR, X_HUB, X_MAT,
         hidden_tension_index, pathology_load_score, adaptive_stability_score,
         adaptive_control_score, decompensation_risk_score, tension_control_ratio
    """
    def g(k, default=50):
        v = raw.get(k, default)
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    # Прямое маппирование в ARCH-пространство (нормализованное 0-100)
    arch = {
        "ARCH_RHYTHM_STABILITY":  g("RS1_RHYTHM") * 5 + 50,
        "ARCH_SYNCHRONY":         g("RS2_SYNC"),
        "ARCH_SEGREGATION":       g("RS3_SEGR") * 5 + 30,
        "ARCH_INTEGRATION":       g("RS4_INTEGRAL"),
        "ARCH_EXCITABILITY":      g("X_EXC") * 3 + 30,
        "ARCH_SENSITIVITY":       g("X_SENS") * 2 + 20,
        "ARCH_STABILITY":         max(0, 80 + g("X_STAB")),
        "ARCH_FLEXIBILITY":       g("X_FLEX") * 2 + 20,
        "ARCH_LABILITY":          g("X_LAB") * 2 + 20,
        "ARCH_HUBNESS":           g("X_HUB") * 0.8 + 20,
        "ARCH_MATURATION":        g("X_MAT") * 0.8 + 20,
        "ARCH_POWER":             g("architecture_power_score"),
        "ARCH_OVERLOAD":          g("pathology_load_score"),
        "ARCH_ADAPTIVE_RESERVE":  g("high_load_compensation_score") * 0.8,
        "ARCH_DECOMPENSATION_RISK": g("decompensation_risk_score"),
    }

    # Клипуем в 0-100
    for k in arch:
        arch[k] = max(0, min(100, arch[k]))

    # 8 интерпретационных индексов (из твоих формул)
    indices = {
        "overload":      (arch["ARCH_OVERLOAD"]
                         + arch["ARCH_LABILITY"]
                         + arch["ARCH_DECOMPENSATION_RISK"]) / 3,

        "recovery":      (arch["ARCH_ADAPTIVE_RESERVE"]
                         + max(0, 100 - arch["ARCH_OVERLOAD"])) / 2,

        "flexibility":   (arch["ARCH_FLEXIBILITY"]
                         + arch["ARCH_SYNCHRONY"]
                         - arch["ARCH_LABILITY"] * 0.5 + 25),

        "rigidity":      (arch["ARCH_HUBNESS"]
                         + arch["ARCH_SEGREGATION"]
                         - arch["ARCH_FLEXIBILITY"] * 0.5 + 25),

        "transition_cost": (arch["ARCH_LABILITY"]
                           + arch["ARCH_SEGREGATION"]
                           - arch["ARCH_SYNCHRONY"] * 0.5 + 25),

        "emo_cost":      (arch["ARCH_SENSITIVITY"]
                         + arch["ARCH_OVERLOAD"]
                         + arch["ARCH_LABILITY"]) / 3,

        "bottleneck":    (arch["ARCH_HUBNESS"]
                         + arch["ARCH_INTEGRATION"]
                         + arch["ARCH_OVERLOAD"]
                         - arch["ARCH_ADAPTIVE_RESERVE"] * 0.5 + 25),

        "autonomic":     (arch["ARCH_SENSITIVITY"]
                         + arch["ARCH_DECOMPENSATION_RISK"]
                         + g("tension_control_ratio") * 10) / 3,
    }

    # Клипуем индексы
    for k in indices:
        indices[k] = max(0, min(100, indices[k]))

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
                     "Your neural architecture is operating well within its capacity. "
                     "Stress response is efficient and resources are not depleted."),
            "mid":  ("Moderate System Load",
                     "Your architecture carries a noticeable but manageable load. "
                     "Performance is maintained but recovery time matters."),
            "high": ("High System Load",
                     "Your neural system is operating near or at its upper limits. "
                     "This is often invisible externally — the system compensates. "
                     "But the cost is real: slower recovery, reduced flexibility under pressure."),
        },
        "recovery": {
            "low":  ("Limited Recovery Reserve",
                     "Your adaptive reserve is currently reduced. Recovery after stress "
                     "takes longer than your architecture is designed for."),
            "mid":  ("Adequate Recovery Capacity",
                     "Your system recovers reasonably well under normal conditions. "
                     "Extended pressure may reduce this."),
            "high": ("Strong Recovery Reserve",
                     "Your architecture has substantial adaptive reserve. "
                     "You bounce back from stress relatively quickly."),
        },
        "flexibility": {
            "low":  ("Low Cognitive Flexibility",
                     "Your architecture favors depth over breadth. "
                     "Context switches and sudden changes of direction are costly."),
            "mid":  ("Moderate Cognitive Flexibility",
                     "You adapt to changing contexts at a normal pace. "
                     "Some transitions are smooth, others require effort."),
            "high": ("High Cognitive Flexibility",
                     "Your architecture handles context shifts efficiently. "
                     "You generate options and adapt to new information quickly."),
        },
        "rigidity": {
            "low":  ("Fluid Pattern Maintenance",
                     "You hold patterns loosely — which supports creativity "
                     "but may challenge consistency."),
            "mid":  ("Balanced Structural Stability",
                     "You maintain useful patterns without being locked into them."),
            "high": ("Strong Structural Rigidity",
                     "Your architecture builds and maintains strong patterns. "
                     "This supports focus and depth but makes rapid pivots costly."),
        },
        "transition_cost": {
            "low":  ("Low Transition Cost",
                     "Moving between tasks or modes is efficient for your architecture."),
            "mid":  ("Moderate Transition Cost",
                     "Task switching takes some effort — building in transition time helps."),
            "high": ("High Transition Cost",
                     "Your architecture pays a significant cost for switching contexts. "
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
                     "Your architecture invests significant resources in emotional processing. "
                     "Stress, conflict, and high-stakes situations drain more than average. "
                     "This is architecture, not weakness."),
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
                     "Geomagnetic and electromagnetic fluctuations have limited impact."),
            "mid":  ("Moderate Autonomic Reactivity",
                     "Environmental factors have a measurable effect on your baseline state."),
            "high": ("High Autonomic Reactivity",
                     "Your nervous system is highly responsive to environmental signals — "
                     "including electromagnetic fluctuations, weather changes, and "
                     "social-emotional fields. This heightens both sensitivity and vulnerability."),
        },
    },
    "RU": {
        "overload": {
            "low":  ("Низкая нагрузка на систему",
                     "Ваша нейронная архитектура работает в пределах нормы. "
                     "Стрессовая реакция эффективна, ресурсы не истощены."),
            "mid":  ("Умеренная нагрузка на систему",
                     "Архитектура несёт заметную, но управляемую нагрузку. "
                     "Производительность сохраняется, но время восстановления имеет значение."),
            "high": ("Высокая нагрузка на систему",
                     "Ваша нейронная система работает вблизи верхних пределов. "
                     "Внешне это часто незаметно — система компенсирует. "
                     "Но цена реальна: замедленное восстановление, сниженная гибкость под давлением."),
        },
        "recovery": {
            "low":  ("Ограниченный адаптивный резерв",
                     "Ваш адаптивный резерв снижен. Восстановление после стресса "
                     "занимает больше времени чем рассчитана ваша архитектура."),
            "mid":  ("Достаточный резерв восстановления",
                     "Система восстанавливается нормально в обычных условиях. "
                     "Длительное давление может снизить этот показатель."),
            "high": ("Сильный резерв восстановления",
                     "Ваша архитектура обладает значительным адаптивным резервом. "
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
                     "Ваша архитектура платит значительную цену за смену контекста. "
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
                     "Это архитектура, а не слабость."),
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
                     "Геомагнитные и электромагнитные колебания имеют ограниченный эффект."),
            "mid":  ("Умеренная автономная реактивность",
                     "Внешние факторы оказывают измеримое влияние на ваше базовое состояние."),
            "high": ("Высокая автономная реактивность",
                     "Ваша нервная система высоко чувствительна к внешним сигналам — "
                     "включая электромагнитные колебания, смену погоды и "
                     "социально-эмоциональный фон. Это повышает и чувствительность, и уязвимость."),
        },
    },
}

GAP_CLASS_TEXTS = {
    "EN": {
        "FULL_MATCH": "Your prenatal solar profile, neural architecture, and behavioral tests align well. What your architecture predicts matches how you actually function.",
        "PARTIAL_MATCH": "Moderate alignment across sources. Your architecture provides a reliable baseline prediction with some individual variation in expression.",
        "COMPENSATED_RUPTURE": "Your prenatal architecture predicts one profile, but your behavior shows significant compensation. You are functioning above your natural baseline — but at a cost.",
        "HIGH_RUPTURE": "Major discrepancy detected between your architectural prediction and measured function. This gap reflects either strong developmental compensation or current situational load.",
        "SSN_EEG_MATCH_BEHAVIORAL_RUPTURE": "Your architecture and neural measurements align, but behavioral output differs. Environment, stress, or learned patterns are modifying how your architecture expresses.",
        "EEG_TESTS_MATCH_SSN_RUPTURE": "Your current neural and behavioral measurements align, but differ from prenatal prediction. Developmental experience has substantially shaped your architecture.",
        "SINGLE_SOURCE": "Profile based on prenatal solar dynamics only. Add cognitive tests to reveal the gap between architecture and current function.",
    },
    "RU": {
        "FULL_MATCH": "Ваш пренатальный солнечный профиль, нейронная архитектура и поведенческие тесты хорошо согласованы. То, что предсказывает архитектура, совпадает с тем, как вы реально функционируете.",
        "PARTIAL_MATCH": "Умеренное согласование источников. Ваша архитектура даёт надёжный базовый прогноз с некоторой индивидуальной вариацией в выражении.",
        "COMPENSATED_RUPTURE": "Ваша пренатальная архитектура предсказывает один профиль, но поведение показывает значительную компенсацию. Вы функционируете выше своего природного базового уровня — но ценой ресурсов.",
        "HIGH_RUPTURE": "Обнаружено значительное расхождение между архитектурным предсказанием и измеренной функцией. Этот разрыв отражает либо сильную компенсацию развития, либо текущую ситуационную нагрузку.",
        "SSN_EEG_MATCH_BEHAVIORAL_RUPTURE": "Ваша архитектура и нейронные измерения согласованы, но поведенческий вывод отличается. Среда, стресс или выученные паттерны изменяют то, как выражается ваша архитектура.",
        "EEG_TESTS_MATCH_SSN_RUPTURE": "Ваши текущие нейронные и поведенческие измерения согласованы, но отличаются от пренатального предсказания. Опыт развития существенно сформировал вашу архитектуру.",
        "SINGLE_SOURCE": "Профиль основан только на пренатальной солнечной динамике. Добавьте когнитивные тесты чтобы выявить разрыв между архитектурой и текущей функцией.",
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
            dynamics.append("Different emotional processing cost — one partner 'pays more' emotionally in conflict. This is architecture, not weakness.")

        if recovery_diff > 20:
            dynamics.append("Different recovery capacity — one needs more restoration time. Accounting for this reduces pair tension.")

    return {
        "score":    round(compatibility_score),
        "dynamics": dynamics,
        "idx1":     idx1,
        "idx2":     idx2,
    }