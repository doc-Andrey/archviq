from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats

try:
    from .common import save_json
except ImportError:
    from common import save_json


DEFAULT_THRESHOLDS = {
    "min_n": 100,
    "min_n_per_item": 5,
    "max_missing_rate": 0.10,
    "max_floor_or_ceiling": 0.25,
    "min_alpha": 0.70,
    "min_omega": 0.70,
    "min_median_item_total": 0.30,
    "min_retest_pairs": 50,
    "min_retest_icc": 0.60,
}


def cronbach_alpha(frame: pd.DataFrame) -> float:
    clean = frame.apply(pd.to_numeric, errors="coerce").dropna()
    if clean.shape[0] < 3 or clean.shape[1] < 2:
        return float("nan")
    item_variances = clean.var(axis=0, ddof=1).sum()
    total_variance = clean.sum(axis=1).var(ddof=1)
    if total_variance <= 0:
        return float("nan")
    k = clean.shape[1]
    return float(k / (k - 1) * (1 - item_variances / total_variance))


def omega_one_factor(frame: pd.DataFrame) -> float:
    clean = frame.apply(pd.to_numeric, errors="coerce").dropna()
    if clean.shape[0] < 5 or clean.shape[1] < 2:
        return float("nan")
    corr = clean.corr().to_numpy(dtype=float)
    if not np.isfinite(corr).all():
        return float("nan")
    vals, vecs = np.linalg.eigh(corr)
    idx = int(np.argmax(vals))
    loadings = vecs[:, idx] * math.sqrt(max(vals[idx], 0.0))
    if loadings.sum() < 0:
        loadings *= -1
    uniqueness = np.clip(1.0 - loadings**2, 0.0, 1.0)
    denominator = float(loadings.sum() ** 2 + uniqueness.sum())
    return float(loadings.sum() ** 2 / denominator) if denominator > 0 else float("nan")


def corrected_item_total(frame: pd.DataFrame) -> Dict[str, float]:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    out: Dict[str, float] = {}
    for col in numeric.columns:
        others = numeric.drop(columns=[col]).sum(axis=1, min_count=1)
        pair = pd.concat([numeric[col], others], axis=1).dropna()
        out[col] = float(pair.iloc[:, 0].corr(pair.iloc[:, 1])) if len(pair) >= 5 else float("nan")
    return out


def spearman_brown_split_half(frame: pd.DataFrame) -> float:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    odd = numeric.iloc[:, ::2].mean(axis=1)
    even = numeric.iloc[:, 1::2].mean(axis=1)
    pair = pd.concat([odd, even], axis=1).dropna()
    if len(pair) < 5 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return float("nan")
    r = float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))
    return 2 * r / (1 + r) if r > -1 else float("nan")


def parallel_first_eigen_ratio(frame: pd.DataFrame, repetitions: int = 200, seed: int = 43) -> Dict[str, float]:
    clean = frame.apply(pd.to_numeric, errors="coerce").dropna()
    if clean.shape[0] < 20 or clean.shape[1] < 3:
        return {"observed_first_eigen": float("nan"), "null95_first_eigen": float("nan"), "ratio": float("nan")}
    observed = float(np.linalg.eigvalsh(clean.corr().to_numpy())[-1])
    rng = np.random.default_rng(seed)
    null_first: List[float] = []
    values = clean.to_numpy(copy=True)
    for _ in range(repetitions):
        shuffled = np.column_stack([rng.permutation(values[:, j]) for j in range(values.shape[1])])
        null_first.append(float(np.linalg.eigvalsh(np.corrcoef(shuffled, rowvar=False))[-1]))
    q95 = float(np.quantile(null_first, 0.95))
    return {"observed_first_eigen": observed, "null95_first_eigen": q95, "ratio": observed / q95 if q95 else float("nan")}


