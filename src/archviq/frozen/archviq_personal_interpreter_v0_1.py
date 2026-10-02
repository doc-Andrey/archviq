#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARCHVIQ Personal Interpreter v0.1
================================

Layer 3 for the ARCHVIQ developmental cyber-calibration pipeline.

INPUT
-----
A directory produced by archviq_brain_cyber_cascade_v0_2_rs4v4.py.
Required files:
    machine_profile_ensemble.csv
    machine_profile_by_run.csv
    parameter_definitions.csv
    machine_parameter_trajectory.csv
    brain_circuit_trajectory.csv
    packet_drivers.csv
    window_cascade_summary.csv
Recommended if present:
    developmental_parameter_map.csv
    brain_exposure_ensemble.csv
    formal_spec_manifest.json
    invariants_manifest.json
    lesion_manifest.json
    explanation_graph.json
    model_config_used.json

OUTPUT
------
    profile.json
    profile_report.md
    brain_map.json
    site_cards.json
    parameter_explanations.csv
    window_contributions.csv
    uncertainty_report.csv
    dominant_packets.csv
    run_metadata.json

IMPORTANT STATUS
----------------
This program does NOT diagnose personality, disease or brain anatomy.
It translates the numerical output of the experimental RS4/v4 developmental
cascade into an auditable, human-readable hypothesis report.

Evidence layers are kept separate:
    measured     : physical SSN-derived input calculated upstream
    modeled      : cascade state, hysteresis and parameter trajectories
    hypothesized : developmental circuit mapping and cybernetic meaning
    experimental : any downstream behavior/health use (not implemented here)

The interpreter intentionally does not turn pressure_only parameters into a
high/low trait. It reports only calibration pressure until a directional rule
is independently frozen.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

VERSION = "0.1"

WINDOW_ORDER = ["W1", "W2", "W3", "F1", "F2", "F3"]
WINDOW_ROLE_RU = {
    "W1": "базовая функциональная калибровка",
    "W2": "допуск и временная интеграция",
    "W3": "межканальная интеграция и сжатие",
    "F1": "удержание состояния / HOLD",
    "F2": "переключение, решение и commit",
    "F3": "обновление модели, гистерезис, recovery и якоря",
}

FAMILY_ORDER = ["BASE", "W", "NU", "D", "U", "RECOVERY", "TRUST", "REALITY", "GAMMA"]
FAMILY_RU = {
    "BASE": "Базовая реактивность",
    "W": "Допуск и накопление свидетельств",
    "NU": "ν: независимость, естественность и происхождение",
    "D": "HOLD, решение и переключение",
    "U": "Обновление модели и маршрутизация ошибки",
    "RECOVERY": "Возврат к рабочему состоянию",
    "TRUST": "Асимметрия доверия",
    "REALITY": "Reality-monitoring",
    "GAMMA": "Γ: офлайн-перекалибровка и память",
}

CIRCUIT_RU = {
    "BRAINSTEM_HOMEOSTATIC": "стволовые/гомеостатические контуры",
    "THALAMUS_TRN": "таламус / TRN",
    "PULVINAR_COHERENCE": "pulvinar / межканальная когерентность",
    "SUBPLATE_THALAMOCORTICAL": "subplate / таламокортикальные контуры",
    "HIPPOCAMPUS_CONTEXT": "гиппокамп / контекстная память",
    "AMYGDALA_INSULA": "амигдала / insula",
    "SALIENCE_DACC_INSULA": "salience-сеть / dACC / insula",
    "BASAL_GANGLIA_STN": "базальные ганглии / STN",
    "PFC_REALITY_CONTROL": "PFC / reality-control",
    "LONG_RANGE_CORTEX": "дальние кортико-кортикальные связи",
}

