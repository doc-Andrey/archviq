#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
254D_43_NEW_V3_SEMANTIC_DEDUP.py

Targeted follow-up to 254C.

Observed on 223 previously processed persons:
- legacy X9 effective rank ~1.51/9, PC1 ~0.90, mean |rho| ~0.889;
- 254C X9 effective rank ~3.49/9, PC1 ~0.482, mean |rho| ~0.440.

Thus the global one-dimensional collapse was substantially removed.

Residual pair audit:
- STAB-MAT ~ +0.922: duplicate-like and targeted here;
- SENS-HUB ~ +0.869: duplicate-like and targeted here;
- STAB-LAB ~ -0.801: semantically bipolar, retained rather than artificially
  decorrelated.

This version changes only the contrast forcing definitions needed for those
residual redundancies. SILSO/SSN features, W0-P8 windows, sensitivities,
NO-LAG, stage decay/gain, and the weak coupling graph are unchanged.

No age, sex, cognition, questionnaire, EEG target, or numerical
orthogonalization is used to tune this version.

Engineering geometry prototype only; not biological validation.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import urllib.request
import argparse

BASE = Path.home()

BATCH_INPUT = BASE / "LEMON_EMF/results/eeg/PSYCHOTYP_RUNTIME/43_NEW_V1_254B_BATCH_AUDIT/01_existing_43_persons_batch.csv"
CLEAN_INPUT = BASE / "LEMON_EMF/results/eeg/PSYCHOTYP_RUNTIME/43_CLEAN_RUN/01_persons_input.csv"
DEFAULT_INPUT = BATCH_INPUT if BATCH_INPUT.exists() else CLEAN_INPUT
SSN_READY = BASE / "Downloads/sensitive2_audit/step13b_ssn_dynamic_daily.csv"
SSN_RAW = BASE / "Downloads/ssn_daily_silso.csv"

OUT_DIR = BASE / "LEMON_EMF/results/eeg/PSYCHOTYP_RUNTIME/43_NEW_V3_254D"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_VERSION = "43_NEW_V3_254D_SEMANTIC_DEDUP"
SCHEMA_VERSION = "ARCHVIQ_FINAL_CANONICAL_OUTPUT_V1"

STATE_NAMES = [
    "X_EXC", "X_SENS", "X_STAB", "X_INTEG", "X_FLEX",
    "X_LAB", "X_SEGR", "X_HUB", "X_MAT"
]

WINDOWS = [
    ("W0_implantation_early_axis", "dpc", 0, 17, "prenatal_early"),
    ("W1_neural_tube_foundation", "dpc", 18, 45, "prenatal_core"),
    ("W2_limbic_thalamic_gating", "dpc", 46, 73, "prenatal_core"),
    ("W3_cortical_interface", "dpc", 74, 100, "prenatal_core"),
    ("W4_prenatal_late_101_180", "dpc", 101, 180, "prenatal_late"),
    ("W5_prenatal_late_181_280", "dpc", 181, 280, "prenatal_late"),

    ("N0_birth_1m_sensory_start", "age", 0, 29, "postnatal"),
    ("P1_1_3m_thalamocortical", "age", 30, 89, "postnatal"),
    ("P2_3_6m_alpha_seed", "age", 90, 179, "postnatal"),
    ("P3_6_9m_sensorimotor", "age", 180, 269, "postnatal"),
    ("P4_9_12m_alpha_scaffold", "age", 270, 364, "postnatal"),
    ("P5_12_18m_social_language", "age", 365, 544, "postnatal"),
    ("P6_18_24m_stabilization", "age", 545, 729, "postnatal"),
    ("P7_24_30m_control_growth", "age", 730, 909, "postnatal"),
    ("P8_30_36m_executive_control", "age", 910, 1095, "postnatal"),
]


def safe_name(x):
    return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in str(x))


def ensure_input_template(path):
    if path.exists():
        return

    df = pd.DataFrame([
        {"name": "P1", "dob": "1986-01-27", "context": ""},
        {"name": "P2", "dob": "1982-11-30", "context": ""},
    ])
    df.to_csv(path, index=False)
    print("Input template created:")
    print(path)
    print("Edit this file and run again.")
    raise SystemExit


def download_silso_if_needed():
    if SSN_READY.exists():
        return SSN_READY

    print("Downloading SILSO daily SSN...")
    SSN_READY.parent.mkdir(parents=True, exist_ok=True)
    SSN_RAW.parent.mkdir(parents=True, exist_ok=True)

    url = "https://www.sidc.be/SILSO/DATA/SN_d_tot_V2.0.csv"
    urllib.request.urlretrieve(url, SSN_RAW)

    raw = pd.read_csv(SSN_RAW, sep=";", header=None)

    if raw.shape[1] >= 8:
        raw = raw.iloc[:, :8]
        raw.columns = ["year", "month", "day", "decimal_date", "SSN", "std", "n_obs", "definitive"]
    else:
        raw = raw.iloc[:, :7]
        raw.columns = ["year", "month", "day", "decimal_date", "SSN", "std", "n_obs"]

    raw["date"] = pd.to_datetime(
        dict(year=raw["year"], month=raw["month"], day=raw["day"]),
        errors="coerce"
    )
    raw["SSN"] = pd.to_numeric(raw["SSN"], errors="coerce")

    out = raw[["date", "SSN"]].dropna().copy()
    out = out[out["SSN"] >= 0].sort_values("date")
    out.to_csv(SSN_READY, index=False)

    return SSN_READY


def robust_z(x):
    x = pd.Series(x).astype(float)
    med = x.median()
    mad = (x - med).abs().median()

    if pd.isna(mad) or mad < 1e-9:
        sd = x.std(ddof=0)
        if pd.isna(sd) or sd < 1e-9:
            return pd.Series(np.zeros(len(x)), index=x.index)
        return (x - x.mean()) / sd

    return 0.6745 * (x - med) / mad


def load_ssn():
    path = download_silso_if_needed()
    df = pd.read_csv(path, low_memory=False)

    date_col = [c for c in df.columns if "date" in c.lower()][0]
    ssn_col = [c for c in df.columns if "ssn" in c.lower()][0]

    df = df[[date_col, ssn_col]].copy()
    df.columns = ["date", "SSN"]

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["SSN"] = pd.to_numeric(df["SSN"], errors="coerce")
    df = df.dropna().sort_values("date").drop_duplicates("date")
    df = df[df["SSN"] >= 0].copy()

    df["dSSN"] = df["SSN"].diff().fillna(0)
    df["abs_dSSN"] = df["dSSN"].abs()
    df["d2SSN"] = df["dSSN"].diff().fillna(0)
    df["abs_d2SSN"] = df["d2SSN"].abs()
    df["sign_dSSN"] = np.sign(df["dSSN"])
    df["sign_flip"] = (df["sign_dSSN"].diff().abs() > 0).astype(float)

    df["volatility_7d"] = df["dSSN"].rolling(7, min_periods=2).std().fillna(0)
    df["volatility_14d"] = df["dSSN"].rolling(14, min_periods=3).std().fillna(0)
    df["volatility_21d"] = df["dSSN"].rolling(21, min_periods=5).std().fillna(0)

    df["range_7d"] = (
        df["SSN"].rolling(7, min_periods=2).max()
        - df["SSN"].rolling(7, min_periods=2).min()
    ).fillna(0)

    df["range_21d"] = (
        df["SSN"].rolling(21, min_periods=5).max()
        - df["SSN"].rolling(21, min_periods=5).min()
    ).fillna(0)

    for c in [
        "SSN", "dSSN", "abs_dSSN", "d2SSN", "abs_d2SSN",
        "volatility_7d", "volatility_14d", "volatility_21d",
        "range_7d", "range_21d"
    ]:
        df[c + "_rz"] = robust_z(df[c])

    return df


