#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ARCHVIQ Engine 43 — v1.0 (NO-LAG)

Purpose
-------
Convert date of birth + daily SILSO sunspot-number series into a transparent,
developmental temporal profile designed to combine with:
- cognitive tests
- questionnaires
- EEG / MRI outcomes

It produces:
1) window-level SSN descriptors,
2) phase summaries,
3) transition descriptors,
4) a compact nonlinear X9-style cascade,
5) functional output scores,
6) conception-date sensitivity estimates.

Core timing and window design
---------------------
Central conception anchor: DOB - 266 days.
Sensitivity anchors: DOB - [252, 259, 266, 273, 280] days.

Prenatal windows relative to conception:
W0  0..17
W1 18..45
W2 46..73
W3 74..100
W4 101..180
W5 181..(birth-1)

Postnatal windows:
N0   0..29 days
P1  30..89
P2  90..179
P3 180..269
P4 270..364
P5 365..544
P6 545..729
P7 730..909
P8 910..1095

Primary window metrics
----------------------
M  mean SSN level
A  activity amplitude = mean(abs(first difference))
V  volatility = std(first difference)
R  reversal / flip rate
D  directional persistence = abs(mean(sign(first difference)))
B  directional bias = mean(sign(first difference))
ACC acceleration magnitude = mean(abs(second difference))
JERK jerk magnitude = mean(abs(third difference))
E  dynamic energy = mean(first difference^2)

No lag optimization. No client-specific outcome fitting.
"""

from __future__ import annotations
import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


ENGINE_VERSION = "ARCHVIQ_43_V1_0_NOLAG"
CENTRAL_GESTATION_DAYS = 266
SENSITIVITY_GESTATION_DAYS = (252, 259, 266, 273, 280)

PRE_WINDOWS = {
    "W0": (0, 17),
    "W1": (18, 45),
    "W2": (46, 73),
    "W3": (74, 100),
    "W4": (101, 180),
}
POST_WINDOWS = {
    "N0": (0, 29),
    "P1": (30, 89),
    "P2": (90, 179),
    "P3": (180, 269),
    "P4": (270, 364),
    "P5": (365, 544),
    "P6": (545, 729),
    "P7": (730, 909),
    "P8": (910, 1095),
}
METRICS = ("M", "A", "V", "R", "D", "B", "ACC", "JERK", "E")


def sigmoid(x):
    x = np.clip(x, -40, 40)
    return 1.0 / (1.0 + np.exp(-x))


def safe_z(x, center, scale):
    if not np.isfinite(x):
        return np.nan
    if not np.isfinite(scale) or scale <= 1e-12:
        return 0.0
    return (x - center) / scale


def robust_center_scale(values: np.ndarray) -> Tuple[float, float]:
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return np.nan, np.nan
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    scale = 1.4826 * mad
    if scale <= 1e-12:
        scale = np.std(values)
    if scale <= 1e-12:
        scale = 1.0
    return float(med), float(scale)


def load_ssn(path: str | Path) -> pd.DataFrame:
    """
    Accepts either:
    - prepared CSV with date + ssn columns, or
    - SILSO SN_d_tot_V2.0.txt whitespace format.

    Returns columns: date, ssn
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        low = {c.lower(): c for c in df.columns}
        date_col = next((low[k] for k in low if k in {"date", "datetime", "day"}), None)
        ssn_col = next((low[k] for k in low if k in {"ssn", "sunspot", "sunspot_number", "sn"}), None)
        if date_col is None:
            # Try year/month/day
            y = next((low[k] for k in low if k in {"year", "yyyy"}), None)
            m = next((low[k] for k in low if k in {"month", "mm"}), None)
            d = next((low[k] for k in low if k in {"day", "dd"}), None)
            if not (y and m and d):
                raise ValueError("CSV must contain date or year/month/day columns.")
            dates = pd.to_datetime(dict(year=df[y], month=df[m], day=df[d]), errors="coerce")
        else:
            dates = pd.to_datetime(df[date_col], errors="coerce")
        if ssn_col is None:
            numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if not numeric:
                raise ValueError("Could not identify SSN column.")
            ssn_col = numeric[-1]
        out = pd.DataFrame({"date": dates, "ssn": pd.to_numeric(df[ssn_col], errors="coerce")})
    else:
        raw = pd.read_csv(path, sep=r"\s+", header=None, names=list(range(8)), comment="#", engine="python")
        if raw.shape[1] < 5:
            raise ValueError("Unexpected SILSO daily file format.")
        dates = pd.to_datetime(dict(year=raw.iloc[:,0], month=raw.iloc[:,1], day=raw.iloc[:,2]), errors="coerce")
        # SILSO daily total SN is typically col 4 (0-index 4)
        out = pd.DataFrame({"date": dates, "ssn": pd.to_numeric(raw.iloc[:,4], errors="coerce")})

    out = out.dropna(subset=["date", "ssn"]).sort_values("date").drop_duplicates("date")
    # SILSO missing sentinel can be -1
    out.loc[out["ssn"] < 0, "ssn"] = np.nan
    return out.reset_index(drop=True)


