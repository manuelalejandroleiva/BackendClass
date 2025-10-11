from datetime import datetime, timedelta
from typing import Dict
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from common.rabbitmq import RabbitMQPublisher
from .models.models import *
from .schema import *
from jose import jwt
from fastapi import HTTPException
import os 

from dotenv import load_dotenv

load_dotenv()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')



  



# Contraseña real: "123456"
# Hash generado con: bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()


ALGORITHM = os.getenv("ALGORITHM", "HS256")



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





async def create_user_service(db: AsyncSession, user: UserSchema):
    # 🔒 Hashear la contraseña
    hashed_pw = hash_password(user.password)

    # 🔍 Verificar si el correo ya existe
    existing_email = await db.scalar(select(User.id).where(User.email == user.email))
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un usuario registrado con ese correo electrónico."
        )

    # 🧱 Crear el nuevo usuario con valores booleanos correctos
    new_user_data = user.dict(exclude={"id"})
    new_user_data["password"] = hashed_pw
    new_user_data["is_active"] = True if user.is_active is None else user.is_active
    new_user_data["is_verified"] = False if user.is_verified is None else user.is_verified

    new_user = User(**new_user_data)

    # 💾 Guardar en la base de datos
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))

    return result.scalar_one_or_none()



async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(User).offset(skip).limit(limit))

    return result.scalars().all()

async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
        return user
    else:
         raise  HTTPException(
            status_code=400,
            detail="Usuario no encontrado."
        )
    

async def update_user(db: AsyncSession, user_id: int, user_data: UserSchema):
    result = await db.execute(select(User).where(User.id == user_id))
    result_email=await db.execute(select(User).where(User.email==user_data.email))
    existing_user = result.scalar_one_or_none()
    existing_email=result_email.scalar_one_or_none()
    if not existing_user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado.")
    if  existing_email:
        raise HTTPException(status_code=400, detail="El email insertado ya le pertenece a otro usuario")

    # Actualizar campos del usuario con los datos del esquema
    for field, value in user_data.dict(exclude_unset=True,exclude={"id"}).items():
        setattr(existing_user, field, value)

    await db.commit()
    await db.refresh(existing_user)
    return {
        'id':existing_user.id,
        'address':existing_user.address,
        'phone':existing_user.phone,
        'name':existing_user.name,
        'email':existing_user.email,
        'is_active':existing_user.is_active
    }

    
