"""Production adapter between Archviq UI and the frozen engine 43.

The adapter never performs lag optimisation.  For the canonical
``43_universal_full_cascade_engine.py`` API it calls ``run_one(..., 0, 0)``.
Set ``PSYCHOTYP_ENGINE_PATH`` when the engine is stored outside this folder.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import os
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd


RAW_KEYS = (
    "RS1_RHYTHM", "RS2_SYNC", "RS3_SEGR", "RS4_INTEGRAL",
    "X_EXC", "X_SENS", "X_STAB", "X_INTEG", "X_FLEX", "X_LAB",
    "X_SEGR", "X_HUB", "X_MAT", "hidden_tension_index",
    "creative_integrator_index", "control_compensation_index",
    "architecture_power_score", "pathology_load_score",
    "adaptive_control_score", "adaptive_stability_score",
    "decompensation_risk_score", "high_load_compensation_score",
    "tension_control_ratio",
)


def _clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


def _engine_candidates() -> list[Path]:
    root = Path(__file__).resolve().parent
    home = Path.home()
    candidates: list[Path] = []
    configured = os.getenv("PSYCHOTYP_ENGINE_PATH", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    for name in ("43_CLIENT_RUN_v2.py", "43_universal_full_cascade_engine.py"):
        candidates.extend((
            root / name,
            root.parent / name,
            home / "Downloads" / name,
            home / "Downloads" / "psychotyp_site" / name,
            home / "Downloads" / "psychotyp_app" / name,
        ))
    seen: set[Path] = set()
    return [p.resolve() for p in candidates if not (p.resolve() in seen or seen.add(p.resolve()))]


def _load_module(path: Path):
    token = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:10]
    spec = importlib.util.spec_from_file_location(f"archviq_engine43_{token}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load engine module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_no_lag(module, dob: str, name: str) -> Dict[str, Any]:
    if not (hasattr(module, "load_ssn") and hasattr(module, "run_one")):
        raise AttributeError("Engine does not expose load_ssn() + run_one()")
    ssn = module.load_ssn()
    person = pd.Series({
        "name": name,
        "dob": dob,
        "dob_parsed": pd.Timestamp(dob),
        "context": "ARCHVIQ_CLIENT_NO_LAG",
    })
    output = module.run_one(ssn, person, 0, 0)
    raw = output[0] if isinstance(output, tuple) else output
    if isinstance(raw, pd.Series):
        raw = raw.to_dict()
    if not isinstance(raw, dict):
        raise TypeError("run_one() did not return a result dictionary")
    raw["pre_lag_days"] = 0
    raw["post_lag_days"] = 0
    if hasattr(module, "classify_profile"):
        raw["profile_class"] = module.classify_profile(raw)
    return raw


def _find_and_run_engine(dob: str, name: str) -> tuple[Dict[str, Any] | None, str, str]:
    errors: list[str] = []
    for path in _engine_candidates():
        if not path.is_file():
            continue
        try:
            raw = _canonical_no_lag(_load_module(path), dob, name)
            return raw, f"ENGINE 43 · NO_LAG · {path.name}", ""
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    return None, "DETERMINISTIC DEMO FALLBACK", "; ".join(errors[-2:])


def _demo_raw(dob: str, sex: str) -> Dict[str, float]:
    """Stable offline fallback; never presented as a production 43 result."""
    digest = hashlib.sha256(f"ARCHVIQ-DEMO|{dob}|{sex}".encode("utf-8")).digest()
    unit = np.frombuffer(digest, dtype=np.uint8).astype(float) / 255.0
    z = (unit - .5) * 2
    raw = {
        "RS1_RHYTHM": z[0] * 4,
        "RS2_SYNC": 24 + unit[1] * 18,
        "RS3_SEGR": 7 + unit[2] * 8,
        "RS4_INTEGRAL": 14 + unit[3] * 16,
        "X_EXC": 6 + unit[4] * 7,
        "X_SENS": 10 + unit[5] * 12,
        "X_STAB": -30 + unit[6] * 18,
        "X_INTEG": 14 + unit[7] * 16,
        "X_FLEX": 11 + unit[8] * 15,
        "X_LAB": 8 + unit[9] * 12,
        "X_SEGR": 12 + unit[10] * 15,
        "X_HUB": 18 + unit[11] * 17,
        "X_MAT": 19 + unit[12] * 18,
    }
    raw["hidden_tension_index"] = raw["X_SENS"] + raw["X_LAB"] - raw["X_STAB"]
    raw["creative_integrator_index"] = raw["X_INTEG"] + raw["X_HUB"] + raw["X_FLEX"] + raw["RS2_SYNC"]
    raw["control_compensation_index"] = raw["X_MAT"] + raw["RS3_SEGR"] - raw["X_LAB"]
    raw["architecture_power_score"] = .35 * raw["X_INTEG"] + .35 * raw["X_HUB"] + .30 * raw["X_MAT"]
    raw["pathology_load_score"] = .45 * raw["hidden_tension_index"] + .55 * raw["X_LAB"]
    raw["adaptive_control_score"] = .55 * raw["control_compensation_index"] + .45 * raw["X_MAT"]
    raw["adaptive_stability_score"] = raw["adaptive_control_score"] + .25 * raw["architecture_power_score"] - .45 * raw["pathology_load_score"]
    raw["decompensation_risk_score"] = raw["pathology_load_score"] + .20 * raw["architecture_power_score"] - .45 * raw["adaptive_control_score"]
    raw["high_load_compensation_score"] = raw["architecture_power_score"] + raw["adaptive_control_score"] - .35 * raw["pathology_load_score"]
    raw["tension_control_ratio"] = raw["pathology_load_score"] / max(raw["adaptive_control_score"], 1e-9)
    raw["pre_lag_days"] = 0
    raw["post_lag_days"] = 0
    return raw


def _architecture_label(raw: Dict[str, Any]) -> str:
    pathology = float(raw.get("pathology_load_score", 0))
    control = float(raw.get("adaptive_control_score", 0))
    if pathology > control * 1.35:
        return "COLLAPSE · OVERLOADED MODE"
    if float(raw.get("X_SENS", 0)) >= 16:
        return "ANTENNA"
    rs3 = float(raw.get("RS3_SEGR", 0)) * 5 + 30
    if rs3 >= 67:
        return "FORTRESS"
    return "FLUID"


def _profile_from_raw(raw: Dict[str, Any], name: str, source: str, error: str) -> Dict[str, Any]:
    cleaned = dict(raw)
    for key in RAW_KEYS:
        if key in cleaned:
            try:
                cleaned[key] = float(cleaned[key])
            except (TypeError, ValueError):
                pass
    label = _architecture_label(cleaned)
    tension = _clamp(cleaned.get("pathology_load_score"))
    adaptive = _clamp(float(cleaned.get("high_load_compensation_score", 0)) * .8)
    profile = {
        "name": name,
        "type_name": label,
        "tagline": {
            "FORTRESS": "Stable pattern maintenance and protected focus",
            "ANTENNA": "High input gain and environmental sensitivity",
            "FLUID": "Adaptive integration and flexible reconfiguration",
            "COLLAPSE · OVERLOADED MODE": "High load with reduced control reserve",
        }[label],
        "rs1": _clamp(float(cleaned.get("RS1_RHYTHM", 0)) * 5 + 50),
        "rs2": _clamp(cleaned.get("RS2_SYNC")),
        "rs3": _clamp(float(cleaned.get("RS3_SEGR", 0)) * 5 + 30),
        "rs4": _clamp(cleaned.get("RS4_INTEGRAL")),
        "tension": tension,
        "adaptive": adaptive,
        "raw": cleaned,
        "engine_source": source,
        "engine_error": error,
        "insights": [
            "RS1–RS4 summarize rhythm, synchrony, functional segregation and integration.",
            "The interpretation layer compares this prior with measured cognition and behavior.",
        ],
        "recommendations": [
            "Use the cognitive test to measure the architecture–function GAP.",
            "Keep wake time stable for 14 days before evaluating a sleep intervention.",
            "Treat Kp-linked observations as an N-of-1 hypothesis, not a causal conclusion.",
        ],
    }
    return profile


def compute_profile(dob: Any, sex: str, name: str, lang: str = "EN") -> Dict[str, Any]:
    if isinstance(dob, (_dt.date, _dt.datetime, pd.Timestamp)):
        dob_text = pd.Timestamp(dob).date().isoformat()
    else:
        dob_text = str(dob)[:10]
    raw, source, error = _find_and_run_engine(dob_text, name)
    if raw is None:
        raw = _demo_raw(dob_text, sex)
    return _profile_from_raw(raw, name, source, error)


def get_compatibility(p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
    axes = ("rs1", "rs2", "rs3", "rs4")
    distance = float(np.mean([abs(float(p1.get(k, 50)) - float(p2.get(k, 50))) for k in axes]))
    score = _clamp(100 - 1.45 * distance)
    return {
        "score": score,
        "summary": "Architectural distance with explicit coordination protocol",
        "dynamics": [
            "Similarity reduces translation cost but does not guarantee relationship quality.",
            "The largest RS gap identifies where thresholds, pace or recovery expectations need explicit negotiation.",
        ],
    }
