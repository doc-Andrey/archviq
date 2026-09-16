from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, Tuple

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

CONSENT_VERSION = "ARCHVIQ-RESEARCH-2026-09-15-v2-simple"
ENGINE_VERSION = "OLD43_PRODUCTION_V1_NO_LAG"
TABLE = "research_data"

# We do not write direct identifiers to the research table. Exact DOB is used
# transiently by the production engine. The derived estimated conception date
# IS deliberately retained for research, so the dataset is pseudonymized rather
# than guaranteed anonymous.
_BLOCKED_EXACT = {
    "name", "full_name", "first_name", "last_name", "display_name",
    "email", "e_mail", "contact", "phone", "telephone", "mobile",
    "dob", "date_of_birth", "birth_date", "birthday", "birthdate",
    "sex", "gender", "age", "exact_age",
    "address", "street", "city", "location", "country", "postal_code", "zip",
    "ip", "ip_address", "remote_addr", "user_agent", "device", "device_type",
    "timestamp", "datetime", "submitted_at", "created_at_client",
    "client_id", "participant_id", "subject_id", "user_id", "userid",
    "context",
}

_BLOCKED_SUFFIXES = (
    "_name", "_email", "_phone", "_address", "_dob", "_birth_date",
    "_date_of_birth", "_sex", "_gender", "_ip", "_ip_address",
    "_user_agent", "_device", "_timestamp", "_submitted_at",
)


def new_id() -> str:
    return str(uuid.uuid4())


def _norm_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def _blocked_key(key: Any) -> bool:
    nk = _norm_key(key)
    if nk in _BLOCKED_EXACT or any(nk.endswith(s) for s in _BLOCKED_SUFFIXES):
        return True
    parts = set(nk.split("_"))
    direct_tokens = {
        "name", "email", "contact", "phone", "dob", "birth", "sex",
        "gender", "age", "ip", "address", "device", "city", "country",
    }
    return bool(parts & direct_tokens)


def _json_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value) if math.isfinite(value) else None
    if hasattr(value, "item"):
        try:
            return _json_scalar(value.item())
        except Exception:
            pass
    if isinstance(value, str):
        return value
    return str(value)


