from fastapi import FastAPI, HTTPException, Query, Body
from dotenv import load_dotenv
import os
load_dotenv()
from common.rabbitmq import MessageBroker
from common.database import Base
from .connection.database import engine
from .service import *
from .schema import OrderCreate, TableCreate, StatusUpdate
from typing import Optional

raw_rabbit = os.getenv("RABBITMQ_URL")
if not raw_rabbit:
    raise RuntimeError("RABBITMQ_URL environment variable is not set")

RABBITMQ_URL = os.path.expandvars(raw_rabbit)
broker = MessageBroker(RABBITMQ_URL)

app = FastAPI(title="Orders Service", description="Gestión de pedidos y mesas de restaurante", version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await broker.connect()
    await broker.subscribe_patterns()
    print("✅ Orders Service: Broker conectado")

@app.on_event("shutdown")
async def shutdown():
    await broker.close()
    print("🔻 Orders Service: Broker cerrado")


@app.post("/tables")
async def create_table(table: TableCreate = Body(...)):
    try:
        payload = table.dict()
        result = await broker.rpc_request("orders.table.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tables/{business_id}")
async def get_tables(business_id: int, available_only: bool = Query(False)):
    try:
        payload = {"business_id": business_id, "available_only": available_only}
        result = await broker.rpc_request("orders.table.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orders")
async def create_order(order: OrderCreate = Body(...)):
    try:
        payload = order.dict()
        result = await broker.rpc_request("orders.order.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{business_id}")
async def get_orders(
    business_id: int,
    table_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    try:
        payload = {"business_id": business_id}
        if table_id:
            payload["table_id"] = table_id
        if status:
            payload["status"] = status
        result = await broker.rpc_request("orders.order.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/detail/{order_id}")
async def get_order_detail(order_id: int):
    try:
        payload = {"order_id": order_id}
        result = await broker.rpc_request("orders.order.get_by_id", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: int, status_update: StatusUpdate = Body(...)):
    try:
        payload = {"order_id": order_id, "status": status_update.status}
        result = await broker.rpc_request("orders.order.update_status", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
