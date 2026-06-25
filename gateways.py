from fastapi import Depends, FastAPI, Header, Body, APIRouter, HTTPException, Query, Request
from dotenv import load_dotenv
import httpx
import os
from typing import Optional

from usuarios.DTO.dto import LoginRequest
from usuarios.dependencies.dependencies import get_current_user
from usuarios.schema import *
from rentas.schema import VehicleCreate, VehicleUpdate, RentalCreate, GeofenceCreate, TrackingUpdate
load_dotenv()
from fastapi.encoders import jsonable_encoder

from buisness.schema import (
    BuisnessCreate, LicenciaCreate, BuisnessUpdate,
    TableCreate, TableStatusUpdate, TableUpdate,
    MenuItemCreate, MenuItemUpdate,
    OrderCreate, OrderItemCreate, OrderStatusUpdate, OrderUpdate,
    MonthlyClosingCreate
)
from inventory.schema import SaleCreate as InventorySaleCreate
from landlord.schema import (
    PropertyCreate, PropertyUpdate,
    TenantCreate, TenantUpdate,
    PaymentCreate, PaymentUpdate,
    ClassificationUpdate
)
from rentas.schema import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    RentalCreate, RentalUpdate, RentalResponse,
    GeofenceCreate, GeofenceUpdate, GeofenceResponse,
    TrackingUpdate, TrackingResponse,
    GPSLocationResponse, GeofenceAlertResponse
)

load_dotenv()

