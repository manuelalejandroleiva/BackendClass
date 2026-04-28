from fastapi import Depends, FastAPI, Header, Body, APIRouter, HTTPException, Query
from dotenv import load_dotenv
import httpx
import os
from typing import Optional, List

from usuarios.DTO.dto import LoginRequest
from usuarios.dependencies.dependencies import get_current_user
from usuarios.schema import *
from inventory.schema import SaleCreate, SaleItemCreate
from orders.schema import OrderCreate, OrderItemCreate, TableCreate
from rentas.schema import VehicleCreate, VehicleUpdate, RentalCreate, GeofenceCreate, TrackingUpdate
load_dotenv()

from buisness.schema import BuisnessCreate, LicenciaCreate, BuisnessUpdate
from inventory.schema import SaleCreate
from orders.schema import OrderCreate, TableCreate, StatusUpdate
from rentas.schema import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    RentalCreate, RentalUpdate, RentalResponse,
    GeofenceCreate, GeofenceUpdate, GeofenceResponse,
    TrackingUpdate, TrackingResponse,
    GPSLocationResponse, GeofenceAlertResponse
)

load_dotenv()

# ===================== APP =====================
app = FastAPI(
    title="API Gateway",
    description="API Gateway para todos los microservicios",
    version="1.0.0"
)

# ===================== ENV =====================
USER_SERVICE_URL = os.getenv("SERVICE_USER_PORT_DATA")
BUSINESS_SERVICE_URL = os.getenv("SERVICE_PAYMENT_PORT_DATA")
INVENTORY_SERVICE_URL = os.getenv("SERVICE_INVENTORY_PORT_DATA")
ORDERS_SERVICE_URL = os.getenv("SERVICE_ORDERS_PORT_DATA")
RENTS_SERVICE_URL = os.getenv("SERVICE_RENTS_PORT_DATA")
REALTIME_SERVICE_URL = os.getenv("REALTIME_SERVICE_URL")

# ===================== ROUTERS =====================
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
public_router = APIRouter()

# ===================== HELPERS =====================
def get_token(authorization: Optional[str] = Header(None, include_in_schema=False)):
    return authorization

async def proxy_request(method: str, url: str, authorization: str = None, json: dict = None, params: dict = None):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
                timeout=30.0
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unreachable: {e}")
    
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

# ===================== PUBLIC =====================
@public_router.post("/login")
async def login(login_data: LoginRequest = Body(...)):
    return await proxy_request("POST", f"{USER_SERVICE_URL}/auth/login", json=login_data.dict())

# ===================== USERS =====================
@protected_router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("GET", f"{USER_SERVICE_URL}/users", authorization, params={"page": page, "page_size": page_size})