def validate_scale(
    df: pd.DataFrame,
    item_columns: Sequence[str],
    thresholds: Mapping[str, float],
    criterion_columns: Sequence[str] = (),
) -> Dict[str, Any]:
    missing = [c for c in item_columns if c not in df.columns]
    if missing:
        return {"status": "FAILED", "reason": "missing_columns", "missing_columns": missing}
    items = df[list(item_columns)].apply(pd.to_numeric, errors="coerce")
    n = int(len(items))
    miss_rate = float(items.isna().mean().mean())
    floor = float((items == 1).mean().mean())
    ceiling = float((items == 5).mean().mean())
    alpha = cronbach_alpha(items)
    omega = omega_one_factor(items)
    item_total = corrected_item_total(items)
    median_item_total = float(np.nanmedian(list(item_total.values()))) if item_total else float("nan")
    split_half = spearman_brown_split_half(items)
    parallel = parallel_first_eigen_ratio(items)
    scale_score = items.mean(axis=1)
    criterion_correlations: Dict[str, Dict[str, float]] = {}
    for criterion in criterion_columns:
        if criterion not in df.columns:
            criterion_correlations[criterion] = {"rho": float("nan"), "p": float("nan"), "n": 0}
            continue
        pair = pd.concat([scale_score, pd.to_numeric(df[criterion], errors="coerce")], axis=1).dropna()
        if len(pair) >= 20 and pair.iloc[:, 0].nunique() > 1 and pair.iloc[:, 1].nunique() > 1:
            result = stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
            criterion_correlations[criterion] = {"rho": float(result.statistic), "p": float(result.pvalue), "n": int(len(pair))}
        else:
            criterion_correlations[criterion] = {"rho": float("nan"), "p": float("nan"), "n": int(len(pair))}
    min_n = max(int(thresholds["min_n"]), int(thresholds["min_n_per_item"] * len(item_columns)))
    checks = {
        "sample_size": n >= min_n,
        "missingness": miss_rate <= thresholds["max_missing_rate"],
        "floor_effect": floor <= thresholds["max_floor_or_ceiling"],
        "ceiling_effect": ceiling <= thresholds["max_floor_or_ceiling"],
        "alpha": math.isfinite(alpha) and alpha >= thresholds["min_alpha"],
        "omega": math.isfinite(omega) and omega >= thresholds["min_omega"],
        "item_total": math.isfinite(median_item_total) and median_item_total >= thresholds["min_median_item_total"],
        "factor_signal": math.isfinite(parallel["ratio"]) and parallel["ratio"] > 1.0,
        "external_criterion": bool(criterion_columns) and any(
            math.isfinite(x["rho"]) and abs(x["rho"]) >= 0.30 and x["p"] < 0.05
            for x in criterion_correlations.values()
        ),
    }
    return {
        "status": "PASSED" if all(checks.values()) else "NEEDS_WORK",
        "n": n,
        "n_required": min_n,
        "items": len(item_columns),
        "missing_rate": miss_rate,
        "floor_rate": floor,
        "ceiling_rate": ceiling,
        "cronbach_alpha": alpha,
        "omega_one_factor": omega,
        "split_half_spearman_brown": split_half,
        "median_corrected_item_total": median_item_total,
        "item_total": item_total,
        "parallel_analysis": parallel,
        "criterion_correlations": criterion_correlations,
        "checks": checks,
    }


def icc_3_1(wide: pd.DataFrame) -> float:
    x = wide.dropna().to_numpy(dtype=float)
    if x.shape[0] < 3 or x.shape[1] != 2:
        return float("nan")
    n, k = x.shape
    subject_means = x.mean(axis=1)
    grand = x.mean()
    ss_subject = k * np.square(subject_means - grand).sum()
    ss_error = np.square(x - subject_means[:, None] - x.mean(axis=0)[None, :] + grand).sum()
    ms_subject = ss_subject / (n - 1)
    ms_error = ss_error / ((n - 1) * (k - 1))
    denom = ms_subject + (k - 1) * ms_error
    return float((ms_subject - ms_error) / denom) if denom else float("nan")


