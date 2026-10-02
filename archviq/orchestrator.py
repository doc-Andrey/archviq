from __future__ import annotations

import hashlib
import json
import gzip
import pickle
from functools import lru_cache
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd

from .contracts import ProfileRequest, parse_request
from .experimental import experimental_branches
from .interpreter_adapter import interpret_from_frames
from .versions import ENGINE_BUNDLE_VERSION
from .frozen import archviq_silso_physical_layer_v0_1_1 as physical
from .frozen import silso_percentile_v2 as context_v2
from .frozen import archviq_brain_cyber_cascade_v0_2_rs4v4 as cascade

DEFAULT_WIDTHS = (5, 7)
DEFAULT_LEVEL_K = 3000
DEFAULT_CONTEXT_LOCAL_DAYS = 365


class UnsupportedGestationError(ValueError):
    pass


@lru_cache(maxsize=4)
def _cached_physical_resources(silso_path_str: str, widths_key: tuple[int, ...], level_k: int):
    """Load trusted precomputed reference banks bundled with the repository when available.

    No network access is used. If a bundled bank is missing, the exact frozen
    algorithm rebuilds it from the bundled SILSO archive and caches it in memory.
    """
    sp = Path(silso_path_str).resolve()
    ssn = physical.load_silso(sp)
    banks = {}
    for w in widths_key:
        cached = sp.parent / f"physical_reference_bank_w{int(w)}_v01.pkl.gz"
        if cached.is_file():
            with gzip.open(cached, "rb") as fh:
                bank = pickle.load(fh)
            if int(getattr(bank, "width", -1)) != int(w):
                raise RuntimeError(f"Bundled reference bank width mismatch: {cached}")
            banks[int(w)] = bank
        else:
            banks[int(w)] = physical.build_reference_bank(
                ssn, int(w), min_coverage=1.0, level_k=int(level_k)
            )
    return ssn, banks


@lru_cache(maxsize=4)
def _cached_context_resources(silso_path_str: str, sigmas_key: tuple[float, ...], level_k: int):
    """Load trusted precomputed SILSO percentile/context curves from the repository."""
    sp = Path(silso_path_str).resolve()
    cached = sp.parent / "silso_context_reference_v2.pkl.gz"
    if cached.is_file() and tuple(float(x) for x in sigmas_key) == (5.0, 7.0) and int(level_k) == 3000:
        with gzip.open(cached, "rb") as fh:
            return pickle.load(fh)
    sn = context_v2.load_silso(sp)
    ref_start, ref_end = sn.index.min(), sn.index.max()
    ctx = context_v2.build_smoothed_context(sn, sigmas_key, ref_start, ref_end, level_k=int(level_k))
    return sn, ref_start, ref_end, ctx


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        x = float(obj)
        return x if np.isfinite(x) else None
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, pd.DataFrame):
        return [_clean(x) for x in obj.to_dict("records")]
    if isinstance(obj, pd.Series):
        return [_clean(x) for x in obj.tolist()]
    try:
        if pd.isna(obj):
            return None
    except Exception:
        pass
    return obj


def _resolve_conception(req: ProfileRequest) -> tuple[pd.Timestamp, pd.Timestamp, int, int, str]:
    birth = pd.Timestamp(req.dob).normalize()
    g = req.gestation
    unc = int(g.uncertainty_days or 0)
    if g.mode == "conception":
        conception = pd.Timestamp(g.conception).normalize()
        ctb = int((birth - conception).days)
        source = "explicit_conception"
    else:
        ctb = int(g.conception_to_birth_days or 266)
        conception = birth - pd.Timedelta(days=ctb)
        source = "unknown_default_266" if g.mode == "unknown" else "explicit_ctb_days"
    if conception >= birth:
        raise ValueError("conception must precede birth")
    if ctb < 203:
        raise UnsupportedGestationError(
            "Current production cascade requires gestation >=203 dpc because the "
            "PRETERM_EXTRAUTERINE_MATURATION layer is not yet implemented."
        )
    return birth, conception, ctb, unc, source


def _physical_layer(
    silso_path: str | Path,
    birth: pd.Timestamp,
    conception: pd.Timestamp,
    unc_days: int,
    widths: Iterable[int],
    level_k: int,
) -> Dict[str, Any]:
    widths = tuple(sorted({int(x) for x in widths}))
    ssn, banks = _cached_physical_resources(str(Path(silso_path).resolve()), widths, int(level_k))
    frames = [
        physical.run_shift(
            ssn=ssn, birth=birth, conception=conception, shift_days=shift,
            widths=widths, banks=banks, level_k=int(level_k), min_target_coverage=1.0,
        )
        for shift in range(-unc_days, unc_days + 1)
    ]
    all_shifts = pd.concat(frames, ignore_index=True)
    central = all_shifts[all_shifts.shift_days == 0].copy()
    return {
        "ssn": ssn,
        "all_shifts": all_shifts,
        "central": central,
        "envelope": physical.build_envelope(all_shifts),
        "window_summary": physical.window_summary(central),
        "reference_stats": physical.reference_stats(banks),
    }


