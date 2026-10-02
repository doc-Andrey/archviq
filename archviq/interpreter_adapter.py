from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .frozen import archviq_personal_interpreter_v0_1 as I


def interpret_from_frames(
    ensemble: pd.DataFrame,
    runs: pd.DataFrame,
    definitions: pd.DataFrame,
    trajectory: pd.DataFrame,
    brain: pd.DataFrame,
    subject_label: str = "subject",
    top_packets: int = 5,
) -> Dict[str, Any]:
    """Pure in-memory adapter around frozen interpreter v0.1.

    Frozen interpreter code is not modified.  This function reproduces its
    deterministic transformation from cascade tables to the site/profile objects
    without argparse, subprocesses, or request-specific file paths.
    """
    wincontrib = I._window_contributions(trajectory)
    dominant = I._top_packets(trajectory, brain, top_n=max(1, int(top_packets)))
    brainmap = I._brain_map(brain, wincontrib)
    defmap = definitions.set_index("parameter", drop=False).to_dict("index")

    records: List[Dict[str, Any]] = []
    uncertainty_rows: List[Dict[str, Any]] = []
    for er in ensemble.itertuples(index=False):
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
        s = I._sign(median)
        consistency = I._consistency(rv, s)
        robustness, robnote = I._robustness_label(mode, median, lo, hi, consistency if math.isfinite(consistency) else 0.0)
        txt = I._parameter_text(p, mode, median, pressure, robustness)

        wc = wincontrib[wincontrib.parameter == p].copy()
        wc["importance"] = wc["pressure_median"].abs() if mode == "pressure_only" else wc["abs_delta_median"].abs()
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
        top_packet_rows = []
        for pr in dp.itertuples(index=False):
            top_packet_rows.append(I._json_clean({k: getattr(pr, k) for k in dp.columns}))

        rec = {
            "parameter": p,
            "name_ru": txt["name_ru"],
            "label_source": str(d.get("label", getattr(er, "label", p))),
            "family": fam,
            "family_ru": I.FAMILY_RU.get(fam, fam),
            "mode": mode,
            "runtime_baseline": I._finite(getattr(er, "runtime_baseline", None)),
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
            "top_packets": top_packet_rows,
            "evidence_status": {
                "numerical_state": "MODELED",
                "circuit_mapping": "HYPOTHESIZED",
                "human_manifestation": "EXPERIMENTAL",
            },
        }
        records.append(rec)
        uncertainty_rows.append({
            "parameter": p, "mode": mode, "state_median": median,
            "state_min": lo, "state_max": hi, "state_iqr": iqr,
            "pressure_median": pressure, "pressure_min": plo, "pressure_max": phi,
            "sign_consistency": consistency, "crosses_zero": rec["crosses_zero"],
            "robustness": robustness, "note": robnote,
        })

    family = I._family_synthesis(records)
    run_pairs = runs[["shift_days", "width"]].drop_duplicates()
    run_meta = {
        "interpreter_version": I.VERSION,
        "subject_label": subject_label,
        "n_runs": int(len(run_pairs)),
        "shift_days": sorted([int(x) for x in run_pairs.shift_days.dropna().unique()]),
        "packet_widths": sorted([int(x) for x in run_pairs.width.dropna().unique()]),
        "n_parameters": int(len(records)),
        "windows": [w for w in I.WINDOW_ORDER if w in set(trajectory.window.astype(str))],
        "status": "experimental developmental cyber-calibration interpreter",
        "warnings": [
            "Natural EMF causality is not established.",
            "Circuit mappings are functional/developmental hypotheses, not anatomical diagnoses.",
            "state_median values are internal model units, not population percentiles.",
            "pressure_only parameters have no directional interpretation in v0.1.",
        ],
    }

    site_cards = [{
        "id": r["parameter"], "title": r["name_ru"], "family": r["family_ru"],
        "mode": r["mode"],
        "model_value": r["state_median"] if r["mode"] == "directional" else None,
        "calibration_pressure": r["pressure_median"],
        "uncertainty": ([r["state_min"], r["state_max"]] if r["mode"] == "directional" else [r["pressure_min"], r["pressure_max"]]),
        "summary": r["summary"], "spiral_role": r["process"], "robustness": r["robustness"],
        "top_windows": r["top_windows"][:3],
        "top_packet": r["top_packets"][0] if r["top_packets"] else None,
        "badges": ["MODELED", "HYPOTHESIZED"],
        "disclaimer": "Research output; not diagnosis or established EMF causality.",
    } for r in records]

    report = I._make_report(subject_label, records, brainmap, run_meta)
    return {
        "parameters": records,
        "families": family,
        "brain_map": brainmap,
        "site_cards": site_cards,
        "uncertainty_rows": uncertainty_rows,
        "window_contributions": wincontrib,
        "dominant_packets": dominant,
        "run_metadata": run_meta,
        "report_markdown": report,
    }
