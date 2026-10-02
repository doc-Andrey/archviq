from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Mapping, Optional

try:
    from .common import (
        ARCHITECTURE_AXES,
        architecture_from_record,
        cognitive_architecture_axes,
        enforce_gate,
        load_json,
        mean,
        save_json,
        section_scores,
    )
except ImportError:
    from common import (
        ARCHITECTURE_AXES,
        architecture_from_record,
        cognitive_architecture_axes,
        enforce_gate,
        load_json,
        mean,
        save_json,
        section_scores,
    )


QUESTIONNAIRE_AXIS_MAP = {
    "resource": "resource_expression",
    "switching": "switching_expression",
    "lock": "lock_expression",
    "novelty": "novelty_expression",
    "control": "control_expression",
    "processing_cost": "processing_cost_expression",
}

GAP_NOTICE = 15.0
GAP_LARGE = 30.0


def _signed(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """Return a-b when both layers are present."""
    return None if a is None or b is None else float(a - b)


def _absolute(value: Optional[float]) -> Optional[float]:
    return None if value is None else abs(float(value))


def _gap_band(values: list[Optional[float]]) -> str:
    clean = [abs(float(value)) for value in values if value is not None]
    if not clean:
        return "missing"
    maximum = max(clean)
    if maximum < GAP_NOTICE:
        return "aligned"
    if maximum < GAP_LARGE:
        return "noticeable_gap"
    return "large_gap"


def calculate_gaps(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Compare independent layers without treating any one layer as ground truth."""
    architecture = architecture_from_record(payload)
    questionnaire = section_scores(payload, "architecture_questionnaire")
    cognition = cognitive_architecture_axes(payload)

    axes: Dict[str, Any] = {}
    patterns = []
    for axis in ARCHITECTURE_AXES:
        predicted = architecture.get(axis)
        experienced = questionnaire.get(QUESTIONNAIRE_AXIS_MAP[axis])
        measured = cognition.get(axis)
        expression_minus_prediction = _signed(experienced, predicted)
        measured_minus_prediction = _signed(measured, predicted)
        measured_minus_expression = _signed(measured, experienced)
        signed_gaps = {
            "questionnaire_minus_43": expression_minus_prediction,
            "cognitive_minus_43": measured_minus_prediction,
            "cognitive_minus_questionnaire": measured_minus_expression,
        }
        absolute_gaps = {name: _absolute(value) for name, value in signed_gaps.items()}
        available = [value for value in (predicted, experienced, measured) if value is not None]
        pairwise = [value for value in absolute_gaps.values() if value is not None]
        axis_patterns = []

        if measured_minus_prediction is not None and measured_minus_prediction <= -GAP_NOTICE:
            axis_patterns.append("measured_below_43_prediction")
        if measured_minus_prediction is not None and measured_minus_prediction >= GAP_NOTICE:
            axis_patterns.append("measured_above_43_prediction")
        if measured_minus_expression is not None and measured_minus_expression >= GAP_NOTICE:
            axis_patterns.append("measured_above_self_report")
        if measured_minus_expression is not None and measured_minus_expression <= -GAP_NOTICE:
            axis_patterns.append("self_report_above_measured")
        if expression_minus_prediction is not None and measured_minus_prediction is not None:
            if (
                abs(expression_minus_prediction) >= GAP_NOTICE
                and abs(measured_minus_prediction) >= GAP_NOTICE
                and expression_minus_prediction * measured_minus_prediction > 0
            ):
                axis_patterns.append("questionnaire_and_test_diverge_from_43_same_direction")
            if (
                abs(expression_minus_prediction) >= GAP_NOTICE
                and abs(measured_minus_prediction) >= GAP_NOTICE
                and expression_minus_prediction * measured_minus_prediction < 0
            ):
                axis_patterns.append("cross_context_divergence")

        axes[axis] = {
            "engine43_prediction": predicted,
            "questionnaire_expression": experienced,
            "cognitive_measurement": measured,
            "signed_gaps": signed_gaps,
            "absolute_gaps": absolute_gaps,
            "mean_pairwise_gap": mean(pairwise),
            "range_across_layers": max(available) - min(available) if len(available) >= 2 else None,
            "alignment": _gap_band(list(signed_gaps.values())),
            "patterns": axis_patterns,
        }
        patterns.extend({"axis": axis, "pattern": pattern} for pattern in axis_patterns)

    effort = questionnaire.get("compensatory_effort")
    state_interference = questionnaire.get("state_interference")
    context_support = questionnaire.get("context_support")
    maintained_axes = []
    overperformance_axes = []
    suppressed_axes = []
    for axis, result in axes.items():
        cognitive_gap = result["signed_gaps"]["cognitive_minus_43"]
        if effort is not None and effort >= 65:
            if cognitive_gap is not None and abs(cognitive_gap) < GAP_NOTICE:
                maintained_axes.append(axis)
            elif cognitive_gap is not None and cognitive_gap >= GAP_NOTICE:
                overperformance_axes.append(axis)
        if (
            state_interference is not None
            and state_interference >= 65
            and cognitive_gap is not None
            and cognitive_gap <= -GAP_NOTICE
        ):
            suppressed_axes.append(axis)

    tension_patterns = []
    if maintained_axes:
        tension_patterns.append({
            "axes": maintained_axes,
            "pattern": "performance_maintained_with_high_compensatory_effort",
        })
    if overperformance_axes:
        tension_patterns.append({
            "axes": overperformance_axes,
            "pattern": "measured_overperformance_with_high_compensatory_effort",
        })
    if suppressed_axes:
        tension_patterns.append({
            "axes": suppressed_axes,
            "pattern": "current_state_may_be_suppressing_measured_performance",
        })

    return {
        "layers": {
            "engine43_prediction": architecture,
            "questionnaire_expression": {
                axis: questionnaire.get(scale)
                for axis, scale in QUESTIONNAIRE_AXIS_MAP.items()
            },
            "cognitive_measurement": cognition,
        },
        "axis_comparison": axes,
        "context": {
            "compensatory_effort": effort,
            "state_interference": state_interference,
            "context_support": context_support,
        },
        "gap_patterns": patterns,
        "tension_patterns": tension_patterns,
        "coverage": {
            "engine43_axes": sum(architecture.get(axis) is not None for axis in ARCHITECTURE_AXES),
            "questionnaire_axes": sum(
                questionnaire.get(scale) is not None
                for scale in QUESTIONNAIRE_AXIS_MAP.values()
            ),
            "cognitive_axes": sum(cognition.get(axis) is not None for axis in ARCHITECTURE_AXES),
        },
        "global_tension_percent": None,
    }


def analyze(
    payload: Mapping[str, Any],
    registry: Mapping[str, Any],
    research_mode: bool = True,
) -> Dict[str, Any]:
    statuses = enforce_gate(
        registry,
        ["architecture_questionnaire", "architecture_gap_outputs"],
        research_mode,
    )
    result = calculate_gaps(payload)
    return {
        "module": "architecture_gap",
        "version": "0.4-research",
        "mode": "RESEARCH_ONLY" if research_mode else "CLIENT",
        "validation": statuses,
        **result,
        "thresholds_provisional": {
            "noticeable_gap": GAP_NOTICE,
            "large_gap": GAP_LARGE,
        },
        "limitations": [
            "Engine 43 is a developmental prior, questionnaire scores are self-reported expression, and cognitive scores are task-bound behavior; none is treated as ground truth.",
            "Gap thresholds are provisional and require prospective calibration.",
            "A gap is not a deficit or diagnosis. It may reflect context, state, compensation, measurement error or an inaccurate prediction.",
            "No global tension percentage is produced.",
            "Raw DDM parameters must be normed in a validation sample before entering 0..100 cognitive architecture axes.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--client-mode", action="store_true")
    args = parser.parse_args()
    try:
        result = analyze(
            load_json(args.input),
            load_json(args.validation),
            research_mode=not args.client_mode,
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
    save_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
