import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
import json

from .schema import BuisnessCreate,LicenciaCreate,BuisnessUpdate  
from .models.models import Buisness, Licencia
from sqlalchemy.future import select
from fastapi import HTTPException
from .connection.database import engine
from common.rabbitmq import message_pattern


@message_pattern("buisness.create")
async def handle_create_buisness(payload):
    """
    Handler RPC seguro para crear un negocio.
    Siempre devuelve un dict con 'success' y 'message/data'.
    """
    import logging
    logging.info("handle_create_buisness start")

    # Asegurarse que payload sea dict
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return {"success": False, "message": "Payload no es un JSON válido."}

    async with AsyncSession(engine) as db:
        try:
            # Validación Pydantic
            buisness_data = BuisnessCreate(**payload)
            buisness_dict = buisness_data.dict(exclude_unset=True, exclude={"id"})

            # Verificar email duplicado
            existing_email = await db.scalar(
                select(Buisness.id).where(Buisness.email == buisness_data.email)
            )
            if existing_email:
                return {"success": False, "message": "Ya existe un usuario con ese correo."}

            # Crear instancia ORM
            new_buisness = Buisness(**buisness_dict)
            db.add(new_buisness)

            # Commit y refresh con timeout interno opcional
            try:
                await asyncio.wait_for(db.commit(), timeout=10)  # ajusta timeout según tu DB
            except asyncio.TimeoutError:
                await db.rollback()
                return {"success": False, "message": "Timeout en commit de DB"}

            await db.refresh(new_buisness)

            # Serializar respuesta
            response = {k: v for k, v in new_buisness.__dict__.items() if k != "_sa_instance_state"}
            logging.info("handle_create_buisness end")
            return {"success": True, "data": response}

        except Exception as e:
            await db.rollback()
            logging.exception("Error en handle_create_buisness")
            return {"success": False, "message": str(e)}




async def get_all_buisness(session: AsyncSession, page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    result = await session.execute(select(Buisness).offset(offset).limit(page_size))
    buisness = result.scalars().all()

    # Contamos total de registros para poder enviar info de paginación
    total_result = await session.execute(select(Buisness))
    total = len(total_result.scalars().all())

    return buisness, total


@message_pattern("buisness.get_all")
async def handle_get_all(payload):
    page = payload.get("page", 1)
    page_size = payload.get("page_size", 10)
    async with AsyncSession(engine) as session:
        users, total = await get_all_buisness(session, page, page_size)

        data = [
            {k: v for k, v in u.__dict__.items() if k not in ("_sa_instance_state") }
            for u in users
        ]

        response = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "data": data
        }

       
        return response
    

@message_pattern("buisness.get_by_id")
async def handle_get_by_id(payload):
    async with AsyncSession(engine) as db:
        try:
            buisness_id = payload.get("id")
            if buisness_id is None:
                return {"success": False, "message": "Falta el ID en el payload."}

            buisness = await db.get(Buisness, int(buisness_id))
            if not buisness:
                return {"success": False, "message": "Usuario no encontrado."}

            user_data = {
                k: v for k, v in buisness.__dict__.items()
                if k not in ("_sa_instance_state")
            }

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