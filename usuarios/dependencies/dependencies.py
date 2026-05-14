from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from usuarios.connection.database import SessionLocal
from usuarios.service import get_user_by_email
oauth2_scheme = HTTPBearer()

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(oauth2_scheme)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    async with SessionLocal() as db:
        user = await get_user_by_email(db, email)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
