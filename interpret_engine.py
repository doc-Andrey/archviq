from __future__ import annotations

from typing import Any, Dict, List

LABELS = {
    "RU": {
        "resource": "Ресурс",
        "switching": "Переключение",
        "lock": "Фиксация",
        "novelty": "Новизна",
        "control": "Контроль",
        "processing_cost": "Цена обработки",
        "maturation": "Поздняя консолидация",
    },
    "EN": {
        "resource": "Resource",
        "switching": "Switching",
        "lock": "Lock",
        "novelty": "Novelty",
        "control": "Control",
        "processing_cost": "Processing cost",
        "maturation": "Late consolidation",
    },
}


def band(v: float) -> str:
    if v < 42:
        return "low"
    if v > 58:
        return "high"
    return "mid"


TEXT = {
    "RU": {
        "resource": {
            "high": "Ресурс — одна из сильных осей профиля. Система рассчитана на длительную нагрузку и устойчивую отдачу, если работа структурирована.",
            "mid": "Ресурс сбалансирован: производительность сильнее зависит от режима, качества задачи и восстановления, чем от простого увеличения часов.",
            "low": "Ресурс лучше расходовать выборочно. Качество среды и приоритетов важнее попытки держать высокий темп постоянно.",
        },
        "switching": {
            "high": "Переключение даётся относительно легко. Профиль допускает несколько параллельных контекстов и быструю смену задачи.",
            "mid": "Переключение работает лучше в умеренном режиме: достаточно гибкости без необходимости постоянно менять контекст.",
            "low": "Профиль выигрывает от непрерывности. Глубокая работа и длинные блоки обычно рациональнее частого переключения.",
        },
        "lock": {
            "high": "Высокая фиксация поддерживает глубокое удержание задачи и устойчивые привычки. Переход между режимами лучше планировать заранее.",
            "mid": "Фиксация умеренная: система может удерживать направление и при этом менять стратегию без большой потери инерции.",
            "low": "Низкая фиксация облегчает перестройку, но требует внешних опор для длинных циклов: дедлайнов, чек-листов и явных критериев завершения.",
        },
        "novelty": {
            "high": "Новизна усиливает вовлечённость. Сложные новые задачи, вариативность и обучение могут поддерживать рабочий тонус.",
            "mid": "Оптимален баланс нового и знакомого: развитие без постоянной смены среды.",
            "low": "Профиль больше выигрывает от мастерства, повторяемости и понятной структуры, чем от непрерывного поиска новых стимулов.",
        },
        "control": {
            "high": "Контроль — сильная сторона профиля: цель легче удерживать при конкурирующих сигналах и внешнем шуме.",
            "mid": "Контроль стабилен при нормальной нагрузке и заметно зависит от сна, усталости и количества одновременно открытых задач.",
            "low": "Контроль выгодно выносить наружу: расписание, заранее принятые правила и уменьшение числа одновременных решений повышают устойчивость.",
        },
        "processing_cost": {
            "high": "Цена сложной обработки повышена. Одновременные решения, быстрые правила и многозадачность могут быть дорогими даже при высокой общей работоспособности.",
            "mid": "Цена обработки умеренная. Система справляется со сложностью, если не перегружать число параллельных правил.",
            "low": "Цена обработки относительно низкая: профиль лучше переносит быстрые правила, сравнение вариантов и динамический поток информации.",
        },
        "maturation": {
            "high": "Профиль выраженно смещён к поздней консолидации: более поздние окна сильнее формируют итоговую структуру, чем ранние.",
            "mid": "Развитие распределено относительно равномерно между ранними и поздними окнами.",
            "low": "Ранние окна имеют больший вес в общей временной конфигурации профиля.",
        },
    },
    "EN": {
        "resource": {
            "high": "Resource is one of the stronger profile axes. The system is configured for sustained throughput when work is well structured.",
            "mid": "Resource is balanced: output depends more on task quality, pacing and recovery than on simply adding hours.",
            "low": "Resource is best spent selectively. Environment and priorities matter more than trying to maintain maximum pace continuously.",
        },
        "switching": {
            "high": "Switching is relatively inexpensive. The profile can carry several contexts and change task state quickly.",
            "mid": "Switching works best in moderation: enough flexibility without constant context change.",
            "low": "The profile benefits from continuity. Deep work and longer blocks are usually more efficient than frequent switching.",
        },
        "lock": {
            "high": "High lock supports deep task retention and stable habits. Transitions work better when they are planned rather than forced abruptly.",
            "mid": "Lock is moderate: the system can hold direction while still changing strategy without excessive inertia.",
            "low": "Low lock supports rapid reconfiguration, but longer cycles benefit from external anchors such as deadlines, checklists and clear finish criteria.",
        },
        "novelty": {
            "high": "Novelty is likely to support engagement. New complex tasks, learning and variation can help maintain activation.",
            "mid": "A balance of familiar and new work is likely to be most efficient.",
            "low": "The profile gains more from mastery, repeatability and clear structure than from continuous novelty seeking.",
        },
        "control": {
            "high": "Control is a strong axis: the target is easier to hold in the presence of competing signals and external noise.",
            "mid": "Control is stable under normal load and becomes more dependent on sleep, fatigue and the number of simultaneous tasks under pressure.",
            "low": "Externalizing control helps: schedules, pre-commitment rules and fewer simultaneous decisions improve consistency.",
        },
        "processing_cost": {
            "high": "Complex processing carries a higher cost. Simultaneous decisions, rapid rules and multitasking may be expensive even when overall capacity is good.",
            "mid": "Processing cost is moderate. The system handles complexity best when the number of concurrent rules is controlled.",
            "low": "Processing cost is relatively low: rapid rule changes, option comparison and dynamic information flow are easier to sustain.",
        },
        "maturation": {
            "high": "The profile is weighted toward later consolidation: later developmental windows contribute more strongly to the final temporal structure.",
            "mid": "Developmental weighting is relatively balanced across early and later windows.",
            "low": "Earlier windows carry more weight in the profile's overall temporal configuration.",
        },
    },
}

