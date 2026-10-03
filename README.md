# EnerGenAI

A React/FastAPI energy-analytics demonstration using the UCI Appliances Energy Prediction dataset: measured KPIs, short-term forecasts, unusual-consumption detection, corrective RAG, and a bounded LangGraph Energy Copilot.

Start with [the complete end-to-end guide](PROJECT_GUIDE.md). It explains purpose, stack, code architecture, dataset/units, training and evaluation, API contracts, privacy, configuration, Windows startup, tests, deployment, and troubleshooting. [Plan audit](IMPLEMENTATION_PLAN_AUDIT.md) identifies implemented requirements and pending hosted deployment.

The frontend now opens at the Log in page. Create an account or log in to enter the workspace; account creation logs you in automatically. The circular top-right profile menu provides user details, browser-local energy settings, and logout.

## Run on Windows

Python 3.12 and Node.js22.12+ required; Node24 tested. From repository root:

```powershell
py -3.12 -m venv energy-backend\.venv
.\energy-backend\.venv\Scripts\python.exe -m pip install -r energy-backend\requirements-lock.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Terminal1, from energy-backend:

```powershell
.\.venv\Scripts\python.exe -m app.init_db
.\.venv\Scripts\python.exe run.py
```

Terminal2, from energy-frontend:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1 --port 8080
```

Open http://localhost:8080/dashboard. API: http://127.0.0.1:5000/api/health; Swagger: http://127.0.0.1:5000/docs.

Use npm.cmd, not npm .cmd. Keep existing .env credentials private. Local SQLite requires no PostgreSQL; set PERSISTENCE_BACKEND=sqlite. Existing Neon accounts can use PERSISTENCE_BACKEND=postgres and their real DATABASE_URL. Optional Groq generation falls back to local evidence if unavailable.

## Honest scope

New: [manual-input prediction guide](PREDICTION_GUIDE.md). The **Predict** page combines two separate modes: UCI appliance conditions (Wh per ten minutes) and an official EIA RECS home-profile model (annual kWh). It includes test metrics, uncertainty, and held-out actual comparisons. The weak conditions model is explicitly experimental; the U.S. home model is not validated for India. Incompatible dataset targets are never blended.

The dataset describes one Belgian household in2016, NOT live/account-specific meter readings. Combined Appliances and separate lights channels are Wh per ten-minute interval. No NILM, appliance fault diagnosis, or renewable-output model.

Selected model: absolute-error XGBoost. Chronological held-out one-step MAE23.51Wh,RMSE61.20Wh,R2 .547. Regression has no single percentage accuracy. Day-ahead recursive R2 is negative and is clearly labeled experimental. Complete metrics are in [metrics.json](energy-backend/models/metrics.json).

Active stack: React18/TypeScript,Vite8,ReactRouter7,Tailwind4,Radix/shadcn,Recharts; Python3.12/FastAPI/Uvicorn,pandas/NumPy,scikit-learn/XGBoost; LangGraph,FAISS/TF-IDF; bcrypt/JWT,SQLite/PostgreSQL; localPDF/optionalTesseractOCR.

The old EnergyConsumptionDataAnalysis code and Work_items notebooks remain historical references. Its app.py forwards to the new FastAPI server. Old manual /predict API returns410; frontend /predict is the new authenticated dual-mode predictor and uses /api/prediction.

## Reproduce and validate

From backend: environment Python with -m ml.eda, -m ml.train_forecast, -m rag.ingest, -m pytest tests -q. From frontend: npx.cmd tsc --noEmit -p tsconfig.app.json, npm.cmd run build, npm.cmd run test:e2e (servers running).

Models/public FAISS are included and loaded at startup, never trained there. Deployment configs: [render.yaml](render.yaml), [Vercel SPA config](energy-frontend/vercel.json). Hosted deployment still requires your accounts/URLs.

Dataset attribution/license: [data README](data/README.md), [official UCI source](https://archive.ics.uci.edu/dataset/374/appliances%2Benergy%2Bprediction), CC BY4.0. Repository code license remains [LICENSE](LICENSE).