PARAM_RU: Dict[str, Dict[str, str]] = {
    "GAIN": {
        "name": "Общий gain / реактивность",
        "pos": "усиленный отклик системы на возмущение",
        "neg": "ослабленный отклик системы на возмущение",
        "process": "задаёт масштаб изменения внутреннего состояния при входном воздействии",
    },
    "NOISE_SENSITIVITY": {
        "name": "Чувствительность к нерегулярному входу",
        "pressure": "сила калибровочного давления на обработку шумного/нерегулярного сигнала",
        "process": "направление пока не заморожено; это не шкала «чувствительный/нечувствительный»",
    },
    "RECOVERY_BASELINE": {
        "name": "Базовая скорость возврата",
        "pos": "тенденция к более быстрому возврату после возмущения",
        "neg": "тенденция к более длительному carry-over после возмущения",
        "process": "характеризует возврат параметров к индивидуальной точке H*",
    },
    "THETA_W": {
        "name": "θ_W — порог допуска",
        "pos": "для допуска требуется более сильное/устойчивое свидетельство",
        "neg": "сигнал проходит на следующий уровень легче",
        "process": "работает на нижнем входном гейте спирали совместно с весом источника w_k",
    },
    "THETA_C": {
        "name": "θ_C — порог запроса Reality",
        "pos": "до запроса Reality требуется больше накопленного свидетельства/когерентности",
        "neg": "Reality подключается раньше",
        "process": "отделяет первично допущенное представление от явной проверки реальности",
    },
    "TAU_INTEGRATION": {
        "name": "τ — временная интеграция",
        "pos": "свидетельства интегрируются на более длинном временном горизонте",
        "neg": "обработка быстрее обновляется по недавнему входу",
        "process": "задаёт временной масштаб накопления информации внутри витка",
    },
    "THETA_NU_TIME": {
        "name": "θ_ν,time — порог временной естественности",
        "pressure": "калибровочное давление на ν_time",
        "process": "контролирует проверку временной регулярности; направление пока не заморожено",
    },
    "THETA_NU_CROSS": {
        "name": "θ_ν,cross — порог независимости источников",
        "pressure": "калибровочное давление на ν_cross",
        "process": "касается различения независимых подтверждений и общего генератора; направление пока не заморожено",
    },
    "THETA_NU_PROVENANCE": {
        "name": "θ_ν,provenance — порог происхождения",
        "pressure": "калибровочное давление на ν_provenance",
        "process": "касается различения внешнего и внутренне порождённого свидетельства; направление пока не заморожено",
    },
    "M_C": {
        "name": "M_C — требование независимых источников",
        "pressure": "калибровочное давление на механизм подсчёта независимых источников",
        "process": "буквальное количество источников не выводится из developmental layer",
    },
    "COMPRESSION_STRENGTH": {
        "name": "Сила рекуррентного сжатия",
        "pos": "более выраженное снижение размерности и рост абстракции",
        "neg": "больше деталей удерживается на каждом уровне",
        "process": "сжатие должно сохранять provenance и ссылки на исходные свидетельства",
    },
    "D_C": {
        "name": "D_C — порог устойчивого подтверждения",
        "pos": "для консолидации требуется более длительная серия PASS",
        "neg": "представление закрепляется после более короткой серии PASS",
        "process": "связан с переходом проверенного состояния в устойчивое",
    },
    "PERSISTENCE": {
        "name": "Persistence / HOLD",
        "pos": "активное состояние дольше сохраняется после выбора",
        "neg": "состояние легче теряет устойчивость и меняется",
        "process": "это устойчивость состояния, а не оценка «упрямства» или личности",
    },
    "HOLD_STABILITY": {
        "name": "Стабильность HOLD",
        "pos": "уже выбранная конфигурация устойчивее к обычным возмущениям",
        "neg": "активная конфигурация легче самопроизвольно меняется",
        "process": "описывает удержание рабочего режима между существенными событиями",
    },
    "THETA_D": {
        "name": "Θ_D — порог решения",
        "pos": "для фиксации решения требуется больше накопленного evidence",
        "neg": "commit решения возможен при меньшем объёме evidence",
        "process": "уровень представления, с которого ушло решение, остаётся отдельной координатой",
    },
    "THETA_A": {
        "name": "Θ_A — порог действия",
        "pressure": "калибровочное давление на преобразование решения в действие",
        "process": "направление пока не заморожено; решение и действие в модели разведены",
    },
    "SWITCH_THRESHOLD": {
        "name": "Порог переключения состояния",
        "pos": "обычное возмущение реже меняет активную конфигурацию",
        "neg": "активная конфигурация переключается легче",
        "process": "не тождественен Θ_D и Θ_U",
    },
    "UPDATE_MAGNITUDE": {
        "name": "Величина post-threshold update",
        "pos": "после превышения порога перестройка крупнее",
        "neg": "обновления более мелкие и инкрементальные",
        "process": "отделяет размер изменения от самого порога изменения",
    },
    "THETA_U": {
        "name": "Θ_U — порог обновления модели",
        "pos": "для изменения самой модели требуется больше накопленного противоречия",
        "neg": "модель пересматривается после меньшего противоречия",
        "process": "U выбирает мишень исправления; Θ_U определяет, достаточно ли ошибки для изменения",
    },
    "HYSTERESIS_W": {
        "name": "H_W — гистерезис допуска",
        "pos": "история сильнее влияет на входной гейт; пороги входа/выхода сильнее различаются",
        "neg": "допуск меньше зависит от предыдущего состояния",
        "process": "одинаковый вход может обрабатываться по-разному в зависимости от траектории",
    },
    "HYSTERESIS_NU": {
        "name": "H_ν — гистерезис ν",
        "pos": "оценка естественности/независимости сильнее зависит от предыдущего состояния",
        "neg": "ν быстрее перестраивается вслед за текущим входом",
        "process": "касается history-dependence в проверке структуры свидетельств",
    },
    "HYSTERESIS_D": {
        "name": "H_D — гистерезис HOLD/решения",
        "pos": "после выбора требуется более сильное противоположное воздействие для переключения",
        "neg": "граница переключения ближе в обоих направлениях",
        "process": "разделяет устойчивость выбранного состояния и первичный порог решения",
    },
    "HYSTERESIS_U": {
        "name": "H_U — гистерезис обновления модели",
        "pos": "после закрепления модели требуется существенно более сильное противоречие для обратной перестройки",
        "neg": "модель слабее зависит от истории предыдущих обновлений",
        "process": "делает model update path-dependent",
    },
    "K_ASYMMETRY": {
        "name": "K↓/K↑ — асимметрия обновления доверия",
        "pressure": "калибровочное давление на асимметрию потери и восстановления доверия",
        "process": "направление ratio пока не выводится developmental layer автоматически",
    },
    "SPAWN_THRESHOLD": {
        "name": "Spawn — чувствительность к новой скрытой модели",
        "pressure": "калибровочное давление на механизм выделения нового latent state",
        "process": "направление пока не заморожено; это не количество «субличностей»",
    },
    "REALITY_CALIBRATION": {
        "name": "Reality — калибровочная нагрузка",
        "pressure": "сила developmental calibration pressure на reality-monitoring",
        "process": "не интерпретируется как «хорошая/плохая связь с реальностью»",
    },
    "U_ROUTING_CAPACITY": {
        "name": "U — маршрутизация ошибки",
        "pressure": "сила калибровочного давления на механизм выбора мишени коррекции",
        "process": "не является прямой оценкой зрелости или эффективности U",
    },
    "GAMMA_CAPACITY": {
        "name": "Γ — офлайн-перекалибровка",
        "pressure": "сила калибровочного давления на поздно формирующиеся sleep/offline контуры",
        "process": "не является измерением качества сна или памяти человека",
    },
    "ANCHOR_STABILITY": {
        "name": "Стабильность якорей",
        "pos": "после офлайн-закрепления якорь устойчивее",
        "neg": "закреплённый якорь легче пересматривается",
        "process": "содержимое якорей developmental layer не задаёт",
    },
    "MEMORY_DUAL_TIMESCALE_CAPACITY": {
        "name": "Двойная шкала памяти Q_use / S_trace",
        "pressure": "калибровочное давление на разделение быстрого доверия к использованию и медленной силы следа",
        "process": "направление и абсолютная ёмкость памяти из этого слоя не выводятся",
    },
}

