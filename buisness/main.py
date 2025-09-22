import uvicorn
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from connection.database import get_db, engine, Base
from schema import BuisnessCreate,LicenciaCreate
from service import create_buisness_service,create_licencia_service,get_licencias_service
from typing import Dict     

from fastapi import Depends, HTTPException

app = FastAPI()
app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
async def get_all_buisness(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    try:
        return await get_licencias_service(db, skip, limit)
    except HTTPException as http_exc:
        raise http_exc  # ✅ Correct way to pass along the error
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(exc)}")