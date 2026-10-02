# Engine 43 · Complete Calculation Logic

## 1. Input

The commercial calculation starts with date of birth. No zodiac sign, symbolic calendar category or client-specific lag is used.

When exact gestational length is unknown, the central conception-to-birth interval is fixed at:

```text
266 days
```

Timing sensitivity is recalculated at five fixed assumptions:

```text
252 / 259 / 266 / 273 / 280 days
```

The 266-day result is the point estimate. The spread across all five is reported as timing sensitivity.

## 2. Developmental windows

### Prenatal

| Window | Days after conception |
|---|---:|
| W0 | 0–17 |
| W1 | 18–45 |
| W2 | 46–73 |
| W3 | 74–100 |
| W4 | 101–180 |
| W5 | 181 to birth−1 |

### Postnatal

| Window | Days after birth |
|---|---:|
| N0 | 0–29 |
| P1 | 30–89 |
| P2 | 90–179 |
| P3 | 180–269 |
| P4 | 270–364 |
| P5 | 365–544 |
| P6 | 545–729 |
| P7 | 730–909 |
| P8 | 910–1095 |

This produces 15 windows covering prenatal development and the first three postnatal years.

## 3. Historical signal

For every calendar day in every window, Engine 43 reads the daily SILSO sunspot number.

The bundled archive is frozen so the same birth date always produces the same numerical input.

## 4. Window descriptors

For the daily sequence `x(t)` in each window the engine retains nine descriptors.

### M — Mean level

```text
M = mean(x)
```

### A — Activity amplitude

```text
A = mean(|Δx|)
```

### V — Volatility

```text
V = std(Δx)
```

### R — Reversal rate

Direction reversals are counted on non-zero first differences.

```text
R = mean(sign(Δx[t]) != sign(Δx[t−1]))
```

### D — Directional persistence

```text
D = |mean(sign(Δx))|
```

### B — Directional bias

```text
B = mean(sign(Δx))
```

### ACC — Acceleration magnitude

```text
ACC = mean(|Δ²x|)
```

### JERK — Third-order change

```text
JERK = mean(|Δ³x|)
```

### E — Dynamic energy

```text
E = mean((Δx)²)
```

The engine therefore uses both signal level and temporal structure. Two windows with the same average SSN can have different reversal, volatility, acceleration and energy profiles.

## 5. Historical normalization

Window descriptors have different scales. Each descriptor is converted to a robust historical Z coordinate using a frozen reference distribution generated from the same daily SILSO archive.

```text
z = (x − median_reference) / robust_scale_reference
```

The robust scale uses median absolute deviation with a standard-deviation fallback.

The scaler file is bundled in:

```text
data/reference_scalers_v1.json
```

## 6. Phase summaries

The 15 windows are summarized into three macro phases:

```text
EARLY_PRE = W0 + W1 + W2
LATE_PRE  = W3 + W4 + W5
POST      = N0 + P1 + ... + P8
```

For each macro phase the engine averages the normalized descriptors.

It then calculates inter-phase changes:

```text
EARLY_PRE → LATE_PRE
LATE_PRE  → POST
```

and four local transitions:

```text
W1 → W2
W2 → W3
W4 → W5
W5 → N0
```

## 7. X9 nonlinear cascade

The phase and transition representation is compressed into nine bounded coordinates:

- `X_EXC` — excitation / activation pressure
- `X_SENS` — sensitivity to dynamic variation
- `X_STAB` — persistence / stability
- `X_INTEG` — cross-phase integration
- `X_FLEX` — switching flexibility
- `X_LAB` — lability / transition intensity
- `X_SEGR` — segregation / selective retention
- `X_HUB` — global resource / hub load
- `X_MAT` — maturation / late consolidation

Each axis is a fixed linear combination of phase descriptors followed by a sigmoid transform to 0–100.

No client-specific coefficient search is performed.

## 8. Practical output layer

X9 is mapped to seven user-facing coordinates.

### Resource

Weighted toward HUB, stability, integration and maturation.

### Switching

Weighted toward flexibility, lability and activation; reduced by segregation.

### Lock

Weighted toward stability, segregation and integration; reduced by flexibility.

### Novelty

Weighted toward flexibility, activation and sensitivity; reduced by stability.

### Control

Weighted toward stability, integration and segregation; reduced by lability.

### Processing Cost

Weighted toward lability, sensitivity and activation; reduced by stability.

### Maturation

Weighted toward X_MAT, integration and HUB.

Every public score is bounded 0–100.

## 9. Timing sensitivity

The complete calculation is repeated for all five conception-to-birth assumptions.

For each X9 and public output the engine stores:

```text
mean
standard deviation
range = max − min
```

The range is presented to the client because a profile that is stable across conception timing assumptions is different from one whose interpretation changes substantially with timing.

## 10. Stage 2: cognitive calibration

The bundled browser battery measures:

- simple reaction time
- forced-choice reaction
- 2-back working memory
- Simon interference
- complex-rule speed and accuracy

The product roadmap uses these measurements to compare architecture with live performance.

Conceptually:

```text
Architecture prior − measured performance = GAP
```

The GAP is where compensation, training, overload and current state become visible.

## 11. Questionnaires and EEG

Questionnaire scores add self-reported behavior and load. EEG can add objective neurophysiological measures when available.

The model is intentionally layered:

```text
date-linked architecture
+ cognitive performance
+ self-report
+ optional EEG
= richer individual operating map
```

## 12. What the customer sees

The commercial interface does not ask users to interpret raw SSN or 425 engine columns. It shows:

1. seven practical axes;
2. timing sensitivity for each axis;
3. a dominant operating signature;
4. explanations in plain language;
5. the next measurement to add;
6. an optional advanced X9 view.

This keeps the product useful without hiding the calculation chain.
