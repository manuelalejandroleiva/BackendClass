import asyncio
import uvicorn
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from .connection.database import get_db, engine, Base
from .schema import BuisnessCreate,LicenciaCreate
from .service import create_buisness_service,create_licencia_service,get_licencias_service,get_buisnesses_service,get_buisness_by_id_service,update_buisness_service,delete_buisness_service,delete_licencia_service
from typing import Dict     

from fastapi import Depends, HTTPException

app = FastAPI(
    title="My Buisness App",   # 👈 Aquí cambias el nombre
    description="API para gestionar negocios, licencias y usuarios",
    version="1.0.0"
)
app.on_event("startup")
async def startup():
    # Crear las tablas en la base de datos al iniciar la aplicación
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 🔹 Arrancar el consumer en segundo plano
   

@app.post("/buisness_create")
async def create_buisness(buisness: BuisnessCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_buisness_service(db, buisness)
    except HTTPException as http_exc:
        raise http_exc  # ✅ Correct way to pass along the error
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")




@app.post("/licence_create")
async def create_licence(licencia: LicenciaCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_licencia_service(db, licencia)
    except HTTPException as http_exc:
        raise http_exc  # ✅ Correct way to pass along the error
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")
    


@app.get("/licence_get")
async def get_all_licences(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    try:
        return await get_licencias_service(db, skip, limit)
    except HTTPException as http_exc:
        raise http_exc  # ✅ Correct way to pass along the error
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")
    

@app.get("/buisness_get")
async def get_all_buisnesses(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    try:
        return await get_buisnesses_service(db, skip, limit)
    except HTTPException as http_exc:
        raise http_exc  # ✅ Correct way to pass along the error
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")
    


@app.put("/buisness/{buisness_id}", response_model=None)
async def update_buisness(
    buisness_id: int,
    buisness_update: BuisnessCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un negocio. Solo se modificarán los campos enviados en el payload.
    """
    try:
        updated_buisness = await update_buisness_service(db, buisness_id, buisness_update)
        return updated_buisness
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")



@app.get("/buisness_get/{buisness_id}")
async def get_buisness_by_id(buisness_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene un negocio por su ID.
    """
    try:
        buisness = await get_buisness_by_id_service(db, buisness_id)
        return buisness
    except HTTPException as http_exc:
        raise http_exc  # Propaga errores 404 u otros que ya definiste
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")
    


@app.delete("/buisness/{buisness_id}", response_model=None)
async def delete_buisness(buisness_id: int, db: AsyncSession = Depends(get_db)):
    """ Elimina un negocio por su ID.
    """
    try:
        buisness = await delete_buisness_service(db, buisness_id)
        return buisness
    except HTTPException as http_exc:
        raise http_exc  # Propaga errores 404 u otros que ya definiste
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")
    



@app.delete("/licence/{licence_id}", response_model=None)
async def delete_licence(licence_id: int, db: AsyncSession = Depends(get_db)):
    """ Elimina una licencia por su ID.
    """
    try:
        buisness = await delete_licencia_service(db, licence_id)
        return buisness
    except HTTPException as http_exc:
        raise http_exc  # Propaga errores 404 u otros que ya definiste
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")
    