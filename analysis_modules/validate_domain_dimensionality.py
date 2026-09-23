"""Check structural and empirical redundancy among client-facing outputs.

The item-level validator tests questionnaire scales. This module tests the
downstream domains/modes produced by the analyzers themselves. Synthetic mode
detects overlap built into formulas; real-data mode evaluates the pilot.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping

import numpy as np
import pandas as pd

try:
    from . import ai_work_analysis, architecture_gap_analysis, burnout_analysis, compatibility_analysis
    from .common import load_json, save_json
except ImportError:
    import ai_work_analysis
    import architecture_gap_analysis
    import burnout_analysis
    import compatibility_analysis
    from common import load_json, save_json


MODULES: Dict[str, Callable[..., Dict[str, Any]]] = {
    "compatibility": compatibility_analysis.analyze,
    "burnout": burnout_analysis.analyze,
    "ai_work": ai_work_analysis.analyze,
    "architecture_gap": architecture_gap_analysis.analyze,
}


def extract_scores(module: str, result: Mapping[str, Any]) -> Dict[str, float]:
    if module == "architecture_gap":
        return {
            axis: float(item["mean_pairwise_gap"])
            for axis, item in result.get("axis_comparison", {}).items()
            if isinstance(item, Mapping) and item.get("mean_pairwise_gap") is not None
        }
    if module in {"compatibility", "ai_work"}:
        node = result.get("domains" if module == "compatibility" else "work_modes", {})
        return {
            name: float(item["score"])
            for name, item in node.items()
            if isinstance(item, Mapping) and item.get("score") is not None
        }
    names = [
        "architecture_susceptibility",
        "current_self_reported_load",
        "recovery_pressure",
        "optional_cognitive_strain",
        "experimental_decision_load",
    ]
    # integrated_research_index is excluded because it is defined from several
    # of these components and must correlate with them by construction.
    return {
        name: float(result[name]["score"])
        for name in names
        if isinstance(result.get(name), Mapping) and result[name].get("score") is not None
    }


def run_batch(module: str, records: List[Mapping[str, Any]], registry: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    for record in records:
        try:
            result = MODULES[module](record, registry, research_mode=True)
            row = extract_scores(module, result)
            if row:
                rows.append(row)
        except (KeyError, TypeError, ValueError):
            continue
    return pd.DataFrame(rows)


def parallel_analysis(x: np.ndarray, repetitions: int, seed: int) -> Dict[str, Any]:
    corr = np.corrcoef(x, rowvar=False)
    observed = np.linalg.eigvalsh(corr)[::-1]
    rng = np.random.default_rng(seed)
    null = np.zeros((repetitions, x.shape[1]))
    for i in range(repetitions):
        random_x = rng.standard_normal(x.shape)
        null[i] = np.linalg.eigvalsh(np.corrcoef(random_x, rowvar=False))[::-1]
    q95 = np.quantile(null, 0.95, axis=0)
    return {
        "observed_eigenvalues": observed.tolist(),
        "null95_eigenvalues": q95.tolist(),
        "retained_components": int(np.sum(observed > q95)),
    }


def dimensionality_report(
    frame: pd.DataFrame,
    data_kind: str,
    repetitions: int = 500,
    seed: int = 43,
) -> Dict[str, Any]:
    complete = frame.apply(pd.to_numeric, errors="coerce").dropna()
    if complete.shape[0] < 20 or complete.shape[1] < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "n_complete": int(complete.shape[0]),
            "n_outputs": int(complete.shape[1]),
        }
    constant = [c for c in complete if complete[c].nunique() < 2]
    if constant:
        return {"status": "FAILED", "reason": "constant_outputs", "outputs": constant}

    corr = complete.corr()
    eigen = np.linalg.eigvalsh(corr.to_numpy())[::-1]
    explained = eigen / eigen.sum() * 100.0
    pairs = []
    columns = list(complete.columns)
    for i, first in enumerate(columns):
        for second in columns[i + 1:]:
            value = float(corr.loc[first, second])
            pairs.append({"a": first, "b": second, "r": value, "abs_r": abs(value)})
    pairs.sort(key=lambda item: item["abs_r"], reverse=True)

    if data_kind == "synthetic":
        # Independent inputs should not create correlated outputs. A modest
        # threshold is intentional because any signal here is formula-made.
        warnings = [p for p in pairs if p["abs_r"] >= 0.25]
        status = "NEEDS_REDESIGN" if warnings else "STRUCTURALLY_DISTINCT"
        interpretation = "Synthetic mode tests formula overlap only; it is not evidence about people."
    else:
        warnings = [p for p in pairs if p["abs_r"] >= 0.80]
        status = "NEEDS_REDESIGN" if warnings else "NO_SEVERE_COLLAPSE_DETECTED"
        interpretation = "Real-data correlations may reflect either construct overlap or genuine higher-order factors; inspect loadings and criteria before merging outputs."

    return {
        "status": status,
        "data_kind": data_kind,
        "n_complete": int(len(complete)),
        "n_outputs": int(complete.shape[1]),
        "output_names": columns,
        "correlation_matrix": corr.round(4).to_dict(),
        "top_correlated_pairs": pairs[:10],
        "warning_pairs": warnings,
        "pca_explained_variance_pct": explained.tolist(),
        "parallel_analysis": parallel_analysis(complete.to_numpy(), repetitions, seed),
        "interpretation": interpretation,
    }


def make_synthetic_records(module: str, n: int, seed: int = 43) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)

    def architecture() -> Dict[str, float]:
        return {axis: float(rng.uniform(0, 100)) for axis in (
            "resource", "switching", "lock", "novelty", "control", "processing_cost"
        )}

    def cognition() -> Dict[str, float]:
        return {key: float(rng.uniform(10, 100)) for key in (
            "speed", "rt_stability", "working_memory", "interference_control",
            "complex_accuracy", "complex_efficiency",
        )}

    def questionnaire(keys: Any) -> Dict[str, float]:
        return {key: float(rng.uniform(1, 5)) for key in keys}

    records: List[Dict[str, Any]] = []
    if module == "compatibility":
        for _ in range(n):
            records.append({
                "person_a": {
                    "architecture": architecture(),
                    "compatibility_questionnaire": questionnaire(compatibility_analysis.QUESTIONNAIRE_KEYS),
                    "cognitive": cognition(),
                },
                "person_b": {
                    "architecture": architecture(),
                    "compatibility_questionnaire": questionnaire(compatibility_analysis.QUESTIONNAIRE_KEYS),
                    "cognitive": cognition(),
                },
            })
    elif module == "burnout":
        for _ in range(n):
            records.append({
                "architecture": architecture(),
                "burnout_questionnaire": questionnaire(burnout_analysis.QUESTIONNAIRE_KEYS),
                "cognitive": cognition(),
            })
    elif module == "ai_work":
        keys = (
            "task_structuring", "verification", "delegation_calibration",
            "iteration_tolerance", "cognitive_offload", "trust_control",
            "overtrust_risk", "novelty_exploration", "agency_retention",
            "verification_role", "role_switch_flexibility", "passive_acceptance_risk",
        )
        for _ in range(n):
            records.append({
                "architecture": architecture(),
                "ai_work_questionnaire": questionnaire(keys),
                "cognitive": cognition(),
            })
    elif module == "architecture_gap":
        q_keys = tuple(architecture_gap_analysis.QUESTIONNAIRE_AXIS_MAP.values()) + (
            "compensatory_effort", "state_interference", "context_support",
        )
        for _ in range(n):
            records.append({
                "architecture": architecture(),
                "architecture_questionnaire": questionnaire(q_keys),
                "cognitive": {
                    **cognition(),
                    "sustained_accuracy": float(rng.uniform(10, 100)),
                    "switching_efficiency": float(rng.uniform(10, 100)),
                    "task_set_stability": float(rng.uniform(10, 100)),
                    "exploration_adaptation": float(rng.uniform(10, 100)),
                },
            })
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True, choices=tuple(MODULES))
    parser.add_argument("--records", help="JSONL with one person/pair record per line")
    parser.add_argument("--synthetic", type=int, default=0)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repetitions", type=int, default=500)
    args = parser.parse_args()

    if bool(args.records) == bool(args.synthetic):
        raise SystemExit("Provide exactly one of --records or --synthetic N")
    registry = load_json(args.validation)
    if args.synthetic:
        records = make_synthetic_records(args.module, args.synthetic)
        kind = "synthetic"
        source = f"independent_inputs_N_{args.synthetic}"
    else:
        records = [json.loads(line) for line in Path(args.records).read_text(encoding="utf-8").splitlines() if line.strip()]
        kind = "real_pilot"
        source = str(args.records)

    frame = run_batch(args.module, records, registry)
    result = {
        "module": args.module,
        "source": source,
        **dimensionality_report(frame, kind, repetitions=args.repetitions),
    }
    save_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
