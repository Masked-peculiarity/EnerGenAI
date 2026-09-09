# EnerGENAI

EnerGENAI is an agentic multimodal framework for personalized residential energy management. It forecasts demand, estimates appliance-level consumption from aggregate meter data (NILM), and delivers evidence-backed recommendations using retrieval-augmented generation (RAG).

## Product scope

- Forecast household load for 15-minute to 7-day horizons.
- Disaggregate whole-home meter signals into appliance estimates and confidence scores.
- Ingest meter streams, utility bills, weather, tariffs, appliance metadata, and homeowner notes.
- Answer questions and recommend tariff-aware actions with source citations.
- Keep device control opt-in, approval-gated, and bounded by safety policies.

## Architecture

```text
Meters / IoT / bills / weather / user context
                  |
             Ingestion API
                  |
TimescaleDB + object storage + vector search
                  |
Forecasting <--> NILM <--> feature pipelines
                  |
      Agent orchestration and RAG guardrails
                  |
 Dashboard, notifications, and device integrations
```

## Stack

### Product and services

- **Web:** Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Recharts.
- **API:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy, Alembic, Uvicorn.
- **Agents:** LangGraph for durable workflows; OpenAI Responses API for multimodal reasoning and tool calling.
- **Jobs:** Celery and Redis initially; consider Temporal for long-running production workflows.
- **Identity:** Auth.js/NextAuth, household-scoped JWTs, and RBAC.

### Data and ML

- **Time series:** PostgreSQL plus TimescaleDB for meter readings and aggregates.
- **Files:** S3-compatible MinIO locally; S3-compatible managed storage in production.
- **RAG:** pgvector initially, with metadata-filtered hybrid retrieval and reranking. Move to Qdrant only when scale warrants it.
- **ML operations:** MLflow for experiments, model registry, and artifacts; Feast is optional after MVP.
- **Forecasting:** LightGBM/XGBoost baseline, progressing to PyTorch Forecasting or GluonTS models when validated.
- **NILM:** scikit-learn/PyTorch event detection and sequence models; NILMTK-compatible datasets/evaluation.
- **Transform and validation:** Polars/Pandas plus Pandera or Great Expectations.

### Platform and quality

- Docker Compose locally; Kubernetes or ECS in production.
- GitHub Actions; OpenTelemetry, Prometheus, Grafana, and Sentry.
- Ruff, mypy, pytest, Playwright, ESLint, Prettier, and pre-commit.

## File structure

