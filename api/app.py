from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from profile_engine import compute_profile, UnsupportedGestationError, InputValidationError

app = FastAPI(title="ARCHVIQ API", version="4.0")


@app.get("/api/health")
def health():
    return {"ok": True, "engine": "ARCHVIQ Spiral v4 / Baseline A"}


@app.post("/api/profile")
def profile(payload: dict):
    try:
        gest = payload.get("gestation") or {"mode": "unknown"}
        mode = gest.get("mode", "unknown")
        result = compute_profile(
            str(payload.get("subject_label") or payload.get("name") or "Client"),
            str(payload.get("dob") or ""),
            str(payload.get("sex") or ""),
            str(mode),
            gest.get("conception_to_birth_days"),
            gest.get("conception"),
            gest.get("uncertainty_days"),
        )
        return JSONResponse(result)
    except UnsupportedGestationError as exc:
        raise HTTPException(status_code=422, detail={"code":"PRETERM_LAYER_REQUIRED","message":str(exc)})
    except (InputValidationError, ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail={"code":"INVALID_INPUT","message":str(exc)})