def sanitize_payload(obj: Any) -> Any:
    """Remove direct identifiers recursively; preserve scientific variables."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if _blocked_key(k):
                continue
            cleaned = sanitize_payload(v)
            if cleaned is not None:
                out[str(k)] = cleaned
        return out
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_payload(v) for v in obj]
    if hasattr(obj, "to_dict") and not isinstance(obj, str):
        try:
            return sanitize_payload(obj.to_dict(orient="records"))
        except TypeError:
            try:
                return sanitize_payload(obj.to_dict())
            except Exception:
                pass
        except Exception:
            pass
    return _json_scalar(obj)


def payload_fingerprint(obj: Any) -> str:
    cleaned = sanitize_payload(obj)
    blob = json.dumps(cleaned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


def _secret(name: str) -> str:
    if st is not None:
        try:
            value = st.secrets.get(name, "")
            if value:
                return str(value).strip()
        except Exception:
            pass
    return os.getenv(name, "").strip()


def storage_configured() -> bool:
    return bool(_secret("SUPABASE_URL") and (_secret("SUPABASE_SECRET_KEY") or _secret("SUPABASE_SERVICE_ROLE_KEY")))


def _api_key() -> str:
    return _secret("SUPABASE_SECRET_KEY") or _secret("SUPABASE_SERVICE_ROLE_KEY")


def _insert(row: Dict[str, Any]) -> Tuple[bool, str]:
    base = _secret("SUPABASE_URL").rstrip("/")
    key = _api_key()
    if not base or not key:
        return False, "research storage is not configured"
    data = json.dumps(sanitize_payload(row), ensure_ascii=False, allow_nan=False).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/rest/v1/{TABLE}",
        data=data,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
            "User-Agent": "Archviq-Research-Backend/2.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = getattr(resp, "status", 200)
            return (True, "ok") if 200 <= status < 300 else (False, f"Supabase HTTP {status}")
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        return False, f"Supabase HTTP {exc.code}: {body or exc.reason}"
    except Exception as exc:
        return False, f"research storage error: {exc}"


def _parse_iso_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def _conception_fields(profile: Dict[str, Any]) -> Dict[str, Any]:
    raw = profile.get("raw", {}) or {}
    # Frozen OLD43 production uses DOB - 280 d. Research V4 will use DOB - 266 d.
    # We retain BOTH anchors without persisting DOB.
    engine_280 = _parse_iso_date(raw.get("conception_est"))
    research_266 = engine_280 + timedelta(days=14) if engine_280 else None
    return {
        "engine_conception_est_280": engine_280.isoformat() if engine_280 else None,
        "research_conception_est_266": research_266.isoformat() if research_266 else None,
        "conception_method": "engine=dob_minus_280d;research=dob_minus_266d",
    }


def _event(*, record_type: str, session_id: str, anonymous_id: str | None,
           app_build: str = "", language: str = "", pair_id: str | None = None,
           secondary_anonymous_id: str | None = None, payload: Any = None,
           conception: Dict[str, Any] | None = None) -> Dict[str, Any]:
    conception = conception or {}
    cleaned = sanitize_payload(payload or {})
    return {
        "session_id": session_id,
        "anonymous_id": anonymous_id,
        "secondary_anonymous_id": secondary_anonymous_id,
        "pair_id": pair_id,
        "record_type": record_type,
        "consent_version": CONSENT_VERSION,
        "research_consent": True,
        "app_build": app_build,
        "language": language,
        "engine_version": ENGINE_VERSION,
        "engine_conception_est_280": conception.get("engine_conception_est_280"),
        "research_conception_est_266": conception.get("research_conception_est_266"),
        "conception_method": conception.get("conception_method"),
        "payload_fingerprint": payload_fingerprint(cleaned),
        "payload": cleaned,
    }


def save_consent(*, session_id: str, anon_subject_id: str, language: str,
                 pair_participant_confirmation: bool = False) -> Tuple[bool, str]:
    return _insert(_event(
        record_type="consent",
        session_id=session_id,
        anonymous_id=anon_subject_id,
        language=language,
        payload={
            "pair_participant_confirmation": bool(pair_participant_confirmation),
            "consent_text_version": CONSENT_VERSION,
        },
    ))


def save_profile(*, session_id: str, anon_subject_id: str, role: str,
                 profile: Dict[str, Any], interpretation: Dict[str, Any] | None,
                 app_build: str, language: str) -> Tuple[bool, str]:
    conception = _conception_fields(profile)
    payload = {
        "role": role,
        "type_name": profile.get("type_name"),
        "rs1": profile.get("rs1"), "rs2": profile.get("rs2"),
        "rs3": profile.get("rs3"), "rs4": profile.get("rs4"),
        "tension": profile.get("tension"), "adaptive": profile.get("adaptive"),
        "engine_source": profile.get("engine_source"),
        "raw": profile.get("raw", {}),
        "interpretation": interpretation or {},
    }
    return _insert(_event(
        record_type="profile",
        session_id=session_id,
        anonymous_id=anon_subject_id,
        app_build=app_build,
        language=language,
        payload=payload,
        conception=conception,
    ))


def save_cognitive(*, session_id: str, anon_subject_id: str,
                   result: Dict[str, Any], gap_rows: Iterable[Dict[str, Any]] | None,
                   app_build: str, language: str) -> Tuple[bool, str]:
    return _insert(_event(
        record_type="cognitive",
        session_id=session_id,
        anonymous_id=anon_subject_id,
        app_build=app_build,
        language=language,
        payload={"result": result, "gap": list(gap_rows or [])},
    ))


def save_questionnaire(*, session_id: str, anon_subject_id: str,
                       questionnaire_type: str, answers: Dict[str, Any],
                       score_pct: int | float, domains: Iterable[Any],
                       app_build: str, language: str) -> Tuple[bool, str]:
    return _insert(_event(
        record_type="questionnaire",
        session_id=session_id,
        anonymous_id=anon_subject_id,
        app_build=app_build,
        language=language,
        payload={
            "questionnaire_type": questionnaire_type,
            "answers": answers,
            "score_pct": score_pct,
            "domains": list(domains),
        },
    ))


def save_compatibility(*, session_id: str, pair_id: str,
                       subject1_id: str, subject2_id: str,
                       p1: Dict[str, Any], p2: Dict[str, Any],
                       compatibility: Dict[str, Any], deep: Dict[str, Any] | None,
                       app_build: str, language: str) -> Tuple[bool, str]:
    c1 = _conception_fields(p1)
    c2 = _conception_fields(p2)
    payload = {
        "subject1": {
            "engine_conception_est_280": c1["engine_conception_est_280"],
            "research_conception_est_266": c1["research_conception_est_266"],
            "type_name": p1.get("type_name"),
            "rs1": p1.get("rs1"), "rs2": p1.get("rs2"),
            "rs3": p1.get("rs3"), "rs4": p1.get("rs4"),
            "tension": p1.get("tension"), "adaptive": p1.get("adaptive"),
            "raw": p1.get("raw", {}),
        },
        "subject2": {
            "engine_conception_est_280": c2["engine_conception_est_280"],
            "research_conception_est_266": c2["research_conception_est_266"],
            "type_name": p2.get("type_name"),
            "rs1": p2.get("rs1"), "rs2": p2.get("rs2"),
            "rs3": p2.get("rs3"), "rs4": p2.get("rs4"),
            "tension": p2.get("tension"), "adaptive": p2.get("adaptive"),
            "raw": p2.get("raw", {}),
        },
        "compatibility": compatibility,
        "deep": deep or {},
    }
    return _insert(_event(
        record_type="compatibility",
        session_id=session_id,
        anonymous_id=subject1_id,
        secondary_anonymous_id=subject2_id,
        pair_id=pair_id,
        app_build=app_build,
        language=language,
        payload=payload,
    ))
