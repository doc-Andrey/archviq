from __future__ import annotations

"""Fast site-facing runner for ARCHVIQ Baseline A.

The frozen scientific layers are unchanged.  This wrapper keeps the SILSO dataset
inside the repository, caches invariant historical references in server memory,
and returns a compact object suitable for the Streamlit UI/API.

Important: SILSO context v2 stays parallel/experimental and is not fed into the
frozen RS4/v4 cascade weights.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable
import hashlib

import numpy as np
import pandas as pd

from .contracts import ProfileRequest, parse_request
from .experimental import experimental_branches
from .interpreter_adapter import interpret_from_frames
from .orchestrator import UnsupportedGestationError, _resolve_conception, _clean
from .versions import ENGINE_BUNDLE_VERSION
from .frozen import archviq_silso_physical_layer_v0_1_1 as physical
from .frozen import silso_percentile_v2 as context_v2
from .frozen import archviq_brain_cyber_cascade_v0_2_rs4v4 as cascade

DEFAULT_WIDTHS = (5, 7)
DEFAULT_LEVEL_K = 3000
DEFAULT_CONTEXT_LOCAL_DAYS = 365


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@lru_cache(maxsize=4)
def _resources(silso_path_s: str, widths: tuple[int, ...], level_k: int):
    """Load repository-local SILSO and invariant historical reference banks once."""
    p = Path(silso_path_s).resolve()
    ssn = physical.load_silso(p)
    banks = {
        int(w): physical.build_reference_bank(ssn, int(w), min_coverage=1.0, level_k=int(level_k))
        for w in widths
    }
    sn_ctx = context_v2.load_silso(p)
    ctx = context_v2.build_smoothed_context(
        sn_ctx,
        tuple(float(w) for w in widths),
        sn_ctx.index.min(),
        sn_ctx.index.max(),
        level_k=int(level_k),
    )
    return ssn, banks, sn_ctx, ctx


def _context_central_only(
    ctx,
    conception: pd.Timestamp,
    birth: pd.Timestamp,
    widths: tuple[int, ...],
    local_days: int,
) -> Dict[str, Any]:
    """Experimental context for the central conception only.

    The context layer is not used by the cascade in Baseline A, so site latency is
    reduced by not repeating it over all gestational uncertainty shifts.  The
    physical/cascade layer still performs the full uncertainty ensemble.
    """
    daily = context_v2.build_daily_runs(
        ctx,
        central_conception=conception,
        birth=birth,
        unc_days=0,
        sigmas=tuple(float(w) for w in widths),
        local_days=int(local_days),
    )
    return {
        "window_summary": context_v2.summarize_windows(daily),
        "central_daily": daily,
    }


def run_site_profile(
    request: ProfileRequest | Dict[str, Any],
    *,
    silso_path: str | Path,
    widths: Iterable[int] = DEFAULT_WIDTHS,
    level_k: int = DEFAULT_LEVEL_K,
    context_local_days: int = DEFAULT_CONTEXT_LOCAL_DAYS,
    top_packets: int = 5,
) -> Dict[str, Any]:
    req = parse_request(request)
    birth, conception, ctb, unc, conception_source = _resolve_conception(req)

    p = Path(silso_path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Repository SILSO dataset not found: {p}")

    widths_t = tuple(sorted({int(x) for x in widths}))
    ssn, banks, sn_ctx, ctx = _resources(str(p), widths_t, int(level_k))

    frames = [
        physical.run_shift(
            ssn=ssn,
            birth=birth,
            conception=conception,
            shift_days=shift,
            widths=widths_t,
            banks=banks,
            level_k=int(level_k),
            min_target_coverage=1.0,
        )
        for shift in range(-unc, unc + 1)
    ]
    all_shifts = pd.concat(frames, ignore_index=True)
    central = all_shifts[all_shifts.shift_days == 0].copy()

    cascade.validate_packets(all_shifts)
    cfg = cascade.load_config(None)
    cres = cascade.run_model(all_shifts, cfg, ablations=[], top_n=max(1, int(top_packets)))
    defs = cascade.parameter_definition_table(cfg)
    interp = interpret_from_frames(
        cres["ensemble"], cres["finals"], defs, cres["trajectory"], cres["brain"],
        subject_label=req.subject_label, top_packets=top_packets,
    )

    ctx_site = _context_central_only(ctx, conception, birth, widths_t, context_local_days)
    exp = experimental_branches(interp["parameters"])

    profile = {
        "meta": {
            "engine_bundle_version": ENGINE_BUNDLE_VERSION,
            "subject": {
                "dob": req.dob,
                "sex": req.sex,
                "label": req.subject_label,
                "gestation_mode": req.gestation.mode,
                "central_conception": str(conception.date()),
                "central_conception_to_birth_days": ctb,
                "uncertainty_days": unc,
                "conception_source": conception_source,
            },
            "dataset": {
                "name": "WDC-SILSO Daily Total Sunspot Number V2.0",
                "sha256": _sha256(p),
                "repository_local": True,
                "runtime_download": False,
                "date_start": str(ssn.date.min().date()),
                "date_end": str(ssn.date.max().date()),
            },
            "frozen_layers": {
                "physical": physical.VERSION,
                "context": context_v2.VERSION,
                "cascade": cascade.VERSION,
                "interpreter": interp["run_metadata"]["interpreter_version"],
            },
            "performance_note": "Full gestation uncertainty is used for physical/cascade; experimental SILSO context is central-run only.",
        },
        "windows": _clean(physical.window_summary(central)),
        "physical": {
            "central_packets": _clean(central),
            "envelope": _clean(physical.build_envelope(all_shifts)),
            "reference_stats": _clean(physical.reference_stats(banks)),
        },
        "silso_context": {
            "status": "EXPERIMENTAL_PARALLEL_INPUT",
            "used_by_cascade": False,
            "uncertainty_scope": "central_conception_only_on_site",
            "window_summary": _clean(ctx_site["window_summary"]),
        },
        "brain_map": _clean(interp["brain_map"]),
        "processing": {
            "architecture": "RS4/v4 gated recurrent compression spiral",
            "parameters": _clean(interp["parameters"]),
            "families": _clean(interp["families"]),
            "h_star_vector": _clean(cres["hstar"]),
            "formal_spec": _clean(cascade.formal_spec_manifest(cfg)),
        },
        "uncertainty": _clean(interp["uncertainty_rows"]),
        "site_cards": _clean(interp["site_cards"]),
        "evidence_status": {
            "physical_silso": "MEASURED",
            "packet_percentiles": "MODELED",
            "developmental_cascade": "MODELED",
            "brain_circuit_mapping": "HYPOTHESIZED",
            "processing_interpretation": "EXPERIMENTAL",
            "somatic": "EXPERIMENTAL",
            "psychophysiology": "EXPERIMENTAL",
            "natural_emf_causality": "UNPROVEN",
        },
        "experimental": _clean(exp),
        "report_markdown": interp["report_markdown"],
    }
    return _clean(profile)


__all__ = ["run_site_profile", "UnsupportedGestationError"]
