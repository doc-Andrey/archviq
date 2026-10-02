# ARCHVIQ SITE V4 — GitHub deployment package

This repository is the public ARCHVIQ site plus the current frozen developmental cyber-calibration engine.

## Product policy

- **Free:** date-linked SSN/SILSO developmental analytics, six-window cascade, Processing Spiral profile, brain/circuit hypothesis map, uncertainty, and explicitly experimental somatic / psychophysiological branches.
- **Paid:** cognitive tests, compatibility work, questionnaires and questionnaire interpretation / GAP work.

The free SSN calculation does **not** download data from the internet. The repository contains the frozen WDC-SILSO Daily Total Sunspot Number V2.0 archive and precomputed reference objects.

## Current free pipeline

`DOB + gestation -> SILSO daily dynamics -> 5/7-day packets -> W1/W2/W3/F1/F2/F3 -> candidate developing circuits -> RS4/v4 Processing Spiral cascade -> personal interpretation`

Important evidence labels are kept separate:

- `MEASURED` — bundled SILSO observations.
- `MODELED` — packet percentiles / cascade state.
- `HYPOTHESIZED` — developmental circuit mapping.
- `EXPERIMENTAL` — human interpretation and downstream somatic / psychophysiological branches.
- Natural-EMF causality remains **unproven**.

## Repository layout

- `app.py` — Streamlit public site.
- `profile_engine.py` — site wrapper around the current engine.
- `archviq/` — current Baseline-A engine/orchestrator and frozen computational layers.
- `data/` — bundled SILSO archive + precomputed historical reference banks/context curves.
- `analysis_modules/` — paid / research questionnaire, compatibility and measurement modules retained from the previous site package.
- `cognitive_test*.html` — paid/private cognitive battery assets.
- `api/` — optional HTTP API (`POST /api/profile`).
- `docs/` — Processing Spiral, evidence levels, model boundaries and deployment notes.
- `legacy_engine43/` — previous Engine 43 code retained for audit only; the V4 public SSN page does not call it.

## Local launch

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## GitHub / Streamlit Cloud

1. Create a new GitHub repository.
2. Upload **the contents of this folder to the repository root**.
3. Confirm that `data/SN_d_tot_V2.0.txt` and the three precomputed `.pkl.gz` reference files are present.
4. In Streamlit Community Cloud choose `app.py` as the main file.
5. Do not add a runtime SILSO downloader; production calculations must use the repository files.

## Paid research mode

The public site hides the embedded questionnaire and cognitive test implementations. For a private/local research installation only:

```bash
export ARCHVIQ_PAID_RESEARCH_MODE=1
streamlit run app.py
```

This environment flag is **not** a payment/authentication system. Public payment access remains an external product workflow.

## Tests

```bash
pytest -q
```

GitHub Actions runs compile checks and tests on pushes and pull requests.
