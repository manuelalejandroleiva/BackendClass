from fastapi import FastAPI, HTTPException, Query
from fastapi import Body
from dotenv import load_dotenv
import os
load_dotenv()
from common.rabbitmq import MessageBroker
from common.database import Base
from .connection.database import engine
from .service import *
from .schema import SaleCreate, SaleResponse, SaleItemCreate
from typing import Optional

raw_rabbit = os.getenv("RABBITMQ_URL")
if not raw_rabbit:
    raise RuntimeError("RABBITMQ_URL environment variable is not set")

RABBITMQ_URL = os.path.expandvars(raw_rabbit)
broker = MessageBroker(RABBITMQ_URL)

app = FastAPI(title="Inventory Service", description="Ventas POS y gestión de inventario", version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await broker.connect()
    await broker.subscribe_patterns()
    print("✅ Inventory Service: Broker conectado")

@app.on_event("shutdown")
async def shutdown():
    await broker.close()
    print("🔻 Inventory Service: Broker cerrado")


@app.post("/sales/create")
async def create_sale(sale: SaleCreate = Body(...)):
    try:
        payload = sale.dict()
        result = await broker.rpc_request("inventory.sale.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/{business_id}")
async def get_sales(business_id: int):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("inventory.sale.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/report/period")
async def sales_report_period(business_id: int = Query(...)):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("inventory.sales.report.period", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/report/top-products")
async def top_products(business_id: int = Query(...), limit: int = Query(10, ge=1, le=50)):
    try:
        payload = {"business_id": business_id, "limit": limit}
        result = await broker.rpc_request("inventory.sales.report.top_products", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/report/summary")
async def sales_summary(business_id: int = Query(...)):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("inventory.sales.report.summary", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    




@app.patch("/products/{product_id}/stock")
async def update_stock(product_id: int, data: dict = Body(...)):
    try:
        payload = {"product_id": product_id, "quantity": data.get("quantity", 0)}
        result = await broker.rpc_request("inventory.product.update_stock", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/products/{product_id}")
async def update_product(product_id: int, data: dict = Body(...)):
    try:
        data["product_id"] = product_id
        result = await broker.rpc_request("inventory.product.update", data)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
