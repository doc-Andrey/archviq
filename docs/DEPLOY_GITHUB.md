# GitHub + Streamlit deployment

## 1. Replace repository contents

Use the complete contents of this package as the repository root.

Expected top level:

```text
app.py
archviq_engine43.py
profile_engine.py
interpret_engine.py
cognitive_test.html
requirements.txt
README.md
PRIVACY.md
TERMS.md
assets/
data/
docs/
.streamlit/
```

Do not omit `data/SN_d_tot_V2.0.txt` or `data/reference_scalers_v1.json`. The calculator requires both.

## 2. GitHub

```bash
git add .
git commit -m "ARCHVIQ 2.0 - Engine 43 developmental architecture"
git push origin main
```

## 3. Streamlit Community Cloud

- Repository: your ARCHVIQ repository
- Branch: `main`
- Main file: `app.py`

No secrets are required for the current build.

## 4. Product links

Current Gumroad links are in the `PRODUCTS` dictionary at the top of `app.py`.

Change them there when offers or prices change.

## 5. Domain

If `archviq.com` already points to the current Streamlit deployment, keep the existing DNS/redirect setup and only redeploy the new code.

## 6. Post-deploy checks

- RU / EN toggle
- Free profile calculation
- Founder image
- Method page
- Stage 2 cognitive battery
- CSV / JSON profile downloads
- Gumroad buttons
- Mobile layout

## 7. Quick local check

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m py_compile app.py archviq_engine43.py profile_engine.py interpret_engine.py
streamlit run app.py
```
