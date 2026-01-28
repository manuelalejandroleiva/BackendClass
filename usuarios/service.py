import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .connection.database import engine
from .models.models import User
from common.rabbitmq import message_pattern
import bcrypt
from datetime import datetime, timedelta,timezone
from .schema import UserCreateDTO
from jose import jwt

import os 
from dotenv import load_dotenv
from google import genai
from playsound import playsound


import re
from google.genai import types



ALGORITHM = "HS256"
SECRET_KEY = "supersecretkey"  # ⚠️ cámbialo por tu valor real
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode()
    return bcrypt.checkpw(plain_password.encode(), hashed_password)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)+expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

ACCESS_TOKEN_EXPIRE_HOURS = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7

@message_pattern("auth.login")
async def handle_login(payload):
    async with AsyncSession(engine) as db:
        try:
            email = payload.get("email")
            password = payload.get("password")

            if not email or not password:
                return {"success": False, "message": "Email y contraseña son requeridos."}

            user = await get_user_by_email(db, email)
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}

            if not verify_password(password, user.password):
                return {"success": False, "message": "Contraseña incorrecta."}

            # ✅ Crear tokens
            access_token = create_token(
                {"sub": user.email, "id": user.id},
                expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
            )
            refresh_token = create_token(
                {"sub": user.email, "id": user.id, "type": "refresh"},
                expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            )

            # ✅ Guardar refresh token en la DB
            user.refresh_token = refresh_token
            db.add(user)
            await db.commit()

            user_data = {
                k: v for k, v in user.__dict__.items()
                if k not in ("_sa_instance_state", "password")
            }

            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_data
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')



async def get_all(session: AsyncSession, page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    result = await session.execute(select(User).offset(offset).limit(page_size))
    users = result.scalars().all()

    # Contamos total de registros para poder enviar info de paginación
    total_result = await session.execute(select(User))
    total = len(total_result.scalars().all())

    return users, total


@message_pattern("companies.get_all")
async def handle_get_all(payload):
    
    page = payload.get("page", 1)
    page_size = payload.get("page_size", 10)

    async with AsyncSession(engine) as session:
        users, total = await get_all(session, page, page_size)

        data = [
            {k: v for k, v in u.__dict__.items() if k not in ("_sa_instance_state","password") }
            for u in users
        ]

        response = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "data": data
        }

       
        return response
    



@message_pattern("users.create")
async def handle_create_user(payload):
    async with AsyncSession(engine) as db:
        try:
            # ⚡ Payload debe ser dict
            if isinstance(payload, str):
                payload = json.loads(payload)

            # Validación con Pydantic
            user_data = UserCreateDTO(**payload)

            # 🔒 Hashear contraseña
            hashed_pw = hash_password(user_data.password)

            # 🔍 Verificar si email ya existe
            existing_email = await db.scalar(select(User.id).where(User.email == user_data.email))
            if existing_email:
                return {"success": False, "message": "Ya existe un usuario con ese correo."}

            # 🧱 Crear nuevo usuario
            new_user_data = user_data.dict(exclude={"id"})
            new_user_data["password"] = hashed_pw
            new_user_data["is_active"] = True if user_data.is_active is None else user_data.is_active
            new_user_data["is_verified"] = False if user_data.is_verified is None else user_data.is_verified

            new_user = User(**new_user_data)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            # ⚠ Excluir password en la respuesta
            response = {k: v for k, v in new_user.__dict__.items() if k not in ("_sa_instance_state", "password")}

            return {"success": True, "data": response}

        except Exception as e:
            return {"success": False, "message": str(e)}


# ✅ handler RabbitMQ
@message_pattern("users.get_by_id")
async def handle_get_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            user_id = payload.get("id")
            if user_id is None:
                return {"success": False, "message": "Falta el ID en el payload."}

            user = await db.get(User, int(user_id))
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}

            user_data = {
                k: v for k, v in user.__dict__.items()
                if k not in ("_sa_instance_state", "password")
            }

            return {"success": True, "data": user_data}

        except Exception as e:
            return {"success": False, "message": str(e)}
        

@message_pattern("users.delete")
async def handle_delete_user(payload):
    async with AsyncSession(engine) as db:
        try:
            user_id = payload.get("id")
            if user_id is None:
                return {"success": False, "message": "Falta el ID en el payload."}

            user = await db.get(User, int(user_id))
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}

            await db.delete(user)
            await db.commit()

            return {"success": True, "message": "Usuario eliminado correctamente."}

        except Exception as e:
            return {"success": False, "message": str(e)}

@message_pattern("users.update")
async def handle_update_user(payload):
    async with AsyncSession(engine) as db:
        try:
            user_id = payload.get("id")
            if user_id is None:
                return {"success": False, "message": "Falta el ID en el payload."}

            user = await db.get(User, int(user_id))
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}

            # Validación con Pydantic
            user_data = UserCreateDTO(**payload)

            update_data = user_data.dict(exclude_unset=True, exclude={"id", "password"})
            for key, value in update_data.items():
                setattr(user, key, value)

            # Si se proporciona una nueva contraseña, hashearla
            if user_data.password:
                user.password = hash_password(user_data.password)

            db.add(user)
            await db.commit()
            await db.refresh(user)

            user_response = {k: v for k, v in user.__dict__.items() if k not in ("_sa_instance_state", "password")}

            return {"success": True, "data": user_response}

        except Exception as e:
            return {"success": False, "message": str(e)}
        



@message_pattern("ai.get_response")
async def handle_airequest(payload):
    try:
        prompt = payload.get("prompt", "").strip()
        if not prompt:
            return {"success": False, "message": "El prompt es requerido."}
        
        # Convertir a string por seguridad
        prompt_str = str(prompt) + ("?" if "?" not in str(prompt) else "")
        
        # Generar contenido
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt_str
        )

        return {
            "success": True, 
            "response": response.text
            }

    except Exception as e:
        return {"success": False, "message": f"Error en Gemini API: {str(e)}"}





@message_pattern("ai.get_image")
async def handle_aiimagerequest(payload):
    try:
        print(payload)
        payload_work=payload.get("prompt", "").strip()
        
        model = "gemini-2.5-flash-image"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""INSERT_INPUT_HERE"""),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
            image_config=types.ImageConfig(
                image_size="1K",
            ),
        )

        file_index = 0
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            for modality in chunk.response_modalities:
                if modality.type == types.ModalityType.IMAGE:
                    for image in modality.images:
                        image_data = image.image_bytes
                        image_filename = f"generated_image_{file_index}.png"
                        with open(image_filename, "wb") as img_file:
                            img_file.write(image_data)
                        file_index += 1
                        return {
                            "success": True,
                            "image_filename": image_filename
                        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
