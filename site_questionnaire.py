from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
BLUEPRINT_PATH = ROOT / "analysis_modules" / "config" / "thematic_questionnaires.json"

AXES = ("resource", "switching", "lock", "novelty", "control", "processing_cost")

AXIS_SCALE = {
    "resource": "resource_expression",
    "switching": "switching_expression",
    "lock": "lock_expression",
    "novelty": "novelty_expression",
    "control": "control_expression",
    "processing_cost": "processing_cost_expression",
}

SCALE_LABELS = {
    "resource_expression": ("Sustained resource", "Устойчивость ресурса"),
    "switching_expression": ("Switching", "Переключение"),
    "lock_expression": ("Task lock", "Фиксация на задаче"),
    "novelty_expression": ("Exploration", "Исследование нового"),
    "control_expression": ("Interference control", "Контроль помех"),
    "processing_cost_expression": ("Processing cost", "Цена обработки"),
    "compensatory_effort": ("Compensatory effort", "Компенсаторные усилия"),
    "state_interference": ("Current-state interference", "Влияние текущего состояния"),
    "context_support": ("Context support", "Поддержка среды"),
}

ITEMS_EN = {
    "ARCH_RES_01": "On an ordinary day, I can maintain mental clarity for a long time without a sharp drop.",
    "ARCH_RES_02": "After several difficult tasks, my mental productivity drops quickly.",
    "ARCH_RES_03": "After a short break, I usually return to a task with restored capacity.",
    "ARCH_RES_04": "After a normal workload, I still have capacity for one more important task.",
    "ARCH_SWITCH_01": "I can move to another task without losing the thread of my work for long.",
    "ARCH_SWITCH_02": "After an unexpected rule change, I need a long time to reconfigure.",
    "ARCH_SWITCH_03": "When I return to an interrupted task, I quickly recover its context.",
    "ARCH_SWITCH_04": "I can change my approach when the previous one stops working.",
    "ARCH_LOCK_01": "Once focused, I steadily maintain the chosen line of action.",
    "ARCH_LOCK_02": "An unfinished task keeps holding my attention even after I switch away.",
    "ARCH_LOCK_03": "I easily abandon an approach even after investing substantial effort in it.",
    "ARCH_LOCK_04": "After making a decision, I find it hard to stop rechecking or refining it.",
    "ARCH_NOV_01": "With a new task, I first consider several possible approaches.",
    "ARCH_NOV_02": "Uncertainty can make me interested in exploring alternatives.",
    "ARCH_NOV_03": "Even when conditions change, I prefer a familiar, proven method.",
    "ARCH_NOV_04": "I notice unusual possibilities before a ready-made instruction appears.",
    "ARCH_CTRL_01": "During a difficult task, I keep the main goal in mind despite distractions.",
    "ARCH_CTRL_02": "I can stop my first impulsive response and check the conditions.",
    "ARCH_CTRL_03": "With conflicting cues, I often answer before checking the rule.",
    "ARCH_CTRL_04": "I can remember a constraint while monitoring whether I follow it.",
    "ARCH_COST_01": "Tasks with several conditions noticeably exhaust me even when I solve them correctly.",
    "ARCH_COST_02": "After intensive mental work, I need separate recovery time.",
    "ARCH_COST_03": "When complexity and speed rise together, my error cost increases sharply.",
    "ARCH_COST_04": "I can process complex information for a long time without internal overload.",
    "ARCH_EFFORT_01": "Maintaining my usual quality takes more effort than others can see.",
    "ARCH_EFFORT_02": "I maintain performance through lists, repeated checks, or strict routines.",
    "ARCH_EFFORT_03": "Most difficult tasks are completed without extra internal strain.",
    "ARCH_EFFORT_04": "In the last two weeks, even a good result often came with noticeable fatigue.",
    "ARCH_STATE_01": "In the last two weeks, sleep loss or physical condition slowed my thinking.",
    "ARCH_STATE_02": "Anxiety or emotional tension occupied part of my attention during tasks.",
    "ARCH_STATE_03": "My current workload impaired switching and error control.",
    "ARCH_STATE_04": "In the last two weeks, my condition allowed me to work at my usual level.",
    "ARCH_CONTEXT_01": "I can organize work at a pace that suits me.",
    "ARCH_CONTEXT_02": "I can limit unnecessary interruptions during difficult work.",
    "ARCH_CONTEXT_03": "Tools and external notes help me avoid keeping every condition in mind.",
    "ARCH_CONTEXT_04": "I am often required to work in a mode that prevents me from using my strengths.",
}


