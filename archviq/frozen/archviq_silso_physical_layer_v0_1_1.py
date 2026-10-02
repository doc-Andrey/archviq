#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARCHVIQ — SILSO physical layer v0.1
==================================

Purpose
-------
Frozen first layer for the new multilayer developmental-cybernetic engine.
It DOES NOT infer brain structures, cybernetic parameters, personality or disease.
It produces an auditable physical trajectory from daily SILSO SSN:

    SILSO daily series
      -> daily dynamics dSSN / acceleration / jerk
      -> contiguous 5- and/or 7-day developmental packets
      -> dynamic descriptors per packet
      -> RAW historical percentile (same packet width)
      -> level-conditioned local residual ("perp")
      -> level-conditioned percentile
      -> deterministic physical regime / transition labels
      -> uncertainty envelope for conception date

Developmental windows (days post-conception, dpc)
--------------------------------------------------
    W1  18..60
    W2  61..100
    W3 101..140
    F1 168..188
    F2 189..202
    F3 203..birth-1

Important scientific boundary
-----------------------------
Mean/max SSN is NOT used as an explanatory output. Mean SSN level is used only
as a nuisance/conditioning variable so that dynamic features are compared with
historical packets observed at similar activity level.

Dynamic descriptors
-------------------
A      = mean(|dSSN|)
V      = sd(dSSN)
JUMP   = max(|dSSN|)
IMP    = max(dSSN) - min(dSSN)
R      = sign-reversal rate of dSSN
D      = 1 - R  (directional persistence; redundant but interpretable)
B      = sum(dSSN) / sum(|dSSN|), in [-1, 1]
BABS   = |B|
ACC    = mean(|d2SSN|)
JERK   = mean(|d3SSN|)
E      = mean(dSSN^2)

For each feature the program reports:
    *_raw_pct   : percentile vs all complete historical packets of same width
    *_perp      : value - local median among historical packets with similar SSN level
    *_perp_z    : robust local z = perp / (1.4826 * local MAD)
    *_cond_pct  : empirical percentile among the same local level-matched reference

The reference is built from all overlapping historical packets of the same width.
These percentiles describe an empirical distribution, not a p-value; overlapping
historical packets are not statistically independent.

Conception uncertainty
----------------------
If --conception is omitted, central conception = birth - --ctb-days (default 266).
For each shift in [-unc_days, +unc_days], the same dpc packets are re-extracted.
Central rows and min/max percentile envelopes are saved separately.

Outputs
-------
  metadata.json
  reference_stats.csv
  packets_all_shifts.csv
  packets_central.csv
  packets_envelope.csv
  window_summary.csv

Example
-------
python3 archviq_silso_physical_layer_v0_1.py \
    --silso SN_d_tot_V2.0.txt \
    --birth 1969-05-19 \
    --ctb-days 266 \
    --unc-days 7 \
    --widths 5 7 \
    --level-k 3000 \
    --out ARCHVIQ_PHYS_1969_05_19

Exact conception can be supplied:
python3 archviq_silso_physical_layer_v0_1.py \
    --silso SN_d_tot_V2.0.txt \
    --birth 2014-09-02 \
    --conception 2013-12-20 \
    --unc-days 0 \
    --out NIKA_PHYSICAL
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

VERSION = "0.1"
DEFAULT_CTB_DAYS = 266
DEFAULT_WIDTHS = (5, 7)
DEFAULT_LEVEL_K = 3000
DEFAULT_MIN_COVERAGE = 1.0

# Inclusive developmental boundaries in days post-conception.
EARLY_WINDOWS: Tuple[Tuple[str, int, int], ...] = (
    ("W1", 18, 60),
    ("W2", 61, 100),
    ("W3", 101, 140),
)
LATE_FIXED_WINDOWS: Tuple[Tuple[str, int, int], ...] = (
    ("F1", 168, 188),
    ("F2", 189, 202),
)

FEATURES: Tuple[str, ...] = (
    "A", "V", "JUMP", "IMP", "R", "D", "B", "BABS", "ACC", "JERK", "E"
)
MAGNITUDE_FEATURES: Tuple[str, ...] = ("A", "V", "JUMP", "ACC", "JERK", "E")

EPS = 1e-12


