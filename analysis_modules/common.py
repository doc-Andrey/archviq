from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


ARCHITECTURE_AXES = (
    "resource",
    "switching",
    "lock",
    "novelty",
    "control",
    "processing_cost",
)

# Group-level evidence used only to motivate research constructs. It is not an
# individual trait score and must never be imputed from Engine 43.
ROLE_PROCESSING_EVIDENCE = {
    "dataset": "DeceptionGame DecisionMaking.mat",
    "status": "GROUP_LEVEL_INTERNAL_VALIDATION",
    "contrast": "Player_vs_Observer",
    "nested_auc": 0.9256198347107437,
    "nested_balanced_accuracy": 0.8409090909090909,
    "n_dyads": 12,
    "within_person_direction": "20_of_20",
    "stable_features": ["r_alpha_late", "r_alpha_sustained"],
    "truth_auc": 0.49741735537190085,
    "restriction": "Supports a role state, not personality, compatibility, burnout, truth detection or Engine 43 calibration.",
}


def finite(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def mean(values: Iterable[Any]) -> Optional[float]:
    clean = [finite(v) for v in values]
    clean = [v for v in clean if v is not None]
    return sum(clean) / len(clean) if clean else None


def reverse100(value: Any) -> Optional[float]:
    v = finite(value)
    return None if v is None else 100.0 - clamp(v)


def normalize_score(value: Any) -> Optional[float]:
    """Accept 0..100 or Stage-2 1..5 and return 0..100."""
    v = finite(value)
    if v is None:
        return None
    if 1.0 <= v <= 5.0:
        return clamp((v - 1.0) * 25.0)
    return clamp(v)


def band(value: Optional[float]) -> str:
    if value is None:
        return "missing"
    if value < 35:
        return "low"
    if value < 65:
        return "moderate"
    return "high"


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def architecture_from_record(record: Mapping[str, Any]) -> Dict[str, Optional[float]]:
    nested = record.get("architecture") if isinstance(record.get("architecture"), Mapping) else {}
    result: Dict[str, Optional[float]] = {}
    for axis in ARCHITECTURE_AXES:
        candidates = (
            nested.get(axis),
            record.get(f"score_{axis}"),
            record.get(axis),
        )
        result[axis] = next((normalize_score(v) for v in candidates if finite(v) is not None), None)
    return result


def section_scores(record: Mapping[str, Any], section: str) -> Dict[str, Optional[float]]:
    raw = record.get(section, {})
    if not isinstance(raw, Mapping):
        return {}
    return {str(k): normalize_score(v) for k, v in raw.items()}


def validation_status(registry: Mapping[str, Any], instrument_id: str) -> str:
    for section_name in ("instruments", "output_models"):
        section = registry.get(section_name, {})
        if not isinstance(section, Mapping):
            continue
        item = section.get(instrument_id, {})
        if isinstance(item, Mapping) and item:
            return str(item.get("status", "MISSING"))
    return "MISSING"


def enforce_gate(
    registry: Mapping[str, Any],
    required: Iterable[str],
    research_mode: bool,
) -> Dict[str, str]:
    statuses = {instrument: validation_status(registry, instrument) for instrument in required}
    blocked = [name for name, status in statuses.items() if status != "PASSED"]
    if blocked and not research_mode:
        raise RuntimeError(
            "Client mode blocked. Instruments not validated: " + ", ".join(blocked)
        )
    return statuses


def completeness(values: Mapping[str, Optional[float]], required: Iterable[str]) -> float:
    keys = list(required)
    if not keys:
        return 1.0
    return sum(values.get(k) is not None for k in keys) / len(keys)


def cognitive_axes(record: Mapping[str, Any]) -> Dict[str, Optional[float]]:
    """Read normalized cognition, including Stage-2 REAL_COG_* field names."""
    raw = record.get("cognitive", {})
    if not isinstance(raw, Mapping):
        raw = {}
    aliases = {
        "speed": ("speed", "REAL_COG_SPEED"),
        "rt_stability": ("rt_stability", "REAL_COG_RT_STABILITY"),
        "working_memory": ("working_memory", "REAL_COG_WORKING_MEMORY"),
        "interference_control": ("interference_control", "REAL_COG_INTERFERENCE_CONTROL"),
        "complex_accuracy": ("complex_accuracy", "REAL_COG_COMPLEX_ACCURACY"),
        "complex_efficiency": ("complex_efficiency", "REAL_COG_COMPLEX_EFFICIENCY"),
        "sustained_accuracy": ("sustained_accuracy", "REAL_COG_SUSTAINED_ACCURACY"),
        "switching_efficiency": ("switching_efficiency", "REAL_COG_SWITCHING_EFFICIENCY"),
        "task_set_stability": ("task_set_stability", "REAL_COG_TASK_SET_STABILITY"),
        "exploration_adaptation": ("exploration_adaptation", "REAL_COG_EXPLORATION_ADAPTATION"),
    }
    out: Dict[str, Optional[float]] = {}
    for key, names in aliases.items():
        value = None
        for name in names:
            if name in raw:
                value = normalize_score(raw.get(name))
                break
            if name in record:
                value = normalize_score(record.get(name))
                break
        out[key] = value
    return out


def cognitive_architecture_axes(record: Mapping[str, Any]) -> Dict[str, Optional[float]]:
    """Map only defensible normalized cognitive anchors onto Engine 43 axes.

    Missing anchors stay missing. In particular, working memory is not used as
    a substitute for switching, lock or novelty. Raw RDM/DDM parameters must be
    normed in a validation sample before they can enter these 0..100 fields.
    """
    cognition = cognitive_axes(record)
    return {
        "resource": mean([cognition.get("rt_stability"), cognition.get("sustained_accuracy")]),
        "switching": cognition.get("switching_efficiency"),
        "lock": cognition.get("task_set_stability"),
        "novelty": cognition.get("exploration_adaptation"),
        "control": cognition.get("interference_control"),
        "processing_cost": reverse100(cognition.get("complex_efficiency")),
    }