def load_persons(path):
    ensure_input_template(path)

    df = pd.read_csv(path, low_memory=False)

    if "name" not in df.columns or "dob" not in df.columns:
        raise ValueError("Input CSV must contain columns: name,dob. Optional: context")

    if "context" not in df.columns:
        df["context"] = ""

    df["dob_parsed"] = pd.to_datetime(df["dob"], errors="coerce")
    bad = df[df["dob_parsed"].isna()]

    if len(bad) > 0:
        raise ValueError("Bad DOB rows:\n" + bad.to_string(index=False))

    return df



def make_subject_day(ssn, dob):
    """
    Production NO-LAG rule.
    Conception anchor is fixed at DOB - 280 days. No pre-lag search exists here.
    """
    birth = pd.Timestamp(dob).normalize()
    conception = birth - pd.Timedelta(days=280)

    start = conception
    end = birth + pd.Timedelta(days=1095)

    df = ssn[(ssn["date"] >= start) & (ssn["date"] <= end)].copy()

    df["birth"] = birth
    df["conception"] = conception
    df["dpc"] = (df["date"] - conception).dt.days
    df["age"] = (df["date"] - birth).dt.days

    return df, conception


def peak_energy(x, q=0.85):
    x = pd.Series(x).astype(float).dropna()
    if len(x) == 0:
        return 0.0
    thr = x.quantile(q)
    return float(x[x >= thr].sum())


def count_runs(signs):
    s = pd.Series(signs).replace(0, np.nan).dropna()
    if len(s) == 0:
        return 0
    return int((s != s.shift()).sum())


def max_run_length(signs):
    s = pd.Series(signs).replace(0, np.nan).dropna().values
    if len(s) == 0:
        return 0

    best = 1
    cur = 1

    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1

    return int(best)


def entropy_sign(signs):
    s = pd.Series(signs).replace(0, np.nan).dropna()
    if len(s) == 0:
        return 0.0

    p1 = (s > 0).mean()
    p2 = (s < 0).mean()
    probs = [p for p in [p1, p2] if p > 0]

    return float(-sum(p * np.log2(p) for p in probs))


def window_sensitivity(name):
    if name.startswith("W1"):
        return 1.30
    if name.startswith("W2"):
        return 1.45
    if name.startswith("W3"):
        return 1.55
    if name.startswith("W4") or name.startswith("W5"):
        return 0.85
    if name.startswith("N0") or name.startswith("P"):
        return 0.65
    return 0.30



def extract_signature(subject_day, name, basis, a, b, group):
    """
    Fixed biological window extraction. No post-lag shift.
    """
    if basis == "age":
        a2, b2 = a, b
        g = subject_day[(subject_day["age"] >= a2) & (subject_day["age"] <= b2)].copy()
    else:
        a2, b2 = a, b
        g = subject_day[(subject_day["dpc"] >= a2) & (subject_day["dpc"] <= b2)].copy()

    row = {
        "window": name,
        "basis": basis,
        "stage_group": group,
        "start": a2,
        "end": b2,
        "n_days": len(g),
    }

    if len(g) == 0:
        for c in [
            "impulse", "jerk_burst", "flip_density", "volatility_burst",
            "range_burst", "direction_signature", "dynamic_signature",
            "instability_signature", "cascade_input"
        ]:
            row[c] = np.nan
        return row

    sens = window_sensitivity(name)

    impulse = peak_energy(g["abs_dSSN_rz"].abs(), 0.85) * sens
    jerk = peak_energy(g["abs_d2SSN_rz"].abs(), 0.85) * sens
    vol = peak_energy(g["volatility_21d_rz"].abs(), 0.85) * sens
    rng = peak_energy(g["range_21d_rz"].abs(), 0.85) * sens

    flip = float(g["sign_flip"].sum() / max(len(g), 1)) * sens
    runs = count_runs(g["sign_dSSN"])
    maxrun = max_run_length(g["sign_dSSN"])
    ent = entropy_sign(g["sign_dSSN"])

    up = float(g["dSSN_rz"].max()) * sens
    down = float(g["dSSN_rz"].min()) * sens
    asym = up + down

    dynamic = 0.35 * impulse + 0.30 * jerk + 0.20 * vol + 0.15 * rng

    instability = (
        2.0 * flip
        + 0.8 * ent
        + 0.25 * runs
        - 0.10 * maxrun
        + 0.30 * jerk
    )

    direction = (
        0.60 * asym
        + 0.25 * float(g["dSSN_rz"].sum()) * sens
        + 0.15 * float(g["d2SSN_rz"].sum()) * sens
    )

    row.update({
        "impulse": float(impulse),
        "jerk_burst": float(jerk),
        "flip_density": float(flip),
        "volatility_burst": float(vol),
        "range_burst": float(rng),
        "direction_signature": float(direction),
        "dynamic_signature": float(dynamic),
        "instability_signature": float(instability),
        "cascade_input": float(dynamic + instability + abs(direction)),
    })

    return row



def make_stage_signatures(subject_day):
    return pd.DataFrame([
        extract_signature(subject_day, *w)
        for w in WINDOWS
    ])


def stage_matrices(group):
    if group == "prenatal_early":
        decay = np.array([0.70, 0.68, 0.74, 0.70, 0.76, 0.72, 0.70, 0.70, 0.76])
        gain = np.array([0.09, 0.10, 0.04, 0.07, 0.06, 0.09, 0.08, 0.06, 0.07])
    elif group == "prenatal_core":
        decay = np.array([0.78, 0.76, 0.74, 0.78, 0.80, 0.82, 0.78, 0.80, 0.78])
        gain = np.array([0.13, 0.17, 0.07, 0.11, 0.09, 0.16, 0.12, 0.11, 0.09])
    elif group == "prenatal_late":
        decay = np.array([0.76, 0.72, 0.82, 0.84, 0.80, 0.74, 0.82, 0.80, 0.84])
        gain = np.array([0.07, 0.08, 0.10, 0.13, 0.09, 0.07, 0.11, 0.10, 0.12])
    else:
        decay = np.array([0.72, 0.68, 0.86, 0.84, 0.80, 0.68, 0.82, 0.78, 0.86])
        gain = np.array([0.06, 0.07, 0.12, 0.11, 0.10, 0.06, 0.09, 0.09, 0.11])

    return decay, gain


def _signed_log1p(x):
    x = float(x)
    return float(np.sign(x) * np.log1p(abs(x)))


def _legacy_forcing(row):
    """Exact 43 V1 forcing, retained only for before/after audit."""
    dyn = row["dynamic_signature"]
    inst = row["instability_signature"]
    direction = row["direction_signature"]
    impulse = row["impulse"]
    jerk = row["jerk_burst"]
    flip = row["flip_density"]
    vol = row["volatility_burst"]
    rng = row["range_burst"]

    return np.array([
        dyn + 0.25 * impulse,
        dyn + inst + 0.15 * vol,
        -inst + 0.20 * rng,
        dyn + 0.35 * abs(direction),
        dyn - 0.25 * inst + 0.15 * rng,
        inst + jerk + 1.5 * flip,
        dyn + 0.35 * abs(direction),
        impulse + jerk + 0.25 * vol,
        dyn + rng - 0.20 * inst,
    ], dtype=float)