@dataclass(frozen=True)
class PacketSpec:
    width: int
    window: str
    packet_index: int
    dpc_start: int
    dpc_end: int


@dataclass
class ReferenceBank:
    width: int
    frame: pd.DataFrame
    sorted_by_level: pd.DataFrame
    all_sorted: Dict[str, np.ndarray]


def _parse_date(x: str) -> pd.Timestamp:
    t = pd.Timestamp(x).normalize()
    if pd.isna(t):
        raise ValueError(f"Invalid date: {x}")
    return t


def load_silso(path: str | Path) -> pd.DataFrame:
    """Load standard SILSO daily-total file or a prepared date/SSN CSV."""
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(p)

    # Try common prepared CSV forms first.
    if p.suffix.lower() == ".csv":
        # 1) named columns
        try:
            df0 = pd.read_csv(p)
            low = {str(c).strip().lower(): c for c in df0.columns}
            date_col = next((low[k] for k in ("date", "datetime") if k in low), None)
            ssn_col = next((low[k] for k in ("ssn", "sunspot", "sunspot_number", "sn") if k in low), None)
            if date_col is not None and ssn_col is not None:
                raw = pd.DataFrame({
                    "date": pd.to_datetime(df0[date_col], errors="coerce"),
                    "SSN": pd.to_numeric(df0[ssn_col], errors="coerce"),
                })
                return _prepare_daily_grid(raw)
        except Exception:
            pass

        # 2) official semicolon CSV without header
        try:
            x = pd.read_csv(p, sep=";", header=None, comment="#", engine="python")
            if x.shape[1] >= 5:
                raw = pd.DataFrame({
                    "date": pd.to_datetime(dict(
                        year=pd.to_numeric(x.iloc[:, 0], errors="coerce"),
                        month=pd.to_numeric(x.iloc[:, 1], errors="coerce"),
                        day=pd.to_numeric(x.iloc[:, 2], errors="coerce"),
                    ), errors="coerce"),
                    "SSN": pd.to_numeric(x.iloc[:, 4], errors="coerce"),
                })
                return _prepare_daily_grid(raw)
        except Exception:
            pass

    # Standard SILSO whitespace TXT. Older/final rows have 7 fields;
    # provisional rows may add an 8th "*" marker.
    x = pd.read_csv(
        p, sep=r"\s+", header=None, comment="#", engine="python",
        names=["year", "month", "day", "decimal_date", "SSN", "std", "n_obs", "provisional"],
    )
    if x.shape[1] < 5:
        raise ValueError(f"Could not parse SILSO file: {p}")
    raw = pd.DataFrame({
        "date": pd.to_datetime(dict(
            year=pd.to_numeric(x.iloc[:, 0], errors="coerce"),
            month=pd.to_numeric(x.iloc[:, 1], errors="coerce"),
            day=pd.to_numeric(x.iloc[:, 2], errors="coerce"),
        ), errors="coerce"),
        "SSN": pd.to_numeric(x.iloc[:, 4], errors="coerce"),
    })
    return _prepare_daily_grid(raw)