SIGNATURES = {
    "RU": {
        "resource": ("Ресурсный профиль", "Сила — в устойчивой отдаче и способности держать нагрузку."),
        "switching": ("Адаптивный профиль", "Сила — в смене контекста, скорости перестройки и вариативности."),
        "lock": ("Глубокий профиль", "Сила — в удержании задачи, специализации и накоплении мастерства."),
        "novelty": ("Исследующий профиль", "Сила — в новых задачах, обучении и поиске нестандартных решений."),
        "control": ("Управляющий профиль", "Сила — в удержании цели, фильтрации помех и последовательности."),
        "processing_cost": ("Интенсивный профиль", "Система способна на сложную работу, но цена одновременной обработки требует управления."),
        "maturation": ("Поздно-консолидирующий профиль", "Поздние окна развития имеют повышенный вес в итоговой конфигурации."),
        "balanced": ("Сбалансированный профиль", "Ни одна ось не доминирует резко: результат определяется сочетанием контекста и режима."),
    },
    "EN": {
        "resource": ("Resource-led profile", "Strength comes from sustained output and the ability to hold load."),
        "switching": ("Adaptive profile", "Strength comes from context change, reconfiguration speed and variability."),
        "lock": ("Deep profile", "Strength comes from task retention, specialization and accumulated mastery."),
        "novelty": ("Exploratory profile", "Strength comes from new tasks, learning and unconventional solution search."),
        "control": ("Control-led profile", "Strength comes from target retention, filtering interference and consistency."),
        "processing_cost": ("High-intensity profile", "Complex work is possible, but concurrent processing cost needs active management."),
        "maturation": ("Late-consolidating profile", "Later developmental windows carry more weight in the final configuration."),
        "balanced": ("Balanced profile", "No axis dominates sharply; performance is driven by the interaction of context and operating mode."),
    },
}


def interpret(profile: Dict[str, Any], lang: str = "RU") -> Dict[str, Any]:
    lang = "RU" if lang.upper().startswith("RU") else "EN"
    scores = profile.get("scores", {})
    items = []
    for key, value in scores.items():
        b = band(float(value))
        items.append({
            "key": key,
            "label": LABELS[lang][key],
            "value": float(value),
            "band": b,
            "text": TEXT[lang][key][b],
            "timing_range": float(profile.get("uncertainty", {}).get(key, 0.0)),
        })
    signature = profile.get("signature", "balanced")
    title, subtitle = SIGNATURES[lang].get(signature, SIGNATURES[lang]["balanced"])

    # Priorities: strongest axis + highest processing cost / lowest control if present.
    ranked = sorted(items, key=lambda x: x["value"], reverse=True)
    priorities: List[str] = []
    if ranked:
        priorities.append(ranked[0]["label"])
    if scores.get("processing_cost", 50) > 60:
        priorities.append(LABELS[lang]["processing_cost"])
    if scores.get("control", 50) < 42:
        priorities.append(LABELS[lang]["control"])
    if scores.get("switching", 50) < 42:
        priorities.append(LABELS[lang]["switching"])

    return {
        "title": title,
        "subtitle": subtitle,
        "items": items,
        "priorities": list(dict.fromkeys(priorities)),
    }