def _align_packet_context_frame(packets: pd.DataFrame, ctx: Dict[float, Any], local_days: int) -> pd.DataFrame:
    p = packets.copy()
    p["date_start"] = pd.to_datetime(p.date_start)
    p["date_end"] = pd.to_datetime(p.date_end)
    eval_cache: Dict[float, pd.DataFrame] = {}
    for sigma in sorted(pd.to_numeric(p.width, errors="coerce").dropna().unique()):
        sigma = float(sigma)
        if sigma not in ctx:
            continue
        pp = p[p.width.astype(float) == sigma]
        dates = sorted(set(pd.date_range(pp.date_start.min(), pp.date_end.max(), freq="D")))
        eval_cache[sigma] = context_v2.evaluate_dates(ctx, sigma, dates, local_days).set_index("date")

    metrics = [
        "level_smooth", "level_raw_pct", "level_local_pct",
        "dyn_smooth", "dyn_raw_pct", "dyn_local_pct", "dyn_cond_pct", "dyn_perp", "dyn_perp_z",
        "dyn7_smooth", "dyn7_raw_pct", "dyn7_local_pct", "dyn7_cond_pct", "dyn7_perp", "dyn7_perp_z",
    ]
    rows = []
    for _, r in p.iterrows():
        rec = r.to_dict()
        ev = eval_cache.get(float(r.width))
        g = None if ev is None else ev.loc[r.date_start:r.date_end]
        for m in metrics:
            vals = pd.Series(dtype=float) if g is None or m not in g else pd.to_numeric(g[m], errors="coerce")
            rec["ctx_" + m] = float(vals.mean()) if len(vals) and vals.notna().any() else np.nan
            rec["ctx_" + m + "_max"] = float(vals.max()) if len(vals) and vals.notna().any() else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def _context_layer(
    silso_path: str | Path,
    packets: pd.DataFrame,
    birth: pd.Timestamp,
    conception: pd.Timestamp,
    unc_days: int,
    widths: Iterable[int],
    level_k: int,
    local_days: int,
) -> Dict[str, Any]:
    sigmas = tuple(float(x) for x in widths)
    sn, ref_start, ref_end, ctx = _cached_context_resources(
        str(Path(silso_path).resolve()), sigmas, int(level_k)
    )
    daily = context_v2.build_daily_runs(ctx, conception, birth, unc_days, sigmas, local_days)
    return {
        "daily": daily,
        "envelope": context_v2.build_central_envelope(daily),
        "window_summary": context_v2.summarize_windows(daily),
        "packet_context": _align_packet_context_frame(packets, ctx, local_days),
        "reference_start": ref_start,
        "reference_end": ref_end,
    }


def run_archviq(
    request: ProfileRequest | Dict[str, Any],
    *,
    silso_path: str | Path,
    widths: Iterable[int] = DEFAULT_WIDTHS,
    level_k: int = DEFAULT_LEVEL_K,
    context_local_days: int = DEFAULT_CONTEXT_LOCAL_DAYS,
    cascade_config: str | Path | None = None,
    top_packets: int = 5,
) -> Dict[str, Any]:
    """Run the frozen Baseline-A chain in memory and return one site-facing object.

    No subprocess is used.  The public request contains no filesystem path or
    executable option; the server injects the frozen SILSO path/config.
    """
    req = parse_request(request)
    birth, conception, ctb, unc, conception_source = _resolve_conception(req)
    silso_path = Path(silso_path).expanduser().resolve()
    if not silso_path.is_file():
        raise FileNotFoundError(f"Frozen SILSO dataset not found: {silso_path}")

    phys = _physical_layer(silso_path, birth, conception, unc, widths, level_k)
    ctx = _context_layer(silso_path, phys["all_shifts"], birth, conception, unc, widths, level_k, context_local_days)

    # Context v2 remains parallel/experimental in Baseline A.  It is exposed to
    # the site but deliberately NOT fed into cascade weights yet.
    packet_input = phys["all_shifts"].copy()
    cascade.validate_packets(packet_input)
    cfg = cascade.load_config(str(cascade_config) if cascade_config else None)
    cres = cascade.run_model(packet_input, cfg, ablations=[], top_n=max(1, int(top_packets)))
    defs = cascade.parameter_definition_table(cfg)
    interp = interpret_from_frames(
        cres["ensemble"], cres["finals"], defs, cres["trajectory"], cres["brain"],
        subject_label=req.subject_label, top_packets=top_packets,
    )

    processing = {
        "architecture": "RS4/v4 gated recurrent compression spiral",
        "parameters": interp["parameters"],
        "families": interp["families"],
        "h_star_vector": cres["hstar"],
        "formal_spec": cascade.formal_spec_manifest(cfg),
    }
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
                "sha256": _sha256(silso_path),
                "path_exposed_to_client": False,
                "physical_date_start": str(phys["ssn"].date.min().date()),
                "physical_date_end": str(phys["ssn"].date.max().date()),
            },
            "frozen_layers": {
                "physical": physical.VERSION,
                "context": context_v2.VERSION,
                "cascade": cascade.VERSION,
                "interpreter": interp["run_metadata"]["interpreter_version"],
            },
        },
        "windows": _clean(phys["window_summary"]),
        "physical": {
            "central_packets": _clean(phys["central"]),
            "envelope": _clean(phys["envelope"]),
            "reference_stats": _clean(phys["reference_stats"]),
        },
        "silso_context": {
            "status": "EXPERIMENTAL_PARALLEL_INPUT",
            "used_by_cascade": False,
            "reason": "Baseline A keeps SILSO context v2 separate until a new mapping is frozen.",
            "packet_context": _clean(ctx["packet_context"]),
            "window_summary": _clean(ctx["window_summary"]),
        },
        "brain_map": _clean(interp["brain_map"]),
        "processing": _clean(processing),
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


def save_profile(profile: Dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
