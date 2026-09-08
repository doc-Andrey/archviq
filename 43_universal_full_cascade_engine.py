import numpy as np
import pandas as pd
from pathlib import Path
import urllib.request
import argparse

BASE = Path.home()

DEFAULT_INPUT = BASE / "LEMON_EMF/results/eeg/PSYCHOTYP_RUNTIME/43_CLEAN_RUN/01_persons_input.csv"
SSN_READY = BASE / "Downloads/sensitive2_audit/step13b_ssn_dynamic_daily.csv"
SSN_RAW = BASE / "Downloads/ssn_daily_silso.csv"

OUT_DIR = BASE / "LEMON_EMF/results/eeg/PSYCHOTYP_RUNTIME/43_CLEAN_RUN"
OUT_DIR.mkdir(parents=True, exist_ok=True)

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


def make_subject_day(ssn, dob, pre_lag):
    birth = pd.Timestamp(dob).normalize()
    conception = birth - pd.Timedelta(days=280) + pd.Timedelta(days=pre_lag)

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


def extract_signature(subject_day, name, basis, a, b, group, post_lag):
    if basis == "age":
        a2 = a + post_lag
        b2 = b + post_lag
        g = subject_day[(subject_day["age"] >= a2) & (subject_day["age"] <= b2)].copy()
    else:
        a2 = a
        b2 = b
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