# These are model-internal descriptive bands, NOT population percentiles.
# They exist only to avoid pretending that a tiny numerical displacement is a strong trait.
DIRECTIONAL_EPS = 0.015
DIRECTIONAL_BANDS = [(0.04, "слабый"), (0.10, "умеренный"), (0.20, "выраженный"), (float("inf"), "сильный")]
PRESSURE_BANDS = [(0.10, "низкое"), (0.25, "умеренное"), (0.50, "заметное"), (0.75, "высокое"), (float("inf"), "очень высокое")]

REQUIRED = [
    "machine_profile_ensemble.csv",
    "machine_profile_by_run.csv",
    "parameter_definitions.csv",
    "machine_parameter_trajectory.csv",
    "brain_circuit_trajectory.csv",
    "packet_drivers.csv",
    "window_cascade_summary.csv",
]


def _finite(x: Any) -> Optional[float]:
    try:
        y = float(x)
        return y if math.isfinite(y) else None
    except Exception:
        return None


def _json_clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _json_clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_clean(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if pd.isna(obj) if not isinstance(obj, (str, bytes)) else False:
        return None
    return obj


def _read_csv(root: Path, name: str) -> pd.DataFrame:
    p = root / name
    if not p.exists():
        raise FileNotFoundError(f"Required input missing: {p}")
    return pd.read_csv(p)


def _read_json_if(root: Path, name: str) -> Any:
    p = root / name
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _band_abs(v: float) -> str:
    a = abs(v)
    for upper, label in DIRECTIONAL_BANDS:
        if a < upper:
            return label
    return "сильный"


def _pressure_band(v: float) -> str:
    for upper, label in PRESSURE_BANDS:
        if v < upper:
            return label
    return "очень высокое"


def _sign(v: float, eps: float = DIRECTIONAL_EPS) -> int:
    if v > eps:
        return 1
    if v < -eps:
        return -1
    return 0


def _fmt(v: Any, nd: int = 3) -> str:
    x = _finite(v)
    return "—" if x is None else f"{x:.{nd}f}"


def _consistency(run_values: np.ndarray, target_sign: int) -> float:
    arr = run_values[np.isfinite(run_values)]
    if len(arr) == 0:
        return float("nan")
    if target_sign == 0:
        return float(np.mean(np.abs(arr) <= DIRECTIONAL_EPS))
    return float(np.mean(np.sign(arr) == target_sign))


def _robustness_label(mode: str, median: float, lo: float, hi: float, consistency: float) -> Tuple[str, str]:
    if mode == "pressure_only":
        return "pressure_only", "Направление не определено спецификацией v0.2."
    s = _sign(median)
    if s == 0:
        return "near_zero", "Итоговое направление близко к нулю внутри модельной шкалы."
    crosses = lo <= 0 <= hi
    if not crosses and consistency >= 0.80:
        return "robust_direction", "Направление сохраняется в большинстве расчётов ширины пакета/сдвига зачатия."
    if consistency >= 0.70:
        return "direction_with_uncertainty", "Направление чаще сохраняется, но диапазон неопределённости пересекает ноль или заметно широк."
    return "unstable_direction", "Направление чувствительно к ширине пакета и/или неопределённости даты зачатия."


def _parameter_text(param: str, mode: str, median: float, pressure: float, robustness: str) -> Dict[str, str]:
    meta = PARAM_RU.get(param, {"name": param, "process": "параметр RS4/v4"})
    if mode == "pressure_only":
        statement = f"{_pressure_band(pressure).capitalize()} калибровочное давление: {meta.get('pressure', 'направление не заморожено')}."
        return {"name_ru": meta.get("name", param), "summary": statement, "process": meta.get("process", "")}

    s = _sign(median)
    if s == 0:
        statement = "Устойчивого направленного сдвига относительно нейтрального состояния модель не показывает."
    elif robustness == "unstable_direction":
        candidate = meta.get("pos" if s > 0 else "neg", "направленный сдвиг")
        statement = f"Есть кандидат на следующий сдвиг: {candidate}, но знак нестабилен между вариантами расчёта."
    else:
        candidate = meta.get("pos" if s > 0 else "neg", "направленный сдвиг")
        statement = f"{_band_abs(median).capitalize()} модельный сдвиг: {candidate}."
    return {"name_ru": meta.get("name", param), "summary": statement, "process": meta.get("process", "")}


def _window_contributions(traj: pd.DataFrame) -> pd.DataFrame:
    t = traj.copy()
    t["delta_state"] = pd.to_numeric(t["delta_state"], errors="coerce")
    t["packet_pressure"] = pd.to_numeric(t["packet_pressure"], errors="coerce")
    per_run = (
        t.groupby(["shift_days", "width", "parameter", "window"], dropna=False)
        .agg(
            net_delta=("delta_state", "sum"),
            abs_delta=("delta_state", lambda x: float(np.nansum(np.abs(x)))),
            mean_pressure=("packet_pressure", "mean"),
            n_parameter_updates=("delta_state", "size"),
        )
        .reset_index()
    )
    out = (
        per_run.groupby(["parameter", "window"], dropna=False)
        .agg(
            net_delta_median=("net_delta", "median"),
            net_delta_min=("net_delta", "min"),
            net_delta_max=("net_delta", "max"),
            abs_delta_median=("abs_delta", "median"),
            pressure_median=("mean_pressure", "median"),
            n_runs=("net_delta", "size"),
        )
        .reset_index()
    )
    out["window_order"] = out["window"].map({w: i for i, w in enumerate(WINDOW_ORDER)}).fillna(99)
    return out.sort_values(["parameter", "window_order"]).drop(columns=["window_order"])


def _top_packets(traj: pd.DataFrame, brain: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    # Explanations use central conception shift when available, preserving both 5d and 7d resolutions.
    if (traj["shift_days"] == 0).any():
        t = traj[traj["shift_days"] == 0].copy()
    else:
        best_shift = sorted(traj["shift_days"].dropna().unique(), key=lambda x: abs(float(x)))[0]
        t = traj[traj["shift_days"] == best_shift].copy()

    t["abs_delta"] = pd.to_numeric(t["delta_state"], errors="coerce").abs()
    t["packet_pressure"] = pd.to_numeric(t["packet_pressure"], errors="coerce")
    # Directional parameters are explained by the packets that changed state most.
    # pressure_only parameters have delta_state == 0 by design, so rank them by
    # calibration pressure rather than returning arbitrary zero-delta packets.
    t["rank_metric"] = np.where(t["mode"].astype(str).eq("pressure_only"), t["packet_pressure"].abs(), t["abs_delta"])
    top = (
        t.sort_values("rank_metric", ascending=False)
        .groupby("parameter", group_keys=False)
        .head(top_n)
        .copy()
    )

    keys = ["shift_days", "width", "step", "window", "packet_index", "dpc_start", "dpc_end"]
    b = brain.copy()
    b["exposure_pressure"] = pd.to_numeric(b["exposure_pressure"], errors="coerce")
    b = b.sort_values("exposure_pressure", ascending=False)
    bc = (
        b.groupby(keys, dropna=False)
        .apply(lambda g: " | ".join(
            f"{CIRCUIT_RU.get(str(r.circuit), str(r.circuit))}:{float(r.exposure_pressure):.3f}"
            for r in g.head(4).itertuples()
        ), include_groups=False)
        .rename("top_circuits")
        .reset_index()
    )
    top = top.merge(bc, on=keys, how="left")
    cols = [
        "parameter", "shift_days", "width", "step", "window", "packet_index",
        "dpc_start", "dpc_end", "date_start", "date_end", "regime", "transition",
        "delta_state", "packet_pressure", "rule_score", "signed_drive", "hysteresis_event",
        "effective_threshold", "top_circuits",
    ]
    return top[[c for c in cols if c in top.columns]].sort_values(["parameter", "width", "dpc_start"])


def _brain_map(brain: pd.DataFrame, wincontrib: pd.DataFrame) -> Dict[str, Any]:
    b = brain.copy()
    b["exposure_pressure"] = pd.to_numeric(b["exposure_pressure"], errors="coerce")
    per_run = (
        b.groupby(["shift_days", "width", "window", "circuit"], dropna=False)
        .agg(mean_exposure=("exposure_pressure", "mean"), peak_exposure=("exposure_pressure", "max"))
        .reset_index()
    )
    agg = (
        per_run.groupby(["window", "circuit"], dropna=False)
        .agg(
            mean_exposure_median=("mean_exposure", "median"),
            mean_exposure_min=("mean_exposure", "min"),
            mean_exposure_max=("mean_exposure", "max"),
            peak_exposure_median=("peak_exposure", "median"),
            peak_exposure_max=("peak_exposure", "max"),
        )
        .reset_index()
    )

    out: Dict[str, Any] = {}
    for w in WINDOW_ORDER:
        gw = agg[agg.window == w].sort_values("mean_exposure_median", ascending=False)
        wc = wincontrib[wincontrib.window == w].sort_values("abs_delta_median", ascending=False)
        top_params = []
        for r in wc.head(8).itertuples():
            pmeta = PARAM_RU.get(str(r.parameter), {})
            top_params.append({
                "parameter": str(r.parameter),
                "name_ru": pmeta.get("name", str(r.parameter)),
                "net_delta_median": _finite(r.net_delta_median),
                "abs_delta_median": _finite(r.abs_delta_median),
                "pressure_median": _finite(r.pressure_median),
            })
        circuits = []
        for r in gw.head(8).itertuples():
            circuits.append({
                "circuit": str(r.circuit),
                "label_ru": CIRCUIT_RU.get(str(r.circuit), str(r.circuit)),
                "mean_exposure_median": _finite(r.mean_exposure_median),
                "mean_exposure_range": [_finite(r.mean_exposure_min), _finite(r.mean_exposure_max)],
                "peak_exposure_median": _finite(r.peak_exposure_median),
                "peak_exposure_max": _finite(r.peak_exposure_max),
                "evidence_status": "hypothesized",
            })
        if len(b[b.window == w]):
            dpc_start = int(pd.to_numeric(b.loc[b.window == w, "dpc_start"], errors="coerce").min())
            dpc_end = int(pd.to_numeric(b.loc[b.window == w, "dpc_end"], errors="coerce").max())
        else:
            dpc_start = dpc_end = None
        out[w] = {
            "role_ru": WINDOW_ROLE_RU.get(w, w),
            "dpc_observed_range": [dpc_start, dpc_end],
            "circuits": circuits,
            "top_parameter_effects": top_params,
            "status": "developmental circuit mapping is a hypothesis; exposure_pressure is a model quantity, not measured fetal brain exposure",
        }
    return out


def _family_synthesis(param_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    byfam: Dict[str, List[Dict[str, Any]]] = {}
    for r in param_records:
        byfam.setdefault(r["family"], []).append(r)
    result = {}
    for fam, rows in byfam.items():
        directional = [r for r in rows if r["mode"] == "directional"]
        pressure = [r for r in rows if r["mode"] == "pressure_only"]
        robust = [r for r in directional if r["robustness"] == "robust_direction"]
        uncertain = [r for r in directional if r["robustness"] in ("direction_with_uncertainty", "unstable_direction")]
        result[fam] = {
            "label_ru": FAMILY_RU.get(fam, fam),
            "n_parameters": len(rows),
            "n_robust_directional": len(robust),
            "n_uncertain_directional": len(uncertain),
            "pressure_only": [r["parameter"] for r in pressure],
            "dominant_parameters": [
                r["parameter"] for r in sorted(rows, key=lambda z: abs(z["state_median"]) if z["mode"] == "directional" else z["pressure_median"], reverse=True)[:5]
            ],
        }
    return result


def _make_report(subject: str, params: List[Dict[str, Any]], brain_map: Dict[str, Any], run_meta: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# ARCHVIQ — экспериментальный профиль процессинга: {subject}")
    lines.append("")
    lines.append(f"**Interpreter:** v{VERSION}  ")
    lines.append("**Основа:** RS4/v4 developmental cascade  ")
    lines.append("**Статус:** исследовательская гипотеза, не медицинская диагностика и не установленная причинная связь ЭМП→мозг.  ")
    lines.append("")
    lines.append("## Как читать результат")
    lines.append("")
    lines.append("В отчёте жёстко разделены четыре уровня: **Measured** — физический SSN-вход рассчитан предыдущим слоем; **Modeled** — каскад, гистерезис и состояния RS4/v4; **Hypothesized** — соответствие developmental windows возможным нервным контурам и кибернетическим функциям; **Experimental** — будущие поведенческие, соматические и психофизиологические ветки. Последний уровень в этом интерпретаторе ещё не рассчитывается.")
    lines.append("")
    lines.append("Числа `state_median` — внутренние единицы модели, **не популяционные перцентили**. Для `pressure_only` параметров направление намеренно не интерпретируется.")
    lines.append("")
    robust = [r for r in params if r["mode"] == "directional" and r["robustness"] == "robust_direction"]
    robust = sorted(robust, key=lambda r: abs(r["state_median"]), reverse=True)
    unstable = [r for r in params if r["mode"] == "directional" and r["robustness"] == "unstable_direction"]
    pressure = [r for r in params if r["mode"] == "pressure_only"]
    pressure = sorted(pressure, key=lambda r: r["pressure_median"], reverse=True)
    lines.append("## Краткий синтез")
    lines.append("")
    if robust:
        lines.append("Наиболее устойчивые направленные сдвиги внутри текущей модели: " + "; ".join(f"**{r['name_ru']}** `{r['state_median']:+.3f}`" for r in robust[:6]) + ".")
    else:
        lines.append("Устойчивых направленных сдвигов, сохраняющих знак во всём ансамбле расчётов, не выявлено.")
    lines.append("")
    if unstable:
        lines.append("Параметры, направление которых особенно чувствительно к ширине пакета/дате зачатия: " + ", ".join(r["name_ru"] for r in unstable[:6]) + ". Их нельзя использовать как твёрдое описание человека.")
        lines.append("")
    if pressure:
        lines.append("Наибольшее `pressure_only` калибровочное давление: " + "; ".join(f"**{r['name_ru']}** `{r['pressure_median']:.3f}`" for r in pressure[:5]) + ". Это показывает, где модель видит сильную developmental-нагрузку, но **не задаёт направление функции**.")
        lines.append("")

    for fam in FAMILY_ORDER:
        grp = [r for r in params if r["family"] == fam]
        if not grp:
            continue
        lines.append(f"## {FAMILY_RU.get(fam, fam)}")
        lines.append("")
        # strongest first
        grp = sorted(grp, key=lambda r: (r["pressure_median"] if r["mode"] == "pressure_only" else abs(r["state_median"])), reverse=True)
        for r in grp:
            lines.append(f"### {r['name_ru']} (`{r['parameter']}`)")
            lines.append("")
            if r["mode"] == "directional":
                lines.append(f"- **Модельный сдвиг:** `{r['state_median']:+.3f}`; диапазон runs `{r['state_min']:+.3f} … {r['state_max']:+.3f}`; sign-consistency `{r['sign_consistency']:.0%}`.")
            else:
                lines.append(f"- **Calibration pressure:** `{r['pressure_median']:.3f}`; диапазон `{r['pressure_min']:.3f} … {r['pressure_max']:.3f}`. Направление не заморожено.")
            lines.append(f"- **Интерпретация модели:** {r['summary']}")
            if r.get("process"):
                lines.append(f"- **На спирали:** {r['process']}.")
            lines.append(f"- **Устойчивость вывода:** {r['robustness_note']}")
            if r["top_windows"]:
                if r["mode"] == "pressure_only":
                    tw = "; ".join(f"{x['window']} (pressure {x['pressure_median']:.3f})" for x in r["top_windows"][:3])
                    lines.append(f"- **Основные developmental-вклады:** {tw}.")
                else:
                    tw = "; ".join(f"{x['window']} (Δ {x['net_delta_median']:+.3f})" for x in r["top_windows"][:3])
                    lines.append(f"- **Основные developmental-вклады:** {tw}.")
            if r["top_packets"]:
                p = r["top_packets"][0]
                circ = p.get("top_circuits") or "—"
                if r["mode"] == "pressure_only":
                    lines.append(f"- **Сильный трассируемый пакет:** {p.get('window')} dpc {p.get('dpc_start')}–{p.get('dpc_end')}, `{p.get('regime')}`, переход `{p.get('transition')}`, pressure={float(p.get('packet_pressure') or 0):.3f}; candidate circuits: {circ}.")
                else:
                    lines.append(f"- **Сильный трассируемый пакет:** {p.get('window')} dpc {p.get('dpc_start')}–{p.get('dpc_end')}, `{p.get('regime')}`, переход `{p.get('transition')}`, Δstate={float(p.get('delta_state') or 0):+.3f}; candidate circuits: {circ}.")
            lines.append("")

    lines.append("## Карта шести окон")
    lines.append("")
    for w in WINDOW_ORDER:
        info = brain_map.get(w)
        if not info:
            continue
        circs = ", ".join(c["label_ru"] for c in info["circuits"][:4]) or "—"
        pars = ", ".join(p["name_ru"] for p in info["top_parameter_effects"][:4]) or "—"
        dr = info.get("dpc_observed_range", [None, None])
        lines.append(f"- **{w}**, dpc {dr[0]}–{dr[1]} — {info['role_ru']}. Наибольшее модельное давление: {circs}. Главные изменявшиеся параметры: {pars}.")
    lines.append("")

    lines.append("## Что этот отчёт НЕ утверждает")
    lines.append("")
    lines.append("- Он не доказывает, что естественное солнечно-/геомагнитное поле причинило конкретное изменение мозга.")
    lines.append("- Он не утверждает изменение анатомии, числа нейронов, миграции или морфологии; рабочая ветка касается функциональной калибровки.")
    lines.append("- Он не диагностирует характер, психиатрическое состояние или заболевание.")
    lines.append("- `pressure_only` параметры нельзя превращать в «высокий/низкий» профиль без отдельного замороженного направления.")
    lines.append("- Соматическая и психофизиологическая ветки должны подключаться downstream от processing-vector и маркироваться как experimental.")
    lines.append("")
    lines.append("## Техническая трассируемость")
    lines.append("")
    lines.append(f"Расчёт объединяет {run_meta.get('n_runs', '—')} runs (варианты ширины пакета × неопределённость даты зачатия). Все ключевые выводы имеют обратную ссылку на окно, пакет, regime/transition, Δstate и candidate circuits в `parameter_explanations.csv`, `dominant_packets.csv` и `brain_map.json`.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="ARCHVIQ personal interpreter v0.1")
    ap.add_argument("--cascade-dir", required=True, help="Directory produced by RS4/v4 cascade v0.2")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--subject", default="subject", help="Display label only; not used in calculations")
    ap.add_argument("--top-packets", type=int, default=5)
    args = ap.parse_args()

    root = Path(args.cascade_dir).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    for name in REQUIRED:
        if not (root / name).exists():
            raise FileNotFoundError(f"Required input missing: {root / name}")

    ens = _read_csv(root, "machine_profile_ensemble.csv")
    runs = _read_csv(root, "machine_profile_by_run.csv")
    defs = _read_csv(root, "parameter_definitions.csv")
    traj = _read_csv(root, "machine_parameter_trajectory.csv")
    brain = _read_csv(root, "brain_circuit_trajectory.csv")
    drivers = _read_csv(root, "packet_drivers.csv")
    window_summary = _read_csv(root, "window_cascade_summary.csv")

    wincontrib = _window_contributions(traj)
    dominant = _top_packets(traj, brain, top_n=max(1, args.top_packets))
    brainmap = _brain_map(brain, wincontrib)

    defmap = defs.set_index("parameter", drop=False).to_dict("index")
    records: List[Dict[str, Any]] = []
    uncertainty_rows: List[Dict[str, Any]] = []

    for er in ens.itertuples(index=False):
        p = str(er.parameter)
        d = defmap.get(p, {})
        mode = str(getattr(er, "mode", d.get("mode", "directional")))
        fam = str(getattr(er, "family", d.get("family", "OTHER")))
        median = float(getattr(er, "state_median", 0.0) or 0.0)
        lo = float(getattr(er, "state_min", 0.0) or 0.0)
        hi = float(getattr(er, "state_max", 0.0) or 0.0)
        iqr = float(getattr(er, "state_iqr", 0.0) or 0.0)
        pressure = float(getattr(er, "pressure_median", 0.0) or 0.0)
        plo = float(getattr(er, "pressure_min", 0.0) or 0.0)
        phi = float(getattr(er, "pressure_max", 0.0) or 0.0)

        rv = pd.to_numeric(runs.loc[runs.parameter == p, "final_calibration_state"], errors="coerce").to_numpy(float)
        s = _sign(median)
        consistency = _consistency(rv, s)
        robustness, robnote = _robustness_label(mode, median, lo, hi, consistency if math.isfinite(consistency) else 0.0)
        txt = _parameter_text(p, mode, median, pressure, robustness)

        wc = wincontrib[wincontrib.parameter == p].copy()
        if mode == "pressure_only":
            wc["importance"] = wc["pressure_median"].abs()
        else:
            wc["importance"] = wc["abs_delta_median"].abs()
        top_windows = []
        for wr in wc.sort_values("importance", ascending=False).head(6).itertuples():
            top_windows.append({
                "window": str(wr.window),
                "net_delta_median": float(wr.net_delta_median),
                "net_delta_range": [float(wr.net_delta_min), float(wr.net_delta_max)],
                "abs_delta_median": float(wr.abs_delta_median),
                "pressure_median": float(wr.pressure_median),
            })

        dp = dominant[dominant.parameter == p]
        top_packets = []
        for pr in dp.itertuples(index=False):
            rec = {k: getattr(pr, k) for k in dp.columns}
            top_packets.append(_json_clean(rec))

        rec = {
            "parameter": p,
            "name_ru": txt["name_ru"],
            "label_source": str(d.get("label", getattr(er, "label", p))),
            "family": fam,
            "family_ru": FAMILY_RU.get(fam, fam),
            "mode": mode,
            "runtime_baseline": _finite(getattr(er, "runtime_baseline", None)),
            "state_median": median,
            "state_min": lo,
            "state_max": hi,
            "state_iqr": iqr,
            "pressure_median": pressure,
            "pressure_min": plo,
            "pressure_max": phi,
            "sign_consistency": consistency,
            "crosses_zero": bool(lo <= 0 <= hi) if mode == "directional" else None,
            "robustness": robustness,
            "robustness_note": robnote,
            "summary": txt["summary"],
            "process": txt["process"],
            "top_windows": top_windows,
            "top_packets": top_packets,
            "evidence_status": {
                "numerical_state": "modeled",
                "circuit_mapping": "hypothesized",
                "human_manifestation": "experimental interpretation",
            },
        }
        records.append(rec)
        uncertainty_rows.append({
            "parameter": p,
            "mode": mode,
            "state_median": median,
            "state_min": lo,
            "state_max": hi,
            "state_iqr": iqr,
            "pressure_median": pressure,
            "pressure_min": plo,
            "pressure_max": phi,
            "sign_consistency": consistency,
            "crosses_zero": rec["crosses_zero"],
            "robustness": robustness,
            "note": robnote,
        })

    family = _family_synthesis(records)

    run_pairs = runs[["shift_days", "width"]].drop_duplicates()
    run_meta = {
        "interpreter_version": VERSION,
        "subject_label": args.subject,
        "cascade_dir": str(root),
        "n_runs": int(len(run_pairs)),
        "shift_days": sorted([int(x) for x in run_pairs.shift_days.dropna().unique()]),
        "packet_widths": sorted([int(x) for x in run_pairs.width.dropna().unique()]),
        "n_parameters": int(len(records)),
        "windows": [w for w in WINDOW_ORDER if w in set(traj.window.astype(str))],
        "status": "experimental developmental cyber-calibration interpreter",
        "warnings": [
            "Natural EMF causality is not established.",
            "Circuit mappings are functional/developmental hypotheses, not anatomical diagnoses.",
            "state_median values are internal model units, not population percentiles.",
            "pressure_only parameters have no directional interpretation in v0.1.",
        ],
    }

    profile = {
        "metadata": run_meta,
        "architecture": "RS4/v4 gated recurrent compression spiral",
        "evidence_layers": {
            "measured": "physical SSN-derived features calculated upstream",
            "modeled": "packet cascade, hysteresis, parameter state/pressure",
            "hypothesized": "developmental circuit mapping and processing interpretation",
            "experimental": "behavioral/somatic/psychophysiological downstream branches; not calculated here",
        },
        "parameters": records,
        "families": family,
        "brain_map": brainmap,
    }

    site_cards = []
    for r in records:
        site_cards.append({
            "id": r["parameter"],
            "title": r["name_ru"],
            "family": r["family_ru"],
            "mode": r["mode"],
            "model_value": r["state_median"] if r["mode"] == "directional" else None,
            "calibration_pressure": r["pressure_median"],
            "uncertainty": [r["state_min"], r["state_max"]] if r["mode"] == "directional" else [r["pressure_min"], r["pressure_max"]],
            "summary": r["summary"],
            "spiral_role": r["process"],
            "robustness": r["robustness"],
            "top_windows": r["top_windows"][:3],
            "top_packet": r["top_packets"][0] if r["top_packets"] else None,
            "badges": ["MODELED", "HYPOTHESIZED"],
            "disclaimer": "Research output; not diagnosis or established EMF causality.",
        })

    # Flat human-readable explanations table.
    flat_rows = []
    for r in records:
        flat_rows.append({
            "parameter": r["parameter"],
            "name_ru": r["name_ru"],
            "family": r["family"],
            "mode": r["mode"],
            "state_median": r["state_median"],
            "state_min": r["state_min"],
            "state_max": r["state_max"],
            "pressure_median": r["pressure_median"],
            "sign_consistency": r["sign_consistency"],
            "robustness": r["robustness"],
            "interpretation_ru": r["summary"],
            "spiral_role_ru": r["process"],
            "top_window_1": r["top_windows"][0]["window"] if r["top_windows"] else "",
            "top_window_1_delta": r["top_windows"][0]["net_delta_median"] if r["top_windows"] else np.nan,
            "top_window_2": r["top_windows"][1]["window"] if len(r["top_windows"]) > 1 else "",
            "top_window_2_delta": r["top_windows"][1]["net_delta_median"] if len(r["top_windows"]) > 1 else np.nan,
        })

    with (out / "profile.json").open("w", encoding="utf-8") as f:
        json.dump(_json_clean(profile), f, ensure_ascii=False, indent=2)
    with (out / "brain_map.json").open("w", encoding="utf-8") as f:
        json.dump(_json_clean(brainmap), f, ensure_ascii=False, indent=2)
    with (out / "site_cards.json").open("w", encoding="utf-8") as f:
        json.dump(_json_clean(site_cards), f, ensure_ascii=False, indent=2)
    with (out / "run_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(_json_clean(run_meta), f, ensure_ascii=False, indent=2)

    pd.DataFrame(flat_rows).to_csv(out / "parameter_explanations.csv", index=False)
    wincontrib.to_csv(out / "window_contributions.csv", index=False)
    pd.DataFrame(uncertainty_rows).to_csv(out / "uncertainty_report.csv", index=False)
    dominant.to_csv(out / "dominant_packets.csv", index=False)

    report = _make_report(args.subject, records, brainmap, run_meta)
    (out / "profile_report.md").write_text(report, encoding="utf-8")

    print("ARCHVIQ Personal Interpreter v0.1")
    print("INPUT :", root)
    print("OUTPUT:", out)
    print("runs=", run_meta["n_runs"], "parameters=", run_meta["n_parameters"])
    print("written: profile.json, profile_report.md, brain_map.json, site_cards.json,")
    print("         parameter_explanations.csv, window_contributions.csv,")
    print("         uncertainty_report.csv, dominant_packets.csv, run_metadata.json")


if __name__ == "__main__":
    main()
