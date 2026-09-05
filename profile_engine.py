from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

SITE_DIR = Path.home() / "psychotyp_site"
ENGINE_PATH = SITE_DIR / "43_CLIENT_RUN_v2.py"

PROFILES: Dict[str, Dict[str, Any]] = {
    "FORTRESS": {
        "type_name": {"EN": "Fortress", "RU": "Крепость"},
        "tagline": {
            "EN": "Stable, structured, resistant to chaos.",
            "RU": "Стабильный, структурный, устойчивый к хаосу.",
        },
        "insights_EN": [
            "You process information best when the task has clear boundaries.",
            "Your strength is stability under pressure.",
            "Too much uncertainty can slow the first step.",
        ],
        "insights_RU": [
            "Вы лучше работаете, когда у задачи есть ясные границы.",
            "Ваша сила — устойчивость под давлением.",
            "Избыток неопределённости может тормозить первый шаг.",
        ],
        "recommendations_EN": [
            "Use checklists and clear success criteria.",
            "Split large tasks into controlled steps.",
            "Avoid too many open tasks at the same time.",
        ],
        "recommendations_RU": [
            "Используйте чек-листы и ясные критерии результата.",
            "Делите большие задачи на контролируемые шаги.",
            "Не держите одновременно слишком много открытых задач.",
        ],
    },
    "ANTENNA": {
        "type_name": {"EN": "Antenna", "RU": "Антенна"},
        "tagline": {
            "EN": "Sensitive, signal-oriented, fast at detecting change.",
            "RU": "Чувствительный тип, быстро улавливающий изменения.",
        },
        "insights_EN": [
            "You detect weak signals earlier than many others.",
            "The main risk is overload from noise and ambiguity.",
            "You need separation between signal detection and final decision.",
        ],
        "insights_RU": [
            "Вы рано замечаете слабые сигналы.",
            "Главный риск — перегрузка шумом и неопределённостью.",
            "Вам полезно разделять обнаружение сигнала и финальное решение.",
        ],
        "recommendations_EN": [
            "Reduce background noise and interruptions.",
            "Use written task criteria.",
            "Do not make important decisions inside emotional noise.",
        ],
        "recommendations_RU": [
            "Снижайте фоновый шум и прерывания.",
            "Используйте письменные критерии задачи.",
            "Не принимайте важные решения внутри эмоционального шума.",
        ],
    },
    "FLUID": {
        "type_name": {"EN": "Fluid Integrator", "RU": "Гибкий интегратор"},
        "tagline": {
            "EN": "Adaptive, associative, strong in connecting distant elements.",
            "RU": "Гибкий, ассоциативный, сильный в связывании разных элементов.",
        },
        "insights_EN": [
            "You work well with complex and changing tasks.",
            "You connect distant ideas quickly.",
            "Efficiency drops when there is no priority or output format.",
        ],
        "insights_RU": [
            "Вы хорошо работаете со сложными и изменчивыми задачами.",
            "Вы быстро связываете далёкие идеи.",
            "Эффективность падает, если нет приоритета и формата результата.",
        ],
        "recommendations_EN": [
            "Use time boxes and milestones.",
            "Keep one main objective visible.",
            "Convert exploration into a concrete deliverable early.",
        ],
        "recommendations_RU": [
            "Используйте временные блоки и промежуточные точки.",
            "Держите перед собой одну главную цель.",
            "Рано переводите исследование в конкретный результат.",
        ],
    },
    "COLLAPSE": {
        "type_name": {"EN": "High-Load System", "RU": "Система высокой нагрузки"},
        "tagline": {
            "EN": "Powerful, but vulnerable to overload without structure.",
            "RU": "Мощная, но уязвимая к перегрузке без структуры.",
        },
        "insights_EN": [
            "You may have high internal intensity.",
            "Too many simultaneous demands can destabilize performance.",
            "Your result improves when pressure and responsibility are structured.",
        ],
        "insights_RU": [
            "У вас может быть высокая внутренняя интенсивность.",
            "Слишком много одновременных требований может снижать устойчивость.",
            "Результат улучшается, когда давление и ответственность структурированы.",
        ],
        "recommendations_EN": [
            "Avoid chaotic multitasking.",
            "Use recovery pauses after high-load decisions.",
            "Break pressure tasks into small execution blocks.",
        ],
        "recommendations_RU": [
            "Избегайте хаотичной многозадачности.",
            "Делайте паузы восстановления после решений с высокой нагрузкой.",
            "Делите стрессовые задачи на малые блоки выполнения.",
        ],
    },
}

