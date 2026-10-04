import json
from fastapi import APIRouter,Depends,Request
from pydantic import BaseModel,Field
from app.api.dependencies import optional_user
router = APIRouter(tags=["Corrective retrieval"])

class RagRequest(BaseModel):
    query:str=Field(min_length=1,max_length=1000)

@router.post("/api/rag/query")
def query(body:RagRequest,request:Request,username=Depends(optional_user)):
    state = request.app.state.rag.search(body.query,username)
    sources = state["sources"]
    local = "\n\n".join(f"[{row['citation']}] {row['source']}: {row['excerpt']}" for row in sources) or "No sufficiently relevant evidence found after corrective retrieval."
    generated = request.app.state.generator.answer([{"role":"user","content":body.query}],json.dumps(sources)) if sources else None
    return {"reply":generated or local,"sources":sources,"retrieval_trace":state["trace"],"mode":"ai" if generated else "local"}
