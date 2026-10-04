from fastapi import APIRouter,Depends,Query
from app.api.dependencies import energy
router = APIRouter(tags=["Analytics"])

@router.get("/api/analytics/summary")
def summary(start:str|None=None,end:str|None=None,tariff:float|None=Query(None,ge=0,le=100000,allow_inf_nan=False),
            factor:float|None=Query(None,ge=0,le=100,allow_inf_nan=False),service=Depends(energy)):
    return service.summary(start,end,tariff,factor)

@router.get("/api/analytics/timeseries")
def timeseries(start:str|None=None,end:str|None=None,resolution:str="hour",limit:int=Query(1000,ge=1,le=1000),service=Depends(energy)):
    return service.timeseries(start,end,resolution,limit)
