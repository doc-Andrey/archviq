from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Mapping, Optional

try:
    from .architecture_gap_analysis import calculate_gaps
    from .common import (
        ARCHITECTURE_AXES, ROLE_PROCESSING_EVIDENCE, architecture_from_record, band, cognitive_axes,
        completeness, enforce_gate, load_json, mean, reverse100, save_json,
        section_scores,
    )
except ImportError:
    from architecture_gap_analysis import calculate_gaps
    from common import (
        ARCHITECTURE_AXES, ROLE_PROCESSING_EVIDENCE, architecture_from_record, band, cognitive_axes,
        completeness, enforce_gate, load_json, mean, reverse100, save_json,
        section_scores,
    )


QUESTIONNAIRE_KEYS = (
    "responsiveness", "dyadic_coping", "repair", "demand_withdraw_risk",
    "escalation_risk", "autonomy_coordination", "change_alignment",
    "decision_initiation", "monitoring_support", "role_switch_flexibility",
    "control_conflict",
)


def gap(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return None if a is None or b is None else abs(a - b)


def pair_mean(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return mean([a, b])


def analyze(payload: Mapping[str, Any], registry: Mapping[str, Any], research_mode: bool = True) -> Dict[str, Any]:
    statuses = enforce_gate(
        registry,
        ["compatibility_questionnaire", "compatibility_outputs"],
        research_mode,
    )
    pa, pb = payload.get("person_a", {}), payload.get("person_b", {})
    aa, ab = architecture_from_record(pa), architecture_from_record(pb)
    qa, qb = section_scores(pa, "compatibility_questionnaire"), section_scores(pb, "compatibility_questionnaire")
    ca, cb = cognitive_axes(pa), cognitive_axes(pb)

    architecture_gaps = {axis: gap(aa.get(axis), ab.get(axis)) for axis in ARCHITECTURE_AXES}
    perceptions = {key: pair_mean(qa.get(key), qb.get(key)) for key in QUESTIONNAIRE_KEYS}
    perception_gaps = {key: gap(qa.get(key), qb.get(key)) for key in QUESTIONNAIRE_KEYS}

    domains = {
        "regulation_under_load": mean([
            pair_mean(aa.get("resource"), ab.get("resource")),
            pair_mean(aa.get("control"), ab.get("control")),
            reverse100(pair_mean(aa.get("processing_cost"), ab.get("processing_cost"))),
            perceptions.get("dyadic_coping"),
        ]),
        "flexibility_and_repair": mean([
            pair_mean(aa.get("switching"), ab.get("switching")),
            reverse100(pair_mean(aa.get("lock"), ab.get("lock"))),
            perceptions.get("repair"),
            reverse100(perceptions.get("demand_withdraw_risk")),
        ]),
        "stability_change_balance": mean([
            reverse100(architecture_gaps.get("novelty")),
            reverse100(architecture_gaps.get("switching")),
            perceptions.get("change_alignment"),
            perceptions.get("autonomy_coordination"),
        ]),
        "difficult_conversation": mean([
            perceptions.get("responsiveness"),
            reverse100(perceptions.get("escalation_risk")),
        ]),
        "decision_role_coordination": mean([
            perceptions.get("monitoring_support"),
            perceptions.get("role_switch_flexibility"),
            reverse100(perceptions.get("control_conflict")),
        ]),
    }

    flags = []
    if architecture_gaps.get("switching") is not None and architecture_gaps["switching"] >= 30:
        flags.append("different_switching_tempo")
    if pair_mean(aa.get("lock"), ab.get("lock")) is not None and pair_mean(aa.get("lock"), ab.get("lock")) >= 70:
        flags.append("mutual_position_holding")
    if perceptions.get("demand_withdraw_risk") is not None and perceptions["demand_withdraw_risk"] >= 65:
        flags.append("demand_withdraw_pattern")
    if any(v is not None and v >= 30 for v in perception_gaps.values()):
        flags.append("different_relationship_perceptions")
    initiation_a = qa.get("decision_initiation")
    initiation_b = qb.get("decision_initiation")
    if initiation_a is not None and initiation_b is not None:
        if initiation_a >= 65 and initiation_b >= 65:
            flags.append("competing_decision_ownership")
        elif initiation_a <= 35 and initiation_b <= 35:
            flags.append("decision_initiation_vacuum")
        elif abs(initiation_a - initiation_b) >= 30 and perceptions.get("autonomy_coordination") is not None and perceptions["autonomy_coordination"] >= 60:
            flags.append("potentially_complementary_decision_roles")

    cognition_available = completeness(ca, ca.keys()) > 0 and completeness(cb, cb.keys()) > 0
    return {
        "module": "compatibility",
        "version": "0.4-research",
        "mode": "RESEARCH_ONLY" if research_mode else "CLIENT",
        "validation": statuses,
        "architecture": {"person_a": aa, "person_b": ab, "absolute_gaps": architecture_gaps},
        "questionnaire": {"pair_means": perceptions, "perception_gaps": perception_gaps},
        "cognitive_optional": {"available_for_both": cognition_available, "person_a": ca, "person_b": cb},
        "individual_architecture_calibration": {
            "person_a": calculate_gaps(pa),
            "person_b": calculate_gaps(pb),
            "included_in_pair_domain_scores": False,
        },
        "domains": {k: {"score": v, "band": band(v)} for k, v in domains.items()},
        "interaction_flags": flags,
        "role_processing_evidence": ROLE_PROCESSING_EVIDENCE,
        "global_compatibility_percent": None,
        "limitations": [
            "Architecture describes interaction conditions, not love, fidelity or probability of separation.",
            "No global compatibility percentage is produced.",
            "Current coefficients are provisional until prospective dyadic validation passes.",
            "EEG supports Player/Observer as a task state, but does not establish a stable couple trait.",
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
