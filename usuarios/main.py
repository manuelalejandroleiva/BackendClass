import os
import bcrypt
from fastapi import FastAPI, HTTPException, Body, Depends, APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta
from typing import Dict
from .DTO.dto import LoginRequest  # Asegúrate de que DTO/model.py esté en el mismo directorio o ajusta la ruta

from .schema import *
from .service import *
from .connection.database import *




load_dotenv()




app = FastAPI()


app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    


# JWT Config
SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")

ACCESS_TOKEN_EXPIRE_MINUTES = 60*24  # 1 día
REFRESH_TOKEN_EXPIRE_DAYS = 7   # 7 días 



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
        "user": UserResponse.model_validate(user, from_attributes=True)#Ojo mirar aca para eliminar algo de un DTO

    }








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


@app.post("/users/create/")
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