from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from datetime import datetime
import json
from common.rabbitmq import message_pattern
from .connection.database import engine
from .schema import OrderCreate, OrderItemCreate, TableCreate
from .models.models import Tables, Product, Order, OrderItem


async def get_table_by_id(db: AsyncSession, table_id: int, business_id: int):
    result = await db.execute(
        select(Tables).where(Tables.id == table_id, Tables.buisness_id == business_id)
    )
    return result.scalar_one_or_none()

async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def get_order_by_id(db: AsyncSession, order_id: int):
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


@message_pattern("orders.table.create")
async def handle_create_table(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            table_data = TableCreate(**payload)
            
            existing = await db.execute(
                select(Tables).where(
                    Tables.name == table_data.name,
                    Tables.buisness_id == table_data.business_id
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "message": "Ya existe una mesa con ese nombre"}

            new_table = Tables(
                name=table_data.name,
                capacity=table_data.capacity,
                buisness_id=table_data.business_id,
                status="libre",
                location=table_data.location
            )
            db.add(new_table)
            await db.commit()
            await db.refresh(new_table)

            return {
                "success": True,
                "data": {
                    "id": new_table.id,
                    "name": new_table.name,
                    "capacity": new_table.capacity,
                    "status": new_table.status,
                    "location": new_table.location
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("orders.table.get_all")
async def handle_get_tables(payload):
    async with AsyncSession(engine) as db:
        try:
            business_id = payload.get("business_id")
            available_only = payload.get("available_only", False)
            
            if not business_id:
                return {"success": False, "message": "business_id requerido"}

            query = select(Tables).where(Tables.buisness_id == business_id)
            if available_only:
                query = query.where(or_(Tables.status == "libre", Tables.status == None))
            
            result = await db.execute(query)
            tables = result.scalars().all()

            tables_data = [
                {
                    "id": t.id,
                    "name": t.name,
                    "capacity": t.capacity,
                    "status": t.status,
                    "location": t.location
                }
                for t in tables
            ]

            return {"success": True, "data": tables_data}

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("orders.order.create")
async def handle_create_order(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            order_data = OrderCreate(**payload)
            
            table = await get_table_by_id(db, order_data.table_id, order_data.business_id)
            if not table:
                return {"success": False, "message": "Mesa no encontrada"}

            order_items = []
            total = 0
            
            for item in order_data.items:
                product = await get_product_by_id(db, item.product_id)
                if not product:
                    await db.rollback()
                    return {"success": False, "message": f"Producto {item.product_id} no encontrado"}
                
                subtotal = product.price * item.quantity
                total += subtotal
                
                order_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "unit_price": float(product.price),
                    "subtotal": float(subtotal)
                })

            now = datetime.utcnow().isoformat()
            new_order = Order(
                table_id=order_data.table_id,
                business_id=order_data.business_id,
                status="pending",
                notes=order_data.notes,
                total=total,
                created_at=now,
                updated_at=now
            )
            db.add(new_order)
            await db.flush()

            for item_data in order_items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    **item_data
                )
                db.add(order_item)

            table.status = "ocupada"
            await db.commit()
            await db.refresh(new_order)

            return {
                "success": True,
                "data": {
                    "id": new_order.id,
                    "business_id": new_order.business_id,
                    "table_id": new_order.table_id,
                    "status": new_order.status,
                    "notes": new_order.notes,
                    "total": float(new_order.total),
                    "items": order_items,
                    "created_at": new_order.created_at,
                    "updated_at": new_order.updated_at
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("orders.order.get_all")
async def handle_get_orders(payload):
    async with AsyncSession(engine) as db:
        try:
            business_id = payload.get("business_id")
            table_id = payload.get("table_id")
            status = payload.get("status")
            
            if not business_id:
                return {"success": False, "message": "business_id requerido"}

            query = select(Order).where(Order.business_id == business_id)
            
            if table_id:
                query = query.where(Order.table_id == table_id)
            if status:
                query = query.where(Order.status == status)
            
            query = query.order_by(Order.created_at.desc())
            
            result = await db.execute(query)
            orders = result.scalars().all()

            orders_data = []
            for order in orders:
                items_result = await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order.id)
                )
                items = items_result.scalars().all()
                
                orders_data.append({
                    "id": order.id,
                    "business_id": order.business_id,
                    "table_id": order.table_id,
                    "status": order.status,
                    "notes": order.notes,
                    "total": float(order.total),
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "items": [
                        {
                            "product_id": item.product_id,
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "unit_price": float(item.unit_price),
                            "subtotal": float(item.subtotal)
                        }
                        for item in items
                    ]
                })

            return {"success": True, "data": orders_data}

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("orders.order.get_by_id")
async def handle_get_order_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            order_id = payload.get("order_id")
            if not order_id:
                return {"success": False, "message": "order_id requerido"}

            order = await get_order_by_id(db, order_id)
            if not order:
                return {"success": False, "message": "Pedido no encontrado"}

            items_result = await db.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            items = items_result.scalars().all()

            return {
                "success": True,
                "data": {
                    "id": order.id,
                    "business_id": order.business_id,
                    "table_id": order.table_id,
                    "status": order.status,
                    "notes": order.notes,
                    "total": float(order.total),
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "items": [
                        {
                            "product_id": item.product_id,
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "unit_price": float(item.unit_price),
                            "subtotal": float(item.subtotal)
                        }
                        for item in items
                    ]
                }
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("orders.order.update_status")
async def handle_update_order_status(payload):
    async with AsyncSession(engine) as db:
        try:
            order_id = payload.get("order_id")
            new_status = payload.get("status")
            
            if not order_id or not new_status:
                return {"success": False, "message": "order_id y status son requeridos"}

            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            if new_status not in valid_statuses:
                return {"success": False, "message": f"Status inválido. Opciones: {valid_statuses}"}

            order = await get_order_by_id(db, order_id)
            if not order:
                return {"success": False, "message": "Pedido no encontrado"}

            old_status = order.status
            order.status = new_status
            order.updated_at = datetime.utcnow().isoformat()

            if new_status in ["completed", "cancelled"]:
                table = await get_table_by_id(db, order.table_id, order.business_id)
                if table:
                    table.status = "libre"

            await db.commit()
            await db.refresh(order)

            return {
                "success": True,
                "data": {
                    "id": order.id,
                    "old_status": old_status,
                    "new_status": order.status,
                    "updated_at": order.updated_at
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}
