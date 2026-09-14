# ARCHVIQ FINAL-7 — 43 NEW V3 linked workflow

This build preserves the original linked product flow while replacing the legacy 43 core with the frozen `43 NEW V3 / 254D` engine.

## Product flow

`DOB → 43 NEW V3 prior → architecture/functional interpretation → cognitive test → questionnaire → integrated profile`

Pair mode remains available:

`Partner 1 43 NEW V3 + Partner 2 43 NEW V3 → overlaid X1–X9 comparison → highlighted gaps → compatibility/coordination analysis`

## What changed

- Production engine: `43_new_v3_engine.py` (254D geometry, fixed NO-LAG).
- Legacy 43 is not used as a fallback.
- X1–X9 are the primary architecture coordinates.
- RS1–RS4 remain summary macrocoordinates for continuity with the existing product.
- Compatibility graph is now one overlaid colored X1–X9 radar:
  - cyan = partner 1
  - gold = partner 2
  - red diamonds = large gaps (>=20 display points)
- Cognitive test still compares measured function with the 43 prior.
- Questionnaire still compares current behavior/state with the 43 prior.
- The final questionnaire screen now merges all available layers in one integrated chart/table:
  - 43 NEW prior
  - cognitive test
  - questionnaire
- The previous relationship/sleep/recovery/AI flows remain in place.
- Headline language is more neutral: the site presents a computational processing profile / developmental prior rather than claiming the brain has been "decoded".
- Legacy public-figure similarity vectors are disabled because they were generated on the old 43 geometry.
- Legacy LEMON percentile normalization is not applied to 43 NEW V3.

## Display scale

The native 43 NEW X and RS coordinates are converted for visualization with a fixed symmetric `tanh` display transform centered at 50. This is **not** a population percentile, clinical norm, or probability.

Cognitive and questionnaire layers use their existing product transformations. The merged 0–100 display is intended for within-report comparison and feedback, not as a validated common normative scale.

## Deployment

The required files are in the root:

- `app.py`
- `profile_engine.py`
- `interpret_engine.py`
- `43_new_v3_engine.py`
- `pdf_report.py`
- `email_report.py`
- `requirements.txt`
- `assets/`

Deploy exactly as the previous Streamlit build. `43_new_v3_engine.py` uses SILSO daily SSN and remains fixed NO-LAG.