def _contrast_forcing(row):
    """
    43 NEW V3 targeted semantic de-duplication.

    254C removed the global one-dimensional collapse, but its pair audit showed
    two clear same-direction redundancies:
        X_STAB <-> X_MAT  rho ~ +0.92
        X_SENS <-> X_HUB  rho ~ +0.87

    It also showed strong negative X_STAB <-> X_LAB coupling. That pair is
    semantically bipolar and is NOT forced to become independent.

    V3 therefore changes only the duplicated definitions:

    - X_STAB stays a short/medium-term persistence-vs-instability construct.
    - X_MAT becomes a DEVELOPMENTALLY LATE accumulation construct, using the
      same fixed stage groups already present in engine 43. It is not another
      copy of stability.
    - X_SENS becomes volatility/flip/directional sensitivity.
    - X_HUB becomes concentrated impulse/jerk event recruitment, not generic
      volatility sensitivity.

    No target/test/questionnaire/age/sex information is used.
    No numerical orthogonalization is used.
    """

    dyn = _signed_log1p(row["dynamic_signature"])
    inst = _signed_log1p(row["instability_signature"])
    direction = _signed_log1p(row["direction_signature"])
    impulse = _signed_log1p(row["impulse"])
    jerk = _signed_log1p(row["jerk_burst"])
    flip = _signed_log1p(row["flip_density"])
    vol = _signed_log1p(row["volatility_burst"])
    rng = _signed_log1p(row["range_burst"])
    adir = abs(direction)

    # Existing biological stage labels are used only to distinguish maturation
    # from generic stability. These are fixed a priori in this V3 prototype.
    stage = str(row["stage_group"])
    mat_stage_gain = {
        "prenatal_early": 0.35,
        "prenatal_core": 0.60,
        "prenatal_late": 1.10,
        "postnatal": 1.35,
    }.get(stage, 1.0)

    raw = np.array([
        # X_EXC — signed activation drive.
        0.55 * direction + 0.30 * impulse + 0.15 * dyn,

        # X_SENS — sensitivity to changing/volatile input; jerk moved out.
        0.55 * vol + 0.25 * flip + 0.20 * adir,

        # X_STAB — persistence opposed by instability/lability.
        0.55 * rng + 0.25 * dyn - 0.45 * inst - 0.15 * flip,

        # X_INTEG — distributed coordination, distinct from hub event concentration.
        0.50 * dyn + 0.35 * adir - 0.15 * flip,

        # X_FLEX — switching/adaptive directional change.
        0.45 * flip + 0.30 * adir + 0.20 * jerk - 0.25 * rng,

        # X_LAB — explicit instability/jerk/flip pole.
        0.55 * inst + 0.30 * jerk + 0.20 * flip - 0.20 * rng,

        # X_SEGR — bounded separation / structured range.
        0.50 * rng + 0.25 * adir - 0.35 * dyn - 0.15 * vol,

        # X_HUB — concentrated event recruitment; generic volatility removed.
        0.60 * impulse + 0.30 * jerk + 0.10 * adir - 0.20 * flip,

        # X_MAT — late developmental accumulation, not a stability duplicate.
        mat_stage_gain * (
            0.45 * direction
            + 0.30 * rng
            - 0.30 * flip
            - 0.20 * inst
        ),
    ], dtype=float)

    common = float(np.mean(raw))
    contrast = raw - common
    return contrast, common, raw



def cascade_update_legacy(prev, row):
    """Exact legacy cascade update for audit only."""
    decay, gain = stage_matrices(row["stage_group"])
    forcing = _legacy_forcing(row)

    raw = decay * prev + gain * forcing

    coupling = np.zeros_like(raw)
    coupling[1] += 0.08 * raw[5]
    coupling[2] -= 0.06 * raw[5]
    coupling[3] += 0.05 * raw[7]
    coupling[4] += 0.04 * raw[3] - 0.03 * raw[5]
    coupling[6] += 0.05 * raw[3]
    coupling[7] += 0.04 * raw[1] + 0.03 * raw[6]
    coupling[8] += 0.05 * raw[2] + 0.04 * raw[3]

    new = np.clip(raw + coupling, -50, 50)
    return new, new - prev, float(np.mean(forcing))


def cascade_update_contrast(prev, row):
    """
    Contrast-coded cascade update.

    Stage-specific decay/gain and the existing weak coupling graph are preserved.
    Only the common-mode-dominated forcing vector is changed.
    """
    decay, gain = stage_matrices(row["stage_group"])
    forcing, common, raw_forcing = _contrast_forcing(row)

    raw = decay * prev + gain * forcing

    # Preserve the existing weak coupling graph for this version so we isolate
    # the effect of the forcing redesign. If collapse remains, coupling/stage
    # matrices become the next target, not the windows or SSN extraction.
    coupling = np.zeros_like(raw)
    coupling[1] += 0.08 * raw[5]
    coupling[2] -= 0.06 * raw[5]
    coupling[3] += 0.05 * raw[7]
    coupling[4] += 0.04 * raw[3] - 0.03 * raw[5]
    coupling[6] += 0.05 * raw[3]
    coupling[7] += 0.04 * raw[1] + 0.03 * raw[6]
    coupling[8] += 0.05 * raw[2] + 0.04 * raw[3]

    new = np.clip(raw + coupling, -50, 50)
    return new, new - prev, common


def run_cascade(stage, mode="contrast"):
    state = np.zeros(len(STATE_NAMES))
    rows = []

    for k, row in stage.reset_index(drop=True).iterrows():
        prev = state.copy()

        if mode == "legacy":
            state, delta, common = cascade_update_legacy(prev, row)
        elif mode == "contrast":
            state, delta, common = cascade_update_contrast(prev, row)
        else:
            raise ValueError(f"Unknown cascade mode: {mode}")

        out = {
            "step": k,
            "window": row["window"],
            "stage_group": row["stage_group"],
            "cascade_mode": mode,
            "cascade_input": row["cascade_input"],
            "dynamic_signature": row["dynamic_signature"],
            "instability_signature": row["instability_signature"],
            "direction_signature": row["direction_signature"],
            "GLOBAL_FORCING": float(common),
        }

        for i, name in enumerate(STATE_NAMES):
            out[f"{name}_state"] = float(state[i])
            out[f"{name}_delta"] = float(delta[i])

        rows.append(out)

    return pd.DataFrame(rows)



