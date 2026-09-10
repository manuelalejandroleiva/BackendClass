import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from .connection.database import engine
from .models.models import Property, Tenant, Payment, TenantStatus, PayerStatus, PaymentMethod
from common.rabbitmq import message_pattern
from datetime import datetime


# ===================== PROPERTY HANDLERS =====================

@message_pattern("landlord.property.create")
async def handle_create_property(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            prop = Property(
                name=payload.get("name"),
                address=payload.get("address"),
                landlord_id=payload.get("landlord_id"),
                monthly_rent=payload.get("monthly_rent", 0.0),
                description=payload.get("description")
            )
            db.add(prop)
            await db.commit()
            await db.refresh(prop)

            return {
                "success": True,
                "data": {
                    "id": prop.id,
                    "name": prop.name,
                    "address": prop.address,
                    "landlord_id": prop.landlord_id
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("landlord.property.get_all")
async def handle_get_all_properties(payload):
    async with AsyncSession(engine) as db:
        try:
            landlord_id = payload.get("landlord_id")
            query = select(Property)
            if landlord_id:
                query = query.where(Property.landlord_id == int(landlord_id))

            result = await db.execute(query)
            properties = result.scalars().all()

            data = [{
                "id": p.id,
                "name": p.name,
                "address": p.address,
                "landlord_id": p.landlord_id,
                "monthly_rent": p.monthly_rent,
                "description": p.description,
                "created_at": p.created_at.isoformat() if p.created_at else None
            } for p in properties]

            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("landlord.property.get_by_id")
async def handle_get_property_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            prop_id = payload.get("id")
            if not prop_id:
                return {"success": False, "message": "Falta el ID de la propiedad"}

            prop = await db.get(Property, int(prop_id))
            if not prop:
                return {"success": False, "message": "Propiedad no encontrada"}

            return {
                "success": True,
                "data": {
                    "id": prop.id,
                    "name": prop.name,
                    "address": prop.address,
                    "landlord_id": prop.landlord_id,
                    "monthly_rent": prop.monthly_rent,
                    "description": prop.description,
                    "created_at": prop.created_at.isoformat() if prop.created_at else None
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("landlord.property.update")
async def handle_update_property(payload):
    async with AsyncSession(engine) as db:
        try:
            prop_id = payload.get("id")
            if not prop_id:
                return {"success": False, "message": "Falta el ID de la propiedad"}

            prop = await db.get(Property, int(prop_id))
            if not prop:
                return {"success": False, "message": "Propiedad no encontrada"}

            for field in ["name", "address", "monthly_rent", "description"]:
                if field in payload:
                    setattr(prop, field, payload[field])

            prop.updated_at = datetime.utcnow()
            db.add(prop)
            await db.commit()
            await db.refresh(prop)

            return {"success": True, "data": {"id": prop.id, "name": prop.name, "address": prop.address}}
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("landlord.property.delete")
async def handle_delete_property(payload):
    async with AsyncSession(engine) as db:
        try:
            prop_id = payload.get("id")
            if not prop_id:
                return {"success": False, "message": "Falta el ID de la propiedad"}

            prop = await db.get(Property, int(prop_id))
            if not prop:
                return {"success": False, "message": "Propiedad no encontrada"}

            await db.delete(prop)
            await db.commit()

            return {"success": True, "message": "Propiedad eliminada correctamente"}
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


# ===================== TENANT HANDLERS =====================

@message_pattern("landlord.tenant.create")
async def handle_create_tenant(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            tenant = Tenant(
                name=payload.get("name"),
                email=payload.get("email"),
                phone=payload.get("phone"),
                property_id=payload.get("property_id"),
                rent_amount=payload.get("rent_amount", 0.0),
                deposit=payload.get("deposit", 0.0),
                start_date=datetime.strptime(payload["start_date"], "%Y-%m-%d").date() if payload.get("start_date") else None,
                notes=payload.get("notes")
            )
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)

            return {
                "success": True,
                "data": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "property_id": tenant.property_id,
                    "status": tenant.status.value,
                    "payer_status": tenant.payer_status.value
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("landlord.tenant.get_all")
async def handle_get_all_tenants(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            property_id = payload.get("property_id")
            status = payload.get("status")

            query = select(Tenant)
            if property_id:
                query = query.where(Tenant.property_id == int(property_id))
            if status:
                try:
                    query = query.where(Tenant.status == TenantStatus(status))
                except ValueError:
                    return {"success": False, "message": f"Estado inválido: {status}"}

            result = await db.execute(query)
            tenants = result.scalars().all()

            data = [{
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "phone": t.phone,
                "property_id": t.property_id,
                "rent_amount": t.rent_amount,
                "deposit": t.deposit,
                "start_date": t.start_date.isoformat() if t.start_date else None,
                "status": t.status.value,
                "payer_status": t.payer_status.value,
                "notes": t.notes,
                "created_at": t.created_at.isoformat() if t.created_at else None
            } for t in tenants]

            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("landlord.tenant.get_by_id")
async def handle_get_tenant_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            tenant_id = payload.get("id")
            if not tenant_id:
                return {"success": False, "message": "Falta el ID del inquilino"}

            tenant = await db.get(Tenant, int(tenant_id))
            if not tenant:
                return {"success": False, "message": "Inquilino no encontrado"}

            return {
                "success": True,
                "data": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "email": tenant.email,
                    "phone": tenant.phone,
                    "property_id": tenant.property_id,
                    "rent_amount": tenant.rent_amount,
                    "deposit": tenant.deposit,
                    "start_date": tenant.start_date.isoformat() if tenant.start_date else None,
                    "status": tenant.status.value,
                    "payer_status": tenant.payer_status.value,
                    "notes": tenant.notes,
                    "created_at": tenant.created_at.isoformat() if tenant.created_at else None
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("landlord.tenant.update")
async def handle_update_tenant(payload):
    async with AsyncSession(engine) as db:
        try:
            tenant_id = payload.get("id")
            if not tenant_id:
                return {"success": False, "message": "Falta el ID del inquilino"}

            tenant = await db.get(Tenant, int(tenant_id))
            if not tenant:
                return {"success": False, "message": "Inquilino no encontrado"}

            for field in ["name", "email", "phone", "property_id", "rent_amount", "deposit", "notes"]:
                if field in payload:
                    setattr(tenant, field, payload[field])

            if "start_date" in payload and payload["start_date"]:
                tenant.start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d").date()

            if "status" in payload:
                status_upper = payload["status"].upper()
                if status_upper not in [s.value for s in TenantStatus]:
                    return {"success": False, "message": "Estado no válido"}
                tenant.status = TenantStatus(status_upper)

            if "payer_status" in payload:
                ps = payload["payer_status"]
                valid_statuses = [s.value for s in PayerStatus]
                if ps not in valid_statuses:
                    return {"success": False, "message": "Estado de pagador no válido"}
                tenant.payer_status = PayerStatus(ps)

            tenant.updated_at = datetime.utcnow()
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)

            return {
                "success": True,
                "data": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "status": tenant.status.value,
                    "payer_status": tenant.payer_status.value
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("landlord.tenant.delete")
async def handle_delete_tenant(payload):
    async with AsyncSession(engine) as db:
        try:
            tenant_id = payload.get("id")
            if not tenant_id:
                return {"success": False, "message": "Falta el ID del inquilino"}

            tenant = await db.get(Tenant, int(tenant_id))
            if not tenant:
                return {"success": False, "message": "Inquilino no encontrado"}

            await db.delete(tenant)
            await db.commit()

            return {"success": True, "message": "Inquilino eliminado correctamente"}
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


# ===================== PAYMENT HANDLERS =====================

@message_pattern("landlord.payment.create")
async def handle_create_payment(payload):
    async with AsyncSession(engine) as db:
        try:
            if isinstance(payload, str):
                payload = json.loads(payload)

            tenant_id = payload.get("tenant_id")
            tenant = await db.get(Tenant, int(tenant_id))
            if not tenant:
                return {"success": False, "message": "Inquilino no encontrado"}

            # Extraemos de forma segura el string de pago y lo convertimos a un objeto date real de Python
            raw_date = payload.get("payment_date")
            if not raw_date:
                return {"success": False, "message": "El campo payment_date es obligatorio"}
            
            # Tomamos los primeros 10 caracteres (YYYY-MM-DD) por si el serializador incluyó horas
            parsed_date = datetime.fromisoformat(str(raw_date)[:10]).date()

            payment = Payment(
                tenant_id=tenant_id,
                amount=payload.get("amount"),
                payment_date=parsed_date,
                method=(payload.get("method") or "cash").lower(),
                notes=payload.get("notes")
            )
            db.add(payment)

            # Auto-clasificar estado basado en historial de pago
            await _update_payer_status(db, tenant)

            await db.commit()
            await db.refresh(payment)

            # Si 'payment.method' en tu modelo SQLAlchemy es un Enum, usa .value. 
            # Si en la base de datos es un String plano, cambia payment.method.value por simplemente payment.method
            method_value = payment.method.value if hasattr(payment.method, "value") else payment.method

            return {
                "success": True,
                "data": {
                    "id": payment.id,
                    "tenant_id": payment.tenant_id,
                    "amount": payment.amount,
                    "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
                    "method": method_value
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": f"Error interno en el handler: {str(e)}"}


@message_pattern("landlord.payment.get_all")
async def handle_get_all_payments(payload):
    async with AsyncSession(engine) as db:
        try:
            tenant_id = payload.get("tenant_id")
            query = select(Payment)
            if tenant_id:
                query = query.where(Payment.tenant_id == int(tenant_id))

            query = query.order_by(Payment.payment_date.desc())

            result = await db.execute(query)
            payments = result.scalars().all()

            data = [{
                "id": p.id,
                "tenant_id": p.tenant_id,
                "amount": p.amount,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "method": p.method.value if p.method else None,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None
            } for p in payments]

            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("landlord.payment.get_by_id")
async def handle_get_payment_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            payment_id = payload.get("id")
            if not payment_id:
                return {"success": False, "message": "Falta el ID del pago"}

            payment = await db.get(Payment, int(payment_id))
            if not payment:
                return {"success": False, "message": "Pago no encontrado"}

            return {
                "success": True,
                "data": {
                    "id": payment.id,
                    "tenant_id": payment.tenant_id,
                    "amount": payment.amount,
                    "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
                    "method": payment.method.value if payment.method else None,
                    "notes": payment.notes,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


@message_pattern("landlord.payment.update")
async def handle_update_payment(payload):
    async with AsyncSession(engine) as db:
        try:
            payment_id = payload.get("id")
            if not payment_id:
                return {"success": False, "message": "Falta el ID del pago"}

            payment = await db.get(Payment, int(payment_id))
            if not payment:
                return {"success": False, "message": "Pago no encontrado"}

            for field in ["amount", "notes"]:
                if field in payload:
                    setattr(payment, field, payload[field])

            if "payment_date" in payload and payload["payment_date"]:
                payment.payment_date = datetime.strptime(payload["payment_date"], "%Y-%m-%d").date()
            if "method" in payload:
                payment.method = payload["method"]

            db.add(payment)
            await db.commit()
            await db.refresh(payment)

            return {
                "success": True,
                "data": {
                    "id": payment.id,
                    "amount": payment.amount,
                    "payment_date": payment.payment_date.isoformat() if payment.payment_date else None
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("landlord.payment.delete")
async def handle_delete_payment(payload):
    async with AsyncSession(engine) as db:
        try:
            payment_id = payload.get("id")
            if not payment_id:
                return {"success": False, "message": "Falta el ID del pago"}

            payment = await db.get(Payment, int(payment_id))
            if not payment:
                return {"success": False, "message": "Pago no encontrado"}

            await db.delete(payment)
            await db.commit()

            return {"success": True, "message": "Pago eliminado correctamente"}
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


# ===================== CLASSIFICATION HANDLER =====================

@message_pattern("landlord.classification.update")
async def handle_update_classification(payload):
    async with AsyncSession(engine) as db:
        try:
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                return {"success": False, "message": "Falta el ID del inquilino"}

            tenant = await db.get(Tenant, int(tenant_id))
            if not tenant:
                return {"success": False, "message": "Inquilino no encontrado"}

            if "payer_status" in payload:
                ps = payload["payer_status"]
                valid_statuses = [s.value for s in PayerStatus]
                if ps not in valid_statuses:
                    return {"success": False, "message": "Estado de pagador no válido"}
                tenant.payer_status = PayerStatus(ps)

            tenant.updated_at = datetime.utcnow()
            db.add(tenant)
            await db.commit()

            return {
                "success": True,
                "data": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "payer_status": tenant.payer_status.value
                }
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


@message_pattern("landlord.classification.auto")
async def handle_auto_classify(payload):
    async with AsyncSession(engine) as db:
        try:
            tenant_id = payload.get("tenant_id")
            if tenant_id:
                tenant = await db.get(Tenant, int(tenant_id))
                if not tenant:
                    return {"success": False, "message": "Inquilino no encontrado"}
                await _update_payer_status(db, tenant)
                await db.commit()
                return {
                    "success": True,
                    "data": {
                        "id": tenant.id,
                        "name": tenant.name,
                        "payer_status": tenant.payer_status.value
                    }
                }
            else:
                result = await db.execute(select(Tenant))
                tenants = result.scalars().all()
                for tenant in tenants:
                    await _update_payer_status(db, tenant)
                await db.commit()
                return {"success": True, "message": f"Clasificación actualizada para {len(tenants)} inquilinos"}
        except Exception as e:
            await db.rollback()
            return {"success": False, "message": str(e)}


# ===================== HELPERS =====================

async def _update_payer_status(db: AsyncSession, tenant: Tenant):
    """Auto-classify tenant based on payment history: good = paid last 3 months, bad = missed 2+ of last 3"""
    from sqlalchemy import select as sel_query

    now = datetime.utcnow()
    current_year = now.year
    current_month = now.month

    payments_result = await db.execute(
        sel_query(Payment).where(
            Payment.tenant_id == tenant.id
        ).order_by(Payment.payment_date.desc())
    )
    payments = payments_result.scalars().all()

    if not payments:
        tenant.payer_status = PayerStatus.REGULAR
        return

    paid_months = {(p.payment_date.year, p.payment_date.month) for p in payments}

    expected_months = []
    for i in range(3):
        m = current_month - i
        y = current_year
        if m <= 0:
            m += 12
            y -= 1
        expected_months.append((y, m))

    paid_count = sum(1 for em in expected_months if em in paid_months)

    if paid_count >= 3:
        tenant.payer_status = PayerStatus.GOOD
    elif paid_count <= 1:
        tenant.payer_status = PayerStatus.BAD
    else:
        tenant.payer_status = PayerStatus.REGULAR