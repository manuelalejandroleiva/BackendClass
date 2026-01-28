import asyncio
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
import os
load_dotenv()
from common.rabbitmq import MessageBroker
from sqlalchemy.ext.asyncio import AsyncSession
from .connection.database import get_db, engine
from common.database import Base
from .schema import BuisnessCreate
from typing import Dict     
from fastapi.staticfiles import StaticFiles
from .service import *
from fastapi import Query

from fastapi import Depends, HTTPException



raw_rabbit = os.getenv("RABBITMQ_URL")
if not raw_rabbit:
    raise RuntimeError("RABBITMQ_URL environment variable is not set")

# Expand possible ${VAR} placeholders from .env
RABBITMQ_URL = os.path.expandvars(raw_rabbit)

broker = MessageBroker(RABBITMQ_URL)

app = FastAPI(
    title="My Buisness App",   # 👈 Aquí cambias el nombre
    description="API para gestionar negocios, licencias y usuarios",
    version="1.0.0"
)
@app.on_event("startup")
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
        result = await broker.rpc_request("buisness.create", payload)
        return result
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/buisness")
async def get_buisness(page: int = Query(1, ge=1), 
                    page_size: int = Query(10, ge=1, le=100)):
    """
    Obtiene usuarios paginados.
    """
    try:
        payload = {"page": page, "page_size": page_size}
        result = await broker.rpc_request("buisness.get_all", payload)
        return result
    except Exception as e:
        print("❌ Error en /users:", e)
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/buisness_id")
async def get_buisness_by_id(buisness_id:int):
   
    try:
        payload = {"id":buisness_id}
        result = await broker.rpc_request("buisness.get_by_id", payload)
        return result
    except Exception as e:
        print("❌ Error en /users:", e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/buisness/{buisness_id}")
async def delete_buisness(user_id: int):
    """
    Elimina un buissness por ID.
    """
    try:
        payload = {"id": user_id}
        result = await broker.rpc_request("buisness.delete", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.put("/buisness/{buissness_id}")
async def update_buisness(buisness_id: int, buisness: BuisnessUpdate):
    """
    Actualiza un usuario por ID.
    """
    try:
        payload = buisness.dict()
        payload["id"] = buisness_id  # incluir ID en el payload
        result = await broker.rpc_request("buisness.update", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



#Productos

@app.get("/productos")
async def get_buisness(page: int = Query(1, ge=1), 
                    page_size: int = Query(10, ge=1, le=100)):
    """
    Obtiene productos paginados.
    """
    try:
        payload = {"page": page, "page_size": page_size}
        result = await broker.rpc_request("products.get_all", payload)
        return result
    except Exception as e:
        print("❌ Error en /users:", e)
        raise HTTPException(status_code=500, detail=str(e))



    