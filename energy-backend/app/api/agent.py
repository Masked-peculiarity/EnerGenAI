from typing import Literal
from fastapi import APIRouter,Depends,Request
from pydantic import BaseModel,Field,model_validator
from app.api.dependencies import optional_user
router = APIRouter(tags=["Energy Copilot"])

class ChatMessage(BaseModel):
    role:Literal["user","assistant"]
    content:str=Field(min_length=1,max_length=1000)

class ChatRequest(BaseModel):
    messages:list[ChatMessage]=Field(min_length=1,max_length=12)
    tariff:float|None=Field(None,ge=0,le=100000,allow_inf_nan=False)
    factor:float|None=Field(None,ge=0,le=100,allow_inf_nan=False)
    @model_validator(mode="after")
    def last_user(self):
        if self.messages[-1].role!="user" or not self.messages[-1].content.strip():
            raise ValueError("Last message must be a nonempty user message")
        return self

@router.post("/api/agent/chat")
@router.post("/chat",include_in_schema=False)
def chat(body:ChatRequest,request:Request,username=Depends(optional_user)):
    return request.app.state.agent.chat([message.model_dump() for message in body.messages],username,body.tariff,body.factor)
