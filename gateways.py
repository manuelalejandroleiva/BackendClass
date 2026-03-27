from fastapi import Depends, FastAPI, Request, Header,Body,APIRouter
from dotenv import load_dotenv
import httpx
from usuarios.connection.database import get_db

from usuarios.DTO.dto import LoginRequest
from sqlalchemy.ext.asyncio import AsyncSession
from usuarios.dependencies.dependencies import get_current_user
from typing import Optional
from buisness.schema import BuisnessCreate,LicenciaCreate,BuisnessUpdate
import os
from fastapi import HTTPException
from fastapi import Query

from usuarios.schema import *
from inventory.schema import SaleCreate, SaleItemCreate
from orders.schema import OrderCreate, OrderItemCreate, TableCreate
load_dotenv()

# 🔐 Router protegido
protected_router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

public_router = APIRouter()



app = FastAPI(title="API Gateway", description="API Gateway para usuarios y negocios", version="1.0.0")


USER_SERVICE_URL = os.getenv("SERVICE_USER_PORT_DATA")
USER_SERVICE_PATH = os.getenv("SERVICE_PAYMENT_PORT_DATA")
INVENTORY_SERVICE_URL = os.getenv("SERVICE_INVENTORY_PORT_DATA")
ORDERS_SERVICE_URL = os.getenv("SERVICE_ORDERS_PORT_DATA")


@public_router.post("/login")
async def login( 
    login_data: LoginRequest = Body(...),
   
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/auth/login",
            json=login_data.dict(),
        )
    return response.json()




def get_token(authorization: Optional[str] = Header(None, include_in_schema=False)):
    return authorization

@protected_router.get("/users/{user_id}")
async def get_user(
    user_id: int,
   authorization: Optional[str] = Depends(get_token)
):  
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)
    return response.json()


@public_router.post("/users/create")
async def create_user(
    data: UserCreate = Body(...),
   
    authorization: Optional[str] = Depends(get_token)
):

    headers = {"Authorization": authorization} if authorization else {}
    url = f"{USER_SERVICE_URL}/users"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data.dict(), headers=headers, timeout=10.0)
        except httpx.RequestError as e:
            # Downstream service unreachable
            raise HTTPException(status_code=503, detail=f"User service unreachable: {e}")

    # Debug info: status and raw text (avoid calling .json() blindly)
    if response.status_code >= 400:
        # return downstream error text in detail when possible
        text = response.text
        raise HTTPException(status_code=response.status_code, detail=f"Downstream error: {text}")

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        # Not JSON — include raw response for debugging
        raise HTTPException(status_code=502, detail=f"Downstream returned non-JSON response: {response.status_code} - {response.text}")

    try:
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to decode JSON from user service: {e}. Raw: {response.text}")




@protected_router.delete('/users/{user_id}', response_model=UserSchema)
async def delete_user(
    user_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)

        # Si el servicio retorna un error
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al eliminar usuario"))

        return response.json()
    

