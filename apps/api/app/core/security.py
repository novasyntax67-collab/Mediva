from fastapi import HTTPException, status, Request
from jose import JWTError, jwt
from app.core.config import settings

def get_current_user(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user
