from collections import Counter
from starlette.concurrency import run_in_threadpool
from fastapi import APIRouter,Depends,File,HTTPException,Request,UploadFile
from app.api.dependencies import require_user
from app.api.bills import read_upload
from app.services.documents import extract_text,safe_filename
router = APIRouter(tags=["Personal documents"])

@router.get("/api/documents")
def documents(request:Request,username=Depends(require_user)):
    counts = Counter(row["source_name"] for row in request.app.state.store.chunks(username))
    return {"documents":[{"source":name,"chunks":count} for name,count in counts.items()]}

@router.post("/api/documents",status_code=201)
async def upload_document(request:Request,file:UploadFile=File(...),username=Depends(require_user)):
    name = safe_filename(file.filename or "")
    if not name:
        raise HTTPException(400,"Choose a document")
    content = await read_upload(file)
    text = await run_in_threadpool(extract_text,name,content)
    try:
        count = await run_in_threadpool(request.app.state.store.index_document,username,name,text)
    except ValueError:
        raise
    except Exception:
        raise HTTPException(503,"Personal document storage is unavailable") from None
    return {"source":name,"chunks":count}

@router.delete("/api/documents/{source_name}")
def remove(source_name:str,request:Request,username=Depends(require_user)):
    if not request.app.state.store.delete_document(username,safe_filename(source_name)):
        raise HTTPException(404,"Document not found")
    return {"deleted":True}