@protected_router.put('/users/{user_id}')
async def updateUsers(
    user: UserSchema,
    user_id: int,
    authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{USER_SERVICE_URL}/users/{user_id}", json=user.dict(), headers=headers)
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al actualizar el  usuario"))
        return response.json()
    




@protected_router.post("/buisness/create")
async def create_buisness(
    data: BuisnessCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:

       response = await client.post(f"{USER_SERVICE_PATH}/buisness_create", json=data.dict(), headers=headers)

    return response.json()



@protected_router.post("/licence/create")
async def create_licence(
    licencia: LicenciaCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)    
):

    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
       response = await client.post(f"{USER_SERVICE_PATH}/licence_create", json=licencia.dict(), headers=headers)

    return response.json()

@protected_router.get("/licence_get")
async def get_all_licences(skip: int = 0, limit: int = 10, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
       response = await client.get(f"{USER_SERVICE_PATH}/licence_get?skip={skip}&limit={limit}", headers=headers)

    return response.json()



@protected_router.get("/buisness_get")
async def get_all_buisnesses(skip: int = 0, limit: int = 10, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
       response = await client.get(f"{USER_SERVICE_PATH}/buisness_get?skip={skip}&limit={limit}", headers=headers)      
    return response.json()  


@protected_router.patch("/buisness/{buisness_id}")
async def update_buisness(
    buisness_id: int,
    buisness_update: BuisnessUpdate,
    authorization: Optional[str] = Depends(get_token)
):
    """
    Actualiza un negocio. Solo se modificarán los campos enviados en el payload.
    """
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{USER_SERVICE_PATH}/buisness/{buisness_id}",
            json=buisness_update.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al actualizar el negocio"))
        return response.json()



@protected_router.get("/buisness_get/{buisness_id}")
async def get_buisness_by_id(
    buisness_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_PATH}/buisness_get/{buisness_id}", headers=headers)
    return response.json()     



@protected_router.delete("/buisness/{buisness_id}", response_model=None)
async def delete_buisness(
    buisness_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_PATH}/buisness/{buisness_id}", headers=headers)
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al eliminar el negocio"))
        return response.json()
    
@protected_router.delete("/licence/{licence_id}", response_model=None)
async def delete_licence(
    licence_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_PATH}/licence/{licence_id}", headers=headers)
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al eliminar la licencia"))
        return response.json()


app.include_router(protected_router,prefix="/api")
app.include_router(public_router, prefix="/api")


# ============== INVENTORY / SALES ==============

@protected_router.post("/sales")
async def create_sale(
    sale: SaleCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{INVENTORY_SERVICE_URL}/sales/create",
            json=sale.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/sales/{business_id}")
async def get_sales(
    business_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INVENTORY_SERVICE_URL}/sales/{business_id}",
            headers=headers
        )
        return response.json()

@protected_router.get("/sales/{business_id}/report/period")
async def sales_report_period(
    business_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INVENTORY_SERVICE_URL}/sales/report/period",
            params={"business_id": business_id},
            headers=headers
        )
        return response.json()

@protected_router.get("/sales/{business_id}/report/top-products")
async def top_products(
    business_id: int,
    limit: int = Query(10, ge=1, le=50),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INVENTORY_SERVICE_URL}/sales/report/top-products",
            params={"business_id": business_id, "limit": limit},
            headers=headers
        )
        return response.json()

@protected_router.get("/sales/{business_id}/report/summary")
async def sales_summary(
    business_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INVENTORY_SERVICE_URL}/sales/report/summary",
            params={"business_id": business_id},
            headers=headers
        )
        return response.json()

@protected_router.patch("/products/{product_id}/stock")
async def update_stock(
    product_id: int,
    quantity: int = Query(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{INVENTORY_SERVICE_URL}/products/{product_id}/stock",
            params={"quantity": quantity},
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()


# ============== ORDERS / TABLES ==============

@protected_router.post("/tables")
async def create_table(
    table: TableCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ORDERS_SERVICE_URL}/tables",
            json=table.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/tables/{business_id}")
async def get_tables(
    business_id: int,
    available_only: bool = Query(False),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ORDERS_SERVICE_URL}/tables/{business_id}",
            params={"available_only": available_only},
            headers=headers
        )
        return response.json()

@protected_router.post("/orders")
async def create_order(
    order: OrderCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ORDERS_SERVICE_URL}/orders",
            json=order.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.get("/orders/{business_id}")
async def get_orders(
    business_id: int,
    table_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        params = {"business_id": business_id}
        if table_id:
            params["table_id"] = table_id
        if status:
            params["status"] = status
        response = await client.get(
            f"{ORDERS_SERVICE_URL}/orders/{business_id}",
            params=params,
            headers=headers
        )
        return response.json()

@protected_router.get("/orders/detail/{order_id}")
async def get_order_detail(
    order_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ORDERS_SERVICE_URL}/orders/detail/{order_id}",
            headers=headers
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error"))
        return response.json()

@protected_router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str = Query(...),
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

    
    