```text
energenai/
├── apps/
│   ├── web/                    # Next.js homeowner dashboard
│   └── api/                    # FastAPI REST and WebSocket gateway
├── services/
│   ├── agent-orchestrator/     # LangGraph, tools, safety and evidence checks
│   ├── forecasting/            # Training, inference, evaluation, model registry
│   ├── nilm/                   # Appliance disaggregation pipelines
│   ├── ingestion/              # Meter, bill, weather, connector ingestion
│   └── notifications/          # Email/push and preference enforcement
├── packages/
│   ├── domain/                 # Shared schemas, units, business rules
│   ├── client-sdk/             # Typed internal API client
│   ├── prompts/                # Versioned agent instructions
│   └── ui/                     # Shared components and tokens
├── data/
│   ├── contracts/              # JSON Schema or Avro contracts
│   ├── seeds/                  # Synthetic household data only
│   └── knowledge/              # Curated RAG source manifests
├── infra/
│   ├── compose/                # Local Docker configuration
│   ├── kubernetes/             # Helm or Kustomize manifests
│   ├── terraform/              # Cloud infrastructure
│   └── monitoring/             # Dashboards and alert rules
├── docs/
│   ├── architecture/           # ADRs, data flow, threat model
│   ├── api/                    # Integration documentation
│   ├── ml/                     # Dataset/model cards and evaluation reports
│   └── runbooks/               # Operational procedures
├── scripts/
├── tests/
│   ├── e2e/
│   ├── integration/
│   └── fixtures/
├── .github/workflows/
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

## Domain model

- `Household`: tenancy boundary, location/time zone, consent, preferences.
- `MeterReading`: timestamped aggregate import/export power and optional electrical measurements.
- `Appliance`: user-confirmed inventory and inferred identity.
- `DisaggregationEvent`: appliance estimate, confidence, interval energy, model version.
- `Tariff`: time-of-use windows, charges, currency, effective dates.
- `Forecast`: horizon, quantiles, input-feature and model versions.
- `Recommendation`: action, estimated impact, evidence citations, confidence, approval status.
- `Document`: bill/manual/guidance metadata, access policy, chunks, and embeddings.

Persist timestamps in UTC, exchange ISO 8601 through APIs, and use canonical units (`W`, `Wh`, `kWh`, local currency).

## Agent workflow

1. An intent agent classifies the homeowner request.
2. A context agent retrieves household preferences, tariffs, forecasts, NILM output, and authorized documents.
3. An analysis agent calls deterministic cost/load tools; it must not invent measurements.
4. A recommendation agent drafts actions with uncertainty and expected impact.
5. A safety agent validates citations, policy constraints, and required approval before any automation.

Responses should include freshness timestamps, model versions, confidence, and supporting source links/snippets.

## RAG requirements

Index only approved, access-controlled documents: tariffs, bills, appliance manuals, user-confirmed metadata, and vetted energy guidance. Attach household ID, source, locale, document type, effective date, and retention policy as metadata. Apply access filters before hybrid lexical/vector search and reranking. Show citations in the UI and say when evidence is unavailable or stale.

## MVP API

```text
POST /v1/ingestion/meter-readings
POST /v1/documents
GET  /v1/households/{id}/dashboard
GET  /v1/households/{id}/forecasts?start=&end=&resolution=
GET  /v1/households/{id}/appliances
GET  /v1/households/{id}/recommendations
POST /v1/assistant/messages
POST /v1/recommendations/{id}/accept
```

Generate OpenAPI from FastAPI. Enforce household isolation on every database, object-store, vector-store, and tool query.

## Prerequisites

- Node.js 22+, pnpm 9+
- Python 3.12+, `uv`
- Docker Desktop with Compose v2
- `make` or an equivalent task runner
- An OpenAI API key for agent functionality; mock providers for offline tests

## Build sequence

1. Configure pnpm workspaces and Python `uv` projects.
2. Start TimescaleDB, Redis, MinIO, and vector search with Compose.
3. Add migrations for households, readings, tariffs, documents, forecasts, NILM events, and recommendations.
4. Implement idempotent ingestion, schema validation, unit conversion, and dead-letter handling.
5. Ship baseline forecasting, NILM, and tariff-cost tools before complex neural models.
6. Build RAG with citations, then expose controlled tools through the agent workflow.
7. Add dashboard views for live usage, appliance estimates, forecast, cost, and ranked actions.
8. Add observability, evaluation, and security gates before device-control work.

## Environment

```dotenv
DATABASE_URL=postgresql+psycopg://energenai:energenai@localhost:5432/energenai
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=energenai
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
OPENAI_API_KEY=
OPENAI_MODEL=
OTEL_EXPORTER_OTLP_ENDPOINT=
```

Keep secrets out of Git; production secrets belong in a managed secret store.

## Testing and evaluation

- Unit-test tariff calculations, unit conversion, tenancy checks, ingestion validation, and tool schemas.
- Run integration tests using ephemeral database, Redis, and object-storage services.
- For NILM, report appliance-level precision, recall, F1, MAE, and energy error on held-out labeled data.
- For forecasting, report MAE, RMSE, sMAPE, quantile pinball loss, and calibration by horizon.
- Evaluate agent outputs for groundedness, citation correctness, numerical accuracy, safety, and usefulness with a fixed scenario suite.
- Evaluate recommendations with counterfactual cost calculations; never promise savings.

## Privacy and safety

- Energy traces are sensitive behavioral data: encrypt them, minimize retention, and support export/deletion.
- Get consent for document uploads, integrations, and control features.
- Redact PII and secrets from application logs and agent traces.
- Use signed webhooks, audit logging, rate limits, least-privilege identities, dependency scanning, and SBOMs.
- Present assumptions and confidence. Require explicit approval for automation, hard-limit power/time actions, and provide a kill switch.

## Milestones

1. Foundation: schema, auth, Compose stack, synthetic data.
2. Insights: ingestion, dashboard, baseline forecast, tariff calculator.
3. Disaggregation: appliance estimates, confidence UX, evaluation pipeline.
4. Assistant: grounded Q&A and evidence-linked recommendations.
5. Personalization: preferences, feedback, and notification rules.
6. Optional control: opt-in connectors and approval workflows.

## License and data

Select a license before publishing; Apache-2.0 is a sensible open-framework default. Never commit real household data. Record data provenance, consent, and limitations for every dataset and model artifact.