def validate_cognitive_summary(df: pd.DataFrame, thresholds: Mapping[str, float]) -> Dict[str, Any]:
    required = [
        "CLIENT_ID", "SRT_median_rt", "CHOICE_accuracy", "CHOICE_median_correct_rt",
        "NBACK_hit_rate", "NBACK_false_alarm_rate", "SIMON_interference_cost",
        "SIMON_accuracy", "COMPLEX_accuracy", "COMPLEX_median_correct_rt",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"status": "FAILED", "reason": "missing_columns", "missing_columns": missing}
    work = df.copy()
    numeric_cols = required[1:]
    for col in numeric_cols:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    qc = {
        "srt_plausible": work["SRT_median_rt"].between(120, 1500),
        "choice_accuracy": work["CHOICE_accuracy"].between(0, 1),
        "nback_rates": work["NBACK_hit_rate"].between(0, 1) & work["NBACK_false_alarm_rate"].between(0, 1),
        "simon_accuracy": work["SIMON_accuracy"].between(0, 1),
        "complex_accuracy": work["COMPLEX_accuracy"].between(0, 1),
    }
    valid_row = pd.DataFrame(qc).all(axis=1)
    valid = work.loc[valid_row].copy()
    expected_effects = {
        "simon_cost_positive": float((valid["SIMON_interference_cost"] > 0).mean()) if len(valid) else float("nan"),
        "complex_slower_than_choice": float((valid["COMPLEX_median_correct_rt"] > valid["CHOICE_median_correct_rt"]).mean()) if len(valid) else float("nan"),
        "nback_discrimination_positive": float(((valid["NBACK_hit_rate"] - valid["NBACK_false_alarm_rate"]) > 0).mean()) if len(valid) else float("nan"),
    }
    retest: Dict[str, Any] = {"pairs": 0, "icc": {}}
    if "SESSION_ID" in valid.columns:
        repeated = valid.groupby("CLIENT_ID").filter(lambda g: len(g) >= 2)
        clients = list(repeated["CLIENT_ID"].dropna().unique())
        retest["pairs"] = len(clients)
        for metric in ["SRT_median_rt", "NBACK_hit_rate", "SIMON_interference_cost", "COMPLEX_accuracy"]:
            rows = []
            for _, group in repeated.groupby("CLIENT_ID"):
                group = group.sort_values("SESSION_ID").head(2)
                if len(group) == 2:
                    rows.append(group[metric].tolist())
            retest["icc"][metric] = icc_3_1(pd.DataFrame(rows, columns=["t1", "t2"])) if rows else float("nan")
    effect_pass = all(math.isfinite(v) and v >= 0.60 for v in expected_effects.values())
    iccs = list(retest["icc"].values())
    retest_pass = (
        retest["pairs"] >= thresholds["min_retest_pairs"]
        and len(iccs) >= 3
        and sum(math.isfinite(v) and v >= thresholds["min_retest_icc"] for v in iccs) >= 3
    )
    checks = {
        "sample_size": len(valid) >= thresholds["min_n"],
        "qc_retention": len(valid) / max(len(work), 1) >= 0.85,
        "expected_effects": effect_pass,
        "test_retest": retest_pass,
    }
    return {
        "status": "PASSED" if all(checks.values()) else "NEEDS_WORK",
        "n_sessions": int(len(work)),
        "n_valid_sessions": int(len(valid)),
        "expected_effects": expected_effects,
        "retest": retest,
        "checks": checks,
        "note": "Aggregate exports can test plausibility and retest reliability; trial-level exports are required for split-half reliability and RT-distribution QC.",
    }


def validate_cognitive_trials(df: pd.DataFrame, thresholds: Mapping[str, float]) -> Dict[str, Any]:
    required = ["CLIENT_ID", "SESSION_ID", "TEST", "TRIAL_INDEX", "CORRECT", "RT_MS"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"status": "FAILED", "reason": "missing_columns", "missing_columns": missing}
    work = df.copy()
    work["CORRECT"] = pd.to_numeric(work["CORRECT"], errors="coerce")
    work["RT_MS"] = pd.to_numeric(work["RT_MS"], errors="coerce")
    work["TRIAL_INDEX"] = pd.to_numeric(work["TRIAL_INDEX"], errors="coerce")
    valid = work[
        work["CORRECT"].isin([0, 1])
        & work["RT_MS"].between(120, 10000)
        & work["TRIAL_INDEX"].notna()
    ].copy()
    valid["HALF"] = np.where(valid["TRIAL_INDEX"].astype(int) % 2 == 0, "even", "odd")
    session_keys = ["CLIENT_ID", "SESSION_ID", "TEST"]
    half = valid.groupby(session_keys + ["HALF"]).agg(
        accuracy=("CORRECT", "mean"),
        median_rt=("RT_MS", "median"),
        trials=("TRIAL_INDEX", "count"),
    ).reset_index()
    reliability: Dict[str, Dict[str, float]] = {}
    for test_name, group in half.groupby("TEST"):
        test_result: Dict[str, float] = {}
        for metric in ["accuracy", "median_rt"]:
            wide = group.pivot_table(index=["CLIENT_ID", "SESSION_ID"], columns="HALF", values=metric).dropna()
            if len(wide) >= 20 and {"odd", "even"}.issubset(wide.columns):
                r = stats.spearmanr(wide["odd"], wide["even"]).statistic
                test_result[f"{metric}_spearman"] = float(r)
                test_result[f"{metric}_spearman_brown"] = float(2 * r / (1 + r)) if r > -1 else float("nan")
                test_result["paired_sessions"] = int(len(wide))
            else:
                test_result[f"{metric}_spearman"] = float("nan")
                test_result[f"{metric}_spearman_brown"] = float("nan")
        reliability[str(test_name)] = test_result

    expected_effects: Dict[str, Any] = {}
    if "CONDITION" in valid.columns:
        simon = valid[valid["TEST"].astype(str).str.upper().eq("SIMON") & valid["CORRECT"].eq(1)].copy()
        if len(simon):
            med = simon.groupby(["CLIENT_ID", "SESSION_ID", "CONDITION"])["RT_MS"].median().unstack()
            compatible = next((c for c in med.columns if str(c).lower() in {"compatible", "congruent"}), None)
            incompatible = next((c for c in med.columns if str(c).lower() in {"incompatible", "incongruent"}), None)
            if compatible is not None and incompatible is not None:
                delta = med[incompatible] - med[compatible]
                expected_effects["simon_incompatible_slower_fraction"] = float((delta > 0).mean())
                expected_effects["simon_median_cost_ms"] = float(delta.median())

    reliability_values = [
        metrics.get("median_rt_spearman_brown")
        for metrics in reliability.values()
        if math.isfinite(metrics.get("median_rt_spearman_brown", float("nan")))
    ]
    checks = {
        "participants": valid["CLIENT_ID"].nunique() >= thresholds["min_n"],
        "trial_retention": len(valid) / max(len(work), 1) >= 0.85,
        "split_half": len(reliability_values) >= 3 and sum(v >= 0.60 for v in reliability_values) >= 3,
    }
    if "simon_incompatible_slower_fraction" in expected_effects:
        checks["simon_effect"] = expected_effects["simon_incompatible_slower_fraction"] >= 0.60
    return {
        "status": "PASSED" if all(checks.values()) else "NEEDS_WORK",
        "n_trials": int(len(work)),
        "n_valid_trials": int(len(valid)),
        "n_participants": int(valid["CLIENT_ID"].nunique()),
        "n_sessions": int(valid[["CLIENT_ID", "SESSION_ID"]].drop_duplicates().shape[0]),
        "split_half": reliability,
        "expected_effects": expected_effects,
        "checks": checks,
    }