def make_stage_signatures(subject_day, post_lag):
    return pd.DataFrame([
        extract_signature(subject_day, *w, post_lag)
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


def cascade_update(prev, row):
    decay, gain = stage_matrices(row["stage_group"])

    dyn = row["dynamic_signature"]
    inst = row["instability_signature"]
    direction = row["direction_signature"]
    impulse = row["impulse"]
    jerk = row["jerk_burst"]
    flip = row["flip_density"]
    vol = row["volatility_burst"]
    rng = row["range_burst"]

    forcing = np.array([
        dyn + 0.25 * impulse,
        dyn + inst + 0.15 * vol,
        -inst + 0.20 * rng,
        dyn + 0.35 * abs(direction),
        dyn - 0.25 * inst + 0.15 * rng,
        inst + jerk + 1.5 * flip,
        dyn + 0.35 * abs(direction),
        impulse + jerk + 0.25 * vol,
        dyn + rng - 0.20 * inst,
    ])

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

    return new, new - prev


def run_cascade(stage):
    state = np.zeros(len(STATE_NAMES))
    rows = []

    for k, row in stage.reset_index(drop=True).iterrows():
        prev = state.copy()
        state, delta = cascade_update(prev, row)

        out = {
            "step": k,
            "window": row["window"],
            "stage_group": row["stage_group"],
            "cascade_input": row["cascade_input"],
            "dynamic_signature": row["dynamic_signature"],
            "instability_signature": row["instability_signature"],
            "direction_signature": row["direction_signature"],
        }

        for i, name in enumerate(STATE_NAMES):
            out[f"{name}_state"] = float(state[i])
            out[f"{name}_delta"] = float(delta[i])

        rows.append(out)

    return pd.DataFrame(rows)


def project_rs(cascade):
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

    v["RS1_RHYTHM"] = 0.35 * X_STAB + 0.25 * X_MAT - 0.25 * X_LAB + 0.15 * X_EXC
    v["RS2_SYNC"] = 0.35 * X_INTEG + 0.30 * X_HUB + 0.20 * X_MAT - 0.15 * X_LAB
    v["RS3_SEGR"] = 0.45 * X_SEGR + 0.25 * X_STAB + 0.20 * X_MAT - 0.10 * X_FLEX
    v["RS4_INTEGRAL"] = 0.30 * X_INTEG + 0.25 * X_HUB + 0.20 * X_MAT + 0.15 * X_STAB - 0.20 * X_LAB

    v["hidden_tension_index"] = X_SENS + X_LAB - X_STAB
    v["creative_integrator_index"] = X_INTEG + X_HUB + X_FLEX + v["RS2_SYNC"]
    v["control_compensation_index"] = X_MAT + v["RS3_SEGR"] - X_LAB

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


def run_one(ssn, person, pre_lag, post_lag):
    sd, conception = make_subject_day(ssn, person["dob_parsed"], pre_lag)
    stage = make_stage_signatures(sd, post_lag)
    cascade = run_cascade(stage)
    rs = project_rs(cascade)
    scores = compute_scores(rs, stage, cascade)

    row = {
        "name": person["name"],
        "dob": str(pd.Timestamp(person["dob_parsed"]).date()),
        "context": person.get("context", ""),
        "pre_lag_days": pre_lag,
        "post_lag_days": post_lag,
        "conception_est": conception.date().isoformat(),
    }

    row.update(rs)
    row.update(scores)
    row.update(stage_wide(stage))
    row.update(raw_synthetic(row))

    return row, stage, cascade


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


def write_card(pdir, row, stage, cascade):
    pdir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([row]).to_csv(pdir / "01_result.csv", index=False)
    stage.to_csv(pdir / "02_stage_signatures.csv", index=False)
    cascade.to_csv(pdir / "03_cascade_states.csv", index=False)

    with open(pdir / f"CARD_{safe_name(row['name'])}.txt", "w", encoding="utf-8") as f:
        f.write("UNIVERSAL FULL CASCADE CARD — V43 NO-LAG\n")
        f.write("=========================================\n\n")

        f.write(f"Name: {row['name']}\n")
        f.write(f"DOB: {row['dob']}\n")
        f.write(f"Context: {row.get('context','')}\n\n")

        f.write("RUN INFO\n")
        f.write("--------\n")
        f.write("mode: NO_LAG (pre_lag_days=0, post_lag_days=0 — fixed, not searched)\n")
        f.write(f"profile_class: {row['profile_class']}\n")
        f.write(f"conception_est: {row['conception_est']}\n\n")

        f.write("RS AXES\n")
        f.write("-------\n")
        for k in ["RS1_RHYTHM", "RS2_SYNC", "RS3_SEGR", "RS4_INTEGRAL"]:
            f.write(f"{k}: {row[k]:.6f}\n")

        f.write("\nHIDDEN STATES\n")
        f.write("-------------\n")
        for k in STATE_NAMES:
            f.write(f"{k}: {row[k]:.6f}\n")

        f.write("\nINDICES\n")
        f.write("-------\n")
        for k in [
            "hidden_tension_index",
            "creative_integrator_index",
            "control_compensation_index",
            "architecture_power_score",
            "pathology_load_score",
            "adaptive_control_score",
            "adaptive_stability_score",
            "decompensation_risk_score",
            "high_load_compensation_score",
            "tension_control_ratio",
        ]:
            f.write(f"{k}: {row[k]:.6f}\n")

        f.write("\nRAW SYNTHETIC PSYCHOTYPE — UNNORMALIZED\n")
        f.write("---------------------------------------\n")
        for k in [
            "RawSynth_Openness",
            "RawSynth_Conscientiousness",
            "RawSynth_Extraversion",
            "RawSynth_Agreeableness",
            "RawSynth_Neuroticism",
        ]:
            f.write(f"{k}: {row[k]:.6f}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()

    input_path = Path(args.input).expanduser()
    persons = load_persons(input_path)
    ssn = load_ssn()

    rows = []

    for _, person in persons.iterrows():
        print("RUN:", person["name"])

        row, stage, cascade = run_one(ssn, person, 0, 0)
        row["profile_class"] = classify_profile(row)
        rows.append(row)

        pdir = OUT_DIR / safe_name(person["name"])
        write_card(pdir, row, stage, cascade)

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_DIR / "00_universal_summary.csv", index=False)

    with open(OUT_DIR / "SUMMARY_UNIVERSAL_ENGINE.txt", "w", encoding="utf-8") as f:
        f.write("UNIVERSAL FULL CASCADE ENGINE SUMMARY — V43 NO-LAG\n")
        f.write("===================================================\n\n")
        f.write(f"input: {input_path}\n")
        f.write("mode: NO_LAG (pre_lag_days=0, post_lag_days=0 — fixed, not searched)\n")
        f.write(f"n: {len(summary)}\n\n")
        f.write(summary[[
            "name", "dob", "profile_class",
            "conception_est",
            "RS1_RHYTHM", "RS2_SYNC", "RS3_SEGR", "RS4_INTEGRAL",
            "X_SENS", "X_STAB", "X_LAB",
            "hidden_tension_index",
            "creative_integrator_index",
            "control_compensation_index",
            "architecture_power_score",
            "pathology_load_score",
            "adaptive_control_score",
            "adaptive_stability_score",
            "decompensation_risk_score",
            "high_load_compensation_score",
            "tension_control_ratio",
        ]].to_string(index=False))
        f.write("\n\nOUTPUT DIR\n")
        f.write(str(OUT_DIR))

    print("\nDONE")
    print("====")
    print("Output:", OUT_DIR)
    print("Open:")
    print(f"open {OUT_DIR / 'SUMMARY_UNIVERSAL_ENGINE.txt'}")


if __name__ == "__main__":
    main()