def _prepare_daily_grid(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.dropna(subset=["date"]).copy()
    raw["date"] = pd.to_datetime(raw["date"]).dt.normalize()
    raw.loc[pd.to_numeric(raw["SSN"], errors="coerce") < 0, "SSN"] = np.nan
    raw["SSN"] = pd.to_numeric(raw["SSN"], errors="coerce")
    raw = raw.sort_values("date").drop_duplicates("date", keep="last")
    if raw.empty:
        raise ValueError("No valid SILSO dates found")

    full = pd.DataFrame({"date": pd.date_range(raw.date.min(), raw.date.max(), freq="D")})
    df = full.merge(raw[["date", "SSN"]], on="date", how="left")

    x = df["SSN"].to_numpy(float)
    prev = np.r_[np.nan, x[:-1]]
    valid_pair = np.isfinite(x) & np.isfinite(prev)

    d1 = np.full(len(df), np.nan, float)
    d1[1:] = x[1:] - x[:-1]
    d1[~valid_pair] = np.nan

    d2 = np.r_[np.nan, np.diff(d1)]
    d3 = np.r_[np.nan, np.diff(d2)]

    s = np.sign(d1)
    flip = np.full(len(df), np.nan, float)
    # A valid non-flip transition counts as 0; zero slopes are neutral and do not create flips.
    for i in range(2, len(df)):
        if np.isfinite(s[i]) and np.isfinite(s[i - 1]):
            if s[i] != 0 and s[i - 1] != 0:
                flip[i] = 1.0 if s[i] != s[i - 1] else 0.0
            else:
                flip[i] = 0.0

    df["d1"] = d1
    df["d2"] = d2
    df["d3"] = d3
    df["flip"] = flip
    return df


def _feature_values(g: pd.DataFrame) -> Dict[str, float]:
    """Compute physical descriptors for one calendar packet."""
    d1 = g["d1"].dropna().to_numpy(float)
    d2 = g["d2"].dropna().to_numpy(float)
    d3 = g["d3"].dropna().to_numpy(float)
    flips = g["flip"].dropna().to_numpy(float)

    if len(d1) < 3:
        return {f: np.nan for f in FEATURES}

    abs_sum = float(np.sum(np.abs(d1)))
    r = float(np.mean(flips)) if len(flips) else np.nan
    b = float(np.sum(d1) / abs_sum) if abs_sum > EPS else 0.0

    out = {
        "A": float(np.mean(np.abs(d1))),
        "V": float(np.std(d1, ddof=0)),
        "JUMP": float(np.max(np.abs(d1))),
        "IMP": float(np.max(d1) - np.min(d1)),
        "R": r,
        "D": float(1.0 - r) if np.isfinite(r) else np.nan,
        "B": b,
        "BABS": abs(b),
        "ACC": float(np.mean(np.abs(d2))) if len(d2) else np.nan,
        "JERK": float(np.mean(np.abs(d3))) if len(d3) else np.nan,
        "E": float(np.mean(d1 * d1)),
    }
    return out


def _rolling_reference_frame(ssn: pd.DataFrame, width: int, min_coverage: float = 1.0) -> pd.DataFrame:
    """
    Vectorised same-width historical reference bank.
    Each row is one overlapping calendar packet ending on date_end.
    """
    n = int(width)
    if n < 3:
        raise ValueError("Packet width must be >= 3")

    x = pd.Series(ssn["SSN"].to_numpy(float))
    d1 = pd.Series(ssn["d1"].to_numpy(float))
    d2 = pd.Series(ssn["d2"].to_numpy(float))
    d3 = pd.Series(ssn["d3"].to_numpy(float))
    flip = pd.Series(ssn["flip"].to_numpy(float))

    valid = x.notna().astype(float)
    coverage = valid.rolling(n, min_periods=n).mean()
    level = x.rolling(n, min_periods=n).mean()

    # Dynamic features: min periods intentionally account for derivatives losing
    # one/two/three observations at the very beginning of the entire archive only.
    minp1 = max(3, n - 1)
    minp2 = max(2, n - 2)
    minp3 = max(2, n - 3)

    A = d1.abs().rolling(n, min_periods=minp1).mean()
    V = d1.rolling(n, min_periods=minp1).std(ddof=0)
    JUMP = d1.abs().rolling(n, min_periods=minp1).max()
    IMP = d1.rolling(n, min_periods=minp1).max() - d1.rolling(n, min_periods=minp1).min()
    R = flip.rolling(n, min_periods=minp1).mean()
    D = 1.0 - R
    num = d1.rolling(n, min_periods=minp1).sum()
    den = d1.abs().rolling(n, min_periods=minp1).sum()
    B = num / den.where(den > EPS)
    B = B.fillna(0.0)
    BABS = B.abs()
    ACC = d2.abs().rolling(n, min_periods=minp2).mean()
    JERK = d3.abs().rolling(n, min_periods=minp3).mean()
    E = (d1 * d1).rolling(n, min_periods=minp1).mean()

    frame = pd.DataFrame({
        "date_end": ssn["date"],
        "level": level,
        "coverage": coverage,
        "A": A, "V": V, "JUMP": JUMP, "IMP": IMP,
        "R": R, "D": D, "B": B, "BABS": BABS,
        "ACC": ACC, "JERK": JERK, "E": E,
    })
    frame = frame[(frame["coverage"] >= min_coverage)].dropna(subset=["level", *FEATURES]).reset_index(drop=True)
    if len(frame) < 1000:
        raise RuntimeError(f"Reference bank too small for width={width}: n={len(frame)}")
    return frame


def build_reference_bank(ssn: pd.DataFrame, width: int, min_coverage: float, level_k: int) -> ReferenceBank:
    frame = _rolling_reference_frame(ssn, width, min_coverage=min_coverage)
    sorted_by_level = frame.sort_values("level").reset_index(drop=True)
    all_sorted = {f: np.sort(frame[f].to_numpy(float)) for f in FEATURES}
    return ReferenceBank(width=width, frame=frame, sorted_by_level=sorted_by_level, all_sorted=all_sorted)


def empirical_percentile(value: float, sorted_ref: np.ndarray) -> float:
    if not np.isfinite(value) or len(sorted_ref) == 0:
        return np.nan
    return 100.0 * np.searchsorted(sorted_ref, value, side="right") / len(sorted_ref)


def _level_neighbors(bank: ReferenceBank, level: float, k: int) -> pd.DataFrame:
    """Return k historical packets with closest mean SSN level."""
    a = bank.sorted_by_level
    levels = a["level"].to_numpy(float)
    n = len(a)
    k = int(max(100, min(k, n)))
    pos = int(np.searchsorted(levels, level))

    # Candidate band from both sides, then exact closest-k by absolute level distance.
    lo = max(0, pos - k)
    hi = min(n, pos + k)
    cand = a.iloc[lo:hi].copy()
    if len(cand) <= k:
        return cand
    dist = np.abs(cand["level"].to_numpy(float) - level)
    take = np.argpartition(dist, k - 1)[:k]
    return cand.iloc[np.sort(take)]


def normalize_packet(features: Mapping[str, float], level: float, bank: ReferenceBank, level_k: int) -> Dict[str, float]:
    """RAW and level-conditioned normalization for one target packet."""
    out: Dict[str, float] = {}
    neigh = _level_neighbors(bank, level, level_k)
    out["level_ref_n"] = int(len(neigh))
    out["level_neighbor_min"] = float(neigh["level"].min())
    out["level_neighbor_max"] = float(neigh["level"].max())
    out["level_raw_pct"] = empirical_percentile(level, np.sort(bank.frame["level"].to_numpy(float)))

    for f in FEATURES:
        v = float(features.get(f, np.nan))
        out[f"{f}_raw_pct"] = empirical_percentile(v, bank.all_sorted[f])
        ref = neigh[f].to_numpy(float)
        ref = ref[np.isfinite(ref)]
        if not np.isfinite(v) or len(ref) < 20:
            out[f"{f}_local_med"] = np.nan
            out[f"{f}_perp"] = np.nan
            out[f"{f}_perp_z"] = np.nan
            out[f"{f}_cond_pct"] = np.nan
            continue
        med = float(np.median(ref))
        mad = float(np.median(np.abs(ref - med)))
        scale = 1.4826 * mad
        if scale <= EPS:
            scale = float(np.std(ref, ddof=0))
        if scale <= EPS:
            scale = 1.0
        out[f"{f}_local_med"] = med
        out[f"{f}_perp"] = v - med
        out[f"{f}_perp_z"] = (v - med) / scale
        out[f"{f}_cond_pct"] = 100.0 * np.searchsorted(np.sort(ref), v, side="right") / len(ref)

    mag = np.array([out.get(f"{f}_cond_pct", np.nan) for f in MAGNITUDE_FEATURES], float)
    out["dynamic_load_pct"] = float(np.nanmedian(mag)) if np.isfinite(mag).any() else np.nan
    return out


def classify_regime(row: Mapping[str, float]) -> str:
    """
    Deterministic PHYSICAL regime only. This is not a brain/personality interpretation.
    Thresholds are intentionally simple and visible so later versions can freeze/validate them.
    """
    load = float(row.get("dynamic_load_pct", np.nan))
    r = float(row.get("R", np.nan))
    d = float(row.get("D", np.nan))
    b = abs(float(row.get("B", np.nan)))
    accp = float(row.get("ACC_cond_pct", np.nan))
    jerkp = float(row.get("JERK_cond_pct", np.nan))

    if not np.isfinite(load):
        return "MISSING"
    if load <= 25:
        return "QUIET"
    if np.isfinite(r) and r >= 0.60 and np.nanmedian([accp, jerkp]) >= 60:
        return "REVERSAL_BURST"
    if np.isfinite(d) and d >= 0.75 and b >= 0.45 and load >= 60:
        return "DIRECTED_PERSISTENT_BURST"
    if np.isfinite(d) and d >= 0.75 and b >= 0.35:
        return "PERSISTENT"
    if load >= 75:
        return "BURST"
    if np.isfinite(r) and r >= 0.60:
        return "REVERSAL"
    return "MODERATE"


def developmental_windows(gestation_days: int) -> List[Tuple[str, int, int]]:
    out = [*EARLY_WINDOWS, *LATE_FIXED_WINDOWS]
    # End at birth-1 because birth time is normally unknown and birth-day exposure is partial.
    f3_end = int(gestation_days) - 1
    if f3_end >= 203:
        out.append(("F3", 203, f3_end))
    return out


def packet_specs(gestation_days: int, widths: Sequence[int]) -> List[PacketSpec]:
    specs: List[PacketSpec] = []
    for width in widths:
        for name, a, b in developmental_windows(gestation_days):
            idx = 0
            start = a
            while start + width - 1 <= b:
                specs.append(PacketSpec(width=int(width), window=name, packet_index=idx,
                                        dpc_start=int(start), dpc_end=int(start + width - 1)))
                idx += 1
                start += width
    return specs


def extract_calendar_packet(ssn: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> Tuple[float, Dict[str, float], float]:
    g = ssn[(ssn["date"] >= start) & (ssn["date"] <= end)].copy()
    expected = int((end - start).days + 1)
    if len(g) != expected:
        return np.nan, {f: np.nan for f in FEATURES}, 0.0
    coverage = float(g["SSN"].notna().mean())
    level = float(g["SSN"].mean()) if g["SSN"].notna().any() else np.nan
    return level, _feature_values(g), coverage


def run_shift(
    ssn: pd.DataFrame,
    birth: pd.Timestamp,
    conception: pd.Timestamp,
    shift_days: int,
    widths: Sequence[int],
    banks: Mapping[int, ReferenceBank],
    level_k: int,
    min_target_coverage: float,
) -> pd.DataFrame:
    c = conception + pd.Timedelta(days=int(shift_days))
    gestation_days = int((birth - c).days)
    specs = packet_specs(gestation_days, widths)
    rows: List[Dict[str, object]] = []

    for s in specs:
        start = c + pd.Timedelta(days=s.dpc_start)
        end = c + pd.Timedelta(days=s.dpc_end)
        if end >= birth:
            continue
        level, feat, coverage = extract_calendar_packet(ssn, start, end)
        row: Dict[str, object] = {
            "shift_days": int(shift_days),
            "conception": str(c.date()),
            "gestation_days": gestation_days,
            "width": s.width,
            "window": s.window,
            "packet_index": s.packet_index,
            "dpc_start": s.dpc_start,
            "dpc_end": s.dpc_end,
            "date_start": str(start.date()),
            "date_end": str(end.date()),
            "coverage": coverage,
            "level": level,
        }
        row.update(feat)
        if coverage >= min_target_coverage and np.isfinite(level):
            row.update(normalize_packet(feat, level, banks[s.width], level_k=level_k))
        else:
            for f in FEATURES:
                for suffix in ("raw_pct", "local_med", "perp", "perp_z", "cond_pct"):
                    row[f"{f}_{suffix}"] = np.nan
            row["level_raw_pct"] = np.nan
            row["level_ref_n"] = 0
            row["level_neighbor_min"] = np.nan
            row["level_neighbor_max"] = np.nan
            row["dynamic_load_pct"] = np.nan
        row["regime"] = classify_regime(row)
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["width", "dpc_start", "window"]).reset_index(drop=True)
        df["transition"] = "START"
        for width in sorted(df["width"].unique()):
            ii = df.index[df["width"] == width].tolist()
            prev = None
            for i in ii:
                reg = str(df.at[i, "regime"])
                df.at[i, "transition"] = "START" if prev is None else f"{prev}->{reg}"
                prev = reg
    return df


def build_envelope(all_shifts: pd.DataFrame) -> pd.DataFrame:
    if all_shifts.empty:
        return pd.DataFrame()
    keys = ["width", "window", "packet_index", "dpc_start", "dpc_end"]
    pct_cols = [c for c in all_shifts.columns if c.endswith("_cond_pct") or c.endswith("_raw_pct")]
    extra = ["dynamic_load_pct"]
    agg: Dict[str, List[str]] = {c: ["min", "max", "median"] for c in [*pct_cols, *extra]}
    env = all_shifts.groupby(keys, dropna=False).agg(agg)
    env.columns = [f"{c}_{stat}" for c, stat in env.columns]
    env = env.reset_index()
    return env


def window_summary(central: pd.DataFrame) -> pd.DataFrame:
    if central.empty:
        return pd.DataFrame()
    rows: List[Dict[str, object]] = []
    for (width, window), g in central.groupby(["width", "window"], sort=False):
        row: Dict[str, object] = {
            "width": int(width),
            "window": window,
            "n_packets": int(len(g)),
            "dpc_start": int(g["dpc_start"].min()),
            "dpc_end": int(g["dpc_end"].max()),
            "dynamic_load_pct_median": float(g["dynamic_load_pct"].median()),
            "dynamic_load_pct_max": float(g["dynamic_load_pct"].max()),
            "dynamic_load_pct_min": float(g["dynamic_load_pct"].min()),
            "regime_sequence": " | ".join(g.sort_values("dpc_start")["regime"].astype(str)),
        }
        for f in FEATURES:
            col = f"{f}_cond_pct"
            row[f"{f}_cond_pct_median"] = float(g[col].median())
            row[f"{f}_cond_pct_max"] = float(g[col].max())
        rows.append(row)
    return pd.DataFrame(rows)


def reference_stats(banks: Mapping[int, ReferenceBank]) -> pd.DataFrame:
    rows = []
    for width, bank in sorted(banks.items()):
        row = {
            "width": int(width),
            "n_reference_packets": int(len(bank.frame)),
            "date_end_min": str(bank.frame["date_end"].min().date()),
            "date_end_max": str(bank.frame["date_end"].max().date()),
            "level_min": float(bank.frame["level"].min()),
            "level_median": float(bank.frame["level"].median()),
            "level_max": float(bank.frame["level"].max()),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ARCHVIQ SILSO physical percentile layer v0.1")
    p.add_argument("--silso", required=True, help="Path to SN_d_tot_V2.0.txt/csv")
    p.add_argument("--birth", required=True, help="Birth date YYYY-MM-DD")
    p.add_argument("--conception", default=None, help="Exact/central conception YYYY-MM-DD; otherwise birth-ctb-days")
    p.add_argument("--ctb-days", type=int, default=DEFAULT_CTB_DAYS, help="Central conception-to-birth days when conception unknown")
    p.add_argument("--unc-days", type=int, default=7, help="Conception-date uncertainty +/- days")
    p.add_argument("--widths", type=int, nargs="+", default=list(DEFAULT_WIDTHS), help="Packet widths, default: 5 7")
    p.add_argument("--level-k", type=int, default=DEFAULT_LEVEL_K, help="Nearest historical packets by mean SSN level")
    p.add_argument("--reference-min-coverage", type=float, default=DEFAULT_MIN_COVERAGE)
    p.add_argument("--target-min-coverage", type=float, default=1.0)
    p.add_argument("--out", required=True, help="Output directory")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    widths = tuple(sorted(set(int(w) for w in args.widths)))
    if any(w < 3 for w in widths):
        raise ValueError("All packet widths must be >=3 days")
    if args.unc_days < 0:
        raise ValueError("--unc-days must be >=0")
    if not (0 < args.reference_min_coverage <= 1 and 0 < args.target_min_coverage <= 1):
        raise ValueError("coverage values must be in (0,1]")

    birth = _parse_date(args.birth)
    conception = _parse_date(args.conception) if args.conception else birth - pd.Timedelta(days=int(args.ctb_days))
    central_ga = int((birth - conception).days)
    if central_ga < 203:
        raise ValueError(f"Gestation from conception is only {central_ga} d; F3 cannot be defined")

    outdir = Path(args.out).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"ARCHVIQ SILSO physical layer v{VERSION}")
    print(f"Loading SILSO: {args.silso}")
    ssn = load_silso(args.silso)
    print(f"Archive: {ssn.date.min().date()} .. {ssn.date.max().date()}  rows={len(ssn)}")
    print(f"Birth: {birth.date()}  central conception: {conception.date()}  GA={central_ga} d")

    banks: Dict[int, ReferenceBank] = {}
    for w in widths:
        print(f"Building historical reference bank: {w} d ...", flush=True)
        banks[w] = build_reference_bank(ssn, w, min_coverage=args.reference_min_coverage, level_k=args.level_k)
        print(f"  n={len(banks[w].frame)}")

    shifts = range(-int(args.unc_days), int(args.unc_days) + 1)
    frames = []
    for shift in shifts:
        print(f"Conception shift {shift:+d} d ...", flush=True)
        frames.append(run_shift(
            ssn=ssn,
            birth=birth,
            conception=conception,
            shift_days=shift,
            widths=widths,
            banks=banks,
            level_k=int(args.level_k),
            min_target_coverage=float(args.target_min_coverage),
        ))

    all_shifts = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    central = all_shifts[all_shifts["shift_days"] == 0].copy() if not all_shifts.empty else pd.DataFrame()
    envelope = build_envelope(all_shifts)
    summary = window_summary(central)
    refstats = reference_stats(banks)

    all_shifts.to_csv(outdir / "packets_all_shifts.csv", index=False)
    central.to_csv(outdir / "packets_central.csv", index=False)
    envelope.to_csv(outdir / "packets_envelope.csv", index=False)
    summary.to_csv(outdir / "window_summary.csv", index=False)
    refstats.to_csv(outdir / "reference_stats.csv", index=False)

    meta = {
        "engine": "ARCHVIQ_SILSO_PHYSICAL_LAYER",
        "version": VERSION,
        "birth": str(birth.date()),
        "central_conception": str(conception.date()),
        "central_gestation_days": central_ga,
        "conception_source": "explicit" if args.conception else f"birth_minus_{args.ctb_days}d",
        "unc_days": int(args.unc_days),
        "packet_widths": list(widths),
        "level_k": int(args.level_k),
        "reference_min_coverage": float(args.reference_min_coverage),
        "target_min_coverage": float(args.target_min_coverage),
        "windows_dpc_inclusive": {name: [a, b] for name, a, b in developmental_windows(central_ga)},
        "features": {
            "A": "mean(abs(dSSN))",
            "V": "sd(dSSN)",
            "JUMP": "max(abs(dSSN))",
            "IMP": "max(dSSN)-min(dSSN)",
            "R": "sign reversal rate",
            "D": "1-R directional persistence",
            "B": "sum(dSSN)/sum(abs(dSSN))",
            "BABS": "abs(B)",
            "ACC": "mean(abs(d2SSN))",
            "JERK": "mean(abs(d3SSN))",
            "E": "mean(dSSN^2)",
        },
        "normalization": {
            "raw_pct": "empirical percentile among all complete historical packets of same width",
            "conditioning_variable": "mean SSN level; nuisance only, not explanatory output",
            "local_reference": "k nearest historical packets by mean SSN level",
            "perp": "feature - local median(feature | similar level)",
            "perp_z": "perp / (1.4826 * local MAD)",
            "cond_pct": "empirical percentile of feature within local level-matched reference",
        },
        "scientific_scope": "physical input layer only; no causal EMF, neurobiological, cybernetic, somatic or psychosomatic inference in this version",
    }
    (outdir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nSaved:")
    for fn in ["metadata.json", "reference_stats.csv", "packets_all_shifts.csv", "packets_central.csv", "packets_envelope.csv", "window_summary.csv"]:
        print(" ", outdir / fn)
    if not summary.empty:
        print("\nCentral window summary:")
        print(summary[["width", "window", "n_packets", "dynamic_load_pct_median", "dynamic_load_pct_max", "regime_sequence"]].to_string(index=False))


if __name__ == "__main__":
    main()
