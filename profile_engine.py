"""Archviq adapter for the frozen 43 NEW V3 / 254D engine.

The public UI keeps the original linked workflow:
DOB -> 43 NEW prior -> functional interpretation -> cognitive test -> questionnaire
and pair compatibility.  The 9 X states are primary; RS1-RS4 are compatibility
macrocoordinates only.

Important: the 0-100 values exposed to the UI are a deterministic display transform
of native 43 NEW values, not population percentiles or clinical norms.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import inspect
import os
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

X_KEYS = (
    "X_EXC", "X_SENS", "X_STAB", "X_INTEG", "X_FLEX",
    "X_LAB", "X_SEGR", "X_HUB", "X_MAT",
)
RS_KEYS = ("RS1_RHYTHM", "RS2_SYNC", "RS3_SEGR", "RS4_INTEGRAL")
RAW_KEYS = RS_KEYS + X_KEYS + (
    "hidden_tension_index", "creative_integrator_index", "control_compensation_index",
    "architecture_power_score", "pathology_load_score", "adaptive_control_score",
    "adaptive_stability_score", "decompensation_risk_score",
    "high_load_compensation_score", "tension_control_ratio",
)


def _clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


def _display(value: Any, scale: float = 1.0) -> float:
    """Symmetric deterministic display transform; 0 native -> 50 display."""
    try:
        x = float(value)
    except (TypeError, ValueError):
        x = 0.0
    scale = max(float(scale), 1e-9)
    return _clamp(50.0 + 50.0 * np.tanh(x / scale))


def _engine_candidates() -> list[Path]:
    root = Path(__file__).resolve().parent
    home = Path.home()
    candidates: list[Path] = []
    configured = os.getenv("PSYCHOTYP_ENGINE_PATH", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    for name in (
        "43_new_v3_engine.py",
        "254D_43_NEW_V3_SEMANTIC_DEDUP.py",
    ):
        candidates.extend((root / name, root.parent / name, home / "Downloads" / name))
    seen: set[Path] = set()
    out = []
    for p in candidates:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


def _load_module(path: Path):
    token = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:10]
    spec = importlib.util.spec_from_file_location(f"archviq_engine43_{token}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load engine module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_engine(module, dob: str, name: str) -> Dict[str, Any]:
    if not (hasattr(module, "load_ssn") and hasattr(module, "run_one")):
        raise AttributeError("Engine does not expose load_ssn() + run_one()")
    ssn = module.load_ssn()
    person = pd.Series({
        "name": name,
        "dob": dob,
        "dob_parsed": pd.Timestamp(dob),
        "context": "ARCHVIQ_CLIENT_43NEW_V3_NO_LAG",
    })

    sig = inspect.signature(module.run_one)
    # 254D has run_one(ssn, person). Older frozen 43 used (..., 0, 0).
    if len(sig.parameters) <= 2:
        output = module.run_one(ssn, person)
    else:
        output = module.run_one(ssn, person, 0, 0)

    raw = output[0] if isinstance(output, tuple) else output
    if isinstance(raw, pd.Series):
        raw = raw.to_dict()
    if not isinstance(raw, dict):
        raise TypeError("run_one() did not return a result dictionary")
    raw["pre_lag_days"] = 0
    raw["post_lag_days"] = 0
    raw["lag_mode"] = "NO_LAG_FIXED"
    raw.setdefault("engine_version", getattr(module, "ENGINE_VERSION", "43_NEW_V3"))
    return raw


def _find_and_run_engine(dob: str, name: str) -> tuple[Dict[str, Any] | None, str, str]:
    errors: list[str] = []
    for path in _engine_candidates():
        if not path.is_file():
            continue
        try:
            module = _load_module(path)
            raw = _run_engine(module, dob, name)
            version = str(raw.get("engine_version", "43 NEW V3"))
            return raw, f"{version} · NO_LAG · {path.name}", ""
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    return None, "ENGINE 43 NEW V3 NOT AVAILABLE", "; ".join(errors[-3:])


def _x_display(raw: Dict[str, Any]) -> Dict[str, float]:
    # Scale=1 is intentionally fixed and transparent. It is not a normative percentile.
    return {k: _display(raw.get(k, 0.0), 1.0) for k in X_KEYS}


def _rs_display(raw: Dict[str, Any]) -> Dict[str, float]:
    return {
        "rs1": _display(raw.get("RS1_RHYTHM", 0.0), 1.0),
        "rs2": _display(raw.get("RS2_SYNC", 0.0), 1.0),
        "rs3": _display(raw.get("RS3_SEGR", 0.0), 1.0),
        "rs4": _display(raw.get("RS4_INTEGRAL", 0.0), 1.0),
    }


def _architecture_label(x: Dict[str, float]) -> str:
    overload = np.mean([x["X_SENS"], x["X_LAB"], 100 - x["X_STAB"]])
    reserve = np.mean([x["X_STAB"], x["X_MAT"], x["X_FLEX"], 100 - x["X_LAB"]])
    if overload >= 70 and reserve < 42:
        return "COLLAPSE · OVERLOADED MODE"
    if x["X_SENS"] >= 67:
        return "ANTENNA"
    if np.mean([x["X_STAB"], x["X_SEGR"], x["X_MAT"]]) >= 62 and x["X_FLEX"] < 55:
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

    x = _x_display(cleaned)
    rs = _rs_display(cleaned)
    label = _architecture_label(x)
    tension = _clamp(np.mean([x["X_SENS"], x["X_LAB"], 100 - x["X_STAB"]]))
    adaptive = _clamp(np.mean([x["X_STAB"], x["X_FLEX"], x["X_MAT"], 100 - x["X_LAB"]]))

    taglines = {
        "FORTRESS": "Stable pattern maintenance and protected focus",
        "ANTENNA": "High input sensitivity and rapid signal registration",
        "FLUID": "Adaptive integration and flexible reconfiguration",
        "COLLAPSE · OVERLOADED MODE": "High load with reduced functional reserve",
    }
    profile = {
        "name": name,
        "type_name": label,
        "tagline": taglines[label],
        **rs,
        "x_axes": x,
        "tension": tension,
        "adaptive": adaptive,
        "raw": cleaned,
        "engine_source": source,
        "engine_error": error,
        "display_scale_note": "Deterministic tanh display transform; not a population percentile.",
        "insights": [
            "43 NEW V3 uses nine X states as the primary architecture; RS1–RS4 are summary macrocoordinates.",
            "Cognitive tests and questionnaires are merged as measured layers over the same functional interpretation.",
        ],
        "recommendations": [
            "Use the cognitive test to compare the developmental prior with current function.",
            "Use questionnaire results as a separate behavioral/state layer in the integrated profile.",
            "Repeat measurements under comparable sleep and workload conditions before interpreting large gaps.",
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
        raise RuntimeError(
            "43 NEW V3 could not be executed. " + (error or "Production engine not found.")
        )
    return _profile_from_raw(raw, name, source, error)


def get_compatibility(p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
    x1 = p1.get("x_axes") or _x_display(p1.get("raw", {}))
    x2 = p2.get("x_axes") or _x_display(p2.get("raw", {}))
    gaps = {k: abs(float(x1[k]) - float(x2[k])) for k in X_KEYS}
    mean_gap = float(np.mean(list(gaps.values())))
    score = _clamp(100.0 - 1.15 * mean_gap, 0, 100)
    largest = sorted(gaps.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return {
        "score": score,
        "summary": "43 NEW V3 coordination index across the nine primary architecture states",
        "axis_gaps": gaps,
        "largest_gaps": largest,
        "dynamics": [
            "Similarity lowers translation cost, while useful differences can be complementary if they are explicit.",
            "The largest X-state gaps identify where pace, sensitivity, switching or recovery expectations need negotiation.",
        ],
    }
