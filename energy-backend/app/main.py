import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import jwt_secret
from app.storage import Store
from app.services.energy import EnergyService
from app.services.llm import Generator
from app.agent.graph import EnergyAgent
from rag.graph import CorrectiveRAG
from app.api import accounts,agent,analytics,anomalies,bills,documents,forecast,rag,prediction

def create_app(store=None,service=None,generator=None):
    @asynccontextmanager
    async def lifespan(application):
        application.state.secret = jwt_secret()
        application.state.store = store or Store()
        application.state.energy = service or EnergyService()
        application.state.generator = generator or Generator()
        application.state.rag = CorrectiveRAG(application.state.store)
        application.state.agent = EnergyAgent(application.state.energy,application.state.rag,application.state.generator)
        yield
    application = FastAPI(title="EnerGenAI",version="2.0.0",lifespan=lifespan,
        description="UCI energy forecasting, unusual-consumption detection, analytics, and corrective-RAG Copilot.")
    default_origins = "http://localhost:8080" if os.getenv("APP_ENV")=="production" else "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8081,http://127.0.0.1:8081"
    origins = [value.strip() for value in os.getenv("WEB_ORIGIN",default_origins).split(",") if value.strip()]
    application.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=["GET","POST","DELETE"],allow_headers=["Authorization","Content-Type"])
    for router in [accounts.router,analytics.router,forecast.router,anomalies.router,rag.router,agent.router,documents.router,bills.router,prediction.router]:
        application.include_router(router)

    @application.get("/api/health")
    @application.get("/health",include_in_schema=False)
    def health(request:Request):
        service = request.app.state.energy
        return {"status":"ok","version":"2.0.0","model":service.artifact["name"],"dataset":service.dataset,
                "rag_sections":len(request.app.state.rag.documents),"artifacts_loaded":True}

    @application.post("/predict",include_in_schema=False)
    def retired_prediction():
        raise HTTPException(410,"The old household-input model is archived. Use /api/forecast with horizon_steps and UCI history.")

    @application.exception_handler(HTTPException)
    async def http_error(_request,error):
        return JSONResponse({"error":error.detail,"msg":error.detail},status_code=error.status_code)

    @application.exception_handler(ValueError)
    async def value_error(_request,error):
        return JSONResponse({"error":str(error)},status_code=400)

    @application.exception_handler(RequestValidationError)
    async def validation_error(_request,error):
        fields = [".".join(str(part) for part in issue["loc"])+": "+issue["msg"] for issue in error.errors()]
        return JSONResponse({"error":"; ".join(fields)},status_code=422)

    @application.exception_handler(Exception)
    async def unexpected(_request,error):
        logging.getLogger(__name__).error("Unhandled API error (%s)",type(error).__name__)
        return JSONResponse({"error":"Service could not complete the request; check backend logs"},status_code=500)
    return application

app = create_app()
