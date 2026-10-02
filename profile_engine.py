from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from archviq.orchestrator import run_archviq, UnsupportedGestationError
from archviq.contracts import InputValidationError

ROOT = Path(__file__).resolve().parent
SSN_PATH = ROOT / "data" / "SN_d_tot_V2.0.txt"


@lru_cache(maxsize=256)
def _compute_cached(
    name: str,
    dob: str,
    sex: str,
    gestation_mode: str,
    ctb_days: int | None,
    conception: str | None,
    uncertainty_days: int | None,
) -> Dict[str, Any]:
    gestation: Dict[str, Any] = {"mode": gestation_mode}
    if gestation_mode == "ctb_days":
        gestation["conception_to_birth_days"] = int(ctb_days) if ctb_days is not None else 266
    elif gestation_mode == "conception":
        gestation["conception"] = conception
    if uncertainty_days is not None:
        gestation["uncertainty_days"] = int(uncertainty_days)

    req = {
        "dob": pd.Timestamp(dob).date().isoformat(),
        "sex": sex,
        "subject_label": name.strip() or "Client",
        "gestation": gestation,
    }
    return run_archviq(req, silso_path=SSN_PATH)


def compute_profile(
    name: str,
    dob: str,
    sex: str = "F",
    gestation_mode: str = "unknown",
    ctb_days: int | None = None,
    conception: str | None = None,
    uncertainty_days: int | None = None,
) -> Dict[str, Any]:
    """Run the bundled, no-network ARCHVIQ v4 pipeline."""
    if not SSN_PATH.is_file():
        raise FileNotFoundError(f"Bundled SILSO archive is missing: {SSN_PATH}")
    return _compute_cached(
        name or "Client",
        pd.Timestamp(dob).date().isoformat(),
        sex.strip().upper(),
        gestation_mode,
        ctb_days,
        conception,
        uncertainty_days,
    )


def export_flat(profile: Dict[str, Any]) -> Dict[str, Any]:
    subject = profile.get("meta", {}).get("subject", {})
    row: Dict[str, Any] = {
        "label": subject.get("label"),
        "dob": subject.get("dob"),
        "sex": subject.get("sex"),
        "central_conception": subject.get("central_conception"),
        "ctb_days": subject.get("central_conception_to_birth_days"),
        "engine_bundle_version": profile.get("meta", {}).get("engine_bundle_version"),
    }
    for p in profile.get("processing", {}).get("parameters", []):
        key = str(p.get("parameter", "")).lower()
        if not key:
            continue
        row[f"{key}_mode"] = p.get("mode")
        row[f"{key}_state"] = p.get("state_median")
        row[f"{key}_pressure"] = p.get("pressure_median")
        row[f"{key}_robustness"] = p.get("robustness")
    return row


__all__ = [
    "compute_profile", "export_flat", "UnsupportedGestationError", "InputValidationError", "SSN_PATH"
]
