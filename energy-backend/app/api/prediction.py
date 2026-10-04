from typing import Annotated, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.services.predictor import artifact, predict

router = APIRouter(tags=["Manual-input prediction"])

class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid",allow_inf_nan=False)

class Conditions(Inputs):
    temperature_c:float=Field(ge=-30,le=60)
    humidity_percent:float=Field(ge=0,le=100)
    lighting_wh:float=Field(ge=0,le=10000)
    outdoor_temperature_c:float=Field(ge=-80,le=80)
    hour:float=Field(ge=0,lt=24)
    day_of_week:int=Field(ge=0,le=6,strict=True)
    month:int=Field(ge=1,le=12,strict=True)

class Home(Inputs):
    floor_area_sqft:float=Field(gt=0,le=100000)
    occupants:int=Field(ge=1,le=7,strict=True)
    heating_degree_days:float=Field(ge=0,le=25000)
    cooling_degree_days:float=Field(ge=0,le=25000)
    home_type:Literal[1,2,3,4,5]
    heating_fuel:Literal[1,2,3,5,7,99,-2]
    air_conditioning:Literal[0,1]

class ConditionsRequest(Inputs):
    mode:Literal["conditions"]
    inputs:Conditions

class HomeRequest(Inputs):
    mode:Literal["home"]
    inputs:Home

def call_safely(function):
    try:
        return function()
    except FileNotFoundError as error:
        raise HTTPException(503,str(error)) from None

@router.get("/api/prediction/models")
def models():
    return call_safely(lambda: {mode:artifact(mode)["report"] for mode in ["conditions","home"]})

@router.post("/api/prediction")
def prediction(body:Annotated[ConditionsRequest|HomeRequest,Field(discriminator="mode")]):
    return call_safely(lambda: predict(body.mode,body.inputs.model_dump()))
