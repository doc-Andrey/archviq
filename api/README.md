# Optional HTTP API

The Streamlit site imports the engine directly and does not require this API.
For a separate backend deployment:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

`POST /api/profile` accepts DOB, sex and gestation metadata only. The client cannot supply filesystem paths or executable options. SILSO and all reference tables are loaded from the repository.
