import re
from datetime import datetime,timedelta,timezone
import bcrypt
import jwt
from fastapi import APIRouter,HTTPException,Request
from pydantic import BaseModel,Field
from fastapi import Depends
from app.api.dependencies import require_user
router = APIRouter(prefix="/api/auth",tags=["Accounts"])

@router.get("/me")
def me(request:Request,username=Depends(require_user)):
    try:
        user=request.app.state.store.user(username)
    except Exception:
        raise HTTPException(503,"Account details are temporarily unavailable") from None
    if not user:
        raise HTTPException(401,"Account not found. Log in again.")
    return {"email":user["username"]}

class Credentials(BaseModel):
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=1,max_length=72)

@router.post("/signup",status_code=201)
def signup(body:Credentials,request:Request):
    username = body.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",username):
        raise HTTPException(400,"Enter a valid email address")
    if len(body.password)<8 or len(body.password.encode())>72:
        raise HTTPException(400,"Password must contain at least eight characters and at most 72 UTF-8 bytes")
    store = request.app.state.store
    try:
        if store.user(username):
            raise HTTPException(409,"Account already exists")
        store.add_user(username,bcrypt.hashpw(body.password.encode(),bcrypt.gensalt()).decode())
    except HTTPException:
        raise
    except Exception as error:
        if getattr(error,"pgcode",None)=="23505" or "UNIQUE constraint" in str(error):
            raise HTTPException(409,"Account already exists") from None
        raise HTTPException(503,"Account storage is unavailable; check persistence configuration") from None
    return {"msg":"Account created successfully"}

@router.post("/login")
def login(body:Credentials,request:Request):
    try:
        user = request.app.state.store.user(body.email.strip().lower())
    except Exception:
        raise HTTPException(503,"Account storage is unavailable; check persistence configuration") from None
    valid = False
    if user and len(body.password.encode())<=72:
        try:
            valid = bcrypt.checkpw(body.password.encode(),user["password"].encode())
        except ValueError:
            pass
    if not valid:
        raise HTTPException(401,"Invalid email or password")
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub":user["username"],"iat":now,"exp":now+timedelta(hours=8)},request.app.state.secret,algorithm="HS256")
    return {"token":token}
