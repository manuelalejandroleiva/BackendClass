from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta
import json
from common.rabbitmq import message_pattern
from .connection.database import engine
from .schema import SaleCreate, SaleItemCreate, ProductUpdate


async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def get_products_by_ids(db: AsyncSession, product_ids: list):
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    return result.scalars().all()

def calculate_totals(items_data: list) -> tuple:
    subtotal = sum(item["subtotal"] for item in items_data)
    return subtotal, subtotal

async def get_sales_by_business(db: AsyncSession, business_id: int):
    result = await db.execute(
        select(Sale)
        .where(Sale.business_id == business_id)
        .order_by(Sale.created_at.desc())
    )
    return result.scalars().all()

async def get_sales_by_period(db: AsyncSession, business_id: int, days: int):
    start_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(Sale)
        .where(
            Sale.business_id == business_id,
            Sale.created_at >= start_date.isoformat()
        )
        .order_by(Sale.created_at.desc())
    )
    return result.scalars().all()


@message_pattern("inventory.sale.create")
async def handle_create_sale(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            sale_data = SaleCreate(**payload)
            
            products_data = []
            total = 0
            
            for item in sale_data.items:
                product = await get_product_by_id(db, item.product_id)
                if not product:
                    return {"success": False, "message": f"Producto {item.product_id} no encontrado"}
                
                if product.stock < item.quantity:
                    return {"success": False, "message": f"Stock insuficiente para {product.name}"}
                
                product.stock -= item.quantity
                product.sold = (product.sold or 0) + item.quantity
                
                subtotal = product.price * item.quantity
                total += subtotal
                
                products_data.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "unit_price": float(product.price),
                    "subtotal": float(subtotal)
                })

            total_with_discount = max(0, total - sale_data.discount)
            
            new_sale = Sale(
                total=total_with_discount,
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
                "data": {
                    "id": new_sale.id,
                    "total": new_sale.total,
                    "payment_method": new_sale.payment_method,
                    "cashier_id": new_sale.cashier_id,
                    "discount": new_sale.discount,
                    "items": products_data,
                    "created_at": new_sale.created_at
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("inventory.sale.get_all")
async def handle_get_sales(payload):
    async with AsyncSession(engine) as db:
        try:
            business_id = payload.get("business_id")
            if not business_id:
                return {"success": False, "message": "business_id requerido"}

            sales = await get_sales_by_business(db, business_id)
            
            sales_data = []
            for sale in sales:
                result = await db.execute(
                    select(Product).where(Product.buisness_id == business_id)
                )
                all_products = {p.id: p for p in result.scalars().all()}
                
                sales_data.append({
                    "id": sale.id,
                    "total": sale.total,
                    "payment_method": sale.payment_method,
                    "cashier_id": sale.cashier_id,
                    "discount": sale.discount,
                    "created_at": sale.created_at
                })

            return {
                "success": True,
                "data": sales_data,
                "total": len(sales_data)
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("inventory.sales.report.period")
async def handle_sales_report_period(payload):
    async with AsyncSession(engine) as db:
        try:
            business_id = payload.get("business_id")
            if not business_id:
                return {"success": False, "message": "business_id requerido"}

            daily_sales = await get_sales_by_period(db, business_id, 1)
            weekly_sales = await get_sales_by_period(db, business_id, 7)
            monthly_sales = await get_sales_by_period(db, business_id, 30)

            def summarize(sales):
                return {
                    "count": len(sales),
                    "total": sum(s.total for s in sales)
                }

            return {
                "success": True,
                "data": {
                    "daily": summarize(daily_sales),
                    "weekly": summarize(weekly_sales),
                    "monthly": summarize(monthly_sales)
                }
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("inventory.sales.report.top_products")
async def handle_top_products(payload):
    async with AsyncSession(engine) as db:
        try:
            business_id = payload.get("business_id")
            limit = payload.get("limit", 10)
            
            if not business_id:
                return {"success": False, "message": "business_id requerido"}

            result = await db.execute(
                select(Product)
                .where(Product.buisness_id == business_id)
                .order_by(Product.sold.desc())
                .limit(limit)
            )
            products = result.scalars().all()

            top_products = []
            for p in products:
                top_products.append({
                    "product_id": p.id,
                    "product_name": p.name,
                    "total_sold": p.sold or 0,
                    "revenue": (p.sold or 0) * p.price
                })

            return {
                "success": True,
                "data": top_products
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("inventory.sales.report.summary")
async def handle_sales_summary(payload):
    async with AsyncSession(engine) as db:
        try:
            business_id = payload.get("business_id")
            if not business_id:
                return {"success": False, "message": "business_id requerido"}

            sales = await get_sales_by_business(db, business_id)
            
            total = sum(s.total for s in sales)
            total_cash = sum(s.total for s in sales if s.payment_method == "cash")
            total_card = sum(s.total for s in sales if s.payment_method == "card")

            return {
                "success": True,
                "data": {
                    "total": total,
                    "total_cash": total_cash,
                    "total_card": total_card,
                    "total_transactions": len(sales)
                }
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("inventory.product.update_stock")
async def handle_update_stock(payload):
    async with AsyncSession(engine) as db:
        try:
            product_id = payload.get("product_id")
            quantity = payload.get("quantity", 0)
            
            if not product_id:
                return {"success": False, "message": "product_id requerido"}

            product = await get_product_by_id(db, product_id)
            if not product:
                return {"success": False, "message": "Producto no encontrado"}

            new_stock = product.stock + quantity
            if new_stock < 0:
                return {"success": False, "message": "Stock no puede ser negativo"}

            product.stock = new_stock
            await db.commit()
            await db.refresh(product)

            return {
                "success": True,
                "data": {
                    "product_id": product.id,
                    "name": product.name,
                    "stock": product.stock
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("inventory.product.update")
async def handle_update_product(payload):
    if isinstance(payload, str):
        payload = json.loads(payload)
    product_id = payload.get("product_id")
    if not product_id:
        return {"success": False, "message": "product_id requerido"}
    async with AsyncSession(engine) as db:
        try:
            product = await get_product_by_id(db, product_id)
            if not product:
                return {"success": False, "message": "Producto no encontrado"}

            update_data = ProductUpdate(**{k: v for k, v in payload.items() if k != "product_id"})
            update_dict = update_data.dict(exclude_unset=True)

            for key, value in update_dict.items():
                setattr(product, key, value)

            await db.commit()
            await db.refresh(product)

            return {
                "success": True,
                "data": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "stock": product.stock,
                    "sold": product.sold
                }
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


from .models import Product, Sale