COMPAT: Dict[Tuple[str, str], Tuple[int, str]] = {
    ("FORTRESS", "FORTRESS"): (78, "Stable pair. Strong structure, but possible rigidity."),
    ("FORTRESS", "ANTENNA"): (74, "Structure plus sensitivity. Good balance if sensitivity is respected."),
    ("FORTRESS", "FLUID"): (82, "Strong complementarity: structure plus adaptability."),
    ("FORTRESS", "COLLAPSE"): (66, "The stable profile can reduce overload, but pressure rules are needed."),
    ("ANTENNA", "FORTRESS"): (74, "Structure plus sensitivity. Good balance if sensitivity is respected."),
    ("ANTENNA", "ANTENNA"): (62, "High mutual sensitivity. Understanding is high, but noise can amplify tension."),
    ("ANTENNA", "FLUID"): (76, "Sensitive detection plus flexible integration. Creative but needs noise control."),
    ("ANTENNA", "COLLAPSE"): (58, "High sensitivity can amplify overload. Boundaries are necessary."),
    ("FLUID", "FORTRESS"): (82, "Strong complementarity: adaptability plus structure."),
    ("FLUID", "ANTENNA"): (76, "Flexible integration plus signal sensitivity. Good for complex tasks."),
    ("FLUID", "FLUID"): (72, "Highly adaptive pair. Needs deadlines and clear output criteria."),
    ("FLUID", "COLLAPSE"): (64, "High creative intensity, but overload risk rises without structure."),
    ("COLLAPSE", "FORTRESS"): (66, "Stability can compensate high load if roles are explicit."),
    ("COLLAPSE", "ANTENNA"): (58, "Sensitivity plus high load needs calm communication and boundaries."),
    ("COLLAPSE", "FLUID"): (64, "Creative intensity is high, but task structure is essential."),
    ("COLLAPSE", "COLLAPSE"): (52, "High intensity on both sides. Strong recovery and conflict rules are needed."),
}

def _text(ptype: str, lang: str) -> Dict[str, Any]:
    lang = "RU" if lang == "RU" else "EN"
    p = PROFILES.get(ptype, PROFILES["FLUID"])
    return {
        "type_name": p["type_name"][lang],
        "tagline": p["tagline"][lang],
        "insights": p[f"insights_{lang}"],
        "recommendations": p[f"recommendations_{lang}"],
    }

def _safe_float(x, default=50.0) -> float:
    try:
        v = float(x)
        if pd.isna(v):
            return default
        return v
    except Exception:
        return default

def _norm(x, default=50.0) -> float:
    v = _safe_float(x, default)
    if 0 <= v <= 1:
        v *= 100.0
    return max(0.0, min(100.0, v))

def _map_profile_class(profile_class: str, row: Dict[str, Any] | None = None) -> str:
    pc = str(profile_class or "").upper()

    if "HIGH_LOAD" in pc or "COLLAPSE" in pc or "DECOMP" in pc or "RISK" in pc:
        return "COLLAPSE"
    if "SENS" in pc or "ANTENNA" in pc:
        return "ANTENNA"
    if "STAB" in pc or "FORTRESS" in pc or "LOW_LOAD" in pc:
        return "FORTRESS"
    if "INTEGR" in pc or "FLEX" in pc or "COMPENSATED" in pc or "MIDDLE" in pc:
        return "FLUID"

    if row:
        tension = _safe_float(row.get("hidden_tension_index", 0), 0)
        adaptive = _safe_float(row.get("adaptive_control_score", 0), 0)
        sens = _safe_float(row.get("X_SENS", 0), 0)
        integ = _safe_float(row.get("X_INTEG", 0), 0)
        stab = _safe_float(row.get("X_STAB", 0), 0)

        if tension > 35 and adaptive < 20:
            return "COLLAPSE"
        if sens > 15:
            return "ANTENNA"
        if stab > 10:
            return "FORTRESS"
        if integ > 15:
            return "FLUID"

    return "FLUID"

def _fallback_profile(dob: str, sex: str, name: str, lang: str) -> Dict[str, Any]:
    seed = f"{dob}|{sex}|{name}".encode("utf-8")
    h = hashlib.md5(seed).hexdigest()
    keys = ["FORTRESS", "ANTENNA", "FLUID", "COLLAPSE"]
    ptype = keys[int(h[0:2], 16) % 4]
    tx = _text(ptype, lang)

    return {
        "name": name,
        "dob": dob,
        "sex": sex,
        "lang": lang,
        "ptype": ptype,
        "type_name": tx["type_name"],
        "tagline": tx["tagline"],
        "rs1": int(h[2:4], 16) % 101,
        "rs2": int(h[4:6], 16) % 101,
        "rs3": int(h[6:8], 16) % 101,
        "rs4": int(h[8:10], 16) % 101,
        "tension": int(h[10:12], 16) % 101,
        "adaptive": int(h[12:14], 16) % 101,
        "insights": tx["insights"],
        "recommendations": tx["recommendations"],
        "source": "fallback_md5",
    }

