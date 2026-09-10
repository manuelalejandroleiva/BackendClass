import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import json
import stripe

from .schema import BuisnessCreate, LicenciaCreate, BuisnessUpdate, ProductCreate, ProductUpdate, CategoryCreate
from .schema import TableCreate, TableStatusUpdate, TableUpdate
from .schema import MenuItemCreate, MenuItemUpdate
from .schema import OrderCreate, OrderItemCreate, OrderStatusUpdate, OrderUpdate
from .schema import SaleCreate, MonthlyClosingCreate
from .models.models import Buisness, Product, Tables, Sale, Category, TipoProducto
from .models.models import MenuItem, Order, OrderItem, MonthlyClosing
from .connection.database import engine
from common.rabbitmq import message_pattern
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func


@message_pattern("buisness.create")
async def handle_create_buisness(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            buisness_data = BuisnessCreate(**payload)
            existing_email = await db.scalar(select(Buisness.id).where(Buisness.email == buisness_data.email))
            if existing_email:
                return {"success": False, "message": "There is another buisness with that email."}
            new_buissness_data = buisness_data.dict(exclude={"id"})
            new_buisness = Buisness(**new_buissness_data)
            db.add(new_buisness)
            await db.commit()
            await db.refresh(new_buisness)
            response = new_buisness.to_dict()
            return {"success": True, "data": response}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.get_all")
async def handle_get_all_buisness(payload):
    async with AsyncSession(engine) as session:
        try:
            page = payload.get("page", 1)
            page_size = payload.get("page_size", 10)
            user_id = payload.get("user_id")
            
            offset = (page - 1) * page_size
            
            query = (
                select(Buisness)
                .options(
                    selectinload(Buisness.tables)
                )
            )
            count_query = select(Buisness.id)
            
            if user_id is not None:
                query = query.where(Buisness.user_id == user_id)
                count_query = count_query.where(Buisness.user_id == user_id)
                
            query = query.offset(offset).limit(page_size)
            
            result = await session.execute(query)
            buisness_list = result.scalars().all()
            
            total_result = await session.execute(count_query)
            total = len(total_result.scalars().all())
            
            data = []
            for b in buisness_list:
                b_dict = b.to_dict()
                
                if hasattr(b, 'tables') and b.tables is not None:
                    b_dict['tables'] = [
                        t.to_dict()
                        for t in b.tables
                    ]
                else:
                    b_dict['tables'] = []
                
                data.append(b_dict)
                
            return {
                "success": True,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
                "data": data
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.get_by_id")
async def handle_get_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            buisness_id = payload.get("id")
            if buisness_id is None:
                return {"success": False, "message": "The Id is missing in the payload."}
            query = (
                select(Buisness)
                .where(Buisness.id == int(buisness_id))
                .options(
                    selectinload(Buisness.tables)
                )
            )
            result = await db.execute(query)
            buisness = result.scalar_one_or_none()
            if not buisness:
                return {"success": False, "message": "Buisness not found."}
            user_data = buisness.to_dict()
            if hasattr(buisness, 'tables') and buisness.tables is not None:
                user_data['tables'] = [
                    t.to_dict()
                    for t in buisness.tables
                ]
            else:
                user_data['tables'] = []
            return {"success": True, "data": user_data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.delete")
async def handle_delete_buissness(payload):
    async with AsyncSession(engine) as db:
        try:
            buisness_id = payload.get("id")
            if buisness_id is None:
                return {"success": False, "message": "Falta el ID en el payload."}
            buisness = await db.get(Buisness, int(buisness_id))
            if not buisness:
                return {"success": False, "message": "Buisness no encontrado."}
            await db.delete(buisness)
            await db.commit()
            return {"success": True, "message": "Buissness eliminado correctamente."}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.update")
async def handle_update_buisness(payload):
    async with AsyncSession(engine) as db:
        try:
            buisness_id = payload.get("id")
            if buisness_id is None:
                return {"success": False, "message": "ID payload missing."}
            buisness = await db.get(Buisness, int(buisness_id))
            if not buisness:
                return {"success": False, "message": "Buisness not found."}
            buisness_data = BuisnessUpdate(**payload)
            update_data = {
                k: v for k, v in buisness_data.dict(exclude_unset=True, exclude={"id"}).items()
                if v is not None
            }
            for key, value in update_data.items():
                setattr(buisness, key, value)
            db.add(buisness)
            await db.commit()
            await db.refresh(buisness)
            buisness_response = buisness.to_dict()
            return {"success": True, "data": buisness_response}
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.category.create")
async def handle_create_category(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            data = CategoryCreate(**payload)
            existing = await db.scalar(select(Category).where(Category.name == data.name))
            if existing:
                return {"success": False, "message": "Ya existe una categoría con ese nombre."}
            new_category = Category(name=data.name)
            db.add(new_category)
            await db.commit()
            await db.refresh(new_category)
            return {"success": True, "data": new_category.to_dict()}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.category.get_all")
async def handle_get_all_categories(payload):
    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(select(Category))
            categories = result.scalars().all()
            data = [c.to_dict() for c in categories]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.product.get_all")
async def handle_get_all_products(payload):
    page = payload.get("page", 1)
    page_size = payload.get("page_size", 10)
    async with AsyncSession(engine) as session:
        offset = (page - 1) * page_size
        result = await session.execute(select(Product).offset(offset).limit(page_size))
        products = result.scalars().all()
        total_result = await session.execute(select(Product))
        total = len(total_result.scalars().all())
        data = [
            u.to_dict()
            for u in products
        ]
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "data": data
        }


@message_pattern("buisness.product.get_by_business")
async def handle_get_products_by_business(payload):
    business_id = payload.get("business_id")
    page = payload.get("page", 1)
    page_size = payload.get("page_size", 50)
    async with AsyncSession(engine) as session:
        try:
            offset = (page - 1) * page_size
            result = await session.execute(
                select(Product)
                .where(Product.buisness_id == business_id)
                .offset(offset)
                .limit(page_size)
            )
            
            products = result.scalars().all()
            total_result = await session.execute(
                select(Product).where(Product.buisness_id == business_id)
            )
            total = len(total_result.scalars().all())
            data = [
                p.to_dict()
                for p in products
            ]
            return {
                "success": True,
                "data": data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.product.create")
async def handle_create_product(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            buisness_id = payload.pop("buisness_id")
            data = ProductCreate(**payload)
            tipo_id = data.tipo_id
            if tipo_id is None:
                result = await db.execute(select(func.max(Product.tipo_id)))
                max_tipo_id = result.scalar()
                tipo_id = (max_tipo_id or 0) + 1
                tipo_exists = await db.execute(
                    select(TipoProducto).where(TipoProducto.id == tipo_id)
                )
                if not tipo_exists.scalar_one_or_none():
                    db.add(TipoProducto(id=tipo_id, nombre=f"Tipo {tipo_id}"))
            new_product = Product(
                name=data.product_name,
                sku=data.sku,
                description=data.description,
                category_id=data.category_id if data.category_id is not None else payload.get("category"),
                tipo_id=tipo_id,
                price=data.sales_price,
                cost=data.cost,
                stock=data.initial_stock,
                min_stock=data.min_stock,
                pz=data.pz,
                sold=0,
                buisness_id=buisness_id
            )
            db.add(new_product)
            await db.commit()
            await db.refresh(new_product)
            return {
                "success": True,
                "data": new_product.to_dict()
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.product.get_by_id")
async def handle_get_product_by_id(payload):
    product_id = payload.get("product_id")
    if product_id is None:
        return {"success": False, "message": "product_id is required"}
    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(
                select(Product).where(Product.id == int(product_id))
            )
            product = result.scalar_one_or_none()
            if not product:
                return {"success": False, "message": "Product not found"}
            return {"success": True, "data": product.to_dict()}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.product.update")
async def handle_update_product(payload):
    if isinstance(payload, str):
        payload = json.loads(payload)
    product_id = payload.get("product_id")
    if product_id is None:
        return {"success": False, "message": "product_id is required"}
    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(
                select(Product).where(Product.id == int(product_id))
            )
            product = result.scalar_one_or_none()
            if not product:
                return {"success": False, "message": "Product not found"}
            update_data = ProductUpdate(**{k: v for k, v in payload.items() if k != "product_id"})
            update_dict = update_data.dict(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(product, key, value)
            await session.commit()
            await session.refresh(product)
            return {"success": True, "data": product.to_dict()}
        except Exception as e:
            await session.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.product.delete")
async def handle_delete_product(payload):
    async with AsyncSession(engine) as db:
        try:
            
            product_id = payload.get("product_id")
            if not product_id:
                return {"success": False, "message": "product_id es requerido."}
           
            result = await db.execute(
                select(Product).where(
                    Product.id == int(product_id)
                )
            )
            product = result.scalar_one_or_none()
            if not product:
                return {"success": False, "message": "Producto no encontrado o no pertenece a este negocio."}
            await db.delete(product)
            await db.commit()
            return {"success": True, "message": "Producto eliminado correctamente."}
        except Exception as e:
            return {"success": False, "message": str(e)}


# ========== TABLES ==========

@message_pattern("buisness.table.create")
async def handle_create_table(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            table_data = TableCreate(**payload)
            new_table = Tables(
                name=table_data.name,
                capacity=table_data.capacity,
                buisness_id=table_data.buisness_id,
                status=table_data.status,
                location=table_data.location,
                tipo_id=table_data.tipo_id,
                precio_wash=table_data.precio_wash
            )
            db.add(new_table)
            await db.commit()
            await db.refresh(new_table)
            return {
                "success": True,
                "data": new_table.to_dict()
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.table.get_all")
async def handle_get_tables(payload):
    business_id = payload.get("business_id")
    status_filter = payload.get("status")
    async with AsyncSession(engine) as db:
        try:
            query = select(Tables).where(Tables.buisness_id == business_id)
            if status_filter:
                query = query.where(Tables.status == status_filter)
            result = await db.execute(query)
            tables = result.scalars().all()
            data = [
                t.to_dict()
                for t in tables
            ]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.table.get_occupied")
async def handle_get_occupied_tables(payload):
    business_id = payload.get("business_id")
    async with AsyncSession(engine) as db:
        try:
            result = await db.execute(
                select(Tables).where(
                    Tables.buisness_id == business_id,
                    Tables.status == "occupied"
                )
            )
            tables = result.scalars().all()
            data = [
                t.to_dict()
                for t in tables
            ]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.table.update_occupied")
async def handle_update_occupied_table(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            table_id = payload.get("table_id")
            if not table_id:
                return {"success": False, "message": "table_id requerido."}
            table = await db.get(Tables, int(table_id))
            if not table:
                return {"success": False, "message": "Mesa no encontrada."}
            table.status = "available" if table.status == "occupied" else "occupied"
            await db.commit()
            await db.refresh(table)
            return {
                "success": True,
                "data": table.to_dict()
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.table.update_status")
async def handle_update_table_status(payload):
    async with AsyncSession(engine) as db:
        try:
            table_id = payload.get("table_id")
            status_data = TableStatusUpdate(**payload)
            table = await db.get(Tables, int(table_id))
            if not table:
                return {"success": False, "message": "Mesa no encontrada."}
            table.status = status_data.status
            await db.commit()
            await db.refresh(table)
            return {
                "success": True,
                "data": table.to_dict()
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.table.update")
async def handle_update_table(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            table_id = payload.get("table_id")
            if not table_id:
                return {"success": False, "message": "table_id requerido."}
            table = await db.get(Tables, int(table_id))
            if not table:
                return {"success": False, "message": "Mesa no encontrada."}
            update_data = TableUpdate(**payload)
            update_dict = update_data.dict(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(table, key, value)
            await db.commit()
            await db.refresh(table)
            return {
                "success": True,
                "data": table.to_dict()
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.table.delete")
async def handle_delete_table(payload):
    async with AsyncSession(engine) as db:
        try:
            table_id = payload.get("table_id")
            if not table_id:
                return {"success": False, "message": "table_id requerido."}
            table = await db.get(Tables, int(table_id))
            if not table:
                return {"success": False, "message": "Mesa no encontrada."}
            await db.delete(table)
            await db.commit()
            return {"success": True, "message": "Mesa eliminada correctamente."}
        except Exception as e:
            return {"success": False, "message": str(e)}


# ========== MENU ITEMS ==========

@message_pattern("buisness.menu.create")
async def handle_create_menu_item(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            item_data = MenuItemCreate(**payload)
            new_item = MenuItem(**item_data.dict())
            db.add(new_item)
            await db.commit()
            await db.refresh(new_item)
            return {
                "success": True,
                "data": new_item.to_dict()
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.menu.get_all")
async def handle_get_menu_items(payload):
    business_id = payload.get("business_id")
    category = payload.get("category")
    only_available = payload.get("only_available", False)
    async with AsyncSession(engine) as db:
        try:
            query = select(MenuItem).where(MenuItem.business_id == business_id)
            if category:
                query = query.where(MenuItem.category == category)
            if only_available:
                query = query.where(MenuItem.available == True)
            result = await db.execute(query)
            items = result.scalars().all()
            data = [
                i.to_dict()
                for i in items
            ]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.menu.update")
async def handle_update_menu_item(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            item_id = payload.get("menu_item_id")
            if not item_id:
                return {"success": False, "message": "menu_item_id requerido."}
            item = await db.get(MenuItem, int(item_id))
            if not item:
                return {"success": False, "message": "Item del menu no encontrado."}
            update_data = MenuItemUpdate(**payload)
            update_dict = update_data.dict(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(item, key, value)
            await db.commit()
            await db.refresh(item)
            return {
                "success": True,
                "data": item.to_dict()
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.menu.delete")
async def handle_delete_menu_item(payload):
    async with AsyncSession(engine) as db:
        try:
            item_id = payload.get("menu_item_id")
            if not item_id:
                return {"success": False, "message": "menu_item_id requerido."}
            item = await db.get(MenuItem, int(item_id))
            if not item:
                return {"success": False, "message": "Item del menu no encontrado."}
            business_id = item.business_id
            await db.delete(item)
            await db.commit()
            return {"success": True, "message": "Item eliminado correctamente.", "business_id": business_id}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.menu.public")
async def handle_get_public_menu(payload):
    business_id = payload.get("business_id")
    async with AsyncSession(engine) as db:
        try:
            business = await db.get(Buisness, business_id)
            if not business:
                return {"success": False, "message": "Business not found"}

            result = await db.execute(
                select(MenuItem)
                .where(
                    MenuItem.business_id == business_id,
                    MenuItem.available == True
                )
                .order_by(MenuItem.category, MenuItem.name)
            )
            items = result.scalars().all()

            from collections import defaultdict
            grouped = defaultdict(list)
            for item in items:
                cat = item.category or "General"
                grouped[cat].append({
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "category": item.category,
                    "image": item.image
                })

            categories = [
                {"category": cat, "items": items_list}
                for cat, items_list in grouped.items()
            ]

            return {
                "success": True,
                "data": {
                    "business_id": business.id,
                    "business_name": business.name,
                    "categories": categories
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


# ========== ORDERS ==========

@message_pattern("buisness.order.create")
async def handle_create_order(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            order_data = OrderCreate(**payload)

            now = datetime.utcnow().isoformat()

            new_order = Order(
                table_id=order_data.table_id,
                business_id=order_data.business_id,
                status="pending",
                total=0,
                notes=order_data.notes,
                created_at=now,
                updated_at=now
            )
            db.add(new_order)
            await db.flush()

            total = 0
            items_data = []
            for item in order_data.items:
                menu_item = await db.get(MenuItem, item.menu_item_id)
                if not menu_item:
                    await db.rollback()
                    return {"success": False, "message": f"MenuItem {item.menu_item_id} no encontrado."}
                if not menu_item.available:
                    await db.rollback()
                    return {"success": False, "message": f"'{menu_item.name}' no esta disponible."}

                unit_price = menu_item.price
                subtotal = unit_price * item.quantity
                total += subtotal

                order_item = OrderItem(
                    order_id=new_order.id,
                    menu_item_id=item.menu_item_id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                    notes=item.notes
                )
                db.add(order_item)
                items_data.append({
                    "menu_item_id": menu_item.id,
                    "name": menu_item.name,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal
                })

            new_order.total = total
            await db.commit()
            await db.refresh(new_order)

            return {
                "success": True,
                "data": {
                    "id": new_order.id,
                    "table_id": new_order.table_id,
                    "business_id": new_order.business_id,
                    "status": new_order.status,
                    "total": new_order.total,
                    "notes": new_order.notes,
                    "created_at": new_order.created_at,
                    "items": items_data
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.order.get_all")
async def handle_get_orders(payload):
    business_id = payload.get("business_id")
    table_id = payload.get("table_id")
    status_filter = payload.get("status")
    async with AsyncSession(engine) as db:
        try:
            query = select(Order).where(Order.business_id == business_id)
            if table_id:
                query = query.where(Order.table_id == table_id)
            if status_filter:
                query = query.where(Order.status == status_filter)
            query = query.order_by(Order.created_at.desc())
            result = await db.execute(query)
            orders = result.scalars().all()

            data = []
            for order in orders:
                items_result = await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order.id)
                )
                items = items_result.scalars().all()
                items_data = []
                for item in items:
                    menu_item = await db.get(MenuItem, item.menu_item_id)
                    items_data.append({
                        "id": item.id,
                        "menu_item_id": item.menu_item_id,
                        "name": menu_item.name if menu_item else "Unknown",
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "subtotal": item.subtotal,
                        "notes": item.notes
                    })
                data.append({
                    "id": order.id,
                    "table_id": order.table_id,
                    "business_id": order.business_id,
                    "status": order.status,
                    "total": order.total,
                    "notes": order.notes,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "items": items_data
                })

            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.order.get_detail")
async def handle_get_order_detail(payload):
    order_id = payload.get("order_id")
    async with AsyncSession(engine) as db:
        try:
            order = await db.get(Order, int(order_id))
            if not order:
                return {"success": False, "message": "Orden no encontrada."}

            items_result = await db.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            items = items_result.scalars().all()
            items_data = []
            for item in items:
                menu_item = await db.get(MenuItem, item.menu_item_id)
                items_data.append({
                    "id": item.id,
                    "menu_item_id": item.menu_item_id,
                    "name": menu_item.name if menu_item else "Unknown",
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                    "notes": item.notes
                })

            return {
                "success": True,
                "data": {
                    "id": order.id,
                    "table_id": order.table_id,
                    "business_id": order.business_id,
                    "status": order.status,
                    "total": order.total,
                    "notes": order.notes,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "items": items_data
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.order.add_item")
async def handle_add_order_item(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            order_id = payload.get("order_id")
            item_data = OrderItemCreate(**payload)

            order = await db.get(Order, int(order_id))
            if not order:
                return {"success": False, "message": "Orden no encontrada."}
            if order.status in ("paid", "cancelled"):
                return {"success": False, "message": "No se pueden agregar items a una orden pagada o cancelada."}

            menu_item = await db.get(MenuItem, item_data.menu_item_id)
            if not menu_item:
                return {"success": False, "message": "MenuItem no encontrado."}
            if not menu_item.available:
                return {"success": False, "message": f"'{menu_item.name}' no esta disponible."}

            unit_price = menu_item.price
            subtotal = unit_price * item_data.quantity

            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_data.menu_item_id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                notes=item_data.notes
            )
            db.add(order_item)

            order.total += subtotal
            order.updated_at = datetime.utcnow().isoformat()
            await db.commit()
            await db.refresh(order_item)

            return {
                "success": True,
                "data": {
                    "id": order_item.id,
                    "menu_item_id": order_item.menu_item_id,
                    "name": menu_item.name,
                    "quantity": order_item.quantity,
                    "unit_price": order_item.unit_price,
                    "subtotal": order_item.subtotal,
                    "order_total": order.total,
                    "business_id": order.business_id
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.order.update_status")
async def handle_update_order_status(payload):
    async with AsyncSession(engine) as db:
        try:
            order_id = payload.get("order_id")
            status_data = OrderStatusUpdate(**payload)

            order = await db.get(Order, int(order_id))
            if not order:
                return {"success": False, "message": "Orden no encontrada."}

            old_status = order.status
            order.status = status_data.status
            order.updated_at = datetime.utcnow().isoformat()

            # If order is being set to "paid", create a sale record
            if status_data.status == "paid" and old_status != "paid":
                sale = Sale(
                    total=order.total,
                    payment_method="cash",
                    business_id=order.business_id,
                    cashier_id=payload.get("cashier_id"),
                    discount=0,
                    created_at=datetime.utcnow().isoformat()
                )
                db.add(sale)

            await db.commit()
            await db.refresh(order)

            return {
                "success": True,
                "data": order.to_dict()
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.order.update")
async def handle_update_order(payload):
    async with AsyncSession(engine) as db:
        try:
            order_id = payload.get("order_id")
            if not order_id:
                return {"success": False, "message": "order_id requerido."}
            order = await db.get(Order, int(order_id))
            if not order:
                return {"success": False, "message": "Orden no encontrada."}
            update_data = OrderUpdate(**payload)
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            for key, value in update_dict.items():
                setattr(order, key, value)
            await db.commit()
            await db.refresh(order)
            return {
                "success": True,
                "message": "Orden actualizada correctamente."
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.order.pay")
async def handle_pay_order(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            order_id = payload.get("order_id")
            payment_method = payload.get("payment_method", "cash")
            cashier_id = payload.get("cashier_id")
            discount = payload.get("discount", 0)

            order = await db.get(Order, int(order_id))
            if not order:
                return {"success": False, "message": "Orden no encontrada."}
            if order.status == "paid":
                return {"success": False, "message": "La orden ya esta pagada."}

            final_total = max(0, order.total - discount)

            sale = Sale(
                total=final_total,
                payment_method=payment_method,
                business_id=order.business_id,
                cashier_id=cashier_id,
                discount=discount,
                created_at=datetime.utcnow().isoformat()
            )
            db.add(sale)

            order.status = "paid"
            order.updated_at = datetime.utcnow().isoformat()

            table = await db.get(Tables, order.table_id)
            if table:
                table.status = "available"

            await db.commit()
            await db.refresh(sale)

            return {
                "success": True,
                "data": {
                    "sale_id": sale.id,
                    "total": final_total,
                    "payment_method": payment_method,
                    "discount": discount,
                    "order_id": order.id,
                    "business_id": order.business_id,
                    "created_at": sale.created_at
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


# ========== SALES ==========

@message_pattern("buisness.sale.create")
async def handle_create_sale(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            sale_data = SaleCreate(**payload)
            new_sale = Sale(
                total=sale_data.total,
                payment_method=sale_data.payment_method,
                business_id=sale_data.business_id,
                cashier_id=sale_data.cashier_id,
                discount=sale_data.discount,
                created_at=datetime.utcnow().isoformat()
            )
            db.add(new_sale)
            await db.commit()
            await db.refresh(new_sale)
            return {
                "success": True,
                "data": new_sale.to_dict()
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.sale.get_all")
async def handle_get_sales(payload):
    business_id = payload.get("business_id")
    async with AsyncSession(engine) as db:
        try:
            result = await db.execute(
                select(Sale)
                .where(Sale.business_id == business_id)
                .order_by(Sale.created_at.desc())
            )
            sales = result.scalars().all()
            data = [
                s.to_dict()
                for s in sales
            ]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.sale.report.daily")
async def handle_daily_report(payload):
    business_id = payload.get("business_id")
    date_str = payload.get("date")
    async with AsyncSession(engine) as db:
        try:
            query = select(Sale).where(Sale.business_id == business_id)
            if date_str:
                query = query.where(Sale.created_at.startswith(date_str[:10]))
            result = await db.execute(query)
            sales = result.scalars().all()

            total = sum(s.total for s in sales)
            total_cash = sum(s.total for s in sales if s.payment_method == "cash")
            total_card = sum(s.total for s in sales if s.payment_method == "card")
            total_discounts = sum(s.discount for s in sales)

            return {
                "success": True,
                "data": {
                    "date": date_str or "all",
                    "total_sales": total,
                    "total_cash": total_cash,
                    "total_card": total_card,
                    "total_discounts": total_discounts,
                    "total_transactions": len(sales)
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("buisness.sale.report.monthly")
async def handle_monthly_report(payload):
    business_id = payload.get("business_id")
    month = payload.get("month")
    year = payload.get("year")
    async with AsyncSession(engine) as db:
        try:
            query = select(Sale).where(Sale.business_id == business_id)
            if month and year:
                prefix = f"{year:04d}-{month:02d}"
                query = query.where(Sale.created_at.startswith(prefix))
            result = await db.execute(query)
            sales = result.scalars().all()

            total = sum(s.total for s in sales)
            total_cash = sum(s.total for s in sales if s.payment_method == "cash")
            total_card = sum(s.total for s in sales if s.payment_method == "card")
            total_discounts = sum(s.discount for s in sales)

            return {
                "success": True,
                "data": {
                    "month": month,
                    "year": year,
                    "total_sales": total,
                    "total_cash": total_cash,
                    "total_card": total_card,
                    "total_discounts": total_discounts,
                    "total_transactions": len(sales)
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


# ========== MONTHLY CLOSING ==========

@message_pattern("buisness.monthly_closing.create")
async def handle_create_monthly_closing(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)
            closing_data = MonthlyClosingCreate(**payload)

            existing = await db.execute(
                select(MonthlyClosing).where(
                    MonthlyClosing.business_id == closing_data.business_id,
                    MonthlyClosing.month == closing_data.month,
                    MonthlyClosing.year == closing_data.year,
                    MonthlyClosing.status == "closed"
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "message": "Este mes ya fue cerrado."}

            prefix = f"{closing_data.year:04d}-{closing_data.month:02d}"
            result = await db.execute(
                select(Sale).where(
                    Sale.business_id == closing_data.business_id,
                    Sale.created_at.startswith(prefix)
                )
            )
            sales = result.scalars().all()

            total_sales = sum(s.total for s in sales)
            total_cash = sum(s.total for s in sales if s.payment_method == "cash")
            total_card = sum(s.total for s in sales if s.payment_method == "card")
            total_discounts = sum(s.discount for s in sales)

            closing = MonthlyClosing(
                business_id=closing_data.business_id,
                month=closing_data.month,
                year=closing_data.year,
                total_sales=total_sales,
                total_cash=total_cash,
                total_card=total_card,
                total_transactions=len(sales),
                total_discounts=total_discounts,
                closed_at=datetime.utcnow().isoformat(),
                status="closed"
            )
            db.add(closing)
            await db.commit()
            await db.refresh(closing)

            return {
                "success": True,
                "data": closing.to_dict()
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.monthly_closing.get_all")
async def handle_get_monthly_closings(payload):
    business_id = payload.get("business_id")
    async with AsyncSession(engine) as db:
        try:
            result = await db.execute(
                select(MonthlyClosing)
                .where(MonthlyClosing.business_id == business_id)
                .order_by(MonthlyClosing.year.desc(), MonthlyClosing.month.desc())
            )
            closings = result.scalars().all()
            data = [
                c.to_dict()
                for c in closings
            ]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


# ========== STRIPE PAYMENT ==========

@message_pattern("buisness.stripe.create_payment_intent")
async def handle_create_payment_intent(payload):
    order_id = payload.get("order_id")
    async with AsyncSession(engine) as db:
        try:
            order = await db.get(Order, int(order_id))
            if not order:
                return {"success": False, "message": "Orden no encontrada."}
            if order.status == "paid":
                return {"success": False, "message": "La orden ya esta pagada."}
            if order.total <= 0:
                return {"success": False, "message": "El total debe ser mayor a cero."}

           
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

            existing_intent_id = order.stripe_payment_intent_id
            if existing_intent_id:
                try:
                    intent = stripe.PaymentIntent.retrieve(existing_intent_id)
                    if intent.status in ("requires_payment_method", "requires_confirmation"):
                        return {
                            "success": True,
                            "data": {
                                "client_secret": intent.client_secret,
                                "payment_intent_id": intent.id
                            }
                        }
                except Exception:
                    pass

            intent = stripe.PaymentIntent.create(
                amount=order.total,
                currency="usd",
                metadata={
                    "order_id": str(order.id),
                    "business_id": str(order.business_id)
                },
                description=f"Orden #{order.id} - Mesa {order.table_id}"
            )

            order.stripe_payment_intent_id = intent.id
            await db.commit()

            return {
                "success": True,
                "data": {
                    "client_secret": intent.client_secret,
                    "payment_intent_id": intent.id
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("buisness.stripe.handle_webhook")
async def handle_stripe_webhook(payload):
    async with AsyncSession(engine) as db:
        try:
            stripe_event = payload
            event_type = stripe_event.get("type")
            data_object = stripe_event.get("data", {}).get("object", {})

            if event_type == "payment_intent.succeeded":
                payment_intent_id = data_object.get("id")
                metadata = data_object.get("metadata", {})

                result = await db.execute(
                    select(Order).where(Order.stripe_payment_intent_id == payment_intent_id)
                )
                order = result.scalar_one_or_none()

                if not order:
                    amount = data_object.get("amount", 0)
                    business_id = metadata.get("business_id")
                    order_id = metadata.get("order_id")
                    if order_id:
                        order = await db.get(Order, int(order_id))

                if not order:
                    return {"success": False, "message": "Orden no encontrada para este payment_intent."}

                if order.status == "paid":
                    return {"success": True, "message": "La orden ya fue procesada."}

                sale = Sale(
                    total=order.total,
                    payment_method="stripe",
                    business_id=order.business_id,
                    discount=0,
                    created_at=datetime.utcnow().isoformat()
                )
                db.add(sale)

                order.status = "paid"
                order.updated_at = datetime.utcnow().isoformat()

                if order.table_id:
                    table = await db.get(Tables, order.table_id)
                    if table:
                        table.status = "available"

                await db.commit()

                return {"success": True, "message": "Pago procesado correctamente."}

            elif event_type == "payment_intent.payment_failed":
                payment_intent_id = data_object.get("id")
                result = await db.execute(
                    select(Order).where(Order.stripe_payment_intent_id == payment_intent_id)
                )
                order = result.scalar_one_or_none()
                if order:
                    order.status = "payment_failed"
                    order.updated_at = datetime.utcnow().isoformat()
                    await db.commit()

                return {"success": True, "message": "Fallo registrado."}

            return {"success": True, "message": f"Evento {event_type} recibido."}

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}



