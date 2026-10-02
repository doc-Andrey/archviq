from __future__ import annotations

from typing import Any, Dict, List


SOMATIC_DOMAINS = [
    "autonomic_cardiovascular",
    "metabolic_endocrine",
    "thyroid",
    "immune_allergic",
    "respiratory",
    "gastrointestinal_visceral",
]

PSYCHOPHYSIOLOGY_DOMAINS = [
    "stress_reactivity",
    "salience_dependent_hysteresis",
    "autonomic_recovery",
    "reentry_after_salient_events",
    "state_recovery_to_H_star",
]


def experimental_branches(processing_parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Expose experimental branches without inventing diagnostic mappings.

    The branches are intentionally present in the public contract.  Until a
    separately frozen downstream mapping is calibrated, results contain only the
    candidate upstream processing parameters and explicit NOT_CALIBRATED status.
    """
    upstream = {
        p["parameter"]: {
            "mode": p["mode"],
            "state_median": p.get("state_median"),
            "pressure_median": p.get("pressure_median"),
            "robustness": p.get("robustness"),
        }
        for p in processing_parameters
    }
    common = {
        "status": "EXPERIMENTAL",
        "diagnostic_use": False,
        "causal_status": "UNPROVEN",
        "mapping_status": "NOT_CALIBRATED",
        "warning": "Research branch only. No diagnosis, disease prediction, or established EMF causality is claimed.",
    }
    return {
        "somatic": {
            **common,
            "domains": SOMATIC_DOMAINS,
            "results": None,
            "upstream_processing": upstream,
        },
        "psychophysiology": {
            **common,
            "domains": PSYCHOPHYSIOLOGY_DOMAINS,
            "results": None,
            "upstream_processing": upstream,
        },
    }
