from fastapi import FastAPI, HTTPException, Body
from usuarios.DTO.dto import LoginRequest
from dotenv import load_dotenv
import os
load_dotenv()
from common.rabbitmq import MessageBroker
from .connection.database import engine
from common.database import Base
from .service import *  # 👈 esto importa y registra los message_pattern
from fastapi import Query
from .schema import UserCreateDTO,UserResponseOne
from fastapi import Form, UploadFile, File
from fastapi.responses import FileResponse

app = FastAPI()

raw_rabbit = os.getenv("RABBITMQ_URL")
if not raw_rabbit:
    raise RuntimeError("RABBITMQ_URL environment variable is not set")

# Expand possible ${VAR} placeholders from .env
RABBITMQ_URL = os.path.expandvars(raw_rabbit)

broker = MessageBroker(RABBITMQ_URL)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await broker.connect()
    await broker.subscribe_patterns()
    print("✅ Broker conectado y patrones suscritos")

@app.on_event("shutdown")
async def shutdown():
    await broker.close()
    print("🔻 Broker cerrado")



@app.post("/auth/login")
async def login_user(credentials: LoginRequest):
    try:
        payload = credentials.dict()
        result = await broker.rpc_request("auth.login", payload)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@app.get("/users")
async def get_users(page: int = Query(1, ge=1), 
                    page_size: int = Query(10, ge=1, le=100)):
    """
    Obtiene usuarios paginados.
    """
    try:
        payload = {"page": page, "page_size": page_size}
        result = await broker.rpc_request("users.get_all", payload)
        return result
    except Exception as e:
        print("❌ Error en /users:", e)
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/users")
async def create_user(user: UserCreateDTO):
    """
    Recibe el JSON de usuario, lo envía por RPC al broker y devuelve el resultado.
    """
    try:
        payload = user.dict()  # convierte a dict para el broker
        result = await broker.rpc_request("users.create", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# ✅ endpoint FastAPI
@app.get("/users/{user_id}", response_model=UserResponseOne)
async def get_user_by_id(user_id: int):
    try:
        payload = {"id": user_id}  # 👈 coincide con el handler
        result = await broker.rpc_request("users.get_by_id", payload)
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}
    

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """
    Elimina un usuario por ID.
    """
    try:
        payload = {"id": user_id}
        result = await broker.rpc_request("users.delete", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserCreateDTO):
    """
    Actualiza un usuario por ID.
    """
    try:
        payload = user.dict()
        payload["id"] = user_id  # incluir ID en el payload
        result = await broker.rpc_request("users.update", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/airesponse")
async def get_ai_response(prompt: str):
    """
    Obtiene una respuesta de la API de IA.
    """
    try:
        payload = {"prompt": prompt}
        result = await broker.rpc_request("ai.get_response", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/aitext")
async def get_ai_text(
    prompt: str = Body(..., embed=True)
):
    """
    Genera texto plano a partir de un prompt usando IA (Gemini).
    """
    try:
        payload = {"prompt": prompt}
        
        # Cambiamos el nombre del evento a algo más lógico: "ai.get_text"
        result = await broker.rpc_request("ai.get_text", payload)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        # Devolver el texto generado por Gemini
        if result.get("text"):
            return {
                "success": True,
                "text": result["text"],
                "message": result.get("message", "Text generated successfully")
            }
        else:
            return {"success": True, "message": result.get("message", "No text received")}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))