def project_rs(cascade):
    """
    43 NEW V1 anti-collapse projection.

    The 9 X-states remain the PRIMARY architecture. RS1-RS4 are only
    backward-compatible macrocoordinates.

    Two changes relative to legacy 43:
    1) RS1-RS3 use sparse, differentiated projections.
    2) higher indices no longer recursively reuse an already projected RS axis.

    The original legacy RS formulas are retained as LEGACY_RS* for audit.
    """
    last = cascade.iloc[-1]
    v = {x: float(last[f"{x}_state"]) for x in STATE_NAMES}

    X_EXC = v["X_EXC"]
    X_SENS = v["X_SENS"]
    X_STAB = v["X_STAB"]
    X_INTEG = v["X_INTEG"]
    X_FLEX = v["X_FLEX"]
    X_LAB = v["X_LAB"]
    X_SEGR = v["X_SEGR"]
    X_HUB = v["X_HUB"]
    X_MAT = v["X_MAT"]

    # Exact legacy projections preserved for before/after geometry audit.
    v["LEGACY_RS1_RHYTHM"] = 0.35 * X_STAB + 0.25 * X_MAT - 0.25 * X_LAB + 0.15 * X_EXC
    v["LEGACY_RS2_SYNC"] = 0.35 * X_INTEG + 0.30 * X_HUB + 0.20 * X_MAT - 0.15 * X_LAB
    v["LEGACY_RS3_SEGR"] = 0.45 * X_SEGR + 0.25 * X_STAB + 0.20 * X_MAT - 0.10 * X_FLEX
    v["LEGACY_RS4_INTEGRAL"] = 0.30 * X_INTEG + 0.25 * X_HUB + 0.20 * X_MAT + 0.15 * X_STAB - 0.20 * X_LAB

    # Sparse differentiated V1 macrocoordinates.
    # These are ENGINEERED summaries, not empirical EEG measurements.
    v["RS1_RHYTHM"] = X_STAB - X_LAB + 0.20 * X_MAT
    v["RS2_SYNC"] = X_INTEG + 0.20 * X_HUB - 0.20 * X_LAB
    v["RS3_SEGR"] = X_SEGR + 0.20 * X_STAB - 0.20 * X_FLEX

    # Integral is allowed to depend on multiple independent primary states.
    v["RS4_INTEGRAL"] = (
        X_INTEG + X_HUB + X_MAT + X_STAB + X_FLEX - X_LAB
    ) / 6.0

    # Non-recursive indices: no RS2 inside integrator, no RS3 inside control.
    v["hidden_tension_index"] = X_SENS + X_LAB - X_STAB
    v["creative_integrator_index"] = X_INTEG + X_FLEX + 0.50 * X_HUB
    v["control_compensation_index"] = X_MAT + X_SEGR + 0.50 * X_STAB - X_LAB

    return v


def compute_scores(rs, stage, cascade):
    tension = rs["hidden_tension_index"]
    lab = rs["X_LAB"]
    sens = rs["X_SENS"]
    stab = rs["X_STAB"]
    control = rs["control_compensation_index"]
    rs4 = rs["RS4_INTEGRAL"]
    rs2 = rs["RS2_SYNC"]
    rs1 = rs["RS1_RHYTHM"]
    integ = rs["X_INTEG"]
    hub = rs["X_HUB"]
    mat = rs["X_MAT"]

    architecture_power_score = (
        0.25 * max(rs4, 0)
        + 0.20 * max(rs2, 0)
        + 0.15 * max(integ, 0)
        + 0.15 * max(hub, 0)
        + 0.15 * max(rs["creative_integrator_index"], 0)
        + 0.10 * max(mat, 0)
    )

    pathology_load_score = (
        0.30 * max(tension, 0)
        + 0.25 * max(lab, 0)
        + 0.20 * max(sens, 0)
        + 0.15 * max(-stab, 0)
        + 0.10 * max(-rs1, 0)
    )

    adaptive_control_score = (
        0.35 * max(control, 0)
        + 0.25 * max(rs4, 0)
        + 0.15 * max(mat, 0)
        + 0.15 * max(rs1, 0)
        + 0.10 * max(stab, 0)
    )

    tension_control_ratio = pathology_load_score / max(adaptive_control_score, 1e-9)

    adaptive_stability_score = (
        adaptive_control_score
        + 0.25 * architecture_power_score
        - 0.45 * pathology_load_score
    )

    decompensation_risk_score = (
        pathology_load_score
        + 0.20 * architecture_power_score
        - 0.45 * adaptive_control_score
    )

    high_load_compensation_score = (
        architecture_power_score
        + adaptive_control_score
        - 0.35 * pathology_load_score
    )

    return {
        "architecture_power_score": float(architecture_power_score),
        "pathology_load_score": float(pathology_load_score),
        "adaptive_control_score": float(adaptive_control_score),
        "adaptive_stability_score": float(adaptive_stability_score),
        "decompensation_risk_score": float(decompensation_risk_score),
        "high_load_compensation_score": float(high_load_compensation_score),
        "tension_control_ratio": float(tension_control_ratio),
    }


def raw_synthetic(row):
    return {
        "RawSynth_Openness":
            0.35 * row["creative_integrator_index"]
            + 0.25 * row["X_FLEX"]
            + 0.20 * row["W1_dynamic_signature"]
            + 0.20 * row["W2_instability_signature"],

        "RawSynth_Conscientiousness":
            0.35 * row["control_compensation_index"]
            + 0.25 * row["X_MAT"]
            + 0.20 * row["RS3_SEGR"]
            + 0.20 * row["P7_range_burst"],

        "RawSynth_Extraversion":
            0.35 * row["X_EXC"]
            + 0.25 * row["RS2_SYNC"]
            + 0.20 * row["P2_direction_signature"]
            + 0.20 * row["P4_flip_density"],

        "RawSynth_Agreeableness":
            0.35 * row["P2_range_burst"]
            + 0.20 * row["P1_instability_signature"]
            + 0.20 * row["W3_direction_signature"]
            + 0.25 * (row["X_STAB"] - row["X_LAB"]),

        "RawSynth_Neuroticism":
            0.35 * (-row["W3_direction_signature"])
            + 0.25 * row["hidden_tension_index"]
            + 0.20 * row["X_LAB"]
            + 0.20 * row["W4_direction_signature"],
    }


def stage_wide(stage):
    out = {}
    keep = [
        "impulse", "jerk_burst", "flip_density", "volatility_burst",
        "range_burst", "direction_signature", "dynamic_signature",
        "instability_signature", "cascade_input"
    ]

    for _, r in stage.iterrows():
        prefix = r["window"].split("_")[0]
        for c in keep:
            out[f"{prefix}_{c}"] = r[c]

    return out



def run_one(ssn, person):
    sd, conception = make_subject_day(ssn, person["dob_parsed"])
    stage = make_stage_signatures(sd)

    # Run both cascades on the identical SSN/window signatures.
    legacy_cascade = run_cascade(stage, mode="legacy")
    cascade = run_cascade(stage, mode="contrast")

    rs = project_rs(cascade)
    old = project_rs(legacy_cascade)

    # Exact old-cascade architecture retained for before/after audit.
    for x in STATE_NAMES:
        rs[f"LEGACY_{x}"] = old[x]

    for k in [
        "LEGACY_RS1_RHYTHM", "LEGACY_RS2_SYNC",
        "LEGACY_RS3_SEGR", "LEGACY_RS4_INTEGRAL"
    ]:
        rs[k] = old[k]

    # The removed common mode is retained explicitly rather than hidden inside X1..X9.
    rs["GLOBAL_FORCING_FINAL"] = float(cascade.iloc[-1]["GLOBAL_FORCING"])
    rs["GLOBAL_FORCING_MEAN"] = float(cascade["GLOBAL_FORCING"].mean())
    rs["GLOBAL_FORCING_MAX_ABS"] = float(cascade["GLOBAL_FORCING"].abs().max())

    scores = compute_scores(rs, stage, cascade)

    row = {
        "name": person["name"],
        "dob": str(pd.Timestamp(person["dob_parsed"]).date()),
        "context": person.get("context", ""),
        "engine_version": ENGINE_VERSION,
        "lag_mode": "NO_LAG_FIXED",
        "pre_lag_days": 0,
        "post_lag_days": 0,
        "conception_est": conception.date().isoformat(),
    }

    row.update(rs)
    row.update(scores)
    row.update(stage_wide(stage))

    # Old synthetic Big5 is retained only as a reproducibility diagnostic.
    row.update(raw_synthetic(row))

    return row, stage, cascade, legacy_cascade



