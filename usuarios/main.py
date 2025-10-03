import bcrypt
from fastapi import FastAPI, HTTPException, Body, Depends, APIRouter
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta
from typing import Dict
from .DTO.dto import LoginRequest  # Asegúrate de que DTO/model.py esté en el mismo directorio o ajusta la ruta

from .schema import *
from .service import *
from .connection.database import *









app = FastAPI()


app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# JWT Config
SECRET_KEY = "my-secret-key"
REFRESH_SECRET_KEY = "my-refresh-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7



# Contraseña real: "123456"
# Hash generado con: bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()




# Verificar password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode()
    return bcrypt.checkpw(plain_password.encode(), hashed_password)

# Autenticar usuario
# utils.py o auth.py

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db=db, email=email)  # ← aquí agregas await
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


# Crear JWT token
def create_token(data: Dict, expires_delta: timedelta, secret: str):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)



@app.post("/login")
async def login(
    login_data: LoginRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        secret=SECRET_KEY
    )

    refresh_token = create_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        secret=REFRESH_SECRET_KEY
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user
    }





# 🔐 Router protegido
# protected_router = APIRouter(
#     dependencies=[Depends(get_current_user)]
# )


# Rutas protegidas
@app.get("/users/", response_model=list[UserSchema])
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    return await get_users(db, skip, limit)

@app.get("/users/{user_id}", response_model=UserSchema)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{user_id}")
async def delete_user_route(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await delete_user(db, user_id)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")

        

# 👥 Registro (ruta pública)


@app.post("/users/")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_user_service(db, user)
    except HTTPException as http_exc:
        raise http_exc  # ✅ Correct way to pass along the error
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")
    
@app.put("/users/{user_id}")
async def update_users(user: UserSchema, user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await update_user(db, user_id, user)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")




# app.include_router(protected_router,prefix="/api")