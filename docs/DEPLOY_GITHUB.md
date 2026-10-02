# Deploy to GitHub / Streamlit Cloud

## 1. Upload
Upload every file and directory from the package root. Do not upload the outer ZIP itself as the repository contents.

Required large-ish data files in `data/`:
- `SN_d_tot_V2.0.txt`
- `physical_reference_bank_w5_v01.pkl.gz`
- `physical_reference_bank_w7_v01.pkl.gz`
- `silso_context_reference_v2.pkl.gz`

They are intentionally versioned with the repository. The site must not fetch SILSO during a user calculation.

## 2. Streamlit
Main file: `app.py`

No secrets are required for free SSN analytics.

## 3. Product policy
The public site exposes SSN analytics for free. Tests, compatibility and questionnaire-based work are paid. The embedded paid instruments are hidden unless `ARCHVIQ_PAID_RESEARCH_MODE=1` is set in a private installation.

## 4. Verification
Before deployment run:

```bash
pip install -r requirements.txt
python -m compileall -q .
pytest -q
```

## 5. Optional HTTP backend
For a separate backend deployment:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

The public request cannot supply a SILSO path or executable options; all data paths are server-controlled.