def classify_profile(row):
    ratio = row["tension_control_ratio"]
    power = row["architecture_power_score"]
    control = row["adaptive_control_score"]
    pathology = row["pathology_load_score"]
    adapt = row["adaptive_stability_score"]
    risk = row["decompensation_risk_score"]

    if power >= 40 and control >= 15 and ratio <= 1.80:
        return "HIGH_LOAD_COMPENSATED"

    if power >= 35 and control >= 13 and ratio <= 2.00:
        return "HIGH_POWER_TENSION_CONTROLLED"

    if pathology >= 30 and control < 12 and ratio > 2.00:
        return "HIGH_DECOMPENSATION_LOAD"

    if control >= pathology and ratio <= 1.10:
        return "CONTROLLED_STABLE"

    if risk > adapt and ratio > 2.00:
        return "TENSION_DOMINANT"

    return "MIDDLE_COMPENSATED"




CANONICAL_FIELDS = ['subject_id', 'person_id', 'name', 'dob', 'source_layer', 'source_type', 'source_context', 'source_file', 'card_version', 'schema_version', 'evidence_class', 'calibration_status', 'scale_id', 'lag_mode', 'pre_lag_days', 'post_lag_days', 'CARD_STATUS', 'MECH_M1_STATUS', 'MECH_M1_N_DIM', 'MECH_M1_ORIENTATION_STATUS', 'MECH_M1_ANCHORED_AXIS', 'MECH_M1_ANCHORED_SCORE', 'MECH_M1_VECTOR_REF', 'MECH_M2_STATUS', 'MECH_M2_N_DIM', 'MECH_M2_ORIENTATION_STATUS', 'MECH_M2_ANCHORED_AXIS', 'MECH_M2_ANCHORED_SCORE', 'MECH_M2_VECTOR_REF', 'MECH_M3_STATUS', 'MECH_M3_N_DIM', 'MECH_M3_ORIENTATION_STATUS', 'MECH_M3_ANCHORED_AXIS', 'MECH_M3_ANCHORED_SCORE', 'MECH_M3_VECTOR_REF', 'MECH_M4_STATUS', 'MECH_M4_N_DIM', 'MECH_M4_ORIENTATION_STATUS', 'MECH_M4_ANCHORED_AXIS', 'MECH_M4_ANCHORED_SCORE', 'MECH_M4_VECTOR_REF', 'MECH_M5_STATUS', 'MECH_M5_N_DIM', 'MECH_M5_ORIENTATION_STATUS', 'MECH_M5_ANCHORED_AXIS', 'MECH_M5_ANCHORED_SCORE', 'MECH_M5_VECTOR_REF', 'MECH_M6_STATUS', 'MECH_M6_N_DIM', 'MECH_M6_ORIENTATION_STATUS', 'MECH_M6_ANCHORED_AXIS', 'MECH_M6_ANCHORED_SCORE', 'MECH_M6_VECTOR_REF', 'MECH_M7_STATUS', 'MECH_M7_N_DIM', 'MECH_M7_ORIENTATION_STATUS', 'MECH_M7_ANCHORED_AXIS', 'MECH_M7_ANCHORED_SCORE', 'MECH_M7_VECTOR_REF', 'MECH_M8_STATUS', 'MECH_M8_N_DIM', 'MECH_M8_ORIENTATION_STATUS', 'MECH_M8_ANCHORED_AXIS', 'MECH_M8_ANCHORED_SCORE', 'MECH_M8_VECTOR_REF', 'MECH_M9_STATUS', 'MECH_M9_N_DIM', 'MECH_M9_ORIENTATION_STATUS', 'MECH_M9_ANCHORED_AXIS', 'MECH_M9_ANCHORED_SCORE', 'MECH_M9_VECTOR_REF', 'COG_SPEED', 'COG_RT_STABILITY', 'COG_RESPONSE_ACCURACY', 'COG_WORKING_MEMORY', 'COG_INTERFERENCE_CONTROL', 'COG_INTERFERENCE_COST_RAW', 'COG_COMPLEX_ACCURACY', 'COG_COMPLEX_SPEED', 'COG_COMPLEX_STABILITY', 'COG_COMPLEX_RULE_INTEGRATION', 'COG_PRESSURE_COST_RAW', 'COG_PRESSURE_RESILIENCE', 'COG_EXECUTIVE', 'COG_GLOBAL', 'COG_ATTENTION_CONTROL', 'COG_SWITCHING_EFFICIENCY', 'COG_REASONING_INTEGRATION', 'COG_MEMORY_INTEGRATION', 'COG_FLUENCY_ACCESS', 'COG_CRYSTALLIZED_KNOWLEDGE', 'COG_LEARNING_SLOPE', 'COG_MEMORY_CONSOLIDATION', 'COG_FORGETTING_RISK', 'COG_RETRIEVAL_STABILITY', 'COG_VALIDITY_SCORE', 'COG_VALIDITY_FLAGS', 'SELF_BIG5_N', 'SELF_BIG5_E', 'SELF_BIG5_O', 'SELF_BIG5_A', 'SELF_BIG5_C', 'SELF_EMO_ANXIETY', 'SELF_EMO_STRESS', 'SELF_BODY_TENSION', 'SELF_EMO_IMPULSIVITY', 'SELF_REWARD_DRIVE', 'SELF_INHIBITION_SENSITIVITY', 'SELF_REG_REAPPRAISAL', 'SELF_REG_SUPPRESSION', 'SELF_REG_RUMINATION', 'SELF_REG_CATASTROPHIZING', 'SELF_REG_PLANNING', 'SELF_REG_AVOIDANCE', 'SELF_REG_ADAPTIVE', 'SELF_REG_MALADAPTIVE', 'SELF_REG_BALANCE', 'SELF_SOCIAL_SUPPORT', 'SELF_ALEXITHYMIA', 'SELF_EMOTIONAL_CLARITY', 'SELF_EMO_LOAD_GLOBAL', 'SELF_CONTROL_PROFILE', 'SELF_ACTIVATION_PROFILE', 'QUESTIONNAIRE_VALIDITY', 'B5_O1_COGNITIVE_OPENNESS', 'B5_O2_FLEXIBILITY_REAPPRAISAL', 'B5_C1_CONTROL_PLANNING', 'B5_C2_STABILITY_PERSISTENCE', 'B5_E1_SOCIAL_ENERGY', 'B5_E2_POSITIVE_ACTIVATION', 'B5_A1_EMPATHY_SUPPORT', 'B5_A2_CONFLICT_LOW_AGGRESSION', 'B5_N1_ANXIETY_TENSION', 'B5_N2_IMPULSIVITY_INSTABILITY', 'ARCH_PROFILE_CLASS', 'ARCH_RHYTHM_STABILITY', 'ARCH_SYNCHRONY', 'ARCH_SEGREGATION', 'ARCH_INTEGRATION', 'ARCH_EXCITABILITY', 'ARCH_SENSITIVITY', 'ARCH_STABILITY', 'ARCH_FLEXIBILITY', 'ARCH_LABILITY', 'ARCH_HUBNESS', 'ARCH_MATURATION', 'ARCH_POWER', 'ARCH_OVERLOAD', 'ARCH_ADAPTIVE_RESERVE', 'ARCH_DECOMPENSATION_RISK', 'PROC_ATTENTION_CONTROL', 'PROC_ATTENTION_VARIABILITY', 'PROC_WORKING_MEMORY_COST', 'PROC_SWITCHING_COST', 'PROC_COGNITIVE_FLEXIBILITY', 'PROC_PROCESSING_SPEED_STABILITY', 'PROC_CONFLICT_COST', 'PROC_VERBAL_FLEXIBILITY', 'PROC_VERBAL_RIGIDITY', 'PROC_LEARNING_SLOPE', 'PROC_MEMORY_CONSOLIDATION', 'PROC_FORGETTING_RISK', 'PROC_RETRIEVAL_RIGIDITY', 'REG_LOAD', 'REG_RESERVE', 'REG_RECOVERY_COST', 'REG_DECOMPENSATION_RISK', 'REG_IMPULSE_CONTROL_GAP', 'REG_THREAT_SENSITIVITY', 'RAW43_RS1_RHYTHM', 'RAW43_RS2_SYNC', 'RAW43_RS3_SEGR', 'RAW43_RS4_INTEGRAL', 'RAW43_X_EXC', 'RAW43_X_SENS', 'RAW43_X_STAB', 'RAW43_X_INTEG', 'RAW43_X_FLEX', 'RAW43_X_LAB', 'RAW43_X_SEGR', 'RAW43_X_HUB', 'RAW43_X_MAT', 'RAW43_PATHOLOGY_LOAD', 'RAW43_ADAPTIVE_CONTROL', 'RAW43_ADAPTIVE_STABILITY', 'RAW43_HIDDEN_TENSION', 'GAP_43_EEG', 'GAP_43_TEST', 'GAP_43_SELF', 'GAP_EEG_TEST', 'GAP_EEG_SELF', 'GAP_TEST_SELF', 'GAP_GLOBAL_MEAN_ABS', 'VALIDATION_CLASS', 'RUPTURE_INDEX', 'COMPENSATION_INDEX', 'GAP_STATUS', 'GAP_SCALE_ID']

