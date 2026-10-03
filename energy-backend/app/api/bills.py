from fastapi import APIRouter,Depends,File,HTTPException,UploadFile
from starlette.concurrency import run_in_threadpool
from app.api.dependencies import require_user
from app.services.documents import analyze_bill,safe_filename
router = APIRouter(tags=["Bill analysis"])

async def read_upload(file):
    content = await file.read(12*1024*1024+1)
    if len(content)>12*1024*1024:
        raise HTTPException(413,"Upload must be at most 12 MB")
    return content

@router.post("/api/bills/analyze")
async def bill(file:UploadFile=File(...),username=Depends(require_user)):
    content = await read_upload(file)
    return await run_in_threadpool(analyze_bill,safe_filename(file.filename or "bill.pdf"),content)
