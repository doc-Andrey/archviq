"""
fit_ddm_ez.py
--------------
Research-only EZ-diffusion analysis for CSV exports from
rdm_perception_test.html.

The script fits each participant, session and coherence condition separately.
It never silently merges repeat sessions. Timeouts are reported as omissions
and excluded from the EZ equations because they are right-censored responses,
not observed error-boundary crossings.

Outputs
-------
1. Per-condition CSV: accuracy, omissions, correct-RT moments, EZ parameters
   and bootstrap confidence intervals.
2. Optional per-session CSV: drift sensitivity to coherence, average boundary
   separation and average non-decision time.

The values are exploratory and must not be interpreted as diagnoses or as
validated measurements of Engine 43 axes.

Usage
-----
python3 fit_ddm_ez.py --csv "rdm_*.csv" --out ddm_fits.csv
    --out-summary ddm_sessions.csv --bootstrap 500
"""

from __future__ import annotations

import argparse
import glob
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


MIN_TRIALS_PER_CELL = 30
MIN_CORRECT_RTS = 8
RT_MIN_MS, RT_MAX_MS = 120, 4000
VAR_EPSILON = 1e-10


def ez_diffusion(accuracy: float, mean_rt_s: float, var_rt_s2: float, n: int) -> Dict[str, float]:
    """Wagenmakers, van der Maas & Grasman (2007), equations 1--6.

    RT moments must come from correct responses only. n is the number of
    observed left/right responses (timeouts excluded) and is used for the
    standard 0/1 accuracy edge correction.
    """
    values = (accuracy, mean_rt_s, var_rt_s2)
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("accuracy and RT moments must be finite")
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= accuracy <= 1:
        raise ValueError("accuracy must be between 0 and 1")
    if mean_rt_s <= 0:
        raise ValueError("mean RT must be positive")
    if var_rt_s2 <= VAR_EPSILON:
        raise ValueError("correct-RT variance is zero or too small")

    if accuracy <= 0 or accuracy >= 1:
        accuracy = min(max(accuracy, 1.0 / (2 * n)), 1 - 1.0 / (2 * n))
    if math.isclose(accuracy, 0.5, abs_tol=1e-12):
        raise ValueError("EZ-diffusion is undefined at exactly chance accuracy")

    s = 0.1
    logit = math.log(accuracy / (1 - accuracy))
    x = logit * (accuracy**2 * logit - accuracy * logit + accuracy - 0.5) / var_rt_s2
    if not math.isfinite(x) or x <= 0:
        raise ValueError("invalid EZ intermediate value")

    v = math.copysign(s * x**0.25, accuracy - 0.5)
    a = (s**2 * logit) / v
    y = (-v * a) / (s**2)
    exp_y = math.exp(max(min(y, 700), -700))
    mean_decision_time = (a / (2 * v)) * ((1 - exp_y) / (1 + exp_y))
    t0 = mean_rt_s - mean_decision_time

    if not all(math.isfinite(z) for z in (v, a, t0)):
        raise ValueError("non-finite EZ estimate")
    if a <= 0:
        raise ValueError("non-positive boundary estimate")
    if t0 < 0 or t0 >= mean_rt_s:
        raise ValueError("implausible non-decision time")
    return {"drift_v": v, "boundary_a": a, "nondecision_t0": t0}


def _as_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _first_nonempty(values: Iterable[object]) -> str:
    for value in values:
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return ""


def _coherence_from_group(group: pd.DataFrame, condition: str) -> float:
    if "COHERENCE" in group.columns:
        values = _as_numeric(group["COHERENCE"]).dropna()
        if not values.empty:
            return float(values.median())
    match = re.search(r"(\d+(?:\.\d+)?)$", str(condition))
    return float(match.group(1)) / 100.0 if match else float("nan")


