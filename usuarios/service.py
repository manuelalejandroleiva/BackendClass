import json
import os 
import bcrypt
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError
from google import genai
from google.genai import types
from playsound import playsound

from .connection.database import engine, SessionLocal
from .models.models import User,Role
from common.rabbitmq import message_pattern
from .schema import UserCreateDTO

# --- Configuración Inicial ---
load_dotenv()

ALGORITHM = "HS256"
SECRET_KEY = "supersecretkey"  # ⚠️ Recuerda cambiarlo por una variable de entorno segura en producción
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Cliente Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# --- Funciones Auxiliares ---

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode()
    return bcrypt.checkpw(plain_password.encode(), hashed_password)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    # Convertimos a timestamp entero para asegurar máxima compatibilidad con JWT
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_role_by_id(db:AsyncSession,role:int):
    result=await db.execute(select(Role).where(Role.id==role))
    return result.scalar_one_or_none().name

async def get_all(session: AsyncSession, page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    result = await session.execute(select(User).offset(offset).limit(page_size))
    users = result.scalars().all()

    # Contamos total de registros para poder enviar info de paginación
    total_result = await session.execute(select(User))
    total = len(total_result.scalars().all())

    return users, total


# --- Handlers de Autenticación ---

@message_pattern("auth.login")
async def handle_login(payload):
    async with SessionLocal() as db:
        try:
            email = payload.get("email")
            password = payload.get("password")
            print(f"DEBUG LOGIN: email recibido={repr(email)}, password={repr(password)}")

            if not email or not password:
                return {"success": False, "message": "Email y contraseña son requeridos."}

            email = email.strip()
            user = await get_user_by_email(db, email)
            role=await get_role_by_id(db,user.role_id)
            print(f"DEBUG LOGIN: user encontrado={user.id if user else None}")
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}

            if not verify_password(password, user.password):
                return {"success": False, "message": "Contraseña incorrecta."}

            # Crear tokens
            access_token = create_token(
                {"sub": user.email, "id": user.id},
                expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
            )
            refresh_token = create_token(
                {"sub": user.email, "id": user.id, "type": "refresh"},
                expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            )

            # Guardar refresh token en la DB
            user.refresh_token = refresh_token
            db.add(user)
            await db.commit()

           

            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user":{
                    "id":user.id,
                    "name":user.name,
                    "email":user.email,
                    "phone":user.phone,
                    "role":role,
                    "image":user.image,
                    "address":user.address,
                }
#               
               
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

@message_pattern("auth.refresh")
async def handle_refresh_token(payload):
    async with SessionLocal() as db:
        try:
            refresh_token = payload.get("refresh_token")
            if not refresh_token:
                return {"success": False, "message": "Refresh token requerido."}

            # Decodificar y validar el refresh_token
            try:
                payload_data = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                email: str = payload_data.get("sub")
                token_type: str = payload_data.get("type")
                
                if email is None or token_type != "refresh":
                    return {"success": False, "message": "Token inválido."}
            except JWTError:
                return {"success": False, "message": "El token ha expirado o es inválido."}

            # Verificar que el usuario exista y que el token coincida con la DB
            user = await get_user_by_email(db, email)
            if not user or user.refresh_token != refresh_token:
                return {"success": False, "message": "Credenciales inválidas, inicia sesión nuevamente."}

            # Generar un NUEVO access token por 24 horas más
            new_access_token = create_token(
                {"sub": user.email, "id": user.id},
                expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
            )

            return {
                "success": True,
                "access_token": new_access_token
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


# --- Handlers de Usuarios y Compañías ---

@message_pattern("users.get_all")
async def handle_get_all(payload):
    page = payload.get("page", 1)
    page_size = payload.get("page_size", 10)

    async with SessionLocal() as session:
        users, total = await get_all(session, page, page_size)

        data = [
            u.to_dict(exclude={"password"})
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
    async with SessionLocal() as db:
        try:
            # Payload debe ser dict
            if isinstance(payload, str):
                payload = json.loads(payload)

            # Validación con Pydantic
            user_data = UserCreateDTO(**payload)

            # Hashear contraseña
            hashed_pw = hash_password(user_data.password)

            # Verificar si email ya existe
            existing_email = await db.scalar(select(User.id).where(User.email == user_data.email))
            if existing_email:
                return {"success": False, "message": "Ya existe un usuario con ese correo."}

            # Crear nuevo usuario
            new_user_data = user_data.dict(exclude={"id"})
            new_user_data["password"] = hashed_pw
            new_user_data["is_active"] = True if user_data.is_active is None else user_data.is_active
            new_user_data["is_verified"] = False if user_data.is_verified is None else user_data.is_verified

            new_user = User(**new_user_data)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            # Excluir password en la respuesta
            response = new_user.to_dict(exclude={"password"})

            return {"success": True, "data": response}

        except Exception as e:
            return {"success": False, "message": str(e)}

@message_pattern("users.get_by_id")
async def handle_get_by_id(payload):
    async with SessionLocal() as db:
        try:
            user_id = payload.get("id")
            if user_id is None:
                return {"success": False, "message": "Falta el ID en el payload."}

            user = await db.get(User, int(user_id))
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}

            user_data = user.to_dict(exclude={"password"})

            return {"success": True, "data": user_data}

        except Exception as e:
            return {"success": False, "message": str(e)}

@message_pattern("users.update")
async def handle_update_user(payload):
    async with SessionLocal() as db:
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

            user_response = user.to_dict(exclude={"password"})

            return {"success": True, "data": user_response}

        except Exception as e:
            return {"success": False, "message": str(e)}

@message_pattern("users.delete")
async def handle_delete_user(payload):
    async with SessionLocal() as db:
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


# --- Handlers de Inteligencia Artificial (Gemini) ---

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

@message_pattern("ai.get_text")
async def handle_aitextrequest(payload):
    # Ya tienes el cliente global arriba, pero si necesitas instanciarlo local:
    local_client = genai.Client()

    try:
        prompt = payload.get("prompt", "").strip()
        
        response = local_client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents="How does AI work?", # Ojo: Aquí estás hardcodeando el prompt. Cámbialo por la variable `prompt` si deseas que sea dinámico.
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="pro")
            ),
        )
        
        return {
            "success": True,
            "message": "Response generated successfully",
            "text": response.text
        }
    except Exception as e:
        return {"success": False, "message": f"Error interno en IA: {str(e)}"}