import jwt
from fastapi import Depends,HTTPException,Request
from fastapi.security import HTTPBearer
bearer = HTTPBearer(auto_error=False)

def energy(request:Request):
    return request.app.state.energy

def optional_user(request:Request,credentials=Depends(bearer)):
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials,request.app.state.secret,algorithms=["HS256"],options={"require":["exp","sub"]})
        username = payload["sub"]
        if not isinstance(username,str) or len(username)>254:
            raise ValueError("Invalid identity")
        return username
    except (jwt.PyJWTError,ValueError):
        raise HTTPException(401,"Your login session is missing or expired. Log in again.") from None

def require_user(username=Depends(optional_user)):
    if username is None:
        raise HTTPException(401,"Log in to access personal documents")
    return username
