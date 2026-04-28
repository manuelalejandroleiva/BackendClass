from fastapi import FastAPI, HTTPException, Query, Body
from dotenv import load_dotenv
import os
load_dotenv()
from common.rabbitmq import MessageBroker
from common.database import Base
from .connection.database import engine
from .service import *
from .schema import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    RentalCreate, RentalUpdate, RentalResponse,
    GeofenceCreate, GeofenceUpdate, GeofenceResponse,
    TrackingUpdate, TrackingResponse,
    GPSLocationResponse, GeofenceAlertResponse
)
from typing import Optional

raw_rabbit = os.getenv("RABBITMQ_URL")
if not raw_rabbit:
    raise RuntimeError("RABBITMQ_URL environment variable is not set")

RABBITMQ_URL = os.path.expandvars(raw_rabbit)
broker = MessageBroker(RABBITMQ_URL)

app = FastAPI(title="Rents Service", description="Gestión de rentals de vehículos con GPS tracking", version="1.0.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await broker.connect()
    await broker.subscribe_patterns()
    print("✅ Rents Service: Broker conectado")


@app.on_event("shutdown")
async def shutdown():
    await broker.close()
    print("🔻 Rents Service: Broker cerrado")


@app.post("/vehicles", response_model=dict)
async def create_vehicle(vehicle: VehicleCreate = Body(...)):
    try:
        payload = vehicle.dict()
        result = await broker.rpc_request("rents.vehicle.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vehicles")
async def get_vehicles(status: Optional[str] = Query(None)):
    try:
        payload = {}
        if status:
            payload["status"] = status
        result = await broker.rpc_request("rents.vehicle.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int):
    try:
        payload = {"id": vehicle_id}
        result = await broker.rpc_request("rents.vehicle.get_by_id", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: int, vehicle: VehicleUpdate = Body(...)):
    try:
        payload = vehicle.dict(exclude_unset=True)
        payload["id"] = vehicle_id
        result = await broker.rpc_request("rents.vehicle.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int):
    try:
        payload = {"id": vehicle_id}
        result = await broker.rpc_request("rents.vehicle.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tracking/update")
async def update_tracking(tracking: TrackingUpdate = Body(...)):
    try:
        payload = tracking.dict()
        result = await broker.rpc_request("rents.tracking.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tracking/{vehicle_id}/current")
async def get_current_location(vehicle_id: int):
    try:
        payload = {"vehicle_id": vehicle_id}
        result = await broker.rpc_request("rents.tracking.get_current", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tracking/{vehicle_id}/history")
async def get_tracking_history(
    vehicle_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    try:
        payload = {
            "vehicle_id": vehicle_id,
            "limit": limit
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        result = await broker.rpc_request("rents.tracking.get_history", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rentals")
async def create_rental(rental: RentalCreate = Body(...)):
    try:
        payload = rental.dict()
        result = await broker.rpc_request("rents.rental.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rentals/{rental_id}/complete")
async def complete_rental(
    rental_id: int,
    end_latitude: Optional[float] = Body(None),
    end_longitude: Optional[float] = Body(None),
    rate_per_hour: Optional[float] = Body(10.0)
):
    try:
        payload = {"rental_id": rental_id}
        if end_latitude is not None:
            payload["end_latitude"] = end_latitude
        if end_longitude is not None:
            payload["end_longitude"] = end_longitude
        if rate_per_hour is not None:
            payload["rate_per_hour"] = rate_per_hour
        result = await broker.rpc_request("rents.rental.complete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rentals")
async def get_rentals(
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None)
):
    try:
        payload = {}
        if status:
            payload["status"] = status
        if user_id:
            payload["user_id"] = user_id
        if vehicle_id:
            payload["vehicle_id"] = vehicle_id
        result = await broker.rpc_request("rents.rental.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/geofences")
async def create_geofence(geofence: GeofenceCreate = Body(...)):
    try:
        payload = geofence.dict()
        result = await broker.rpc_request("rents.geofence.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/geofences")
async def get_geofences(vehicle_id: Optional[int] = Query(None)):
    try:
        payload = {}
        if vehicle_id:
            payload["vehicle_id"] = vehicle_id
        result = await broker.rpc_request("rents.geofence.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/geofences/{geofence_id}")
async def delete_geofence(geofence_id: int):
    try:
        payload = {"id": geofence_id}
        result = await broker.rpc_request("rents.geofence.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts")
async def get_alerts(
    vehicle_id: Optional[int] = Query(None),
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    try:
        payload = {"limit": limit}
        if vehicle_id:
            payload["vehicle_id"] = vehicle_id
        if is_read is not None:
            payload["is_read"] = is_read
        result = await broker.rpc_request("rents.alerts.get", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int):
    try:
        payload = {"alert_id": alert_id}
        result = await broker.rpc_request("rents.alerts.mark_read", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))