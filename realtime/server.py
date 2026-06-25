import socketio
import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25,
    async_handlers=True
)

sio_app = FastAPI()


# ============== Socket.IO Events ==============

@sio.event
async def connect(sid, environ):
    print(f"Cliente conectado: {sid}")
    await sio.emit("connected", {"sid": sid, "timestamp": datetime.utcnow().isoformat()})


@sio.event
async def disconnect(sid):
    print(f"Cliente desconectado: {sid}")


@sio.event
async def authenticate(sid, data):
    user_type = data.get("user_type")
    user_id = data.get("user_id")
    vehicle_id = data.get("vehicle_id")
    
    if user_type == "user":
        await sio.enter_room(sid, f"user_{user_id}")
    elif user_type == "driver":
        await sio.enter_room(sid, f"driver_{user_id}")
        if vehicle_id:
            await sio.enter_room(sid, f"vehicle_{vehicle_id}")
    
    return {"success": True, "message": f"Autenticado como {user_type}"}


@sio.event
async def join_vehicle(sid, data):
    vehicle_id = data.get("vehicle_id")
    if vehicle_id:
        await sio.enter_room(sid, f"vehicle_{vehicle_id}")
    return {"success": True}


@sio.event
async def leave_vehicle(sid, data):
    vehicle_id = data.get("vehicle_id")
    if vehicle_id:
        await sio.leave_room(sid, f"vehicle_{vehicle_id}")
    return {"success": True}


@sio.event
async def request_location(sid, data):
    vehicle_id = data.get("vehicle_id")
    user_id = data.get("user_id")
    await sio.emit("location_request", {"user_id": user_id}, room=f"vehicle_{vehicle_id}")
    return {"success": True, "message": "Solicitud enviada"}


@sio.event
async def join_business(sid, data):
    business_id = data.get("business_id")
    if business_id:
        await sio.enter_room(sid, f"business_{business_id}")
    return {"success": True}



# ============== Emit Functions ==============

async def emit_reservation_created(rental_id: int, vehicle_id: int, user_id: int, status: str = "pending"):
    data = {
        "rental_id": rental_id,
        "vehicle_id": vehicle_id,
        "user_id": user_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    await sio.emit("reservation_created", data, room=f"vehicle_{vehicle_id}")


async def emit_reservation_accepted(rental_id: int, driver_id: int, vehicle_id: int, user_id: int):
    data = {
        "rental_id": rental_id,
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    await sio.emit("reservation_accepted", data, room=f"user_{user_id}")


async def emit_tracking_update(vehicle_id: int, latitude: float, longitude: float, speed: float = 0, 
                      heading: float = None, battery_level: float = None):
    data = {
        "vehicle_id": vehicle_id,
        "latitude": latitude,
        "longitude": longitude,
        "speed": speed,
        "timestamp": datetime.utcnow().isoformat()
    }
    if heading:
        data["heading"] = heading
    if battery_level:
        data["battery_level"] = battery_level
    
    await sio.emit("tracking_update", data, room=f"vehicle_{vehicle_id}")


async def emit_rental_started(rental_id: int, vehicle_id: int, user_id: int):
    await sio.emit("rental_started", {
        "rental_id": rental_id,
        "vehicle_id": vehicle_id,
        "timestamp": datetime.utcnow().isoformat()
    }, room=f"user_{user_id}")


async def emit_rental_completed(rental_id: int, vehicle_id: int, user_id: int, 
                           total_distance: float, total_cost: float):
    await sio.emit("rental_completed", {
        "rental_id": rental_id,
        "vehicle_id": vehicle_id,
        "total_distance": total_distance,
        "total_cost": total_cost,
        "timestamp": datetime.utcnow().isoformat()
    }, room=f"user_{user_id}")


async def emit_geofence_alert(vehicle_id: int, alert_type: str, message: str, 
                           latitude: float, longitude: float):
    await sio.emit("geofence_alert", {
        "vehicle_id": vehicle_id,
        "alert_type": alert_type,
        "message": message,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": datetime.utcnow().isoformat()
    }, room=f"vehicle_{vehicle_id}")


async def emit_notification(user_id: int, title: str, body: str, data: Dict = None):
    await sio.emit("notification", {
        "title": title,
        "body": body,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }, room=f"user_{user_id}")


async def emit_business_event(event_type: str, entity_type: str, data: dict, business_id: int):
    event_data = {
        "event_type": event_type,
        "entity_type": entity_type,
        "data": data,
        "business_id": business_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    await sio.emit("business_event", event_data, room=f"business_{business_id}")


# ============== FastAPI Routes ==============

@sio_app.get("/health")
async def health():
    return {"status": "ok", "service": "realtime"}


@sio_app.post("/internal/emit_reservation_created")
async def internal_reservation_created(request: Request):
    data = await request.json()
    await emit_reservation_created(
        data.get("rental_id"),
        data.get("vehicle_id"),
        data.get("user_id"),
        data.get("status", "pending")
    )
    return JSONResponse({"success": True})


@sio_app.post("/internal/emit_reservation_accepted")
async def internal_reservation_accepted(request: Request):
    data = await request.json()
    await emit_reservation_accepted(
        data.get("rental_id"),
        data.get("driver_id"),
        data.get("vehicle_id"),
        data.get("user_id")
    )
    return JSONResponse({"success": True})


@sio_app.post("/internal/emit_tracking_update")
async def internal_tracking_update(request: Request):
    data = await request.json()
    await emit_tracking_update(
        data.get("vehicle_id"),
        data.get("latitude"),
        data.get("longitude"),
        data.get("speed", 0),
        data.get("heading"),
        data.get("battery_level")
    )
    return JSONResponse({"success": True})


@sio_app.post("/internal/emit_rental_started")
async def internal_rental_started(request: Request):
    data = await request.json()
    await emit_rental_started(
        data.get("rental_id"),
        data.get("vehicle_id"),
        data.get("user_id")
    )
    return JSONResponse({"success": True})


@sio_app.post("/internal/emit_rental_completed")
async def internal_rental_completed(request: Request):
    data = await request.json()
    await emit_rental_completed(
        data.get("rental_id"),
        data.get("vehicle_id"),
        data.get("user_id"),
        data.get("total_distance"),
        data.get("total_cost")
    )
    return JSONResponse({"success": True})


@sio_app.post("/internal/emit_geofence_alert")
async def internal_geofence_alert(request: Request):
    data = await request.json()
    await emit_geofence_alert(
        data.get("vehicle_id"),
        data.get("alert_type"),
        data.get("message"),
        data.get("latitude"),
        data.get("longitude")
    )
    return JSONResponse({"success": True})


@sio_app.post("/internal/emit_notification")
async def internal_notification(request: Request):
    data = await request.json()
    await emit_notification(
        data.get("user_id"),
        data.get("title"),
        data.get("body"),
        data.get("data")
    )
    return JSONResponse({"success": True})


@sio_app.post("/internal/emit_business_event")
async def internal_business_event(request: Request):
    data = await request.json()
    await emit_business_event(
        data.get("event_type", "created"),
        data.get("entity_type"),
        data.get("data", {}),
        data.get("business_id")
    )
    return JSONResponse({"success": True})


# Mount Socket.IO to FastAPI
app = socketio.ASGIApp(sio, sio_app)