COG_FIELDS = ['COG_SPEED', 'COG_RT_STABILITY', 'COG_RESPONSE_ACCURACY', 'COG_WORKING_MEMORY', 'COG_INTERFERENCE_CONTROL', 'COG_INTERFERENCE_COST_RAW', 'COG_COMPLEX_ACCURACY', 'COG_COMPLEX_SPEED', 'COG_COMPLEX_STABILITY', 'COG_COMPLEX_RULE_INTEGRATION', 'COG_PRESSURE_COST_RAW', 'COG_PRESSURE_RESILIENCE', 'COG_EXECUTIVE', 'COG_GLOBAL', 'COG_ATTENTION_CONTROL', 'COG_SWITCHING_EFFICIENCY', 'COG_REASONING_INTEGRATION', 'COG_MEMORY_INTEGRATION', 'COG_FLUENCY_ACCESS', 'COG_CRYSTALLIZED_KNOWLEDGE', 'COG_LEARNING_SLOPE', 'COG_MEMORY_CONSOLIDATION', 'COG_FORGETTING_RISK', 'COG_RETRIEVAL_STABILITY', 'COG_VALIDITY_SCORE', 'COG_VALIDITY_FLAGS']
SELF_FIELDS = ['SELF_BIG5_N', 'SELF_BIG5_E', 'SELF_BIG5_O', 'SELF_BIG5_A', 'SELF_BIG5_C', 'SELF_EMO_ANXIETY', 'SELF_EMO_STRESS', 'SELF_BODY_TENSION', 'SELF_EMO_IMPULSIVITY', 'SELF_REWARD_DRIVE', 'SELF_INHIBITION_SENSITIVITY', 'SELF_REG_REAPPRAISAL', 'SELF_REG_SUPPRESSION', 'SELF_REG_RUMINATION', 'SELF_REG_CATASTROPHIZING', 'SELF_REG_PLANNING', 'SELF_REG_AVOIDANCE', 'SELF_REG_ADAPTIVE', 'SELF_REG_MALADAPTIVE', 'SELF_REG_BALANCE', 'SELF_SOCIAL_SUPPORT', 'SELF_ALEXITHYMIA', 'SELF_EMOTIONAL_CLARITY', 'SELF_EMO_LOAD_GLOBAL', 'SELF_CONTROL_PROFILE', 'SELF_ACTIVATION_PROFILE', 'QUESTIONNAIRE_VALIDITY']
BIG5_10_FIELDS = ['B5_O1_COGNITIVE_OPENNESS', 'B5_O2_FLEXIBILITY_REAPPRAISAL', 'B5_C1_CONTROL_PLANNING', 'B5_C2_STABILITY_PERSISTENCE', 'B5_E1_SOCIAL_ENERGY', 'B5_E2_POSITIVE_ACTIVATION', 'B5_A1_EMPATHY_SUPPORT', 'B5_A2_CONFLICT_LOW_AGGRESSION', 'B5_N1_ANXIETY_TENSION', 'B5_N2_IMPULSIVITY_INSTABILITY']
PROC_FIELDS = ['PROC_ATTENTION_CONTROL', 'PROC_ATTENTION_VARIABILITY', 'PROC_WORKING_MEMORY_COST', 'PROC_SWITCHING_COST', 'PROC_COGNITIVE_FLEXIBILITY', 'PROC_PROCESSING_SPEED_STABILITY', 'PROC_CONFLICT_COST', 'PROC_VERBAL_FLEXIBILITY', 'PROC_VERBAL_RIGIDITY', 'PROC_LEARNING_SLOPE', 'PROC_MEMORY_CONSOLIDATION', 'PROC_FORGETTING_RISK', 'PROC_RETRIEVAL_RIGIDITY']
REG_FIELDS = ['REG_LOAD', 'REG_RESERVE', 'REG_RECOVERY_COST', 'REG_DECOMPENSATION_RISK', 'REG_IMPULSE_CONTROL_GAP', 'REG_THREAT_SENSITIVITY']


