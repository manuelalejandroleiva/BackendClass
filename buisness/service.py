from sqlalchemy.ext.asyncio import AsyncSession
from schema import BuisnessCreate,LicenciaCreate  
from models.models import Buisness, Licencia
from sqlalchemy.future import select
from fastapi import HTTPException
#Crear un nuevo negocio
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
#Crear una nueva licencia
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

#Obtener todas las licencias
async def get_licencias_service(db: AsyncSession,skip: int = 0, limit: int = 10):
    result = await db.execute(select(Licencia).offset(skip).limit(limit))
    licencias = result.scalars().all()
    return licencias

#Obtener todos los negocios
async def get_buisnesses_service(db: AsyncSession,skip: int = 0, limit: int = 10):
    result = await db.execute(select(Buisness).offset(skip).limit(limit))
    buisnesses = result.scalars().all()
    return buisnesses

#Obtener un negocio por su ID
async def get_buisness_by_id_service(db: AsyncSession, buisness_id: int):
    result = await db.execute(select(Buisness).where(Buisness.id == buisness_id))
    buisness = result.scalars().first()
    if not buisness:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return buisness

#Actualizar un negocio

async def update_buisness_service(
    db: AsyncSession, 
    buisness_id: int, 
    buisness_update: BuisnessCreate
):
    # 1️⃣ Buscar el negocio por ID
    result = await db.get(Buisness, buisness_id)
    if not result:
        raise HTTPException(status_code=404, detail="Buisness not found")

    # 2️⃣ Actualizar solo los campos que vienen en el DTO
    update_data = buisness_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(result, key, value)

    # 3️⃣ Guardar cambios en la base de datos
    db.add(result)
    await db.commit()
    await db.refresh(result)

    return result

#Eliminar un negocio
async def delete_buisness_service(db: AsyncSession, buisness_id: int):
    result = await db.execute(select(Buisness).where(Buisness.id == buisness_id))
    buisness = result.scalars().first()
    if not buisness:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    await db.delete(buisness)
    await db.commit()
    return {"detail": "Negocio eliminado correctamente"}        
#Eliminar una licencia
async def delete_licencia_service(db: AsyncSession, licencia_id: int):
    result = await db.execute(select(Licencia).where(Licencia.id == licencia_id))
    licencia = result.scalars().first()
    if not licencia:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    await db.delete(licencia)
    await db.commit()
    return {"detail": "Licencia eliminada correctamente"}    