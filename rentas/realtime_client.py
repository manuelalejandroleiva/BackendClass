import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

REALTIME_SERVICE_URL = os.getenv("REALTIME_SERVICE_URL", "http://realtime:8001")


class RealtimeClient:
    def __init__(self):
        self.base_url = REALTIME_SERVICE_URL
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def emit_reservation_created(self, rental_id: int, vehicle_id: int, user_id: int):
        await self._call_realtime("emit_reservation_created", {
            "rental_id": rental_id,
            "vehicle_id": vehicle_id,
            "user_id": user_id
        })
    
    async def emit_reservation_accepted(self, rental_id: int, driver_id: int, vehicle_id: int):
        await self._call_realtime("emit_reservation_accepted", {
            "rental_id": rental_id,
            "driver_id": driver_id,
            "vehicle_id": vehicle_id
        })
    
    async def emit_tracking_update(self, vehicle_id: int, latitude: float, longitude: float,
                                  speed: float = 0, heading: float = None, 
                                  battery_level: float = None):
        data = {
            "vehicle_id": vehicle_id,
            "latitude": latitude,
            "longitude": longitude,
            "speed": speed
        }
        if heading:
            data["heading"] = heading
        if battery_level:
            data["battery_level"] = battery_level
        
        await self._call_realtime("emit_tracking_update", data)
    
    async def emit_rental_started(self, rental_id: int, vehicle_id: int, user_id: int):
        await self._call_realtime("emit_rental_started", {
            "rental_id": rental_id,
            "vehicle_id": vehicle_id,
            "user_id": user_id
        })
    
    async def emit_rental_completed(self, rental_id: int, vehicle_id: int, user_id: int,
                                  total_distance: float, total_cost: float):
        await self._call_realtime("emit_rental_completed", {
            "rental_id": rental_id,
            "vehicle_id": vehicle_id,
            "user_id": user_id,
            "total_distance": total_distance,
            "total_cost": total_cost
        })
    
    async def emit_geofence_alert(self, vehicle_id: int, alert_type: str, message: str,
                                latitude: float, longitude: float):
        await self._call_realtime("emit_geofence_alert", {
            "vehicle_id": vehicle_id,
            "alert_type": alert_type,
            "message": message,
            "latitude": latitude,
            "longitude": longitude
        })
    
    async def emit_notification(self, user_id: int, title: str, body: str, data: Dict = None):
        payload = {
            "user_id": user_id,
            "title": title,
            "body": body
        }
        if data:
            payload["data"] = data
        await self._call_realtime("emit_notification", payload)
    
    async def _call_realtime(self, function: str, data: Dict):
        try:
            session = await self._get_session()
            await session.post(
                f"{self.base_url}/internal/{function}",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            )
        except Exception as e:
            print(f"Error calling realtime: {e}")
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


realtime_client = RealtimeClient()