def window_metrics(values: Iterable[float]) -> Dict[str, float]:
    x = np.asarray(list(values), dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 4:
        return {k: np.nan for k in METRICS}

    d1 = np.diff(x)
    s = np.sign(d1)
    nz = s != 0
    snz = s[nz]

    if len(snz) >= 2:
        flip = np.mean(snz[1:] != snz[:-1])
    else:
        flip = np.nan

    bias = float(np.mean(s)) if len(s) else np.nan
    d2 = np.diff(d1)
    d3 = np.diff(d2)

    return {
        "M": float(np.mean(x)),
        "A": float(np.mean(np.abs(d1))) if len(d1) else np.nan,
        "V": float(np.std(d1, ddof=0)) if len(d1) else np.nan,
        "R": float(flip),
        "D": float(abs(bias)) if np.isfinite(bias) else np.nan,
        "B": bias,
        "ACC": float(np.mean(np.abs(d2))) if len(d2) else np.nan,
        "JERK": float(np.mean(np.abs(d3))) if len(d3) else np.nan,
        "E": float(np.mean(d1**2)) if len(d1) else np.nan,
    }


def slice_ssn(ssn: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> np.ndarray:
    m = (ssn["date"] >= start) & (ssn["date"] <= end)
    return ssn.loc[m, "ssn"].to_numpy(float)


def build_windows(dob: pd.Timestamp, gest_days: int) -> Dict[str, Tuple[pd.Timestamp, pd.Timestamp]]:
    conception = dob - pd.Timedelta(days=gest_days)
    wins = {}
    for name, (a,b) in PRE_WINDOWS.items():
        wins[name] = (conception + pd.Timedelta(days=a),
                      conception + pd.Timedelta(days=b))
    # W5 ends one day before birth, not at fixed dpc 280.
    wins["W5"] = (conception + pd.Timedelta(days=181),
                  dob - pd.Timedelta(days=1))
    for name, (a,b) in POST_WINDOWS.items():
        wins[name] = (dob + pd.Timedelta(days=a),
                      dob + pd.Timedelta(days=b))
    return wins


def extract_for_anchor(ssn: pd.DataFrame, dob: pd.Timestamp, gest_days: int) -> Dict[str, float]:
    out = {}
    wins = build_windows(dob, gest_days)
    for w, (start,end) in wins.items():
        vals = slice_ssn(ssn, start, end)
        met = window_metrics(vals)
        out[f"{w}_N_DAYS"] = float(np.sum(np.isfinite(vals)))
        for k,v in met.items():
            out[f"{w}_{k}"] = v
    return out


def reference_scalers(ssn: pd.DataFrame, n_samples=2500, seed=43) -> Dict[str, Tuple[float,float]]:
    """
    Build robust reference scalers for window metrics from random eligible DOBs
    across the available SSN history. This avoids person-specific normalization.
    """
    rng = np.random.default_rng(seed)
    min_date = ssn["date"].min() + pd.Timedelta(days=CENTRAL_GESTATION_DAYS)
    max_date = ssn["date"].max() - pd.Timedelta(days=1095)
    if max_date <= min_date:
        raise ValueError("SSN series too short for reference calibration.")

    span = (max_date - min_date).days
    dobs = [min_date + pd.Timedelta(days=int(d)) for d in rng.integers(0, span+1, size=n_samples)]

    bucket = {}
    for dob in dobs:
        feats = extract_for_anchor(ssn, dob, CENTRAL_GESTATION_DAYS)
        for k,v in feats.items():
            if k.endswith("_N_DAYS"):
                continue
            bucket.setdefault(k, []).append(v)

    scalers = {}
    for k, vals in bucket.items():
        scalers[k] = robust_center_scale(np.asarray(vals,float))
    return scalers


def zscore_windows(raw: Dict[str,float], scalers: Dict[str,Tuple[float,float]]) -> Dict[str,float]:
    out={}
    for k,v in raw.items():
        if k.endswith("_N_DAYS"):
            out[k]=v
            continue
        c,s = scalers.get(k,(np.nan,np.nan))
        out[k+"_Z"]=safe_z(v,c,s)
    return out


def mean_keys(z: Dict[str,float], windows: List[str], metric: str) -> float:
    vals=[z.get(f"{w}_{metric}_Z", np.nan) for w in windows]
    vals=np.asarray(vals,float)
    return float(np.nanmean(vals)) if np.any(np.isfinite(vals)) else np.nan


def phase_features(z: Dict[str,float]) -> Dict[str,float]:
    early=["W0","W1","W2"]
    late=["W3","W4","W5"]
    post=["N0","P1","P2","P3","P4","P5","P6","P7","P8"]
    out={}
    for phase, ws in [("EARLY_PRE",early),("LATE_PRE",late),("POST",post)]:
        for m in ("M","A","V","R","D","ACC","JERK","E"):
            out[f"{phase}_{m}"]=mean_keys(z,ws,m)

    for m in ("M","A","V","R","D","ACC","JERK","E"):
        out[f"D_EARLY_TO_LATE_{m}"] = out[f"LATE_PRE_{m}"] - out[f"EARLY_PRE_{m}"]
        out[f"D_LATE_TO_POST_{m}"] = out[f"POST_{m}"] - out[f"LATE_PRE_{m}"]

    # Specific transition landmarks
    for a,b in [("W1","W2"),("W2","W3"),("W4","W5"),("W5","N0")]:
        for m in ("M","A","V","R","D","ACC","JERK","E"):
            out[f"{a}_{b}_d{m}"] = z.get(f"{b}_{m}_Z",np.nan) - z.get(f"{a}_{m}_Z",np.nan)
    return out


def x9_cascade(p: Dict[str,float]) -> Dict[str,float]:
    """
    Transparent nonlinear compression.
    Scores are 0..100 latent coordinates, not diagnoses and not validated traits.
    """
    ep=lambda m:p.get(f"EARLY_PRE_{m}",0.0)
    lp=lambda m:p.get(f"LATE_PRE_{m}",0.0)
    po=lambda m:p.get(f"POST_{m}",0.0)

    # Nonlinear latent drives
    exc   = 0.45*po("A") + 0.25*po("E") + 0.20*po("JERK") + 0.10*lp("A")
    sens  = 0.35*ep("V") + 0.25*lp("V") + 0.25*po("R") + 0.15*po("JERK")
    stab  = 0.45*po("D") - 0.30*po("R") - 0.15*po("JERK") + 0.10*lp("D")
    integ = 0.30*po("M") + 0.20*po("D") + 0.20*lp("M") + 0.15*ep("M") - 0.15*po("R")
    flex  = 0.50*po("R") + 0.20*po("V") - 0.20*po("D") + 0.10*lp("R")
    lab   = 0.35*po("R") + 0.30*po("JERK") + 0.20*po("ACC") + 0.15*lp("R")
    segr  = 0.40*po("D") + 0.20*lp("D") - 0.20*po("R") - 0.20*po("JERK")
    hub   = 0.35*po("M") + 0.25*po("E") + 0.20*po("A") + 0.20*lp("M")
    mat   = 0.35*p.get("D_EARLY_TO_LATE_M",0.0) + 0.35*p.get("D_LATE_TO_POST_M",0.0) \
            -0.15*p.get("D_LATE_TO_POST_R",0.0) + 0.15*p.get("D_LATE_TO_POST_D",0.0)

    raw = {
        "X_EXC":exc, "X_SENS":sens, "X_STAB":stab, "X_INTEG":integ,
        "X_FLEX":flex, "X_LAB":lab, "X_SEGR":segr, "X_HUB":hub, "X_MAT":mat
    }
    return {k: float(100*sigmoid(v)) for k,v in raw.items()}


def functional_scores(x: Dict[str,float], p: Dict[str,float]) -> Dict[str,float]:
    """
    Practical 0..100 output coordinates derived from the compact cascade.
    """
    centered={k:(v-50)/12.5 for k,v in x.items()}  # ~rough latent z
    c=lambda k:centered.get(k,0.0)

    resource = 0.35*c("X_HUB")+0.25*c("X_STAB")+0.20*c("X_INTEG")+0.20*c("X_MAT")
    switching = 0.50*c("X_FLEX")+0.25*c("X_LAB")+0.15*c("X_EXC")-0.10*c("X_SEGR")
    lock = 0.45*c("X_STAB")+0.30*c("X_SEGR")+0.20*c("X_INTEG")-0.25*c("X_FLEX")
    novelty = 0.35*c("X_FLEX")+0.30*c("X_EXC")+0.20*c("X_SENS")-0.15*c("X_STAB")
    control = 0.30*c("X_STAB")+0.30*c("X_INTEG")+0.25*c("X_SEGR")-0.20*c("X_LAB")
    processing_cost = 0.40*c("X_LAB")+0.30*c("X_SENS")+0.20*c("X_EXC")-0.20*c("X_STAB")
    maturation = 0.60*c("X_MAT")+0.20*c("X_INTEG")+0.20*c("X_HUB")

    vals={
        "PRED_RESOURCE":resource,
        "PRED_SWITCHING":switching,
        "PRED_LOCK":lock,
        "PRED_NOVELTY":novelty,
        "PRED_CONTROL":control,
        "PRED_PROCESSING_COST":processing_cost,
        "PRED_MATURATION":maturation,
    }
    return {k:float(100*sigmoid(v)) for k,v in vals.items()}


def run_person(ssn, scalers, person_id, dob_str):
    dob=pd.Timestamp(dob_str)

    # central
    raw=extract_for_anchor(ssn,dob,CENTRAL_GESTATION_DAYS)
    z=zscore_windows(raw,scalers)
    phase=phase_features(z)
    x=x9_cascade(phase)
    pred=functional_scores(x,phase)

    out={
        "engine_version":ENGINE_VERSION,
        "person_id":person_id,
        "dob":dob.date().isoformat(),
        "central_gestation_days":CENTRAL_GESTATION_DAYS,
        **raw, **z, **phase, **x, **pred
    }

    # conception sensitivity: rerun same engine across 5 fixed anchors.
    anchor_outputs=[]
    for gd in SENSITIVITY_GESTATION_DAYS:
        ar=extract_for_anchor(ssn,dob,gd)
        az=zscore_windows(ar,scalers)
        ap=phase_features(az)
        ax=x9_cascade(ap)
        apr=functional_scores(ax,ap)
        anchor_outputs.append((gd,ax,apr))

    keys=list(x.keys())+list(pred.keys())
    for k in keys:
        vals=np.array([(xx.get(k) if k in xx else pp.get(k))
                       for _,xx,pp in anchor_outputs],float)
        out[f"{k}_SENS_MEAN"]=float(np.nanmean(vals))
        out[f"{k}_SENS_SD"]=float(np.nanstd(vals))
        out[f"{k}_SENS_RANGE"]=float(np.nanmax(vals)-np.nanmin(vals))

    return out



def load_scalers(path: str | Path) -> Dict[str, Tuple[float,float]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k:(float(v[0]),float(v[1])) for k,v in raw.items()}


def compute_archviq_profile(
    dob: str,
    person_id: str = "client",
    ssn_path: str | Path | None = None,
    scaler_path: str | Path | None = None,
) -> Dict[str, float]:
    """Convenience API used by the ARCHVIQ web application."""
    root = Path(__file__).resolve().parent
    ssn_path = Path(ssn_path) if ssn_path else root / "data" / "SN_d_tot_V2.0.txt"
    scaler_path = Path(scaler_path) if scaler_path else root / "data" / "reference_scalers_v1.json"
    ssn = load_ssn(ssn_path)
    scalers = load_scalers(scaler_path)
    out = run_person(ssn, scalers, person_id, dob)
    alias = {
        "ARCH_RESOURCE":"PRED_RESOURCE",
        "ARCH_SWITCHING":"PRED_SWITCHING",
        "ARCH_LOCK":"PRED_LOCK",
        "ARCH_NOVELTY":"PRED_NOVELTY",
        "ARCH_CONTROL":"PRED_CONTROL",
        "ARCH_PROCESSING_COST":"PRED_PROCESSING_COST",
        "ARCH_MATURATION":"PRED_MATURATION",
    }
    for public_key, internal_key in alias.items():
        out[public_key] = float(out[internal_key])
        out[public_key + "_TIMING_RANGE"] = float(out.get(internal_key + "_SENS_RANGE", 0.0))
        out[public_key + "_TIMING_SD"] = float(out.get(internal_key + "_SENS_SD", 0.0))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ssn",required=True,help="SILSO daily file or prepared CSV")
    ap.add_argument("--input",required=True,help="CSV with person_id,dob")
    ap.add_argument("--out",required=True,help="Output CSV")
    ap.add_argument("--reference-cache",default=None,help="Optional JSON cache for reference scalers")
    ap.add_argument("--reference-samples",type=int,default=2500)
    args=ap.parse_args()

    ssn=load_ssn(args.ssn)
    inp=pd.read_csv(args.input)
    if not {"person_id","dob"}.issubset(inp.columns):
        raise ValueError("Input CSV must contain columns: person_id,dob")

    cache=Path(args.reference_cache) if args.reference_cache else None
    if cache and cache.exists():
        raw_cache=json.loads(cache.read_text(encoding="utf-8"))
        scalers={k:(float(v[0]),float(v[1])) for k,v in raw_cache.items()}
    else:
        print(f"Building historical reference scalers from {args.reference_samples} random DOB anchors...")
        scalers=reference_scalers(ssn,n_samples=args.reference_samples)
        if cache:
            cache.write_text(json.dumps(scalers,ensure_ascii=False,indent=2),encoding="utf-8")

    rows=[]
    for i,r in inp.iterrows():
        rows.append(run_person(ssn,scalers,str(r["person_id"]),str(r["dob"])))
        if (i+1)%25==0 or (i+1)==len(inp):
            print(f"{i+1}/{len(inp)}")

    out=pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(args.out,index=False)
    print(f"WROTE: {args.out}")
    print(f"ROWS: {len(out)}  COLS: {len(out.columns)}")


if __name__=="__main__":
    main()
