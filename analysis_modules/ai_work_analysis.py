from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Mapping

try:
    from .common import ROLE_PROCESSING_EVIDENCE, architecture_from_record, band, cognitive_axes, enforce_gate, load_json, mean, reverse100, save_json, section_scores
    from .architecture_gap_analysis import calculate_gaps
except ImportError:
    from common import ROLE_PROCESSING_EVIDENCE, architecture_from_record, band, cognitive_axes, enforce_gate, load_json, mean, reverse100, save_json, section_scores
    from architecture_gap_analysis import calculate_gaps


def analyze(payload: Mapping[str, Any], registry: Mapping[str, Any], research_mode: bool = True) -> Dict[str, Any]:
    statuses = enforce_gate(
        registry,
        ["ai_work_questionnaire", "ai_work_outputs"],
        research_mode,
    )
    architecture = architecture_from_record(payload)
    q = section_scores(payload, "ai_work_questionnaire")
    cognition = cognitive_axes(payload)
    architecture_calibration = calculate_gaps(payload)

    modes = {
        "prompt_structure_need": mean([
            reverse100(q.get("task_structuring")),
            architecture.get("processing_cost"),
            reverse100(cognition.get("complex_efficiency")),
        ]),
        "agency_retention": mean([
            q.get("agency_retention"),
            q.get("delegation_calibration"),
            architecture.get("control"),
        ]),
        "verification_capacity": mean([
            q.get("verification_role"),
            q.get("verification"),
            cognition.get("interference_control"),
        ]),
        "role_switch_flexibility": mean([
            q.get("role_switch_flexibility"),
            q.get("iteration_tolerance"),
            architecture.get("switching"),
        ]),
        "cognitive_offload_fit": mean([
            q.get("cognitive_offload"),
            reverse100(cognition.get("working_memory")),
            reverse100(cognition.get("rt_stability")),
        ]),
        "exploration_fit": mean([
            q.get("novelty_exploration"),
            architecture.get("novelty"),
            cognition.get("complex_accuracy"),
        ]),
        "passive_acceptance_risk": mean([
            q.get("passive_acceptance_risk"),
            q.get("overtrust_risk"),
            reverse100(q.get("trust_control")),
        ]),
    }

    recommendations = []
    if modes["prompt_structure_need"] is not None and modes["prompt_structure_need"] >= 65:
        recommendations.append("Use one goal, explicit constraints and a fixed output format per prompt.")
    if architecture.get("processing_cost") is not None and architecture["processing_cost"] >= 65:
        recommendations.append("Ask AI to split complex work into short sequential decisions.")
    if architecture.get("lock") is not None and architecture["lock"] >= 65:
        recommendations.append("Define a stop rule and ask AI to challenge the current frame before finalizing.")
    if q.get("overtrust_risk") is not None and q["overtrust_risk"] >= 60:
        recommendations.append("Require sources, uncertainty and an independent verification step for consequential claims.")
    if cognition.get("working_memory") is not None and cognition["working_memory"] < 40:
        recommendations.append("Keep an external decision log so intermediate assumptions are not lost.")
    if modes["agency_retention"] is not None and modes["agency_retention"] < 40:
        recommendations.append("Before accepting an AI proposal, restate the final decision in your own words and record who owns it.")
    if modes["role_switch_flexibility"] is not None and modes["role_switch_flexibility"] < 40:
        recommendations.append("Separate generation and verification into two explicit passes instead of mixing them in one prompt.")
    if modes["passive_acceptance_risk"] is not None and modes["passive_acceptance_risk"] >= 60:
        recommendations.append("Require a deliberate human decision checkpoint before the output can be used.")
    control_gap = architecture_calibration["axis_comparison"]["control"]["signed_gaps"]["cognitive_minus_43"]
    if control_gap is not None and control_gap <= -15:
        recommendations.append("Use an external verification checklist: measured interference control was below the Engine 43 prediction in this session.")

    return {
        "module": "ai_work",
        "version": "0.4-research",
        "mode": "RESEARCH_ONLY" if research_mode else "CLIENT",
        "validation": statuses,
        "work_modes": {k: {"score": v, "band": band(v)} for k, v in modes.items()},
        "recommendations": recommendations,
        "architecture_calibration": architecture_calibration,
        "role_processing_evidence": ROLE_PROCESSING_EVIDENCE,
        "inputs": {"architecture": architecture, "questionnaire": q, "cognitive": cognition},
        "limitations": [
            "This module recommends interaction format; it does not measure intelligence or employability.",
            "AI-use questionnaire scales require behavioral validation against task accuracy, time and verification errors.",
            "The EEG result validates a Player/Observer task-state contrast, not hallucination detection or a stable AI-use personality trait.",
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