def compute_profile(dob: str, sex: str, name: str, lang: str = "EN") -> Dict[str, Any]:
    lang = "RU" if lang == "RU" else "EN"

    if not ENGINE_PATH.exists():
        return _fallback_profile(dob, sex, name, lang)

    with tempfile.TemporaryDirectory(prefix="psychotyp_") as tmp:
        tmpdir = Path(tmp)
        input_csv = tmpdir / "input.csv"
        out_dir = tmpdir / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        with input_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "dob", "sex"])
            writer.writeheader()
            writer.writerow({"name": name, "dob": dob, "sex": sex})

        env = os.environ.copy()
        env["PSYCHOTYP_OUT"] = str(out_dir)

        cmd = [
            sys.executable,
            str(ENGINE_PATH),
            "--input",
            str(input_csv),
            "--no_lag",
        ]

        try:
            subprocess.run(
                cmd,
                cwd=str(SITE_DIR),
                env=env,
                check=True,
                capture_output=True,
                text=True,
                timeout=90,
            )

            summary_path = out_dir / "00_universal_summary.csv"
            if not summary_path.exists():
                found = list(out_dir.rglob("00_universal_summary.csv"))
                if found:
                    summary_path = found[0]

            if not summary_path.exists():
                return _fallback_profile(dob, sex, name, lang)

            df = pd.read_csv(summary_path)
            if df.empty:
                return _fallback_profile(dob, sex, name, lang)

            row = df.iloc[0].to_dict()
            profile_class = row.get("profile_class", "")
            ptype = _map_profile_class(profile_class, row)
            tx = _text(ptype, lang)

            return {
                "name": name,
                "dob": dob,
                "sex": sex,
                "lang": lang,
                "ptype": ptype,
                "type_name": tx["type_name"],
                "tagline": tx["tagline"],
                "rs1": _norm(row.get("RS1_RHYTHM", row.get("rs1", 50))),
                "rs2": _norm(row.get("RS2_SYNC", row.get("rs2", 50))),
                "rs3": _norm(row.get("RS3_SEGR", row.get("rs3", 50))),
                "rs4": _norm(row.get("RS4_INTEGRAL", row.get("rs4", 50))),
                "tension": _norm(row.get("hidden_tension_index", row.get("tension", 50))),
                "adaptive": _norm(row.get("adaptive_control_score", row.get("adaptive", 50))),
                "insights": tx["insights"],
                "recommendations": tx["recommendations"],
                "profile_class_raw": profile_class,
                "source": "43_engine",
            }

        except Exception:
            return _fallback_profile(dob, sex, name, lang)

def get_compatibility(p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
    ptype1 = p1.get("ptype", "FLUID")
    ptype2 = p2.get("ptype", "FLUID")

    score, summary = COMPAT.get(
        (ptype1, ptype2),
        (65, "Mixed profile. Compatibility depends on task structure and communication rules."),
    )

    lang = p1.get("lang", "EN")
    dynamics: List[str] = []

    if lang == "RU":
        if ptype1 == ptype2:
            dynamics.append("Профили похожи. Это улучшает понимание, но может усиливать одну и ту же слабость.")
        else:
            dynamics.append("Профили дополняют друг друга. Это работает лучше при ясном разделении ролей.")

        if "ANTENNA" in [ptype1, ptype2]:
            dynamics.append("Есть высокая чувствительность к сигналам. Нужно снижать шум и неопределённость.")
        if "FORTRESS" in [ptype1, ptype2]:
            dynamics.append("Есть стабилизирующий компонент. Помогают планы, границы и критерии.")
        if "FLUID" in [ptype1, ptype2]:
            dynamics.append("Есть гибкий интегратор. Нужны сроки и понятный формат результата.")
        if "COLLAPSE" in [ptype1, ptype2]:
            dynamics.append("Возможна высокая нагрузка. Нельзя смешивать давление, конфликт и размытую ответственность.")
    else:
        if ptype1 == ptype2:
            dynamics.append("Both profiles are similar. This improves mutual understanding but may amplify the same weakness.")
        else:
            dynamics.append("The profiles are complementary. This works best when roles are explicit.")

        if "ANTENNA" in [ptype1, ptype2]:
            dynamics.append("High signal sensitivity is present. Reduce noise and ambiguity.")
        if "FORTRESS" in [ptype1, ptype2]:
            dynamics.append("A stabilizing component is present. Plans, boundaries and criteria help.")
        if "FLUID" in [ptype1, ptype2]:
            dynamics.append("A flexible integration component is present. Deadlines and output format are important.")
        if "COLLAPSE" in [ptype1, ptype2]:
            dynamics.append("High-load dynamics are possible. Avoid pressure, conflict and unclear responsibility at the same time.")

    return {
        "score": int(score),
        "summary": summary,
        "dynamics": dynamics,
        "p1_type": ptype1,
        "p2_type": ptype2,
    }
