#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARCHVIQ — SILSO percentile/context layer v2.0
==============================================

Purpose
-------
Build a subject-specific solar-activity context layer from WDC-SILSO Daily Total
Sunspot Number V2.0 without using mean/max SSN as a direct explanatory feature.

This layer is deliberately separate from the richer ARCHVIQ physical packet layer.
It supplies three contextual observables at Gaussian integration scales sigma=5/7 d:

    level : SN itself (slow solar-cycle context; nuisance/context only)
    dyn   : |ΔSN| on genuinely consecutive observed days
    dyn7  : 7-day rolling SD of SN (>=5 observed days)

For dyn and dyn7 the program reports:
    * historical raw percentile
    * calendar-local percentile (±N days; descriptive only)
    * level-conditioned percentile
    * residual relative to activity-matched historical neighbors
    * robust residual z score

Key safeguards
--------------
1. No interpolation is used to create dynamics. Missing SN remains NaN.
2. level is never converted into a causal architecture score here.
3. Gaussian sigma is an integration scale, NOT a window width.  FWHM=2.355*sigma.
4. Developmental windows are the current ARCHVIQ research windows:
       W1 18-60 dpc, W2 61-100, W3 101-140,
       F1 168-188, F2 189-202, F3 203 dpc to birth.
5. If --packets is supplied, a packet_context.csv is emitted with context variables
   aligned to the existing physical-layer packet rows.  This is intended for later
   merge into the RS4/v4 cascade, not as a replacement for A/V/R/D/B/ACC/JERK/E/J.

Examples
--------
Explicit conception:
    python3 silso_percentile_v2.py SN_d_tot_V2.0.txt \
        --birth 1967-12-19 --conception 1967-04-11 --unc-days 7 \
        --out ANDREY_SILSO_CONTEXT

Back-calculate conception:
    python3 silso_percentile_v2.py SN_d_tot_V2.0.txt \
        --birth 1967-12-19 --ctb-days 252 --unc-days 7 \
        --packets packets_all_shifts.csv --out ANDREY_SILSO_CONTEXT

Notes
-----
This is an experimental research layer.  It does not establish that solar or
geomagnetic variation causes developmental neural effects.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d

VERSION = "2.0"

WINDOWS: List[Tuple[str, int, Optional[int]]] = [
    ("W1", 18, 60),
    ("W2", 61, 100),
    ("W3", 101, 140),
    ("F1", 168, 188),
    ("F2", 189, 202),
    ("F3", 203, None),
]

SIGMAS_DEFAULT = (5.0, 7.0)


def _safe_date(x: str | pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(x).normalize()


def load_silso(path: str | Path) -> pd.Series:
    """Load SILSO Daily Total Sunspot Number V2.0.

    Supports both the official semicolon CSV and whitespace TXT.  The current TXT
    may contain a trailing '*' on provisional rows, so only the first five fields
    are required.  Missing SN (<0) remains NaN.  No interpolation is performed.
    """
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"SILSO file not found: {p}")

    first = ""
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.strip() and not line.lstrip().startswith("#"):
                first = line
                break

    # Parse line-by-line and keep only the first five fields.  This avoids the
    # official TXT format change where provisional rows append a trailing '*',
    # producing 8 fields while finalized rows have 7.
    rows = []
    delim = ";" if ";" in first else None
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [x.strip() for x in line.split(";")] if delim == ";" else line.split()
            if len(parts) < 5:
                continue
            rows.append(parts[:5])
    if not rows:
        raise ValueError("No valid SILSO rows parsed")
    raw = pd.DataFrame(rows, columns=["y", "m", "d", "frac", "SN"])
    y = pd.to_numeric(raw["y"], errors="coerce")
    m = pd.to_numeric(raw["m"], errors="coerce")
    d = pd.to_numeric(raw["d"], errors="coerce")
    sn = pd.to_numeric(raw["SN"], errors="coerce")
    date = pd.to_datetime(dict(year=y, month=m, day=d), errors="coerce")

    df = pd.DataFrame({"date": date, "SN": sn}).dropna(subset=["date"])
    df.loc[df["SN"] < 0, "SN"] = np.nan
    df = df.sort_values("date").drop_duplicates("date", keep="last")

    grid = pd.date_range(df.date.min(), df.date.max(), freq="D")
    s = df.set_index("date")["SN"].reindex(grid).astype(float)
    s.index.name = "date"
    return s