# ===================== APP =====================
fastapi_app = FastAPI(
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
LANDLORD_SERVICE_URL = os.getenv("SERVICE_LANDLORD_PORT_DATA")
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
    prompt: str = Body(..., embed=True),
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("POST", f"{USER_SERVICE_URL}/aitext", authorization, json={"prompt": prompt})

# ===================== BUSINESS TYPES / CATEGORIES =====================
@public_router.get("/business-types")
async def get_business_types():
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/business-types")


# ===================== BUSINESS =====================
@protected_router.post("/business")
async def create_business(data: BuisnessCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{BUSINESS_SERVICE_URL}/buisness_create", authorization, json=data.dict())

@protected_router.get("/business")
async def get_businesses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    authorization: Optional[str] = Depends(get_token),
    current_user = Depends(get_current_user)
):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/buisness", authorization, params={"page": page, "page_size": page_size, "user_id": current_user.id})

@protected_router.get("/business/{business_id}")
async def get_business_by_id(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/buisness_id", authorization, params={"buisness_id": business_id})

@protected_router.patch("/business/{business_id}")
async def update_business(
    business_id: int,
    data: BuisnessUpdate,
    authorization: Optional[str] = Depends(get_token)
):
    return await proxy_request("PATCH", f"{BUSINESS_SERVICE_URL}/buisness/{business_id}", authorization, json=data.dict(exclude_unset=True))

@protected_router.delete("/business/{business_id}")
async def delete_business(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{BUSINESS_SERVICE_URL}/buisness/{business_id}", authorization)

@protected_router.get("/business/{business_id}/products")
async def get_business_products(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/productos", authorization, params={"business_id": business_id})

# ===================== TABLES =====================
@protected_router.post("/tables")
async def create_table(data: TableCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{BUSINESS_SERVICE_URL}/tables", authorization, json=data.dict())

@protected_router.get("/tables/{business_id}")
async def get_tables(
    business_id: int,
    status: Optional[str] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    params = {"business_id": business_id}
    if status:
        params["status"] = status
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/tables/{business_id}", authorization, params=params)

@protected_router.get("/tables/{business_id}/occupied")
async def get_occupied_tables(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/tables/{business_id}/occupied", authorization)

@protected_router.patch("/tables/{table_id}/status")
async def update_table_status(table_id: int, status_data: TableStatusUpdate, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BUSINESS_SERVICE_URL}/tables/{table_id}/status",
            json=status_data.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.put("/tables/{table_id}/occupied")
async def update_occupied_tables(table_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("PUT", f"{BUSINESS_SERVICE_URL}/tables/{table_id}/occupied", authorization)

@protected_router.delete("/tables/{table_id}")
async def delete_table(table_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{BUSINESS_SERVICE_URL}/tables/{table_id}", authorization)

@protected_router.patch("/tables/{table_id}")
async def update_table(table_id: int, table_data: TableUpdate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("PATCH", f"{BUSINESS_SERVICE_URL}/tables/{table_id}", authorization, json=table_data.dict(exclude_unset=True))

# ===================== MENU ITEMS =====================
@protected_router.post("/menu-items")
async def create_menu_item(data: MenuItemCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{BUSINESS_SERVICE_URL}/menu-items", authorization, json=data.dict())

@protected_router.get("/menu-items/{business_id}")
async def get_menu_items(
    business_id: int,
    category: Optional[str] = Query(None),
    only_available: bool = Query(False),
    authorization: Optional[str] = Depends(get_token)
):
    params = {"business_id": business_id}
    if category:
        params["category"] = category
    if only_available:
        params["only_available"] = "true"
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/menu-items/{business_id}", authorization, params=params)

@protected_router.patch("/menu-items/{menu_item_id}")
async def update_menu_item(menu_item_id: int, data: MenuItemUpdate, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BUSINESS_SERVICE_URL}/menu-items/{menu_item_id}",
            json=data.dict(exclude_unset=True),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.delete("/menu-items/{menu_item_id}")
async def delete_menu_item(menu_item_id: int, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{BUSINESS_SERVICE_URL}/menu-items/{menu_item_id}",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

# ===================== ORDERS =====================
@protected_router.post("/orders")
async def create_order(data: OrderCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{BUSINESS_SERVICE_URL}/orders", authorization, json=data.dict())

@protected_router.get("/orders/{business_id}")
async def get_orders(
    business_id: int,
    table_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    params = {"business_id": business_id}
    if table_id:
        params["table_id"] = table_id
    if status:
        params["status"] = status
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/orders/{business_id}", authorization, params=params)

@protected_router.get("/orders/detail/{order_id}")
async def get_order_detail(order_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/orders/detail/{order_id}", authorization)

@protected_router.post("/orders/{order_id}/items")
async def add_order_item(order_id: int, item: OrderItemCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{BUSINESS_SERVICE_URL}/orders/{order_id}/items", authorization, json=item.dict())

@protected_router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: int, status_data: OrderStatusUpdate, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BUSINESS_SERVICE_URL}/orders/{order_id}/status",
            json=status_data.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.patch("/orders/{order_id}")
async def update_order(order_id: int, data: OrderUpdate, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BUSINESS_SERVICE_URL}/orders/{order_id}",
            json=data.dict(exclude_unset=True),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.post("/orders/{order_id}/pay")
async def pay_order(
    order_id: int,
    payment_method: str = Body("cash"),
    cashier_id: Optional[int] = Body(None),
    discount: int = Body(0),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BUSINESS_SERVICE_URL}/orders/{order_id}/pay",
            json={"payment_method": payment_method, "cashier_id": cashier_id, "discount": discount},
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

# ===================== SALES REPORTS =====================
@protected_router.get("/sales/report/daily/{business_id}")
async def daily_sales_report(business_id: int, date: Optional[str] = Query(None), authorization: Optional[str] = Depends(get_token)):
    params = {"business_id": business_id}
    if date:
        params["date"] = date
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/sales/report/daily/{business_id}", authorization, params=params)

@protected_router.get("/sales/report/monthly/{business_id}")
async def monthly_sales_report(
    business_id: int,
    month: int = Query(...),
    year: int = Query(...),
    authorization: Optional[str] = Depends(get_token)
):
    params = {"business_id": business_id, "month": month, "year": year}
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/sales/report/monthly/{business_id}", authorization, params=params)

# ===================== MONTHLY CLOSING (ARQUEO) =====================
@protected_router.post("/monthly-closing")
async def create_monthly_closing(data: MonthlyClosingCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{BUSINESS_SERVICE_URL}/monthly-closing", authorization, json=data.dict())

@protected_router.get("/monthly-closing/{business_id}")
async def get_monthly_closings(business_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/monthly-closing/{business_id}", authorization)

# ===================== INVENTORY/SALES =====================
@protected_router.post("/sales")
async def create_sale(sale: InventorySaleCreate, authorization: Optional[str] = Depends(get_token)):
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


# ============== LANDLORD / PROPERTIES ==============

@protected_router.post("/properties")
async def create_property(data: PropertyCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{LANDLORD_SERVICE_URL}/properties", authorization, json=data.dict())

@protected_router.get("/properties")
async def get_properties(
    landlord_id: Optional[int] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    params = {}
    if landlord_id:
        params["landlord_id"] = landlord_id
    return await proxy_request("GET", f"{LANDLORD_SERVICE_URL}/properties", authorization, params=params)

@protected_router.get("/properties/{property_id}")
async def get_property(property_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{LANDLORD_SERVICE_URL}/properties/{property_id}", authorization)

@protected_router.put("/properties/{property_id}")
async def update_property(property_id: int, data: PropertyUpdate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("PUT", f"{LANDLORD_SERVICE_URL}/properties/{property_id}", authorization, json=data.dict(exclude_unset=True))

@protected_router.delete("/properties/{property_id}")
async def delete_property(property_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{LANDLORD_SERVICE_URL}/properties/{property_id}", authorization)

# ============== LANDLORD / TENANTS ==============

@protected_router.post("/tenants")
async def create_tenant(data: TenantCreate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{LANDLORD_SERVICE_URL}/tenants", authorization, json=data.model_dump(mode='json'))

@protected_router.get("/tenants")
async def get_tenants(
    property_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    params = {}
    if property_id:
        params["property_id"] = property_id
    if status:
        params["status"] = status
    return await proxy_request("GET", f"{LANDLORD_SERVICE_URL}/tenants", authorization, params=params)

@protected_router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{LANDLORD_SERVICE_URL}/tenants/{tenant_id}", authorization)

@protected_router.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: int, data: TenantUpdate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("PATCH", f"{LANDLORD_SERVICE_URL}/tenants/{tenant_id}", authorization, json=data.dict(exclude_none=True))

@protected_router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{LANDLORD_SERVICE_URL}/tenants/{tenant_id}", authorization)

# ============== LANDLORD / PAYMENTS ==============

@protected_router.post("/payments")
async def create_payment(data: PaymentCreate, authorization: Optional[str] = Depends(get_token)):
    # jsonable_encoder automatically converts date objects to ISO format strings
    safe_payload = jsonable_encoder(data) 
    
    return await proxy_request(
        "POST", 
        f"{LANDLORD_SERVICE_URL}/payments", 
        authorization, 
        json=safe_payload
    )

@protected_router.get("/payments")
async def get_payments(
    tenant_id: Optional[int] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    params = {}
    if tenant_id:
        params["tenant_id"] = tenant_id
    return await proxy_request("GET", f"{LANDLORD_SERVICE_URL}/payments", authorization, params=params)

@protected_router.get("/payments/{payment_id}")
async def get_payment(payment_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("GET", f"{LANDLORD_SERVICE_URL}/payments/{payment_id}", authorization)

@protected_router.put("/payments/{payment_id}")
async def update_payment(payment_id: int, data: PaymentUpdate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("PUT", f"{LANDLORD_SERVICE_URL}/payments/{payment_id}", authorization, json=data.dict(exclude_unset=True))

@protected_router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: int, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("DELETE", f"{LANDLORD_SERVICE_URL}/payments/{payment_id}", authorization)

# ============== LANDLORD / CLASSIFICATION ==============

@protected_router.post("/classification/{tenant_id}")
async def update_classification(tenant_id: int, data: ClassificationUpdate, authorization: Optional[str] = Depends(get_token)):
    return await proxy_request("POST", f"{LANDLORD_SERVICE_URL}/classification/{tenant_id}", authorization, json=data.dict())

@protected_router.post("/classification/auto")
async def auto_classify(tenant_id: Optional[int] = Body(None), authorization: Optional[str] = Depends(get_token)):
    payload = {}
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return await proxy_request("POST", f"{LANDLORD_SERVICE_URL}/classification/auto", authorization, json=payload)


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


# ===================== STRIPE PAYMENT =====================
@protected_router.post("/orders/{order_id}/create-payment-intent")
async def create_payment_intent(order_id: int, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BUSINESS_SERVICE_URL}/orders/{order_id}/create-payment-intent",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@public_router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    async with httpx.AsyncClient() as client:
        body = await request.body()
        headers = dict(request.headers)
        response = await client.post(
            f"{BUSINESS_SERVICE_URL}/stripe/webhook",
            content=body,
            headers=headers
        )
        return response.json()

# ===================== PUBLIC MENU =====================
@public_router.get("/public/menu/{business_id}")
async def get_public_menu(business_id: int):
    return await proxy_request("GET", f"{BUSINESS_SERVICE_URL}/public/menu/{business_id}")


# ===================== REALTIME =====================
@protected_router.get("/realtime/health")
async def realtime_health(authorization: Optional[str] = Depends(get_token)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REALTIME_SERVICE_URL}/health")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Realtime service unavailable: {e}")

# ===================== REGISTER ROUTERS =====================
fastapi_app.include_router(public_router, prefix="/api")
fastapi_app.include_router(protected_router, prefix="/api")


# ===================== SOCKET.IO =====================
import socketio
from datetime import datetime

gateway_sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25,
    async_handlers=True
)


@gateway_sio.event
async def connect(sid, environ):
    print(f"Cliente conectado al gateway: {sid}")


@gateway_sio.event
async def disconnect(sid):
    print(f"Cliente desconectado del gateway: {sid}")


@gateway_sio.event
async def join_business(sid, data):
    business_id = data.get("business_id")
    if business_id:
        await gateway_sio.enter_room(sid, f"business_{business_id}")
    return {"success": True}


async def emit_business_event(event_type: str, entity_type: str, data: dict, business_id: int):
    event_data = {
        "event_type": event_type,
        "entity_type": entity_type,
        "data": data,
        "business_id": business_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    await gateway_sio.emit("business_event", event_data, room=f"business_{business_id}")


@fastapi_app.post("/internal/emit_business_event")
async def internal_business_event(request: Request):
    body = await request.json()
    await emit_business_event(
        body.get("event_type", "created"),
        body.get("entity_type"),
        body.get("data", {}),
        body.get("business_id")
    )
    return {"success": True}


# Wrap gateway FastAPI app with Socket.IO ASGI app
from socketio import ASGIApp
app = ASGIApp(gateway_sio, fastapi_app)
