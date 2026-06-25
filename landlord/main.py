import asyncio
from fastapi import FastAPI, HTTPException, Query, Body
from dotenv import load_dotenv
import os
load_dotenv()
from common.rabbitmq import MessageBroker
from common.database import Base
from .connection.database import engine
from .service import *
from .schema import (
    PropertyCreate, PropertyUpdate, PropertyResponse,
    TenantCreate, TenantUpdate, TenantResponse,
    PaymentCreate, PaymentUpdate, PaymentResponse,
    ClassificationUpdate
)
from typing import Optional
from fastapi.encoders import jsonable_encoder

raw_rabbit = os.getenv("RABBITMQ_URL")
if not raw_rabbit:
    raise RuntimeError("RABBITMQ_URL environment variable is not set")

RABBITMQ_URL = os.path.expandvars(raw_rabbit)
broker = MessageBroker(RABBITMQ_URL)

app = FastAPI(title="Landlord Service", description="Gestión de propiedades, inquilinos y pagos", version="1.0.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await broker.connect()
    await broker.subscribe_patterns()
    print("✅ Landlord Service: Broker conectado")


@app.on_event("shutdown")
async def shutdown():
    await broker.close()
    print("🔻 Landlord Service: Broker cerrado")


# ===================== PROPERTIES =====================

@app.post("/properties", response_model=dict)
async def create_property(prop: PropertyCreate = Body(...)):
    try:
        payload = prop.dict()
        result = await broker.rpc_request("landlord.property.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties")
async def get_properties(landlord_id: Optional[int] = Query(None)):
    try:
        payload = {}
        if landlord_id:
            payload["landlord_id"] = landlord_id
        result = await broker.rpc_request("landlord.property.get_all", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties/{property_id}")
async def get_property(property_id: int):
    try:
        payload = {"id": property_id}
        result = await broker.rpc_request("landlord.property.get_by_id", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/properties/{property_id}")
async def update_property(property_id: int, prop: PropertyUpdate = Body(...)):
    try:
        payload = prop.dict(exclude_unset=True)
        payload["id"] = property_id
        result = await broker.rpc_request("landlord.property.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/properties/{property_id}")
async def delete_property(property_id: int):
    try:
        payload = {"id": property_id}
        result = await broker.rpc_request("landlord.property.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== TENANTS =====================

@app.post("/tenants", response_model=dict)
async def create_tenant(tenant: TenantCreate = Body(...)):
    try:
        payload = tenant.model_dump(mode='json')
        result = await broker.rpc_request("landlord.tenant.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tenants")
async def get_tenants(
    property_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    try:
        payload = {}
        if property_id:
            payload["property_id"] = property_id
        if status:
            payload["status"] = status
        result = await broker.rpc_request("landlord.tenant.get_all", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: int):
    try:
        payload = {"id": tenant_id}
        result = await broker.rpc_request("landlord.tenant.get_by_id", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: int, tenant: TenantUpdate = Body(...)):
    try:
        payload = tenant.dict(exclude_none=True)
        payload["id"] = tenant_id
        result = await broker.rpc_request("landlord.tenant.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: int):
    try:
        payload = {"id": tenant_id}
        result = await broker.rpc_request("landlord.tenant.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== PAYMENTS =====================

@app.post("/payments", response_model=dict)
async def create_payment(payment: PaymentCreate = Body(...)):
    try:
        # jsonable_encoder previene errores de serialización del objeto date
        payload = jsonable_encoder(payment)
        
        result = await broker.rpc_request("landlord.payment.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
        
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="El servicio de pagos no respondió a tiempo (timeout)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/payments")
async def get_payments(
    tenant_id: Optional[int] = Query(None)
):
    try:
        payload = {}
        if tenant_id:
            payload["tenant_id"] = tenant_id
        result = await broker.rpc_request("landlord.payment.get_all", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="El servicio de pagos no respondió a tiempo (timeout)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/payments/{payment_id}")
async def get_payment(payment_id: int):
    try:
        payload = {"id": payment_id}
        result = await broker.rpc_request("landlord.payment.get_by_id", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="El servicio de pagos no respondió a tiempo (timeout)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/payments/{payment_id}")
async def update_payment(payment_id: int, payment: PaymentUpdate = Body(...)):
    try:
        payload = payment.dict(exclude_unset=True)
        payload["id"] = payment_id
        result = await broker.rpc_request("landlord.payment.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="El servicio de pagos no respondió a tiempo (timeout)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/payments/{payment_id}")
async def delete_payment(payment_id: int):
    try:
        payload = {"id": payment_id}
        result = await broker.rpc_request("landlord.payment.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="El servicio de pagos no respondió a tiempo (timeout)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== CLASSIFICATION =====================

@app.post("/classification/{tenant_id}")
async def update_classification(tenant_id: int, data: ClassificationUpdate = Body(...)):
    try:
        payload = data.dict()
        payload["tenant_id"] = tenant_id
        result = await broker.rpc_request("landlord.classification.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classification/auto")
async def auto_classify(tenant_id: Optional[int] = Body(None)):
    try:
        payload = {}
        if tenant_id:
            payload["tenant_id"] = tenant_id
        result = await broker.rpc_request("landlord.classification.auto", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))