def load_and_clean(csv_paths: List[str]) -> pd.DataFrame:
    frames = []
    for path in csv_paths:
        frame = pd.read_csv(path)
        frame["SOURCE_FILE"] = Path(path).name
        frames.append(frame)
    if not frames:
        raise SystemExit("No input CSVs matched.")
    df = pd.concat(frames, ignore_index=True)

    required = {
        "CLIENT_ID", "SESSION_ID", "TEST", "TRIAL_INDEX", "CONDITION",
        "CORRECT", "RT_MS", "PHASE",
    }
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Input CSV(s) missing required columns: {sorted(missing)}")

    df["CLIENT_ID"] = df["CLIENT_ID"].astype(str).str.strip()
    df["SESSION_ID"] = df["SESSION_ID"].astype(str).str.strip()
    df["TEST"] = df["TEST"].astype(str).str.upper().str.strip()
    df["PHASE"] = df["PHASE"].astype(str).str.lower().str.strip()
    df = df[(df["TEST"] == "RDM") & (df["PHASE"] == "main")].copy()

    df["TRIAL_INDEX"] = _as_numeric(df["TRIAL_INDEX"])
    df["CORRECT"] = _as_numeric(df["CORRECT"])
    df["RT_MS"] = _as_numeric(df["RT_MS"])

    duplicate_key = ["CLIENT_ID", "SESSION_ID", "TRIAL_INDEX"]
    duplicates = df.duplicated(duplicate_key, keep=False)
    if duplicates.any():
        examples = df.loc[duplicates, duplicate_key + ["SOURCE_FILE"]].head(8)
        raise SystemExit(
            "Duplicate trials detected; refusing to double-count sessions:\n"
            + examples.to_string(index=False)
        )

    if "TRIAL_VALID" in df.columns:
        df = df[_as_numeric(df["TRIAL_VALID"]) == 1].copy()

    if "TIMEOUT" in df.columns:
        df["TIMEOUT"] = _as_numeric(df["TIMEOUT"]).fillna(0).astype(int)
    else:
        # Backward-compatible inference: the original export had a 4000 ms deadline.
        df["TIMEOUT"] = (df["RT_MS"] >= 3990).astype(int)

    valid_core = df["CORRECT"].isin([0, 1]) & df["RT_MS"].between(RT_MIN_MS, RT_MAX_MS)
    df = df[valid_core].copy()
    if df.empty:
        raise SystemExit("No valid main-phase RDM trials after filtering.")
    return df


def _fit_group(group: pd.DataFrame) -> Dict[str, object]:
    condition = str(group["CONDITION"].iloc[0])
    response = group[group["TIMEOUT"] == 0].copy()
    correct = response[response["CORRECT"] == 1]
    n_presented = len(group)
    n_response = len(response)
    omission_rate = 1 - n_response / n_presented if n_presented else float("nan")
    accuracy = float(response["CORRECT"].mean()) if n_response else float("nan")

    base: Dict[str, object] = {
        "CLIENT_ID": str(group["CLIENT_ID"].iloc[0]),
        "SESSION_ID": str(group["SESSION_ID"].iloc[0]),
        "DOB": _first_nonempty(group["DOB"]) if "DOB" in group else "",
        "HANDEDNESS": _first_nonempty(group["HANDEDNESS"]) if "HANDEDNESS" in group else "",
        "CONDITION": condition,
        "coherence": _coherence_from_group(group, condition),
        "n_presented": n_presented,
        "n_responses": n_response,
        "n_correct": len(correct),
        "omission_rate": omission_rate,
        "accuracy_response": accuracy,
    }

    if n_response < MIN_TRIALS_PER_CELL:
        return {**base, "status": f"skipped_fewer_than_{MIN_TRIALS_PER_CELL}_responses"}
    if len(correct) < MIN_CORRECT_RTS:
        return {**base, "status": f"skipped_fewer_than_{MIN_CORRECT_RTS}_correct_rts"}

    correct_rt_s = correct["RT_MS"].to_numpy(float) / 1000.0
    mean_rt = float(np.mean(correct_rt_s))
    var_rt = float(np.var(correct_rt_s, ddof=1))
    try:
        fit = ez_diffusion(accuracy, mean_rt, var_rt, n_response)
    except ValueError as exc:
        return {
            **base,
            "mean_rt_correct_s": mean_rt,
            "var_rt_correct_s2": var_rt,
            "status": "failed_" + str(exc).lower().replace(" ", "_"),
        }

    warnings = []
    if omission_rate > 0.05:
        warnings.append("high_omission")
    if accuracy < 0.5:
        warnings.append("below_chance")
    status = "ok" if not warnings else "ok_warning_" + "_".join(warnings)
    return {
        **base,
        "mean_rt_correct_s": mean_rt,
        "var_rt_correct_s2": var_rt,
        **fit,
        "status": status,
    }


