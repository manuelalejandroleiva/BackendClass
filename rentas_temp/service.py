import json
import math
import asyncio
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .connection.database import engine
from .models.models import Vehicle, GPSLocation, Rental, Geofence, GeofenceAlert, VehicleStatus, RentalStatus, AlertType
from common.rabbitmq import message_pattern
from datetime import datetime, timedelta
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

REALTIME_URL = os.getenv("REALTIME_SERVICE_URL", "http://realtime-service:8080")


async def notify_realtime(endpoint: str, data: dict):
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{REALTIME_URL}{endpoint}",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            )
    except Exception as e:
        print(f"Error notifying realtime: {e}")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def is_inside_geofence(lat: float, lon: float, center_lat: float, center_lon: float, radius_meters: float) -> bool:
    distance = haversine_distance(lat, lon, center_lat, center_lon)
    return distance <= radius_meters


async def check_geofences(db: AsyncSession, vehicle_id: int, latitude: float, longitude: float):
    result = await db.execute(
        select(Geofence).where(
            Geofence.vehicle_id == vehicle_id,
            Geofence.is_active == True
        )
    )
    geofences = result.scalars().all()

    alerts_created = []
    for geofence in geofences:
        was_inside = getattr(geofence, '_was_inside', None)
        is_now_inside = is_inside_geofence(latitude, longitude, geofence.center_latitude, geofence.center_longitude, geofence.radius_meters)

        if was_inside is None:
            geofence._was_inside = is_now_inside
            continue

        if not was_inside and is_now_inside and geofence.alert_on_entry:
            alert = GeofenceAlert(
                geofence_id=geofence.id,
                vehicle_id=vehicle_id,
                alert_type=AlertType.GEOFENCE_ENTRY,
                latitude=latitude,
                longitude=longitude,
                message=f"Vehículo entró a la zona: {geofence.name}"
            )
            db.add(alert)
            alerts_created.append(alert)

        elif was_inside and not is_now_inside and geofence.alert_on_exit:
            alert = GeofenceAlert(
                geofence_id=geofence.id,
                vehicle_id=vehicle_id,
                alert_type=AlertType.GEOFENCE_EXIT,
                latitude=latitude,
                longitude=longitude,
                message=f"Vehículo salió de la zona: {geofence.name}"
            )
            db.add(alert)
            alerts_created.append(alert)

        geofence._was_inside = is_now_inside

    if alerts_created:
        await db.commit()