def indicators(sn: pd.Series) -> Dict[str, pd.Series]:
    """Return level, |ΔSN|, and 7-day SD without interpolating dynamics."""
    x = sn.astype(float)

    # diff() on a daily grid is valid only when both current and previous dates were observed.
    prev = x.shift(1)
    dyn = (x - prev).abs().where(x.notna() & prev.notna())

    # Weekly-scale variability; missing days are permitted only up to 2/7.
    dyn7 = x.rolling(7, min_periods=5, center=False).std(ddof=0)

    return {"level": x, "dyn": dyn, "dyn7": dyn7}


def normalized_gaussian(x: pd.Series, sigma: float, min_weight: float = 0.50) -> pd.Series:
    """NaN-aware Gaussian smoothing with explicit normalization by valid-data weight."""
    v = x.to_numpy(dtype=float)
    ok = np.isfinite(v)
    num = gaussian_filter1d(np.where(ok, v, 0.0), sigma=float(sigma), mode="nearest")
    den = gaussian_filter1d(ok.astype(float), sigma=float(sigma), mode="nearest")
    out = np.divide(num, np.maximum(den, 1e-12), out=np.full_like(num, np.nan), where=den >= min_weight)
    return pd.Series(out, index=x.index, name=x.name)


def ecdf_percentile(values: pd.Series, ref_mask: pd.Series) -> pd.Series:
    """Historical percentile of every value against a fixed reference population."""
    base = values[ref_mask & values.notna()].to_numpy(dtype=float)
    base = np.sort(base[np.isfinite(base)])
    if len(base) < 100:
        raise RuntimeError(f"Historical reference too small: n={len(base)}")
    arr = values.to_numpy(dtype=float)
    pct = np.full(len(arr), np.nan)
    good = np.isfinite(arr)
    pct[good] = 100.0 * np.searchsorted(base, arr[good], side="right") / len(base)
    return pd.Series(pct, index=values.index)


def calendar_local_percentile(values: pd.Series, dates: Iterable[pd.Timestamp], local_days: int = 365) -> Dict[pd.Timestamp, float]:
    """Percentile within ±local_days around each target date.

    This is a descriptive calendar-local comparator, not the primary activity-level
    correction.  It deliberately does not claim to remove cycle phase perfectly.
    """
    out: Dict[pd.Timestamp, float] = {}
    for t in dates:
        t = _safe_date(t)
        if t not in values.index or not np.isfinite(values.loc[t]):
            out[t] = np.nan
            continue
        w = values.loc[t - pd.Timedelta(days=local_days): t + pd.Timedelta(days=local_days)].dropna().to_numpy(float)
        out[t] = float(100.0 * np.mean(w <= float(values.loc[t]))) if len(w) else np.nan
    return out


