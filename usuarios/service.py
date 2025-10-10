import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from common.rabbitmq import RabbitMQPublisher
from .models.models import *
from .schema import *
from fastapi import HTTPException




def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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

    