def _bootstrap_group(group: pd.DataFrame, n_boot: int, rng: np.random.Generator) -> Dict[str, float]:
    response = group[group["TIMEOUT"] == 0]
    if n_boot <= 0 or len(response) < MIN_TRIALS_PER_CELL:
        return {}
    estimates = []
    rows = response.reset_index(drop=True)
    for _ in range(n_boot):
        sample = rows.iloc[rng.integers(0, len(rows), size=len(rows))]
        correct = sample[sample["CORRECT"] == 1]
        if len(correct) < MIN_CORRECT_RTS:
            continue
        rt = correct["RT_MS"].to_numpy(float) / 1000.0
        try:
            fit = ez_diffusion(
                float(sample["CORRECT"].mean()),
                float(np.mean(rt)),
                float(np.var(rt, ddof=1)),
                len(sample),
            )
        except ValueError:
            continue
        estimates.append([fit["drift_v"], fit["boundary_a"], fit["nondecision_t0"]])
    if len(estimates) < max(50, n_boot // 5):
        return {"bootstrap_valid": len(estimates)}
    arr = np.asarray(estimates)
    out: Dict[str, float] = {"bootstrap_valid": len(estimates)}
    for i, name in enumerate(("drift_v", "boundary_a", "nondecision_t0")):
        out[f"{name}_ci_low"] = float(np.quantile(arr[:, i], 0.025))
        out[f"{name}_ci_high"] = float(np.quantile(arr[:, i], 0.975))
    return out


def fit_all(df: pd.DataFrame, bootstrap: int = 500, seed: int = 43) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    keys = ["CLIENT_ID", "SESSION_ID", "CONDITION"]
    for _, group in df.groupby(keys, sort=True, dropna=False):
        row = _fit_group(group)
        if str(row.get("status", "")).startswith("ok"):
            row.update(_bootstrap_group(group, bootstrap, rng))
        rows.append(row)
    return pd.DataFrame(rows)


def participant_summary(fits: pd.DataFrame) -> pd.DataFrame:
    ok = fits[fits["status"].astype(str).str.startswith("ok")].copy()
    columns = [
        "CLIENT_ID", "SESSION_ID", "DOB", "n_conditions_fit",
        "drift_coherence_slope", "drift_intercept",
        "mean_boundary_a", "mean_nondecision_t0", "status",
    ]
    if ok.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (client, session), group in ok.groupby(["CLIENT_ID", "SESSION_ID"], sort=True):
        finite = group[np.isfinite(group["coherence"]) & np.isfinite(group["drift_v"])]
        slope = intercept = float("nan")
        if len(finite) >= 3 and finite["coherence"].nunique() >= 3:
            weights = np.sqrt(finite["n_responses"].to_numpy(float))
            slope, intercept = np.polyfit(
                finite["coherence"].to_numpy(float),
                finite["drift_v"].to_numpy(float),
                deg=1,
                w=weights,
            )
        weights = group["n_responses"].to_numpy(float)
        rows.append({
            "CLIENT_ID": client,
            "SESSION_ID": session,
            "DOB": _first_nonempty(group["DOB"]) if "DOB" in group else "",
            "n_conditions_fit": len(group),
            "drift_coherence_slope": slope,
            "drift_intercept": intercept,
            "mean_boundary_a": float(np.average(group["boundary_a"], weights=weights)),
            "mean_nondecision_t0": float(np.average(group["nondecision_t0"], weights=weights)),
            "status": "research_only" if len(group) >= 3 else "insufficient_conditions",
        })
    return pd.DataFrame(rows, columns=columns)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", nargs="+", required=True, help="CSV files or glob patterns")
    parser.add_argument("--out", required=True, help="Per-condition output CSV")
    parser.add_argument("--out-summary", help="Optional per-session summary CSV")
    parser.add_argument("--bootstrap", type=int, default=500, help="Bootstrap replicates per cell (default: 500)")
    parser.add_argument("--seed", type=int, default=43)
    args = parser.parse_args()

    paths: List[str] = []
    for pattern in args.csv:
        matched = glob.glob(pattern)
        paths.extend(matched if matched else [pattern])
    paths = list(dict.fromkeys(paths))
    missing = [path for path in paths if not Path(path).is_file()]
    if missing:
        raise SystemExit(f"Input file(s) not found: {missing}")

    print(f"Loading {len(paths)} file(s).")
    df = load_and_clean(paths)
    print(f"{len(df)} valid main-phase RDM trials after filtering.")

    fits = fit_all(df, bootstrap=max(args.bootstrap, 0), seed=args.seed)
    fits.to_csv(args.out, index=False)
    print(f"Wrote per-condition fits to {args.out}")
    print(fits.to_string(index=False))

    if args.out_summary:
        summary = participant_summary(fits)
        summary.to_csv(args.out_summary, index=False)
        print(f"\nWrote per-session summary to {args.out_summary}")
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