@protected_router.post("/users/create")
async def create_user(
    data: UserCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("POST", f"{USER_SERVICE_URL}/users", authorization, json=data.dict())

@protected_router.get("/users/{user_id}")
async def get_user(user_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{USER_SERVICE_URL}/users/{user_id}", authorization)

@protected_router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user: UserCreate,
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("PUT", f"{USER_SERVICE_URL}/users/{user_id}", authorization, json=user.dict())

@protected_router.delete("/users/{user_id}")
async def delete_user(user_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{USER_SERVICE_URL}/users/{user_id}", authorization)

# ===================== AI ENDPOINTS =====================
@protected_router.post("/ai/response")
async def get_ai_response(
    prompt: str = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("POST", f"{USER_SERVICE_URL}/airesponse", authorization, json={"prompt": prompt})

@protected_router.post("/ai/image")
async def get_ai_image(
    prompt: str = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("POST", f"{USER_SERVICE_URL}/aiimage", authorization, json={"prompt": prompt})

# ===================== BUSINESS =====================
@protected_router.post("/business")
async def create_business(data: BuisnessCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{BUSINESS_SERVICE_URL}/buisness_create", authorization, json=data.dict())

@protected_router.get("/business")
async def get_businesses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/buisness_get", authorization, params={"skip": skip, "limit": limit})

@protected_router.get("/business/{business_id}")
async def get_business_by_id(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/buisness_id/{business_id}", authorization)

@protected_router.put("/business/{business_id}")
async def update_business(
    business_id: int,
    data: BuisnessUpdate,
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("PUT", f"{BUSINESS_SERVICE_URL}/buisness/{business_id}", authorization, json=data.dict(exclude_unset=True))

@protected_router.delete("/business/{business_id}")
async def delete_business(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{BUSINESS_SERVICE_URL}/buisness/{business_id}", authorization)

@protected_router.get("/business/{business_id}/products")
async def get_business_products(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/productos/{business_id}", authorization)

# ===================== INVENTORY/SALES =====================
@protected_router.post("/sales")
async def create_sale(sale: SaleCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{INVENTORY_SERVICE_URL}/sales/create", authorization, json=sale.dict())

@protected_router.get("/sales/{business_id}")
async def get_sales(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{INVENTORY_SERVICE_URL}/sales/{business_id}", authorization)

@protected_router.get("/sales/report/period")
async def get_sales_by_period(
    business_id: int = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("GET", f"{INVENTORY_SERVICE_URL}/sales/report/period", authorization, params={"business_id": business_id, "start_date": start_date, "end_date": end_date})

@protected_router.get("/sales/report/top-products")
async def get_top_products(
    business_id: int = Query(...),
    limit: int = Query(10, ge=1, le=100),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("GET", f"{INVENTORY_SERVICE_URL}/sales/report/top-products", authorization, params={"business_id": business_id, "limit": limit})

@protected_router.get("/sales/report/summary")
async def get_sales_summary(
    business_id: int = Query(...),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("GET", f"{INVENTORY_SERVICE_URL}/sales/report/summary", authorization, params={"business_id": business_id})

@protected_router.patch("/products/{product_id}/stock")
async def update_product_stock(
    product_id: int,
    stock: int = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("PATCH", f"{INVENTORY_SERVICE_URL}/products/{product_id}/stock", authorization, json={"stock": stock})

@protected_router.patch("/products/{product_id}")
async def update_product(
    product_id: int,
    data: dict = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("PATCH", f"{INVENTORY_SERVICE_URL}/products/{product_id}", authorization, json=data)

# ===================== ORDERS =====================
@protected_router.post("/tables")
async def create_table(data: TableCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{ORDERS_SERVICE_URL}/tables", authorization, json=data.dict())

@protected_router.get("/tables/{business_id}")
async def get_tables(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{ORDERS_SERVICE_URL}/tables/{business_id}", authorization)

@protected_router.post("/orders")
async def create_order(data: OrderCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{ORDERS_SERVICE_URL}/orders", authorization, json=data.dict())

@protected_router.get("/orders/{business_id}")
async def get_orders(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{ORDERS_SERVICE_URL}/orders/{business_id}", authorization)

@protected_router.get("/orders/detail/{order_id}")
async def get_order_detail(order_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{ORDERS_SERVICE_URL}/orders/detail/{order_id}", authorization)

@protected_router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{ORDERS_SERVICE_URL}/orders/{order_id}/status",
            json={"status": status},
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()


# ============== RENTS / GPS ==============

@protected_router.post("/vehicles")
async def create_vehicle(
    vehicle: VehicleCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RENTS_SERVICE_URL}/vehicles",
            json=vehicle.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/vehicles")
async def get_vehicles(
    status: Optional[str] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        params = {}
        if status:
            params["status"] = status
        response = await client.get(
            f"{RENTS_SERVICE_URL}/vehicles",
            params=params,
            headers=headers
        )
        return response.json()

@protected_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{RENTS_SERVICE_URL}/vehicles/{vehicle_id}",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: int,
    vehicle: VehicleUpdate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{RENTS_SERVICE_URL}/vehicles/{vehicle_id}",
            json=vehicle.dict(exclude_unset=True),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{RENTS_SERVICE_URL}/vehicles/{vehicle_id}",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.post("/tracking/update")
async def update_tracking(
    tracking: TrackingUpdate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RENTS_SERVICE_URL}/tracking/update",
            json=tracking.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/tracking/{vehicle_id}/current")
async def get_current_location(
    vehicle_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{RENTS_SERVICE_URL}/tracking/{vehicle_id}/current",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/tracking/{vehicle_id}/history")
async def get_tracking_history(
    vehicle_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        response = await client.get(
            f"{RENTS_SERVICE_URL}/tracking/{vehicle_id}/history",
            params=params,
            headers=headers
        )
        return response.json()

@protected_router.post("/rentals")
async def create_rental(
    rental: RentalCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RENTS_SERVICE_URL}/rentals",
            json=rental.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.post("/rentals/{rental_id}/complete")
async def complete_rental(
    rental_id: int,
    end_latitude: Optional[float] = Body(None),
    end_longitude: Optional[float] = Body(None),
    rate_per_hour: Optional[float] = Body(10.0),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    payload = {}
    if end_latitude is not None:
        payload["end_latitude"] = end_latitude
    if end_longitude is not None:
        payload["end_longitude"] = end_longitude
    if rate_per_hour is not None:
        payload["rate_per_hour"] = rate_per_hour
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RENTS_SERVICE_URL}/rentals/{rental_id}/complete",
            json=payload,
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/rentals")
async def get_rentals(
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        params = {}
        if status:
            params["status"] = status
        if user_id:
            params["user_id"] = user_id
        if vehicle_id:
            params["vehicle_id"] = vehicle_id
        response = await client.get(
            f"{RENTS_SERVICE_URL}/rentals",
            params=params,
            headers=headers
        )
        return response.json()

@protected_router.post("/geofences")
async def create_geofence(
    geofence: GeofenceCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RENTS_SERVICE_URL}/geofences",
            json=geofence.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/geofences")
async def get_geofences(
    vehicle_id: Optional[int] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        params = {}
        if vehicle_id:
            params["vehicle_id"] = vehicle_id
        response = await client.get(
            f"{RENTS_SERVICE_URL}/geofences",
            params=params,
            headers=headers
        )
        return response.json()

@protected_router.delete("/geofences/{geofence_id}")
async def delete_geofence(
    geofence_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{RENTS_SERVICE_URL}/geofences/{geofence_id}",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/alerts")
async def get_alerts(
    vehicle_id: Optional[int] = Query(None),
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        params = {"limit": limit}
        if vehicle_id:
            params["vehicle_id"] = vehicle_id
        if is_read is not None:
            params["is_read"] = is_read
        response = await client.get(
            f"{RENTS_SERVICE_URL}/alerts",
            params=params,
            headers=headers
        )
        return response.json()

@protected_router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RENTS_SERVICE_URL}/alerts/{alert_id}/read",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()


# ============== REALTIME / WEBSOCKET ==============

@protected_router.get("/realtime/health")
async def realtime_health(authorization: Optional[str] = Depends(get_token)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REALTIME_SERVICE_URL}/health")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Realtime service unavailable: {e}")

@protected_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{RENTS_SERVICE_URL}/vehicles/{vehicle_id}", authorization)

@protected_router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: int,
    vehicle: VehicleUpdate,
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("PUT", f"{RENTS_SERVICE_URL}/vehicles/{vehicle_id}", authorization, json=vehicle.dict(exclude_unset=True))

@protected_router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{RENTS_SERVICE_URL}/vehicles/{vehicle_id}", authorization)

# ===================== TRACKING =====================
@protected_router.post("/tracking/update")
async def update_tracking(data: TrackingUpdate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{RENTS_SERVICE_URL}/tracking/update", authorization, json=data.dict())

@protected_router.get("/tracking/{vehicle_id}/current")
async def get_current_location(vehicle_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{RENTS_SERVICE_URL}/tracking/{vehicle_id}/current", authorization)

@protected_router.get("/tracking/{vehicle_id}/history")
async def get_tracking_history(
    vehicle_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    authorization: Optional[str] = Depends(get_token)
):
    params = {"limit": limit}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await proxy_request("GET", f"{RENTS_SERVICE_URL}/tracking/{vehicle_id}/history", authorization, params=params)

# ===================== RENTALS =====================
@protected_router.post("/rentals")
async def create_rental(data: RentalCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{RENTS_SERVICE_URL}/rentals", authorization, json=data.dict())

@protected_router.post("/rentals/{rental_id}/complete")
async def complete_rental(
    rental_id: int,
    end_latitude: Optional[float] = Body(None),
    end_longitude: Optional[float] = Body(None),
    rate_per_hour: Optional[float] = Body(10.0),
    authorization: Optional[str] = Depends(get_token)
):
    payload = {"rental_id": rental_id}
    if end_latitude is not None:
        payload["end_latitude"] = end_latitude
    if end_longitude is not None:
        payload["end_longitude"] = end_longitude
    if rate_per_hour is not None:
        payload["rate_per_hour"] = rate_per_hour
    return await proxy_request("POST", f"{RENTS_SERVICE_URL}/rentals/{rental_id}/complete", authorization, json=payload)

@protected_router.get("/rentals")
async def get_rentals(
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    params = {}
    if status:
        params["status"] = status
    if user_id:
        params["user_id"] = user_id
    if vehicle_id:
        params["vehicle_id"] = vehicle_id
    return await proxy_request("GET", f"{RENTS_SERVICE_URL}/rentals", authorization, params=params)

# ===================== GEOFENCES =====================
@protected_router.post("/geofences")
async def create_geofence(data: GeofenceCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{RENTS_SERVICE_URL}/geofences", authorization, json=data.dict())

@protected_router.get("/geofences")
async def get_geofences(
    vehicle_id: Optional[int] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    params = {"vehicle_id": vehicle_id} if vehicle_id else {}
    return await proxy_request("GET", f"{RENTS_SERVICE_URL}/geofences", authorization, params=params)

@protected_router.delete("/geofences/{geofence_id}")
async def delete_geofence(geofence_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{RENTS_SERVICE_URL}/geofences/{geofence_id}", authorization)

# ===================== ALERTS =====================
@protected_router.get("/alerts")
async def get_alerts(
    vehicle_id: Optional[int] = Query(None),
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    authorization: Optional[str] = Depends(get_token)
):
    params = {"limit": limit}
    if vehicle_id:
        params["vehicle_id"] = vehicle_id
    if is_read is not None:
        params["is_read"] = is_read
    return await proxy_request("GET", f"{RENTS_SERVICE_URL}/alerts", authorization, params=params)

@protected_router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{RENTS_SERVICE_URL}/alerts/{alert_id}/read", authorization)

# ===================== REALTIME =====================
@protected_router.get("/realtime/health")
async def realtime_health():
    return await proxy_request("GET", f"{REALTIME_SERVICE_URL}/health")

# ===================== REGISTER ROUTERS =====================
app.include_router(public_router, prefix="/api")
app.include_router(protected_router, prefix="/api")