class LevelConditioner:
    """Nearest-neighbor activity-level conditioning for one indicator and sigma."""

    def __init__(self, level: pd.Series, feature: pd.Series, ref_mask: pd.Series, k: int = 3000):
        df = pd.DataFrame({"level": level, "feature": feature})
        df = df[ref_mask & df.level.notna() & df.feature.notna()].copy()
        if len(df) < 200:
            raise RuntimeError(f"Too few valid rows for level conditioning: {len(df)}")
        self.k = int(max(100, min(k, len(df))))
        self.levels = df.level.to_numpy(float)
        self.features = df.feature.to_numpy(float)
        order = np.argsort(self.levels)
        self.levels = self.levels[order]
        self.features = self.features[order]

    def evaluate(self, target_level: float, target_feature: float) -> Dict[str, float]:
        if not (np.isfinite(target_level) and np.isfinite(target_feature)):
            return dict(cond_pct=np.nan, local_med=np.nan, perp=np.nan, perp_z=np.nan,
                        neighbor_n=0, level_neighbor_min=np.nan, level_neighbor_max=np.nan)

        n = len(self.levels)
        pos = int(np.searchsorted(self.levels, target_level))
        radius = min(n, max(self.k * 2, self.k + 50))
        lo = max(0, pos - radius // 2)
        hi = min(n, lo + radius)
        lo = max(0, hi - radius)

        cand_idx = np.arange(lo, hi)
        dist = np.abs(self.levels[cand_idx] - target_level)
        if len(cand_idx) > self.k:
            take = np.argpartition(dist, self.k - 1)[: self.k]
            idx = cand_idx[take]
        else:
            idx = cand_idx

        f = self.features[idx]
        l = self.levels[idx]
        f = f[np.isfinite(f)]
        if len(f) < 50:
            return dict(cond_pct=np.nan, local_med=np.nan, perp=np.nan, perp_z=np.nan,
                        neighbor_n=len(f), level_neighbor_min=np.nan, level_neighbor_max=np.nan)

        med = float(np.median(f))
        mad = float(np.median(np.abs(f - med)))
        scale = 1.4826 * mad
        if not np.isfinite(scale) or scale < 1e-12:
            q25, q75 = np.quantile(f, [0.25, 0.75])
            scale = float((q75 - q25) / 1.349) if q75 > q25 else float(np.std(f))
        if not np.isfinite(scale) or scale < 1e-12:
            scale = 1.0

        perp = float(target_feature - med)
        return dict(
            cond_pct=float(100.0 * np.mean(f <= target_feature)),
            local_med=med,
            perp=perp,
            perp_z=float(perp / scale),
            neighbor_n=int(len(f)),
            level_neighbor_min=float(np.min(l)) if len(l) else np.nan,
            level_neighbor_max=float(np.max(l)) if len(l) else np.nan,
        )


def _window_for_dpc(dpc: int, gestation_days: int) -> Optional[str]:
    for name, a, b in WINDOWS:
        end = gestation_days if b is None else b
        if a <= dpc <= end:
            return name
    return None


def _subject_dates(conception: pd.Timestamp, birth: pd.Timestamp) -> pd.DataFrame:
    dates = pd.date_range(conception, birth, freq="D")
    ga = int((birth - conception).days)
    dpc = np.arange(ga + 1, dtype=int)
    return pd.DataFrame({"dpc": dpc, "date": dates, "window": [_window_for_dpc(int(x), ga) for x in dpc]})


def build_smoothed_context(sn: pd.Series, sigmas: Iterable[float], ref_start: pd.Timestamp, ref_end: pd.Timestamp, level_k: int):
    ind = indicators(sn)
    ref_mask = pd.Series((sn.index >= ref_start) & (sn.index <= ref_end), index=sn.index)
    result = {}
    for sigma in sigmas:
        sm = {k: normalized_gaussian(v, sigma) for k, v in ind.items()}
        raw = {k: ecdf_percentile(v, ref_mask) for k, v in sm.items()}
        conditioners = {
            "dyn": LevelConditioner(sm["level"], sm["dyn"], ref_mask, k=level_k),
            "dyn7": LevelConditioner(sm["level"], sm["dyn7"], ref_mask, k=level_k),
        }
        result[float(sigma)] = dict(smoothed=sm, raw_pct=raw, conditioners=conditioners)
    return result


def evaluate_dates(context, sigma: float, dates: List[pd.Timestamp], local_days: int) -> pd.DataFrame:
    ctx = context[float(sigma)]
    sm, raw, conds = ctx["smoothed"], ctx["raw_pct"], ctx["conditioners"]

    local_maps = {k: calendar_local_percentile(sm[k], dates, local_days=local_days) for k in ("level", "dyn", "dyn7")}
    rows = []
    for t in dates:
        t = _safe_date(t)
        row = {"date": t, "sigma": float(sigma)}
        for name in ("level", "dyn", "dyn7"):
            val = float(sm[name].loc[t]) if t in sm[name].index and np.isfinite(sm[name].loc[t]) else np.nan
            rp = float(raw[name].loc[t]) if t in raw[name].index and np.isfinite(raw[name].loc[t]) else np.nan
            row[f"{name}_smooth"] = val
            row[f"{name}_raw_pct"] = rp
            row[f"{name}_local_pct"] = local_maps[name].get(t, np.nan)

        for name in ("dyn", "dyn7"):
            ev = conds[name].evaluate(row["level_smooth"], row[f"{name}_smooth"])
            for key, value in ev.items():
                row[f"{name}_{key}"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def build_daily_runs(context, central_conception: pd.Timestamp, birth: pd.Timestamp, unc_days: int,
                     sigmas: Iterable[float], local_days: int) -> pd.DataFrame:
    all_rows = []
    for shift in range(-unc_days, unc_days + 1):
        c = central_conception + pd.Timedelta(days=shift)
        subj = _subject_dates(c, birth)
        dates = subj.date.tolist()
        for sigma in sigmas:
            e = evaluate_dates(context, sigma, dates, local_days)
            out = subj.merge(e, on="date", how="left")
            out.insert(0, "shift_days", shift)
            out.insert(1, "conception", str(c.date()))
            out.insert(2, "gestation_days", int((birth - c).days))
            all_rows.append(out)
    return pd.concat(all_rows, ignore_index=True)


def build_central_envelope(daily: pd.DataFrame) -> pd.DataFrame:
    central = daily[daily.shift_days == 0].copy()
    metric_cols = [c for c in daily.columns if c.endswith("_pct") or c.endswith("_perp_z") or c.endswith("_perp")]
    rows = []
    for sigma in sorted(central.sigma.unique()):
        c0 = central[central.sigma == sigma].sort_values("dpc")
        # Uncertainty is aligned by developmental day (dpc), because conception is uncertain.
        for _, r in c0.iterrows():
            dpc = int(r.dpc)
            pool = daily[(daily.sigma == sigma) & (daily.dpc == dpc)]
            rec = {
                "sigma": sigma,
                "dpc": dpc,
                "date_central": r.date,
                "window": r.window,
            }
            for m in metric_cols:
                vals = pd.to_numeric(pool[m], errors="coerce").to_numpy(float)
                vals = vals[np.isfinite(vals)]
                rec[m] = r[m]
                rec[m + "_lo"] = float(np.min(vals)) if len(vals) else np.nan
                rec[m + "_hi"] = float(np.max(vals)) if len(vals) else np.nan
            rows.append(rec)
    return pd.DataFrame(rows)


def summarize_windows(daily: pd.DataFrame) -> pd.DataFrame:
    """Central-run descriptive summaries for the six developmental windows."""
    c = daily[daily.shift_days == 0].copy()
    metrics = [
        "level_raw_pct", "level_local_pct",
        "dyn_raw_pct", "dyn_local_pct", "dyn_cond_pct", "dyn_perp_z",
        "dyn7_raw_pct", "dyn7_local_pct", "dyn7_cond_pct", "dyn7_perp_z",
    ]
    rows = []
    for sigma in sorted(c.sigma.unique()):
        for window, _, _ in WINDOWS:
            g = c[(c.sigma == sigma) & (c.window == window)]
            if g.empty:
                continue
            rec = {"sigma": sigma, "window": window, "n_days": len(g)}
            for m in metrics:
                vals = pd.to_numeric(g[m], errors="coerce")
                rec[m + "_mean"] = float(vals.mean()) if vals.notna().any() else np.nan
                rec[m + "_median"] = float(vals.median()) if vals.notna().any() else np.nan
                rec[m + "_max"] = float(vals.max()) if vals.notna().any() else np.nan
                rec[m + "_min"] = float(vals.min()) if vals.notna().any() else np.nan
            rows.append(rec)
    return pd.DataFrame(rows)


def align_packet_context(packets_path: str | Path, context, local_days: int) -> pd.DataFrame:
    """Attach contextual SILSO metrics to physical-layer packet rows.

    Uses each packet's own calendar start/end and its width as Gaussian sigma when
    width is 5 or 7.  Existing physical columns are retained, then ctx_* columns are
    appended.  No architecture/cyber score is calculated here.
    """
    p = pd.read_csv(packets_path)
    required = {"date_start", "date_end", "width"}
    missing = required - set(p.columns)
    if missing:
        raise ValueError(f"Packet table lacks required columns: {sorted(missing)}")

    p["date_start"] = pd.to_datetime(p.date_start)
    p["date_end"] = pd.to_datetime(p.date_end)

    # Cache daily evaluations for all needed dates by sigma.
    eval_cache = {}
    for sigma in sorted(pd.to_numeric(p.width, errors="coerce").dropna().unique()):
        sigma = float(sigma)
        if sigma not in context:
            # Context was only prepared for selected sigmas.
            continue
        pp = p[p.width.astype(float) == sigma]
        dates = sorted(set(pd.date_range(pp.date_start.min(), pp.date_end.max(), freq="D")))
        ev = evaluate_dates(context, sigma, dates, local_days).set_index("date")
        eval_cache[sigma] = ev

    context_metrics = [
        "level_smooth", "level_raw_pct", "level_local_pct",
        "dyn_smooth", "dyn_raw_pct", "dyn_local_pct", "dyn_cond_pct", "dyn_perp", "dyn_perp_z",
        "dyn7_smooth", "dyn7_raw_pct", "dyn7_local_pct", "dyn7_cond_pct", "dyn7_perp", "dyn7_perp_z",
    ]

    rows = []
    for _, r in p.iterrows():
        rec = r.to_dict()
        sigma = float(r.width)
        ev = eval_cache.get(sigma)
        if ev is None:
            for m in context_metrics:
                rec["ctx_" + m] = np.nan
                rec["ctx_" + m + "_max"] = np.nan
            rows.append(rec)
            continue
        g = ev.loc[r.date_start:r.date_end]
        for m in context_metrics:
            vals = pd.to_numeric(g[m], errors="coerce") if m in g else pd.Series(dtype=float)
            rec["ctx_" + m] = float(vals.mean()) if len(vals) and vals.notna().any() else np.nan
            rec["ctx_" + m + "_max"] = float(vals.max()) if len(vals) and vals.notna().any() else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def parse_args():
    ap = argparse.ArgumentParser(description="ARCHVIQ SILSO percentile/context layer v2")
    ap.add_argument("silso", help="Official SILSO SN_d_tot_V2.0.txt or .csv")
    ap.add_argument("--birth", required=True, help="Birth date YYYY-MM-DD")
    cg = ap.add_mutually_exclusive_group(required=False)
    cg.add_argument("--conception", help="Explicit central conception date YYYY-MM-DD")
    cg.add_argument("--ctb-days", type=int, default=None, help="Central conception-to-birth days (e.g. 266; known GA supersedes)")
    ap.add_argument("--unc-days", type=int, default=3, help="Conception uncertainty ±days")
    ap.add_argument("--sigmas", type=float, nargs="+", default=list(SIGMAS_DEFAULT), help="Gaussian integration scales in days")
    ap.add_argument("--ref-start", default=None, help="Historical reference start; default=data start")
    ap.add_argument("--ref-end", default=None, help="Historical reference end; default=data end")
    ap.add_argument("--local-days", type=int, default=365, help="Calendar-local comparator half-width")
    ap.add_argument("--level-k", type=int, default=3000, help="Number of activity-matched historical neighbors")
    ap.add_argument("--packets", default=None, help="Optional physical-layer packets_all_shifts.csv")
    ap.add_argument("--out", default="SILSO_CONTEXT_V2", help="Output directory")
    return ap.parse_args()


def main():
    a = parse_args()
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    sn = load_silso(a.silso)
    birth = _safe_date(a.birth)
    if a.conception:
        conception = _safe_date(a.conception)
        ctb_days = int((birth - conception).days)
        conception_source = "explicit"
    else:
        ctb_days = int(a.ctb_days if a.ctb_days is not None else 266)
        conception = birth - pd.Timedelta(days=ctb_days)
        conception_source = f"birth_minus_{ctb_days}_days"

    if conception >= birth:
        raise ValueError("Conception must precede birth")

    ref_start = _safe_date(a.ref_start) if a.ref_start else sn.index.min()
    ref_end = _safe_date(a.ref_end) if a.ref_end else sn.index.max()
    ref_start = max(ref_start, sn.index.min())
    ref_end = min(ref_end, sn.index.max())
    if ref_start >= ref_end:
        raise ValueError("Invalid reference interval")

    sigmas = tuple(float(x) for x in a.sigmas)
    context = build_smoothed_context(sn, sigmas, ref_start, ref_end, level_k=a.level_k)
    daily = build_daily_runs(context, conception, birth, a.unc_days, sigmas, a.local_days)
    envelope = build_central_envelope(daily)
    summary = summarize_windows(daily)

    daily.to_csv(out / "daily_all_shifts.csv", index=False)
    envelope.to_csv(out / "daily_central_envelope.csv", index=False)
    summary.to_csv(out / "window_context_summary.csv", index=False)

    if a.packets:
        packet_ctx = align_packet_context(a.packets, context, a.local_days)
        packet_ctx.to_csv(out / "packet_context.csv", index=False)

    metadata = {
        "engine": "ARCHVIQ SILSO percentile/context layer",
        "version": VERSION,
        "silso_file": str(Path(a.silso).expanduser()),
        "silso_date_start": str(sn.index.min().date()),
        "silso_date_end": str(sn.index.max().date()),
        "birth": str(birth.date()),
        "central_conception": str(conception.date()),
        "conception_source": conception_source,
        "central_conception_to_birth_days": ctb_days,
        "uncertainty_days": int(a.unc_days),
        "gaussian_sigmas_days": list(sigmas),
        "gaussian_fwhm_days": {str(s): 2.354820045 * s for s in sigmas},
        "reference_start": str(ref_start.date()),
        "reference_end": str(ref_end.date()),
        "calendar_local_halfwidth_days": int(a.local_days),
        "level_conditioning_neighbors": int(a.level_k),
        "developmental_windows": [{"name": n, "dpc_start": x, "dpc_end": y if y is not None else "birth"} for n, x, y in WINDOWS],
        "interpretation_guardrails": [
            "level is context/nuisance only, not a causal architecture feature",
            "no interpolation is used to manufacture daily dynamics",
            "dyn/dyn7 level-conditioned outputs are primary for activity-amplitude control",
            "calendar-local percentile is descriptive and not equivalent to causal phase removal",
            "this layer does not establish EMF-to-neurodevelopment causality",
        ],
        "outputs": [
            "daily_all_shifts.csv",
            "daily_central_envelope.csv",
            "window_context_summary.csv",
        ] + (["packet_context.csv"] if a.packets else []),
    }
    with (out / "metadata.json").open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)

    print("ARCHVIQ SILSO percentile/context layer v2.0")
    print(f"SILSO: {sn.index.min().date()} .. {sn.index.max().date()}")
    print(f"Subject: conception {conception.date()} -> birth {birth.date()} ({ctb_days} d central)")
    print(f"Reference: {ref_start.date()} .. {ref_end.date()}")
    print(f"Sigma: {sigmas}; uncertainty ±{a.unc_days} d")
    print(f"Output: {out.resolve()}")
    if a.packets:
        print("packet_context.csv: written")


if __name__ == "__main__":
    main()
