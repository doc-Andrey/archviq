from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from archviq import InputValidationError, UnsupportedGestationError, run_site_profile

SILSO_PATH = ROOT / "data" / "SN_d_tot_V2.0.txt"

app = FastAPI(title="ARCHVIQ API", version="4.0")


class GestationIn(BaseModel):
    mode: str = "unknown"
    conception_to_birth_days: int | None = None
    conception: str | None = None
    uncertainty_days: int | None = None


class ProfileIn(BaseModel):
    dob: str
    sex: str
    subject_label: str = "subject"
    gestation: GestationIn = Field(default_factory=GestationIn)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "silso_repository_local": SILSO_PATH.is_file(),
        "runtime_download": False,
    }


@app.post("/api/profile")
def profile(req: ProfileIn) -> Dict[str, Any]:
    try:
        return run_site_profile(req.model_dump(), silso_path=SILSO_PATH)
    except UnsupportedGestationError as exc:
        raise HTTPException(status_code=422, detail={"code":"PRETERM_LAYER_REQUIRED","message":str(exc)}) from exc
    except InputValidationError as exc:
        raise HTTPException(status_code=422, detail={"code":"INVALID_INPUT","message":str(exc)}) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail={"code":"SILSO_MISSING","message":str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code":"INVALID_RESEARCH_INPUT","message":str(exc)}) from exc
