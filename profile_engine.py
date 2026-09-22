from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import pandas as pd

import archviq_engine43 as engine43

ROOT = Path(__file__).resolve().parent
SSN_PATH = ROOT / "data" / "SN_d_tot_V2.0.txt"
SCALER_PATH = ROOT / "data" / "reference_scalers_v1.json"

PUBLIC_SCORES = {
    "resource": "PRED_RESOURCE",
    "switching": "PRED_SWITCHING",
    "lock": "PRED_LOCK",
    "novelty": "PRED_NOVELTY",
    "control": "PRED_CONTROL",
    "processing_cost": "PRED_PROCESSING_COST",
    "maturation": "PRED_MATURATION",
}

X9_KEYS = [
    "X_EXC", "X_SENS", "X_STAB", "X_INTEG", "X_FLEX",
    "X_LAB", "X_SEGR", "X_HUB", "X_MAT",
]


@lru_cache(maxsize=1)
def _resources():
    if not SSN_PATH.exists():
        raise FileNotFoundError(f"Missing bundled SILSO archive: {SSN_PATH}")
    if not SCALER_PATH.exists():
        raise FileNotFoundError(f"Missing reference scalers: {SCALER_PATH}")
    return engine43.load_ssn(SSN_PATH), engine43.load_scalers(SCALER_PATH)


def _score(raw: Dict[str, Any], key: str) -> float:
    try:
        return round(float(raw[key]), 2)
    except Exception:
        return 50.0


def _signature(scores: Dict[str, float]) -> str:
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    first, second = ranked[0], ranked[1]
    if first[1] - second[1] < 5:
        return "balanced"
    return first[0]


def compute_profile(name: str, dob: str) -> Dict[str, Any]:
    """Compute one ARCHVIQ profile from date of birth."""
    # Validate before touching engine resources.
    parsed = pd.Timestamp(dob)
    if parsed.year < 1819:
        raise ValueError("ARCHVIQ currently requires dates of birth from 1819 onward because the bundled daily SILSO series starts in the 19th century.")

    ssn, scalers = _resources()
    raw = engine43.run_person(ssn, scalers, name or "Client", parsed.date().isoformat())

    scores = {k: _score(raw, v) for k, v in PUBLIC_SCORES.items()}
    uncertainty = {
        k: round(float(raw.get(v + "_SENS_RANGE", 0.0)), 2)
        for k, v in {
            "resource": "PRED_RESOURCE",
            "switching": "PRED_SWITCHING",
            "lock": "PRED_LOCK",
            "novelty": "PRED_NOVELTY",
            "control": "PRED_CONTROL",
            "processing_cost": "PRED_PROCESSING_COST",
            "maturation": "PRED_MATURATION",
        }.items()
    }
    x9 = {k: _score(raw, k) for k in X9_KEYS}

    central_conception = parsed - pd.Timedelta(days=engine43.CENTRAL_GESTATION_DAYS)

    return {
        "name": name.strip() if name else "Client",
        "dob": parsed.date().isoformat(),
        "engine_version": engine43.ENGINE_VERSION,
        "central_conception": central_conception.date().isoformat(),
        "conception_ensemble_days": list(engine43.SENSITIVITY_GESTATION_DAYS),
        "scores": scores,
        "uncertainty": uncertainty,
        "x9": x9,
        "signature": _signature(scores),
        "raw": raw,
    }


def export_flat(profile: Dict[str, Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "name": profile.get("name"),
        "dob": profile.get("dob"),
        "engine_version": profile.get("engine_version"),
        "central_conception": profile.get("central_conception"),
        "signature": profile.get("signature"),
    }
    for k, v in profile.get("scores", {}).items():
        row[f"score_{k}"] = v
    for k, v in profile.get("uncertainty", {}).items():
        row[f"timing_range_{k}"] = v
    row.update(profile.get("x9", {}))
    return row
