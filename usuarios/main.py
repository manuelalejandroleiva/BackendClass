from fastapi import FastAPI, HTTPException
from usuarios.DTO.dto import LoginRequest
from common.rabbitmq import MessageBroker
from .connection.database import engine, Base
from .service import *  # 👈 esto importa y registra los message_pattern
from fastapi import Query
from .schema import UserCreateDTO,UserResponseOne

app = FastAPI()

broker = MessageBroker("amqp://guest:guest@localhost:5672/")

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
        result = await broker.rpc_request("companies.get_all", payload)
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