def canonical_card_from_43(row):
    """
    Export 43 NEW into the frozen final contract.

    Only fields directly supported by the current 43 engine are populated.
    Cognition/questionnaire/Big5-10 and M1-M9 mechanism predictions remain NA
    until a separately frozen mapper exists.
    """
    card = {k: np.nan for k in CANONICAL_FIELDS}

    card.update({
        "subject_id": safe_name(row["name"]),
        "person_id": safe_name(row["name"]),
        "name": row["name"],
        "dob": row["dob"],
        "source_layer": "SSN43_PRIOR",
        "source_type": "DOB_SSN_DEVELOPMENTAL_PRIOR",
        "source_context": row.get("context", ""),
        "source_file": ENGINE_VERSION,
        "card_version": ENGINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "evidence_class": "ENGINEERED_DEVELOPMENTAL_PRIOR",
        "calibration_status": "UNCALIBRATED_TO_COMMON_SCALE",
        "scale_id": "43_NATIVE_V1",
        "lag_mode": "NO_LAG_FIXED",
        "pre_lag_days": 0,
        "post_lag_days": 0,
        "CARD_STATUS": "43_NEW_PRIOR_ONLY",
    })

    # M1..M9 are NOT fabricated from 43 at this stage.
    for m in range(1, 10):
        card[f"MECH_M{m}_STATUS"] = "NOT_MAPPED_FROM_43_YET"
        card[f"MECH_M{m}_N_DIM"] = np.nan
        card[f"MECH_M{m}_ORIENTATION_STATUS"] = "NA"
        card[f"MECH_M{m}_ANCHORED_AXIS"] = np.nan
        card[f"MECH_M{m}_ANCHORED_SCORE"] = np.nan
        card[f"MECH_M{m}_VECTOR_REF"] = ""

    # Direct primary-state architecture mapping.
    direct = {
        "ARCH_EXCITABILITY": "X_EXC",
        "ARCH_SENSITIVITY": "X_SENS",
        "ARCH_STABILITY": "X_STAB",
        "ARCH_INTEGRATION": "X_INTEG",
        "ARCH_FLEXIBILITY": "X_FLEX",
        "ARCH_LABILITY": "X_LAB",
        "ARCH_SEGREGATION": "X_SEGR",
        "ARCH_HUBNESS": "X_HUB",
        "ARCH_MATURATION": "X_MAT",
    }
    for out_col, raw_col in direct.items():
        card[out_col] = row.get(raw_col, np.nan)

    # Engineered 43 summaries; kept in native units.
    card["ARCH_PROFILE_CLASS"] = row.get("profile_class", "")
    card["ARCH_RHYTHM_STABILITY"] = row.get("RS1_RHYTHM", np.nan)
    card["ARCH_SYNCHRONY"] = row.get("RS2_SYNC", np.nan)
    card["ARCH_POWER"] = row.get("architecture_power_score", np.nan)
    card["ARCH_OVERLOAD"] = row.get("pathology_load_score", np.nan)
    card["ARCH_ADAPTIVE_RESERVE"] = row.get("adaptive_stability_score", np.nan)
    card["ARCH_DECOMPENSATION_RISK"] = row.get("decompensation_risk_score", np.nan)

    # Regulation: only direct pre-existing 43 indices are exposed.
    card["REG_LOAD"] = row.get("pathology_load_score", np.nan)
    card["REG_RESERVE"] = row.get("adaptive_stability_score", np.nan)
    card["REG_DECOMPENSATION_RISK"] = row.get("decompensation_risk_score", np.nan)

    # Native 43 block.
    raw_map = {
        "RAW43_RS1_RHYTHM": "RS1_RHYTHM",
        "RAW43_RS2_SYNC": "RS2_SYNC",
        "RAW43_RS3_SEGR": "RS3_SEGR",
        "RAW43_RS4_INTEGRAL": "RS4_INTEGRAL",
        "RAW43_X_EXC": "X_EXC",
        "RAW43_X_SENS": "X_SENS",
        "RAW43_X_STAB": "X_STAB",
        "RAW43_X_INTEG": "X_INTEG",
        "RAW43_X_FLEX": "X_FLEX",
        "RAW43_X_LAB": "X_LAB",
        "RAW43_X_SEGR": "X_SEGR",
        "RAW43_X_HUB": "X_HUB",
        "RAW43_X_MAT": "X_MAT",
        "RAW43_PATHOLOGY_LOAD": "pathology_load_score",
        "RAW43_ADAPTIVE_CONTROL": "adaptive_control_score",
        "RAW43_ADAPTIVE_STABILITY": "adaptive_stability_score",
        "RAW43_HIDDEN_TENSION": "hidden_tension_index",
    }
    for out_col, raw_col in raw_map.items():
        card[out_col] = row.get(raw_col, np.nan)

    # No common scale yet => all numeric GAP fields stay NA.
    card["GAP_STATUS"] = "UNCALIBRATED"
    card["GAP_SCALE_ID"] = ""

    return card


def _rank_corr(df):
    """
    Spearman without scipy: Pearson correlation of column ranks.
    """
    if df.empty:
        return pd.DataFrame()
    ranks = df.rank(axis=0, method="average")
    return ranks.corr(method="pearson")


def _effective_rank(df):
    X = df.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if X.shape[0] < 2 or X.shape[1] < 1:
        return np.nan, np.nan, np.nan

    # Median impute.
    for j in range(X.shape[1]):
        col = X[:, j]
        finite = np.isfinite(col)
        med = np.nanmedian(col) if finite.any() else 0.0
        col[~finite] = med
        X[:, j] = col

    # Standardize across persons only for geometry audit.
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd < 1e-12] = 1.0
    Z = (X - mu) / sd

    s = np.linalg.svd(Z, full_matrices=False, compute_uv=False)
    power = s ** 2
    if power.sum() <= 0:
        return 0.0, 0.0, 0.0
    p = power / power.sum()
    p = p[p > 0]
    erank = float(np.exp(-(p * np.log(p)).sum()))
    pc1 = float(power[0] / power.sum())
    ratio = float(erank / X.shape[1])
    return erank, ratio, pc1


def geometry_audit(summary, outdir):
    """
    Before/after collapse audit on the same persons.

    This is a geometry diagnostic only. It does not validate biology or psychotype.
    """
    new_x = [c for c in STATE_NAMES if c in summary.columns]
    old_x = [f"LEGACY_{c}" for c in STATE_NAMES if f"LEGACY_{c}" in summary.columns]
    new_rs = [c for c in ["RS1_RHYTHM","RS2_SYNC","RS3_SEGR","RS4_INTEGRAL"] if c in summary.columns]
    old_rs = [c for c in ["LEGACY_RS1_RHYTHM","LEGACY_RS2_SYNC","LEGACY_RS3_SEGR","LEGACY_RS4_INTEGRAL"] if c in summary.columns]

    rows = []
    for label, cols in [
        ("NEW_CONTRAST_X9", new_x),
        ("LEGACY_CASCADE_X9", old_x),
        ("NEW_RS4", new_rs),
        ("LEGACY_FULL_RS4", old_rs),
    ]:
        if not cols:
            continue

        sub = summary[cols].apply(pd.to_numeric, errors="coerce")
        corr = _rank_corr(sub)
        corr.to_csv(outdir / f"GEOMETRY_{label}_SPEARMAN.csv")

        if len(cols) > 1 and not corr.empty:
            arr = corr.to_numpy(dtype=float)
            mask = ~np.eye(len(cols), dtype=bool)
            vals = np.abs(arr[mask])
            max_abs = float(np.nanmax(vals)) if np.isfinite(vals).any() else np.nan
            mean_abs = float(np.nanmean(vals)) if np.isfinite(vals).any() else np.nan
        else:
            max_abs = np.nan
            mean_abs = np.nan

        erank, erank_ratio, pc1 = _effective_rank(sub)


        # Declared semantic bipolar pair. Its strong inverse correlation is not
        # treated as same-direction duplication, but raw metrics remain reported.
        adjusted_mean_abs = mean_abs
        adjusted_max_abs = max_abs
        if label == "NEW_CONTRAST_X9" and len(cols) > 1 and not corr.empty:
            excluded = {
                frozenset(("X_STAB", "X_LAB")),
            }
            kept = []
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    if frozenset((cols[i], cols[j])) in excluded:
                        continue
                    v = corr.iloc[i, j]
                    if np.isfinite(v):
                        kept.append(abs(float(v)))
            if kept:
                adjusted_mean_abs = float(np.mean(kept))
                adjusted_max_abs = float(np.max(kept))
        rows.append({
            "layer": label,
            "n_subjects": len(summary),
            "n_axes": len(cols),
            "effective_rank": erank,
            "effective_rank_ratio": erank_ratio,
            "pc1_variance_fraction": pc1,
            "max_abs_pairwise_spearman": max_abs,
            "mean_abs_pairwise_spearman": mean_abs,
            "max_abs_pairwise_spearman_excluding_declared_bipolar": adjusted_max_abs,
            "mean_abs_pairwise_spearman_excluding_declared_bipolar": adjusted_mean_abs,
            "note": "DIAGNOSTIC_ONLY_NOT_VALIDATION"
        })

    audit = pd.DataFrame(rows)
    audit.to_csv(outdir / "00_GEOMETRY_AUDIT.csv", index=False)

    # Simple before/after decision table.
    def row_for(label):
        z = audit[audit["layer"] == label]
        return z.iloc[0] if len(z) else None

    newr = row_for("NEW_CONTRAST_X9")
    oldr = row_for("LEGACY_CASCADE_X9")

    decision = "INSUFFICIENT_DATA"
    if newr is not None and oldr is not None and len(summary) >= 20:
        improved_rank = newr["effective_rank"] > oldr["effective_rank"]
        lower_pc1 = newr["pc1_variance_fraction"] < oldr["pc1_variance_fraction"]
        lower_mean_rho = newr["mean_abs_pairwise_spearman"] < oldr["mean_abs_pairwise_spearman"]

        if improved_rank and lower_pc1 and lower_mean_rho:
            if (
                newr["effective_rank_ratio"] >= 0.40
                and newr["pc1_variance_fraction"] <= 0.55
                and newr["mean_abs_pairwise_spearman"] <= 0.60
            ):
                decision = "ANTI_COLLAPSE_WORKED_GEOMETRICALLY"
            else:
                decision = "IMPROVED_BUT_STILL_COLLAPSED"
        else:
            decision = "FORCING_REDESIGN_DID_NOT_IMPROVE"

    pd.DataFrame([{
        "decision": decision,
        "n_subjects": len(summary),
        "rule_note": "Engineering geometry diagnostic; thresholds are diagnostic, not biological validation."
    }]).to_csv(outdir / "00B_GEOMETRY_DECISION.csv", index=False)

    return audit, decision



