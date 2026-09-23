from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, Mapping

import pandas as pd


def load_blueprint(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def score_instrument_row(row: Mapping[str, Any], instrument: Mapping[str, Any]) -> Dict[str, Any]:
    output: Dict[str, Any] = {"CLIENT_ID": row.get("CLIENT_ID", "")}
    scoring = instrument.get("scoring", {}) if isinstance(instrument.get("scoring", {}), Mapping) else {}
    min_fraction = float(scoring.get("min_answer_fraction", 0.75))
    all_valid_values = []
    invalid_responses = 0
    answered_total = 0
    item_total = 0
    for scale_id, scale_spec in instrument.get("scales", {}).items():
        items = scale_spec.get("items", scale_spec) if isinstance(scale_spec, dict) else scale_spec
        values = []
        item_total += len(items)
        for item in items:
            item = item if isinstance(item, dict) else {"id": item, "reverse": False}
            value = pd.to_numeric(pd.Series([row.get(item["id"])]), errors="coerce").iloc[0]
            if pd.isna(value):
                continue
            value = float(value)
            if 1.0 <= value <= 5.0:
                answered_total += 1
                all_valid_values.append(value)
                values.append(6.0 - value if item.get("reverse", False) else value)
            else:
                invalid_responses += 1
        required = max(1, math.ceil(len(items) * min_fraction))
        output[scale_id] = ((sum(values) / len(values)) - 1.0) * 25.0 if len(values) >= required else float("nan")
        output[f"{scale_id}__answered"] = len(values)
        output[f"{scale_id}__total"] = len(items)
        output[f"{scale_id}__required"] = required
    completion = answered_total / item_total if item_total else 0.0
    response_sd = float(pd.Series(all_valid_values).std(ddof=0)) if all_valid_values else float("nan")
    output["QUESTIONNAIRE_COMPLETION"] = completion
    output["QUESTIONNAIRE_INVALID_RESPONSES"] = invalid_responses
    output["QUESTIONNAIRE_RESPONSE_SD"] = response_sd
    output["QUESTIONNAIRE_STRAIGHTLINE_FLAG"] = bool(len(all_valid_values) >= 12 and response_sd < 0.15)
    output["QUESTIONNAIRE_VALID"] = bool(
        completion >= min_fraction
        and invalid_responses == 0
        and not output["QUESTIONNAIRE_STRAIGHTLINE_FLAG"]
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Score one ARCHVIQ thematic questionnaire.")
    parser.add_argument("--responses", required=True)
    parser.add_argument("--blueprint", required=True)
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    blueprint = load_blueprint(args.blueprint)
    instrument = blueprint["instruments"].get(args.instrument)
    if not instrument:
        raise KeyError(f"Unknown instrument: {args.instrument}")
    responses = pd.read_csv(args.responses)
    scored = pd.DataFrame([score_instrument_row(row, instrument) for _, row in responses.iterrows()])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(args.out, index=False)
    print(scored.to_string(index=False))


if __name__ == "__main__":
    main()
