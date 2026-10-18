import asyncio
import uvicorn
from fastapi import FastAPI, Query, Body, HTTPException
from dotenv import load_dotenv
import os
load_dotenv()
from common.rabbitmq import MessageBroker
from sqlalchemy.ext.asyncio import AsyncSession
from .connection.database import engine
from common.database import Base
from .schema import (
    BuisnessCreate, BuisnessUpdate,
    TableCreate, TableStatusUpdate, TableUpdate,
    MenuItemCreate, MenuItemUpdate,
    OrderCreate, OrderStatusUpdate, OrderUpdate,
    SaleCreate, MonthlyClosingCreate,
    ProductCreate, CategoryCreate
)
from typing import Optional
from fastapi import Request
import stripe
import httpx
from .service import *

raw_rabbit = os.getenv("RABBITMQ_URL")
if not raw_rabbit:
    raise RuntimeError("RABBITMQ_URL environment variable is not set")

RABBITMQ_URL = os.path.expandvars(raw_rabbit)

REALTIME_SERVICE_URL = os.getenv("REALTIME_SERVICE_URL", "http://realtime-service:8080")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")

broker = MessageBroker(RABBITMQ_URL)


async def _notify_realtime(event_type: str, entity_type: str, data: dict, business_id: int):
    tasks = []
    for url in [REALTIME_SERVICE_URL, GATEWAY_URL]:
        tasks.append(_send_event(url, event_type, entity_type, data, business_id))
    await asyncio.gather(*tasks)


async def _send_event(base_url: str, event_type: str, entity_type: str, data: dict, business_id: int):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{base_url}/internal/emit_business_event",
                json={
                    "event_type": event_type,
                    "entity_type": entity_type,
                    "data": data,
                    "business_id": business_id
                },
                timeout=5.0
            )
    except Exception as e:
        print(f"⚠️ [Realtime] Error notificando a {base_url}: {e}")


def notify_realtime(event_type: str, entity_type: str, data: dict, business_id: int):
    asyncio.create_task(_notify_realtime(event_type, entity_type, data, business_id))


async def _push_public_menu(business_id: int):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("buisness.menu.public", payload)
        if result.get("success"):
            data = result.get("data", {})
            await _notify_realtime("menu_updated", "menu", data, business_id)
    except Exception as e:
        print(f"⚠️ [Menu] Error pushing public menu: {e}")


def push_public_menu(business_id: int):
    asyncio.create_task(_push_public_menu(business_id))

