from fastapi import APIRouter,Depends,Query
from app.api.dependencies import energy
router = APIRouter(tags=["Unusual consumption"])

@router.get("/api/anomalies")
def anomalies(start:str|None=None,end:str|None=None,limit:int=Query(200,ge=1,le=1000),flagged_only:bool=True,service=Depends(energy)):
    return service.anomalies(start,end,limit,flagged_only)
