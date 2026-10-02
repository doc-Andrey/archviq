# ARCHVIQ HTTP API

Optional API surface for a non-Streamlit frontend.

```bash
pip install -r requirements-api.txt
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

- `GET /api/health`
- `POST /api/profile`

The API never accepts a filesystem path. It always uses `data/SN_d_tot_V2.0.txt` from the repository. Runtime SILSO download is disabled by design.