def load_architecture_instrument() -> Dict[str, Any]:
    blueprint = json.loads(BLUEPRINT_PATH.read_text(encoding="utf-8"))
    return blueprint["instruments"]["architecture_questionnaire"]


def item_text(item: Mapping[str, Any], lang: str) -> str:
    if lang == "EN":
        return ITEMS_EN.get(str(item["id"]), str(item["id"]))
    return str(item.get("ru", item["id"]))


def scale_label(scale_id: str, lang: str) -> str:
    en, ru = SCALE_LABELS.get(scale_id, (scale_id, scale_id))
    return ru if lang == "RU" else en


def score_architecture_responses(responses: Mapping[str, Any]) -> Dict[str, float]:
    instrument = load_architecture_instrument()
    result: Dict[str, float] = {}
    for scale_id, scale in instrument["scales"].items():
        values = []
        for item in scale["items"]:
            raw = responses.get(item["id"])
            if raw is None:
                continue
            value = float(raw)
            values.append(6.0 - value if item.get("reverse") else value)
        if len(values) >= 3:
            result[scale_id] = round((sum(values) / len(values) - 1.0) * 25.0, 2)
    return result


def architecture_gap(profile_scores: Mapping[str, Any], questionnaire_scores: Mapping[str, Any]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for axis in AXES:
        engine = float(profile_scores[axis])
        questionnaire = float(questionnaire_scores[AXIS_SCALE[axis]])
        gap = questionnaire - engine
        out[axis] = {
            "engine43": round(engine, 2),
            "questionnaire": round(questionnaire, 2),
            "signed_gap": round(gap, 2),
            "absolute_gap": round(abs(gap), 2),
        }
    return out


COGNITIVE_FIELDS = {
    "SRT_median_rt": ("Simple reaction median", "Медиана простой реакции", "ms"),
    "SRT_sd_rt": ("Reaction-time variability", "Вариативность реакции", "ms"),
    "CHOICE_accuracy": ("Choice accuracy", "Точность выбора", "ratio"),
    "CHOICE_median_correct_rt": ("Choice reaction median", "Медиана реакции выбора", "ms"),
    "NBACK_accuracy": ("2-back accuracy", "Точность 2-back", "ratio"),
    "NBACK_false_alarm_rate": ("2-back false-alarm rate", "Ложные тревоги 2-back", "ratio"),
    "SIMON_accuracy": ("Simon accuracy", "Точность теста Саймона", "ratio"),
    "SIMON_interference_cost": ("Simon interference cost", "Цена интерференции Саймона", "ms"),
    "COMPLEX_ACC_accuracy": ("Complex-rule accuracy", "Точность сложного правила", "ratio"),
    "COMPLEX_ACC_median_correct_rt": ("Complex-rule reaction median", "Медиана реакции сложного правила", "ms"),
    "COMPLEX_SPEED_GAIN_MS": ("Speed gain under deadline", "Выигрыш скорости при дедлайне", "ms"),
    "COMPLEX_ERROR_INCREASE_RATE": ("Error increase under deadline", "Прирост ошибок при дедлайне", "ratio"),
}


def parse_cognitive_csv(uploaded: Any) -> Dict[str, Any]:
    frame = pd.read_csv(uploaded)
    if frame.empty:
        raise ValueError("The cognitive CSV has no data rows.")
    row = frame.iloc[0]
    metrics: Dict[str, float] = {}
    for field in COGNITIVE_FIELDS:
        if field not in frame.columns:
            continue
        value = pd.to_numeric(pd.Series([row[field]]), errors="coerce").iloc[0]
        if pd.notna(value):
            metrics[field] = round(float(value), 4)
    if len(metrics) < 4:
        raise ValueError("This file is not an ARCHVIQ cognitive-battery export.")
    return {
        "source": "ARCHVIQ cognitive battery",
        "status": "RAW_TASK_METRICS_NOT_NORMED",
        "metrics": metrics,
        "note": "Raw task metrics are retained in the integrated record but are not mapped to 0–100 architecture axes until external norms are validated.",
    }
