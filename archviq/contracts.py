from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping


class InputValidationError(ValueError):
    pass


@dataclass(frozen=True)
class GestationSpec:
    mode: str = "unknown"  # unknown | ctb_days | conception
    conception_to_birth_days: int | None = None
    conception: str | None = None
    uncertainty_days: int | None = None


@dataclass(frozen=True)
class ProfileRequest:
    dob: str
    sex: str
    gestation: GestationSpec = field(default_factory=GestationSpec)
    subject_label: str = "subject"


def _iso_date(value: str, field_name: str) -> str:
    try:
        return date.fromisoformat(str(value)).isoformat()
    except Exception as exc:
        raise InputValidationError(f"{field_name} must be ISO date YYYY-MM-DD") from exc


def parse_request(obj: ProfileRequest | Mapping[str, Any]) -> ProfileRequest:
    if isinstance(obj, ProfileRequest):
        req = obj
    elif isinstance(obj, Mapping):
        g = obj.get("gestation") or {}
        if not isinstance(g, Mapping):
            raise InputValidationError("gestation must be an object")
        req = ProfileRequest(
            dob=str(obj.get("dob", "")),
            sex=str(obj.get("sex", "")),
            gestation=GestationSpec(
                mode=str(g.get("mode", "unknown")),
                conception_to_birth_days=(None if g.get("conception_to_birth_days") is None else int(g["conception_to_birth_days"])),
                conception=(None if g.get("conception") is None else str(g["conception"])),
                uncertainty_days=(None if g.get("uncertainty_days") is None else int(g["uncertainty_days"])),
            ),
            subject_label=str(obj.get("subject_label") or "subject"),
        )
    else:
        raise InputValidationError("request must be ProfileRequest or mapping")

    dob = _iso_date(req.dob, "dob")
    sex = req.sex.strip().upper()
    aliases = {"FEMALE": "F", "WOMAN": "F", "Ж": "F", "MАLE": "M", "MALE": "M", "MAN": "M", "М": "M"}
    sex = aliases.get(sex, sex)
    if sex not in {"F", "M"}:
        raise InputValidationError("sex must be F or M")

    mode = req.gestation.mode.strip().lower()
    if mode not in {"unknown", "ctb_days", "conception"}:
        raise InputValidationError("gestation.mode must be unknown, ctb_days or conception")

    ctb = req.gestation.conception_to_birth_days
    conception = req.gestation.conception
    unc = req.gestation.uncertainty_days

    if mode == "unknown":
        if ctb is not None or conception is not None:
            raise InputValidationError("unknown gestation must not provide conception or conception_to_birth_days")
        ctb = 266
        unc = 14 if unc is None else unc
    elif mode == "ctb_days":
        if ctb is None:
            raise InputValidationError("ctb_days mode requires conception_to_birth_days")
        if conception is not None:
            raise InputValidationError("ctb_days mode must not also provide conception")
        unc = 7 if unc is None else unc
    else:
        if conception is None:
            raise InputValidationError("conception mode requires conception")
        conception = _iso_date(conception, "gestation.conception")
        if ctb is not None:
            raise InputValidationError("conception mode must not also provide conception_to_birth_days")
        unc = 0 if unc is None else unc

    if unc is None or unc < 0 or unc > 60:
        raise InputValidationError("gestation uncertainty_days must be in 0..60")
    if ctb is not None and not (140 <= ctb <= 300):
        raise InputValidationError("conception_to_birth_days outside supported research range 140..300")

    return ProfileRequest(
        dob=dob,
        sex=sex,
        gestation=GestationSpec(mode=mode, conception_to_birth_days=ctb, conception=conception, uncertainty_days=unc),
        subject_label=req.subject_label.strip() or "subject",
    )
