from sqlalchemy.ext.asyncio import AsyncSession
from schema import BuisnessCreate,LicenciaCreate  
from models.models import Buisness, Licencia
from sqlalchemy.future import select
from fastapi import HTTPException

async def create_buisness_service(db: AsyncSession, buisness: BuisnessCreate):
    existing_email_name = await db.scalar(select(Buisness.id).where
                                     ((Buisness.email == buisness.email) or (Buisness.name == buisness.name)))
    if existing_email_name:
        raise  HTTPException(
            status_code=400,
            detail="Ya existe un negocio registrado con ese correo electrónico o con ese nombre ."
        )

    # 🧱 Crear el nuevo negocio
    new_buisness = Buisness(**buisness.dict())
    db.add(new_buisness)
    await db.commit()
    await db.refresh(new_buisness)
    return new_buisness

async def create_licencia_service(db: AsyncSession, licencia: LicenciaCreate):
    existing_licencia = await db.scalar(select(Licencia.id).where
                                     ((Licencia.name == licencia.name) ))
    if existing_licencia:
        raise  HTTPException(
            status_code=400,
            detail="Ya existe una licencia con ese nombre."
        )
    
    new_licencia = Licencia(**licencia.dict())
    db.add(new_licencia)
    await db.commit()
    await db.refresh(new_licencia)
    return new_licencia