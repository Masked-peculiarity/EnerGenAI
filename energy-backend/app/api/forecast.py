from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from app.api.dependencies import energy
router = APIRouter(tags=["Forecasting"])

class ForecastRequest(BaseModel):
    horizon_steps:int=Field(6,ge=1,le=144,strict=True)
    origin:str|None=None

@router.post("/api/forecast")
def forecast(body:ForecastRequest,service=Depends(energy)):
    return service.forecast(body.horizon_steps,body.origin)

@router.get("/api/forecast/evaluation")
def evaluation(limit:int=Query(288,ge=1,le=3000),service=Depends(energy)):
    return service.backtest(limit)