@message_pattern("rents.vehicle.create")
async def handle_create_vehicle(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            new_vehicle = Vehicle(
                plate=payload.get("plate"),
                brand=payload.get("brand"),
                model=payload.get("model"),
                year=payload.get("year"),
                color=payload.get("color"),
                vin=payload.get("vin"),
                device_id=payload.get("device_id"),
                status=VehicleStatus.AVAILABLE
            )
            db.add(new_vehicle)
            await db.commit()
            await db.refresh(new_vehicle)

            return {"success": True, "data": {"id": new_vehicle.id, "plate": new_vehicle.plate, "status": new_vehicle.status.value}}

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.vehicle.get_all")
async def handle_get_all_vehicles(payload):
    async with AsyncSession(engine) as db:
        try:
            status_filter = payload.get("status")
            
            # Validar que el status sea válido (case-insensitive)
            if status_filter:
                status_filter_upper = status_filter.upper()
                if status_filter_upper not in [s.value for s in VehicleStatus]:
                    return {"success": False, "message": "Estado no encontrado"}
                status_filter = status_filter_upper
            
            query = select(Vehicle)
            if status_filter:
                query = query.where(Vehicle.status == status_filter)

            result = await db.execute(query)
            vehicles = result.scalars().all()

            data = [{
                "id": v.id,
                "plate": v.plate,
                "brand": v.brand,
                "model": v.model,
                "year": v.year,
                "color": v.color,
                "status": v.status.value,
                "current_latitude": v.current_latitude,
                "current_longitude": v.current_longitude,
                "speed": v.speed,
                "battery_level": v.battery_level,
                "last_update": v.last_update.isoformat() if v.last_update else None
            } for v in vehicles]

            return {"success": True, "data": data}

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("rents.vehicle.get_by_id")
async def handle_get_vehicle_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("id")
            if not vehicle_id:
                return {"success": False, "message": "Falta el ID del vehículo"}

            vehicle = await db.get(Vehicle, int(vehicle_id))
            if not vehicle:
                return {"success": False, "message": "Vehículo no encontrado"}

            return {
                "success": True,
                "data": {
                    "id": vehicle.id,
                    "plate": vehicle.plate,
                    "brand": vehicle.brand,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "color": vehicle.color,
                    "vin": vehicle.vin,
                    "device_id": vehicle.device_id,
                    "status": vehicle.status.value,
                    "current_latitude": vehicle.current_latitude,
                    "current_longitude": vehicle.current_longitude,
                    "speed": vehicle.speed,
                    "battery_level": vehicle.battery_level,
                    "last_update": vehicle.last_update.isoformat() if vehicle.last_update else None
                }
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("rents.vehicle.update")
async def handle_update_vehicle(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("id")
            if not vehicle_id:
                return {"success": False, "message": "Falta el ID del vehículo"}

            vehicle = await db.get(Vehicle, int(vehicle_id))
            if not vehicle:
                return {"success": False, "message": "Vehículo no encontrado"}

            update_fields = ["plate", "brand", "model", "year", "color", "vin", "device_id", "status"]
            for field in update_fields:
                if field in payload:
                    if field == "status":
                        # Validar que el status sea válido (case-insensitive)
                        status_upper = payload[field].upper()
                        if status_upper not in [s.value for s in VehicleStatus]:
                            return {"success": False, "message": "Estado no encontrado"}
                        setattr(vehicle, field, VehicleStatus(status_upper))
                    else:
                        setattr(vehicle, field, payload[field])

            vehicle.updated_at = datetime.utcnow()
            db.add(vehicle)
            await db.commit()
            await db.refresh(vehicle)

            return {"success": True, "data": {"id": vehicle.id, "plate": vehicle.plate, "status": vehicle.status.value}}

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.vehicle.delete")
async def handle_delete_vehicle(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("id")
            if not vehicle_id:
                return {"success": False, "message": "Falta el ID del vehículo"}

            vehicle = await db.get(Vehicle, int(vehicle_id))
            if not vehicle:
                return {"success": False, "message": "Vehículo no encontrado"}

            await db.delete(vehicle)
            await db.commit()

            return {"success": True, "message": "Vehículo eliminado correctamente"}

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.tracking.update")
async def handle_tracking_update(payload):
    async with AsyncSession(engine) as db:
        try:
            device_id = payload.get("device_id")
            latitude = payload.get("latitude")
            longitude = payload.get("longitude")

            if not all([device_id, latitude, longitude]):
                return {"success": False, "message": "Faltan datos requeridos"}

            result = await db.execute(select(Vehicle).where(Vehicle.device_id == device_id))
            vehicle = result.scalar_one_or_none()

            if not vehicle:
                return {"success": False, "message": "Vehículo no encontrado"}

            speed = payload.get("speed", 0)
            heading = payload.get("heading")
            altitude = payload.get("altitude")
            accuracy = payload.get("accuracy")
            battery_level = payload.get("battery_level")

            location = GPSLocation(
                vehicle_id=vehicle.id,
                latitude=latitude,
                longitude=longitude,
                speed=speed,
                heading=heading,
                altitude=altitude,
                accuracy=accuracy,
                source=payload.get("source", "gps")
            )
            db.add(location)

            vehicle.current_latitude = latitude
            vehicle.current_longitude = longitude
            vehicle.speed = speed
            vehicle.last_update = datetime.utcnow()

            if battery_level is not None:
                vehicle.battery_level = battery_level

            await check_geofences(db, vehicle.id, latitude, longitude)

            await db.commit()

            # Notificar ubicación en tiempo real
            await notify_realtime("/internal/emit_tracking_update", {
                "vehicle_id": vehicle.id,
                "latitude": latitude,
                "longitude": longitude,
                "speed": speed,
                "heading": heading,
                "battery_level": battery_level
            })

            return {"success": True, "message": "Ubicación actualizada", "vehicle_id": vehicle.id}

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.tracking.get_current")
async def handle_get_current_location(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("vehicle_id")
            if not vehicle_id:
                return {"success": False, "message": "Falta el ID del vehículo"}

            vehicle = await db.get(Vehicle, int(vehicle_id))
            if not vehicle:
                return {"success": False, "message": "Vehículo no encontrado"}

            return {
                "success": True,
                "data": {
                    "vehicle_id": vehicle.id,
                    "plate": vehicle.plate,
                    "latitude": vehicle.current_latitude,
                    "longitude": vehicle.current_longitude,
                    "speed": vehicle.speed,
                    "battery_level": vehicle.battery_level,
                    "last_update": vehicle.last_update.isoformat() if vehicle.last_update else None
                }
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("rents.tracking.get_history")
async def handle_get_tracking_history(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("vehicle_id")
            if not vehicle_id:
                return {"success": False, "message": "Falta el ID del vehículo"}

            start_date = payload.get("start_date")
            end_date = payload.get("end_date")

            query = select(GPSLocation).where(GPSLocation.vehicle_id == int(vehicle_id))

            if start_date:
                query = query.where(GPSLocation.timestamp >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.where(GPSLocation.timestamp <= datetime.fromisoformat(end_date))

            query = query.order_by(GPSLocation.timestamp.desc())

            limit = payload.get("limit", 100)
            query = query.limit(limit)

            result = await db.execute(query)
            locations = result.scalars().all()

            data = [{
                "id": loc.id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "speed": loc.speed,
                "heading": loc.heading,
                "altitude": loc.altitude,
                "timestamp": loc.timestamp.isoformat()
            } for loc in locations]

            return {"success": True, "data": data}

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("rents.rental.create")
async def handle_create_rental(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("vehicle_id")
            user_id = payload.get("user_id")
            start_latitude = payload.get("start_latitude")
            start_longitude = payload.get("start_longitude")

            if not all([vehicle_id, user_id, start_latitude, start_longitude]):
                return {"success": False, "message": "Faltan datos requeridos"}

            vehicle = await db.get(Vehicle, int(vehicle_id))
            if not vehicle:
                return {"success": False, "message": "Vehículo no encontrado"}

            if vehicle.status != VehicleStatus.AVAILABLE:
                return {"success": False, "message": "El vehículo no está disponible"}

            rental = Rental(
                vehicle_id=vehicle.id,
                user_id=user_id,
                start_latitude=start_latitude,
                start_longitude=start_longitude,
                status=RentalStatus.ACTIVE
            )
            db.add(rental)

            vehicle.status = VehicleStatus.RENTED

            await db.commit()
            await db.refresh(rental)

            # Notificar al conductor sobre nueva reserva
            await notify_realtime("/internal/emit_reservation_created", {
                "rental_id": rental.id,
                "vehicle_id": vehicle.id,
                "user_id": user_id,
                "status": "pending"
            })

            # Notificar al usuario
            await notify_realtime("/internal/emit_notification", {
                "user_id": user_id,
                "title": "Nueva Reserva",
                "body": f"Tu reserva #{rental.id} ha sido creada",
                "data": {"rental_id": rental.id, "vehicle_id": vehicle.id}
            })

            return {
                "success": True,
                "data": {
                    "id": rental.id,
                    "vehicle_id": rental.vehicle_id,
                    "user_id": rental.user_id,
                    "status": rental.status.value,
                    "start_time": rental.start_time.isoformat()
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.rental.complete")
async def handle_complete_rental(payload):
    async with AsyncSession(engine) as db:
        try:
            rental_id = payload.get("rental_id")
            if not rental_id:
                return {"success": False, "message": "Falta el ID del rental"}

            rental = await db.get(Rental, int(rental_id))
            if not rental:
                return {"success": False, "message": "Rental no encontrado"}

            if rental.status != RentalStatus.ACTIVE:
                return {"success": False, "message": "El rental no está activo"}

            end_latitude = payload.get("end_latitude", rental.vehicle.current_latitude)
            end_longitude = payload.get("end_longitude", rental.vehicle.current_longitude)

            total_distance = haversine_distance(
                rental.start_latitude, rental.start_longitude,
                end_latitude, end_longitude
            )

            hours = (datetime.utcnow() - rental.start_time).total_seconds() / 3600
            rate_per_hour = payload.get("rate_per_hour", 10.0)
            total_cost = total_distance / 1000 * 2 + hours * rate_per_hour

            rental.end_latitude = end_latitude
            rental.end_longitude = end_longitude
            rental.end_time = datetime.utcnow()
            rental.total_distance = total_distance
            rental.total_cost = total_cost
            rental.status = RentalStatus.COMPLETED

            rental.vehicle.status = VehicleStatus.AVAILABLE

            await db.commit()
            await db.refresh(rental)

            return {
                "success": True,
                "data": {
                    "id": rental.id,
                    "status": rental.status.value,
                    "total_distance": total_distance,
                    "total_cost": total_cost,
                    "end_time": rental.end_time.isoformat()
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.rental.get_all")
async def handle_get_all_rentals(payload):
    async with AsyncSession(engine) as db:
        try:
            status = payload.get("status")
            user_id = payload.get("user_id")
            vehicle_id = payload.get("vehicle_id")

            query = select(Rental)
            if status:
                query = query.where(Rental.status == status)
            if user_id:
                query = query.where(Rental.user_id == int(user_id))
            if vehicle_id:
                query = query.where(Rental.vehicle_id == int(vehicle_id))

            query = query.order_by(Rental.created_at.desc())

            result = await db.execute(query)
            rentals = result.scalars().all()

            data = [{
                "id": r.id,
                "vehicle_id": r.vehicle_id,
                "user_id": r.user_id,
                "start_latitude": r.start_latitude,
                "start_longitude": r.start_longitude,
                "end_latitude": r.end_latitude,
                "end_longitude": r.end_longitude,
                "start_time": r.start_time.isoformat(),
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "total_distance": r.total_distance,
                "total_cost": r.total_cost,
                "status": r.status.value
            } for r in rentals]

            return {"success": True, "data": data}

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("rents.geofence.create")
async def handle_create_geofence(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("vehicle_id")
            name = payload.get("name")
            center_latitude = payload.get("center_latitude")
            center_longitude = payload.get("center_longitude")
            radius_meters = payload.get("radius_meters")

            if not all([vehicle_id, name, center_latitude, center_longitude, radius_meters]):
                return {"success": False, "message": "Faltan datos requeridos"}

            vehicle = await db.get(Vehicle, int(vehicle_id))
            if not vehicle:
                return {"success": False, "message": "Vehículo no encontrado"}

            geofence = Geofence(
                vehicle_id=vehicle.id,
                name=name,
                center_latitude=center_latitude,
                center_longitude=center_longitude,
                radius_meters=radius_meters,
                alert_on_entry=payload.get("alert_on_entry", True),
                alert_on_exit=payload.get("alert_on_exit", True),
                is_active=True
            )
            db.add(geofence)
            await db.commit()
            await db.refresh(geofence)

            return {
                "success": True,
                "data": {
                    "id": geofence.id,
                    "name": geofence.name,
                    "radius_meters": geofence.radius_meters
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.geofence.get_all")
async def handle_get_all_geofences(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("vehicle_id")
            query = select(Geofence)
            if vehicle_id:
                query = query.where(Geofence.vehicle_id == int(vehicle_id))

            result = await db.execute(query)
            geofences = result.scalars().all()

            data = [{
                "id": g.id,
                "vehicle_id": g.vehicle_id,
                "name": g.name,
                "center_latitude": g.center_latitude,
                "center_longitude": g.center_longitude,
                "radius_meters": g.radius_meters,
                "is_active": g.is_active,
                "alert_on_entry": g.alert_on_entry,
                "alert_on_exit": g.alert_on_exit
            } for g in geofences]

            return {"success": True, "data": data}

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("rents.geofence.delete")
async def handle_delete_geofence(payload):
    async with AsyncSession(engine) as db:
        try:
            geofence_id = payload.get("id")
            if not geofence_id:
                return {"success": False, "message": "Falta el ID del geofence"}

            geofence = await db.get(Geofence, int(geofence_id))
            if not geofence:
                return {"success": False, "message": "Geofence no encontrado"}

            await db.delete(geofence)
            await db.commit()

            return {"success": True, "message": "Geofence eliminado"}

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("rents.alerts.get")
async def handle_get_alerts(payload):
    async with AsyncSession(engine) as db:
        try:
            vehicle_id = payload.get("vehicle_id")
            is_read = payload.get("is_read")

            query = select(GeofenceAlert)
            if vehicle_id:
                query = query.where(GeofenceAlert.vehicle_id == int(vehicle_id))
            if is_read is not None:
                query = query.where(GeofenceAlert.is_read == is_read)

            query = query.order_by(GeofenceAlert.timestamp.desc())
            query = query.limit(payload.get("limit", 50))

            result = await db.execute(query)
            alerts = result.scalars().all()

            data = [{
                "id": a.id,
                "geofence_id": a.geofence_id,
                "vehicle_id": a.vehicle_id,
                "alert_type": a.alert_type.value,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "message": a.message,
                "is_read": a.is_read,
                "timestamp": a.timestamp.isoformat()
            } for a in alerts]

            return {"success": True, "data": data}

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("rents.alerts.mark_read")
async def handle_mark_alert_read(payload):
    async with AsyncSession(engine) as db:
        try:
            alert_id = payload.get("alert_id")
            if not alert_id:
                return {"success": False, "message": "Falta el ID de la alerta"}

            alert = await db.get(GeofenceAlert, int(alert_id))
            if not alert:
                return {"success": False, "message": "Alerta no encontrada"}

            alert.is_read = True
            db.add(alert)
            await db.commit()

            return {"success": True, "message": "Alerta marcada como leída"}

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}