def build_registry(
    questionnaire_csv: str | None,
    scale_map_path: str | None,
    cognitive_csv: str | None,
    cognitive_trials_csv: str | None = None,
) -> Dict[str, Any]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    instruments: Dict[str, Any] = {}
    if questionnaire_csv and scale_map_path:
        df = pd.read_csv(questionnaire_csv)
        scale_map = json.loads(Path(scale_map_path).read_text(encoding="utf-8"))
        for instrument_id, spec in scale_map.get("instruments", {}).items():
            scale_results = {}
            for scale_id, scale_spec in spec.get("scales", {}).items():
                if isinstance(scale_spec, list):
                    items = scale_spec
                else:
                    items = scale_spec.get("items", [])
                columns = [x["id"] if isinstance(x, dict) else x for x in items]
                scored_df = df.copy()
                for item in items:
                    if isinstance(item, dict) and item.get("reverse") and item["id"] in scored_df.columns:
                        scored_df[item["id"]] = 6.0 - pd.to_numeric(scored_df[item["id"]], errors="coerce")
                criteria = spec.get("validation_criteria", {}).get(scale_id, [])
                scale_results[scale_id] = validate_scale(scored_df, columns, thresholds, criteria)
            instruments[instrument_id] = {
                "status": "PASSED" if scale_results and all(x["status"] == "PASSED" for x in scale_results.values()) else "NEEDS_WORK",
                "scales": scale_results,
            }
    if cognitive_csv:
        instruments["cognitive_battery"] = validate_cognitive_summary(pd.read_csv(cognitive_csv), thresholds)
    if cognitive_trials_csv:
        trial_result = validate_cognitive_trials(pd.read_csv(cognitive_trials_csv), thresholds)
        if "cognitive_battery" in instruments:
            summary_result = instruments["cognitive_battery"]
            instruments["cognitive_battery"] = {
                "status": "PASSED" if summary_result.get("status") == "PASSED" and trial_result.get("status") == "PASSED" else "NEEDS_WORK",
                "summary_validation": summary_result,
                "trial_validation": trial_result,
            }
        else:
            instruments["cognitive_battery"] = {
                "status": "NEEDS_WORK",
                "reason": "summary_export_required_together_with_trial_export",
                "trial_validation": trial_result,
            }
    return {
        "schema_version": "0.1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "thresholds": thresholds,
        "instruments": instruments,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate ARCHVIQ questionnaires and cognitive battery.")
    parser.add_argument("--questionnaire", help="Item-level questionnaire CSV")
    parser.add_argument("--scale-map", help="JSON mapping instrument -> scale -> item columns")
    parser.add_argument("--cognitive", help="Cognitive summary CSV; repeated SESSION_ID values enable retest ICC")
    parser.add_argument("--cognitive-trials", help="Trial-level cognitive CSV for split-half and RT quality validation")
    parser.add_argument("--out", required=True, help="Output validation_registry.json")
    args = parser.parse_args()
    registry = build_registry(args.questionnaire, args.scale_map, args.cognitive, args.cognitive_trials)
    save_json(args.out, registry)
    print(json.dumps(registry, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