app = FastAPI(
    title="Restaurant Business Service",
    description="API para gestionar restaurantes, mesas, menus, ordenes, ventas y arqueos mensuales",
    version="2.0.0"
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await broker.connect()
    await broker.subscribe_patterns()


@app.on_event("shutdown")
async def shutdown():
    await broker.close()


# ========== BUSINESS TYPES / CATEGORIES ==========

@app.get("/business-types")
async def get_business_types():
    try:
        result = await broker.rpc_request("buisness.category.get_all", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== BUSINESS CRUD ==========

@app.post("/buisness_create")
async def create_buisness(buisness: BuisnessCreate):
    payload = buisness.dict(exclude_unset=True)
    try:
        result = await broker.rpc_request("buisness.create", payload)
        if result.get("success"):
            data = result.get("data", {})
            notify_realtime("created", "buisness", data, data.get("id"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/buisness")
async def get_buisness(page: int = Query(1, ge=1),
                       page_size: int = Query(10, ge=1, le=100),
                       user_id: int = Query(...)):
    try:
        payload = {"page": page, "page_size": page_size, "user_id": user_id}
        result = await broker.rpc_request("buisness.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/buisness_id")
async def get_buisness_by_id(buisness_id: int):
    try:
        payload = {"id": buisness_id}
        result = await broker.rpc_request("buisness.get_by_id", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/buisness/{buisness_id}")
async def delete_buisness(buisness_id: int):
    try:
        payload = {"id": buisness_id}
        result = await broker.rpc_request("buisness.delete", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/buisness/{buissness_id}")
async def update_buisness(buissness_id: int, buisness: BuisnessUpdate):
    try:
        payload = buisness.dict()
        payload["id"] = buissness_id
        result = await broker.rpc_request("buisness.update", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== PRODUCTS ==========

@app.get("/productos")
async def get_products(page: int = Query(1, ge=1),
                       page_size: int = Query(10, ge=1, le=100)):
    try:
        payload = {"page": page, "page_size": page_size}
        result = await broker.rpc_request("buisness.product.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{business_id}")
async def get_products_by_business(business_id: int,
                                   page: int = Query(1, ge=1),
                                   page_size: int = Query(50, ge=1, le=100)):
    try:
        payload = {"business_id": business_id, "page": page, "page_size": page_size}
        result = await broker.rpc_request("buisness.product.get_by_business", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/product/{product_id}")
async def get_product_by_id(product_id: int):
    try:
        payload = {"product_id": product_id}
        result = await broker.rpc_request("buisness.product.get_by_id", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/products/{buisness_id}")
async def create_product(buisness_id: int, product: ProductCreate = Body(...)):
    try:
        payload = product.dict()
        payload["buisness_id"] = buisness_id
        result = await broker.rpc_request("buisness.product.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "product", data, buisness_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/products/{product_id}")
async def update_product(product_id: int, data: dict = Body(...)):
    try:
        payload = data
        payload["product_id"] = product_id
        result = await broker.rpc_request("buisness.product.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    try:
        payload = {"product_id": product_id}
        result = await broker.rpc_request("buisness.product.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== CATEGORIES ==========

@app.get("/categories")
async def get_categories():
    try:
        payload = {}
        result = await broker.rpc_request("buisness.category.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/categories")
async def create_category(category: CategoryCreate = Body(...)):
    try:
        payload = category.dict()
        result = await broker.rpc_request("buisness.category.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "category", data, 0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== TABLES ==========

@app.post("/tables")
async def create_table(table: TableCreate = Body(...)):
    try:
        payload = table.dict()
        result = await broker.rpc_request("buisness.table.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "table", data, data.get("buisness_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tables/{business_id}")
async def get_tables(business_id: int, status: Optional[str] = Query(None)):
    try:
        payload = {"business_id": business_id}
        if status:
            payload["status"] = status
        result = await broker.rpc_request("buisness.table.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tables/{business_id}/occupied")
async def get_occupied_tables(business_id: int):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("buisness.table.get_occupied", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@app.put("/tables/{table_id}/occupied")
async def update_occupied_tables(table_id: int):
    try:
        payload = {"table_id": table_id}
        result = await broker.rpc_request("buisness.table.update_occupied", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("updated", "table", data, data.get("buisness_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/tables/{table_id}/status")
async def update_table_status(table_id: int, status_data: TableStatusUpdate = Body(...)):
    try:
        payload = status_data.dict()
        payload["table_id"] = table_id
        result = await broker.rpc_request("buisness.table.update_status", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tables/{table_id}")
async def delete_table(table_id: int):
    try:
        payload = {"table_id": table_id}
        result = await broker.rpc_request("buisness.table.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/tables/{table_id}")
async def update_table(table_id: int, table_data: TableUpdate = Body(...)):
    try:
        payload = table_data.dict(exclude_unset=True)
        payload["table_id"] = table_id
        result = await broker.rpc_request("buisness.table.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("updated", "table", data, data.get("buisness_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== MENU ITEMS ==========

@app.post("/menu-items")
async def create_menu_item(item: MenuItemCreate = Body(...)):
    try:
        payload = item.dict()
        result = await broker.rpc_request("buisness.menu.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "menu_item", data, data.get("business_id"))
        push_public_menu(data.get("business_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/menu-items/{business_id}")
async def get_menu_items(business_id: int,
                         category: Optional[str] = Query(None),
                         only_available: bool = Query(False)):
    try:
        payload = {
            "business_id": business_id,
            "category": category,
            "only_available": only_available
        }
        result = await broker.rpc_request("buisness.menu.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/menu-items/{menu_item_id}")
async def update_menu_item(menu_item_id: int, item: MenuItemUpdate = Body(...)):
    try:
        payload = item.dict(exclude_unset=True)
        payload["menu_item_id"] = menu_item_id
        result = await broker.rpc_request("buisness.menu.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        if data.get("business_id"):
            push_public_menu(data["business_id"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/menu-items/{menu_item_id}")
async def delete_menu_item(menu_item_id: int):
    try:
        payload = {"menu_item_id": menu_item_id}
        result = await broker.rpc_request("buisness.menu.delete", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        business_id = result.get("business_id")
        if business_id:
            push_public_menu(business_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== PUBLIC MENU (CONSUMER-FACING) ==========

@app.get("/public/menu/{business_id}")
async def get_public_menu(business_id: int):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("buisness.menu.public", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ORDERS ==========

@app.post("/orders")
async def create_order(order: OrderCreate = Body(...)):
    try:
        payload = order.dict()
        result = await broker.rpc_request("buisness.order.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "order", data, data.get("business_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{business_id}")
async def get_orders(business_id: int,
                     table_id: Optional[int] = Query(None),
                     status: Optional[str] = Query(None)):
    try:
        payload = {"business_id": business_id}
        if table_id:
            payload["table_id"] = table_id
        if status:
            payload["status"] = status
        result = await broker.rpc_request("buisness.order.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/detail/{order_id}")
async def get_order_detail(order_id: int):
    try:
        payload = {"order_id": order_id}
        result = await broker.rpc_request("buisness.order.get_detail", payload)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orders/{order_id}/items")
async def add_order_item(order_id: int, item: OrderItemCreate = Body(...)):
    try:
        payload = item.dict()
        payload["order_id"] = order_id
        result = await broker.rpc_request("buisness.order.add_item", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "order_item", data, data.get("business_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: int, status_data: OrderStatusUpdate = Body(...)):
    try:
        payload = status_data.dict()
        payload["order_id"] = order_id
        result = await broker.rpc_request("buisness.order.update_status", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/orders/{order_id}")
async def update_order(order_id: int, order_data: OrderUpdate = Body(...)):
    try:
        payload = order_data.dict(exclude_unset=True)
        payload["order_id"] = order_id
        result = await broker.rpc_request("buisness.order.update", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orders/{order_id}/pay")
async def pay_order(order_id: int,
                    payment_method: str = Body("cash"),
                    cashier_id: Optional[int] = Body(None),
                    discount: int = Body(0)):
    try:
        payload = {
            "order_id": order_id,
            "payment_method": payment_method,
            "cashier_id": cashier_id,
            "discount": discount
        }
        result = await broker.rpc_request("buisness.order.pay", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "sale", data, data.get("business_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== SALES ==========

@app.post("/sales")
async def create_sale(sale: SaleCreate = Body(...)):
    try:
        payload = sale.dict()
        result = await broker.rpc_request("buisness.sale.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "sale", data, data.get("business_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/{business_id}")
async def get_sales(business_id: int):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("buisness.sale.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/report/daily/{business_id}")
async def daily_report(business_id: int, date: Optional[str] = Query(None)):
    try:
        payload = {"business_id": business_id, "date": date}
        result = await broker.rpc_request("buisness.sale.report.daily", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sales/report/monthly/{business_id}")
async def monthly_report(business_id: int,
                         month: int = Query(...),
                         year: int = Query(...)):
    try:
        payload = {"business_id": business_id, "month": month, "year": year}
        result = await broker.rpc_request("buisness.sale.report.monthly", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== MONTHLY CLOSING (ARQUEO) ==========

@app.post("/monthly-closing")
async def create_monthly_closing(closing: MonthlyClosingCreate = Body(...)):
    try:
        payload = closing.dict()
        result = await broker.rpc_request("buisness.monthly_closing.create", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        data = result.get("data", {})
        notify_realtime("created", "monthly_closing", data, data.get("business_id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monthly-closing/{business_id}")
async def get_monthly_closings(business_id: int):
    try:
        payload = {"business_id": business_id}
        result = await broker.rpc_request("buisness.monthly_closing.get_all", payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== STRIPE PAYMENT ==========

@app.post("/orders/{order_id}/create-payment-intent")
async def create_payment_intent(order_id: int):
    try:
        payload = {"order_id": order_id}
        result = await broker.rpc_request("buisness.stripe.create_payment_intent", payload)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if endpoint_secret and sig_header:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
                event_data = {
                    "type": event.type,
                    "data": event.data.dict() if hasattr(event.data, "dict") else event.data
                }
            except stripe.error.SignatureVerificationError:
                raise HTTPException(status_code=400, detail="Invalid signature")
        else:
            import json as json_mod
            event_data = json_mod.loads(payload)

        result = await broker.rpc_request("buisness.stripe.handle_webhook", event_data)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
