# ARCHVIQ · Engine 43

**Your brain does not need another label. It needs an operating map.**

ARCHVIQ is a commercial neurocognitive profiling platform built around Engine 43. It converts a date-linked developmental temporal signature into a structured profile and then supports deeper calibration with cognitive tests, questionnaires and optional EEG.

## Product logic

```text
Date of birth
    ↓
Central conception anchor (DOB − 266 days)
+ fixed timing sensitivity ensemble (252 / 259 / 266 / 273 / 280)
    ↓
15 developmental windows
W0–W5 · N0 · P1–P8
    ↓
Daily SILSO solar-activity dynamics
M · A · V · R · D · B · ACC · JERK · E
    ↓
Historical robust normalization
    ↓
Early prenatal / late prenatal / postnatal phases
+ transition deltas
    ↓
X9 nonlinear cascade
    ↓
Seven practical operating axes
Resource · Switching · Lock · Novelty · Control · Processing Cost · Maturation
    ↓
Cognitive tests / questionnaires / optional EEG
    ↓
GAP analysis and personalized operating strategy
```

There is **no per-client lag search**. The point estimate is always anchored at 266 days when gestational information is unavailable. Neighboring fixed timing anchors quantify uncertainty rather than optimize the answer.

## Repository

- `app.py` — bilingual RU/EN Streamlit commercial site
- `archviq_engine43.py` — Engine 43 calculation core
- `profile_engine.py` — fast web adapter and output packaging
- `interpret_engine.py` — client-facing interpretation layer
- `cognitive_test.html` / `cognitive_test_en.html` — bilingual browser cognitive battery
- `site_questionnaire.py` — free architecture questionnaire, GAP comparison and cognitive CSV intake
- `analysis_modules/cognitive_tools/rdm_perception_test.html` — optional research RDM task
- `assets/andrey_osipov.jpg` — founder portrait
- `data/SN_d_tot_V2.0.txt` — frozen daily SILSO archive
- `data/reference_scalers_v1.json` — frozen historical robust scalers
- `data/SILSO_ARCHIVE_SHA256.txt` — data integrity hash
- `docs/MODEL_LOGIC.md` — complete calculation logic
- `docs/DEPLOY_GITHUB.md` — GitHub + Streamlit deployment
- `docs/PRODUCT_COPY.md` — commercial positioning and site copy
- `PRIVACY.md` — privacy note
- `TERMS.md` — product boundaries

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

The package is self-contained. No secret is required for the free architecture calculator. The current Gumroad product links are already wired into `app.py` and can be changed there later.

For Streamlit Community Cloud:

1. Upload the entire repository to GitHub.
2. Create a Streamlit app from the repository.
3. Main file: `app.py`.
4. Deploy.

## Commercial structure

The site keeps the complete calibration entry path free and routes users toward paid thematic depth:

- Engine 43 architecture + architecture questionnaire + cognitive battery + GAP — free
- Couple compatibility — $19
- Burnout — $19
- Working with AI — $19
- Full Architecture Report — $39

The paid modules add topic-specific interpretation and the integrated full report. Payment URLs are isolated in the `PRODUCTS` mapping at the top of `app.py`, so they can be replaced without changing the analysis logic.

## Data source

Daily sunspot number series: SILSO World Data Center, Royal Observatory of Belgium.

Official source: https://www.sidc.be/SILSO/

## Product boundary

ARCHVIQ provides an analytical neurocognitive profile. It is not a medical diagnostic service and does not replace medical or psychological care.
