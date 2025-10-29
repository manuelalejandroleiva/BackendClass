import asyncio
import uvicorn
from fastapi import FastAPI
from common.rabbitmq import MessageBroker
from sqlalchemy.ext.asyncio import AsyncSession
from .connection.database import get_db, engine, Base
from .schema import BuisnessCreate
from typing import Dict     
from fastapi.staticfiles import StaticFiles

from fastapi import Depends, HTTPException



broker = MessageBroker("amqp://guest:guest@localhost:5672/")

app = FastAPI(
    title="My Buisness App",   # 👈 Aquí cambias el nombre
    description="API para gestionar negocios, licencias y usuarios",
    version="1.0.0"
)
app.on_event("startup")
async def startup():
    # Crear las tablas en la base de datos al iniciar la aplicación
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 🔹 Arrancar el consumer en segundo plano
    await broker.connect()
    await broker.subscribe_patterns()
   

@app.on_event("shutdown")
async def shutdown():
    await broker.close()
    print("🔻 Broker cerrado")
   

@app.post("/buisness_create")
async def create_buisness(buisness: BuisnessCreate):
    payload = buisness.dict(exclude_unset=True)
    try:
        # timeout más alto para pruebas
        result = await broker.rpc_request("buisness.create", payload, timeout=30)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout en RPC con broker")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


    