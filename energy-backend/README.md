# EnerGenAI backend

Active backend: Python3.12/FastAPI. Entry point app.main:app, local launcher run.py. See [complete project guide](../PROJECT_GUIDE.md) and [plan audit](../IMPLEMENTATION_PLAN_AUDIT.md).

From this directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m app.init_db
.\.venv\Scripts\python.exe run.py
```

Create .venv with Python3.12 first if absent. Root .env supplies configuration. SQLite works without cloud setup; PostgreSQL is optional account/document persistence. init_db is additive and preserves existing accounts.

API health localhost:5000/api/health; Swagger localhost:5000/docs. Routers under app/api validate HTTP inputs; services/energy.py owns measured KPIs, recursive forecast, held-out anomalies. LangGraph agent calls fixed read-only tools and corrective retrieval. Server-side optional Groq; public evidence works without it.

Reproduce: python -m ml.eda, python -m ml.train_forecast, python -m rag.ingest. Test: python -m pytest tests -q using the environment executable. Models and public index must exist before serving; no training at boot. Source CSV defaults to ../energydata_complete.csv and hash is checked.

EnergyConsumptionDataAnalysis is archived. Its app.py is a compatibility launcher, not a second Flask service. Do not train/run its old manual-input model for the final UCI application.

The new manual-input predictor uses /api/prediction and /api/prediction/models, separately from /api/forecast. Reproduce it with python -m ml.train_predictor. Its new pipelines/artifacts and curated EIA RECS household data are documented in [PREDICTION_GUIDE.md](../PREDICTION_GUIDE.md). No data downloads or retraining happen at startup.

If a traceback ends with KeyboardInterrupt while importing scipy or sklearn, the Python process received an interrupt (for example Ctrl+C or an IDE stop command). This alone does not indicate a broken package. Restart run.py and wait for Application startup complete / Uvicorn running; keep the terminal open. The launcher now prints a loading notice immediately and handles startup interruption with a concise message. Import time can vary with disk and machine load.
