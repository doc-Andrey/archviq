from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Mapping

try:
    from .common import architecture_from_record, band, cognitive_axes, enforce_gate, load_json, mean, reverse100, save_json, section_scores
    from .architecture_gap_analysis import calculate_gaps
except ImportError:
    from common import architecture_from_record, band, cognitive_axes, enforce_gate, load_json, mean, reverse100, save_json, section_scores
    from architecture_gap_analysis import calculate_gaps


QUESTIONNAIRE_KEYS = (
    "exhaustion", "detachment", "cognitive_wear", "recovery_deficit",
    "demand_control_mismatch", "sleep_load", "decision_load", "decision_recovery",
)


def analyze(payload: Mapping[str, Any], registry: Mapping[str, Any], research_mode: bool = True) -> Dict[str, Any]:
    statuses = enforce_gate(
        registry,
        ["burnout_questionnaire", "burnout_outputs"],
        research_mode,
    )
    architecture = architecture_from_record(payload)
    q = section_scores(payload, "burnout_questionnaire")
    cognition = cognitive_axes(payload)
    architecture_calibration = calculate_gaps(payload)

    architecture_susceptibility = mean([
        reverse100(architecture.get("resource")),
        architecture.get("processing_cost"),
        reverse100(architecture.get("switching")),
        architecture.get("lock"),
        reverse100(architecture.get("control")),
    ])
    current_load = mean([q.get("exhaustion"), q.get("detachment"), q.get("cognitive_wear"), q.get("sleep_load")])
    recovery_pressure = mean([q.get("recovery_deficit"), q.get("demand_control_mismatch")])
    experimental_decision_load = mean([
        q.get("decision_load"),
        reverse100(q.get("decision_recovery")),
    ])

    objective_strain = None
    if any(v is not None for v in cognition.values()):
        objective_strain = mean([
            reverse100(cognition.get("rt_stability")),
            reverse100(cognition.get("working_memory")),
            reverse100(cognition.get("interference_control")),
            reverse100(cognition.get("complex_efficiency")),
        ])

    integrated = mean([current_load, recovery_pressure, architecture_susceptibility, objective_strain])
    flags = []
    if current_load is not None and current_load >= 65:
        flags.append("high_current_load")
    if recovery_pressure is not None and recovery_pressure >= 65:
        flags.append("recovery_not_matching_demands")
    if q.get("detachment") is not None and q["detachment"] >= 65:
        flags.append("detachment_or_cynicism")
    if objective_strain is not None and current_load is not None and abs(objective_strain - current_load) >= 30:
        flags.append("subjective_objective_gap_repeat_measurement")
    if experimental_decision_load is not None and experimental_decision_load >= 65:
        flags.append("high_decision_load_experimental")
    tension_names = {item["pattern"] for item in architecture_calibration["tension_patterns"]}
    if "performance_maintained_with_high_compensatory_effort" in tension_names:
        flags.append("performance_maintained_with_compensatory_effort")
    if "current_state_may_be_suppressing_measured_performance" in tension_names:
        flags.append("current_state_may_suppress_cognitive_performance")

    return {
        "module": "burnout",
        "version": "0.4-research",
        "mode": "RESEARCH_ONLY" if research_mode else "CLIENT",
        "validation": statuses,
        "architecture_susceptibility": {"score": architecture_susceptibility, "band": band(architecture_susceptibility)},
        "current_self_reported_load": {"score": current_load, "band": band(current_load)},
        "recovery_pressure": {"score": recovery_pressure, "band": band(recovery_pressure)},
        "optional_cognitive_strain": {"score": objective_strain, "band": band(objective_strain)},
        "experimental_decision_load": {
            "score": experimental_decision_load,
            "band": band(experimental_decision_load),
            "included_in_integrated_index": False,
        },
        "integrated_research_index": {"score": integrated, "band": band(integrated)},
        "flags": flags,
        "architecture_calibration": architecture_calibration,
        "inputs": {"architecture": architecture, "questionnaire": q, "cognitive": cognition},
        "limitations": [
            "This is a workload and recovery profile, not a medical diagnosis.",
            "Architecture is a susceptibility modifier and must not be treated as current burnout.",
            "Prospective validation against repeated outcomes is required before client risk claims.",
            "The decision-load block is a new hypothesis; the Player/Observer EEG study did not measure fatigue or burnout.",
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
        result = analyze(load_json(args.input), load_json(args.validation), research_mode=not args.client_mode)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
    save_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