def write_card(pdir, row, stage, cascade, legacy_cascade, canonical_card):
    pdir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([row]).to_csv(pdir / "01_result_43new_native.csv", index=False)
    stage.to_csv(pdir / "02_stage_signatures.csv", index=False)
    cascade.to_csv(pdir / "03_cascade_states_CONTRAST.csv", index=False)
    legacy_cascade.to_csv(pdir / "03B_cascade_states_LEGACY.csv", index=False)
    pd.DataFrame([canonical_card]).to_csv(pdir / "04_final_canonical_card_v1.csv", index=False)

    with open(pdir / f"CARD_{safe_name(row['name'])}.txt", "w", encoding="utf-8") as f:
        f.write("43 NEW V3 — TARGETED SEMANTIC DE-DUP / NO-LAG\n")
        f.write("================================================\n\n")
        f.write(f"Name: {row['name']}\n")
        f.write(f"DOB: {row['dob']}\n")
        f.write(f"Context: {row.get('context','')}\n")
        f.write(f"Engine: {ENGINE_VERSION}\n")
        f.write("mode: NO_LAG_FIXED (0/0; no search)\n\n")

        f.write("PRIMARY 9-STATE ARCHITECTURE\n")
        f.write("----------------------------\n")
        for k in STATE_NAMES:
            f.write(f"{k}: {row[k]:.6f}\n")

        f.write("\nNEW SPARSE MACROCOORDINATES\n")
        f.write("---------------------------\n")
        for k in ["RS1_RHYTHM","RS2_SYNC","RS3_SEGR","RS4_INTEGRAL"]:
            f.write(f"{k}: {row[k]:.6f}\n")

        f.write("\nLEGACY MACROCOORDINATES — AUDIT ONLY\n")
        f.write("------------------------------------\n")
        for k in ["LEGACY_RS1_RHYTHM","LEGACY_RS2_SYNC","LEGACY_RS3_SEGR","LEGACY_RS4_INTEGRAL"]:
            f.write(f"{k}: {row[k]:.6f}\n")

        f.write("\nINDICES\n")
        f.write("-------\n")
        for k in [
            "hidden_tension_index","creative_integrator_index","control_compensation_index",
            "architecture_power_score","pathology_load_score","adaptive_control_score",
            "adaptive_stability_score","decompensation_risk_score",
            "high_load_compensation_score","tension_control_ratio"
        ]:
            f.write(f"{k}: {row[k]:.6f}\n")

        f.write("\nCANONICAL EXPORT\n")
        f.write("----------------\n")
        f.write("M1-M9 prediction from 43: NOT_MAPPED_YET\n")
        f.write("COG/SELF/BIG5-10 from 43: NA until frozen mapper exists\n")
        f.write("GAP: UNCALIBRATED until common scale exists\n")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--outdir", default=str(OUT_DIR))
    args = parser.parse_args()

    input_path = Path(args.input).expanduser()
    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    persons = load_persons(input_path)
    ssn = load_ssn()

    rows = []
    cards = []

    for _, person in persons.iterrows():
        print("RUN:", person["name"])

        row, stage, cascade, legacy_cascade = run_one(ssn, person)
        row["legacy_threshold_profile_class"] = classify_profile(row)
        row["profile_class"] = "UNCALIBRATED_43_NEW_V2"
        rows.append(row)

        canonical = canonical_card_from_43(row)
        cards.append(canonical)

        pdir = outdir / safe_name(person["name"])
        write_card(pdir, row, stage, cascade, legacy_cascade, canonical)

    summary = pd.DataFrame(rows)
    summary.to_csv(outdir / "00_43NEW_NATIVE_SUMMARY.csv", index=False)

    card_df = pd.DataFrame(cards, columns=CANONICAL_FIELDS)
    card_df.to_csv(outdir / "01_FINAL_CANONICAL_CARDS_V1.csv", index=False)

    audit, geometry_decision = geometry_audit(summary, outdir)

    with open(outdir / "SUMMARY_43_NEW_V3.txt", "w", encoding="utf-8") as f:
        f.write("43 NEW V3 — TARGETED SEMANTIC DE-DUP / NO-LAG\n")
        f.write("================================================\n\n")
        f.write(f"engine: {ENGINE_VERSION}\n")
        f.write(f"input: {input_path}\n")
        f.write("lag_mode: NO_LAG_FIXED; pre=0; post=0; no lag search exists in production path\n")
        f.write(f"n: {len(summary)}\n\n")

        f.write("WHAT CHANGED FROM 254C\n")
        f.write("------------\n")
        f.write("1. 254C removed the global one-dimensional collapse: X9 effective rank rose from ~1.51 to ~3.49.\n")
        f.write("2. Pair audit localized residual redundancy to STAB↔MAT and SENS↔HUB.\n")
        f.write("3. STAB↔LAB is retained as an explicit bipolar relationship, not forced independent.\n")
        f.write("4. MAT is redefined as late developmental accumulation rather than another stability proxy.\n")
        f.write("5. HUB is redefined as concentrated impulse/jerk recruitment rather than generic sensitivity.\n")
        f.write("6. SSN features, W0-P8 windows, window sensitivity, decay/gain and coupling graph remain unchanged.\n")
        f.write("7. No numerical orthogonalization and no EEG/test/questionnaire fitting are used.\n")
        f.write("8. Old profile thresholds remain UNCALIBRATED for 43 NEW V3.\n\n")

        f.write("GEOMETRY AUDIT\n")
        f.write("--------------\n")
        if len(audit):
            f.write(audit.to_string(index=False))
        else:
            f.write("No audit rows.")
        f.write("\n\n")

        f.write("NEXT DECISION RULE\n")
        f.write("------------------\n")
        f.write("254D targets only the residual duplicated definitions identified by the 254C pair audit.\n")
        f.write("Do not chase zero correlations. If residual high pairs are semantically expected, freeze geometry; only unexplained same-direction duplication warrants another change.\n")

    print("\nDONE")
    print("====")
    print("ENGINE:", ENGINE_VERSION)
    print("OUT:", outdir)
    print("N:", len(summary))
    print("Open:")
    print(outdir / "SUMMARY_43_NEW_V3.txt")
    print(outdir / "00_GEOMETRY_AUDIT.csv")
    print(outdir / "01_FINAL_CANONICAL_CARDS_V1.csv")




if __name__ == "__main__":
    main()
