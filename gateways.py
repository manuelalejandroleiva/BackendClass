from fastapi import Depends, FastAPI, Request, Header,Body,APIRouter
from dotenv import load_dotenv
import httpx
from usuarios.connection.database import get_db

from usuarios.DTO.dto import LoginRequest  # Asegúrate de que DTO/model.py esté en el mismo directorio o ajusta la ruta
# from usuarios.connection.database import SessionLocal, engine, Base,get_db
from sqlalchemy.ext.asyncio import AsyncSession
from usuarios.dependencies.dependencies import get_current_user
from typing import Optional
from buisness.schema import BuisnessCreate,LicenciaCreate,BuisnessUpdate
import os
from fastapi import HTTPException



from usuarios.schema import *
load_dotenv()

# 🔐 Router protegido
protected_router = APIRouter(
    dependencies=[Depends(get_current_user)]
)


app = FastAPI(title="API Gateway", description="API Gateway para usuarios y negocios", version="1.0.0")


USER_SERVICE_URL = os.getenv("SERVICE_USER_PORT_DATA")
USER_SERVICE_PATH = os.getenv("SERVICE_PAYMENT_PORT_DATA")


@app.post("/login")
async def login( 
    login_data: LoginRequest = Body(...),
   
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/login",
            json=login_data.dict()
        )
    return response.json()




def get_token(authorization: Optional[str] = Header(None, include_in_schema=False)):
    return authorization

@protected_router.get("/users/{user_id}")
async def get_user(
    user_id: int,
   authorization: Optional[str] = Depends(get_token)
):  
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)
    return response.json()


@app.post("/users/create")
async def create_user(
    data: UserCreate = Body(...),
   
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:

       response = await client.post(f"{USER_SERVICE_URL}/users/create/", json=data.dict(), headers=headers)

    return response.json()




@protected_router.delete('/users/{user_id}', response_model=UserSchema)
async def delete_user(
    user_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)

        # Si el servicio retorna un error
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al eliminar usuario"))

        return response.json()
    

@protected_router.put('/users/{user_id}')
async def updateUsers(
    user: UserSchema,
    user_id: int,
    authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response= await client.put(f"{USER_SERVICE_URL}/users/{user_id}", json=user.dict() ,headers=headers)
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al actualizar el  usuario"))
        return response.json()
    




@protected_router.post("/buisness/create")
async def create_buisness(
    data: BuisnessCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:

       response = await client.post(f"{USER_SERVICE_PATH}/buisness_create", json=data.dict(), headers=headers)

    return response.json()



@protected_router.post("/licence/create")
async def create_licence(
    licencia: LicenciaCreate = Body(...),
    authorization: Optional[str] = Depends(get_token)    
):

    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
       response = await client.post(f"{USER_SERVICE_PATH}/licence_create", json=licencia.dict(), headers=headers)

    return response.json()

@protected_router.get("/licence_get")
async def get_all_licences(skip: int = 0, limit: int = 10, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
       response = await client.get(f"{USER_SERVICE_PATH}/licence_get?skip={skip}&limit={limit}", headers=headers)

    return response.json()



protected_router.get("/buisness_get")
async def get_all_buisnesses(skip: int = 0, limit: int = 10, authorization: Optional[str] = Depends(get_token)):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
       response = await client.get(f"{USER_SERVICE_PATH}/buisness_get?skip={skip}&limit={limit}", headers=headers)      
    return response.json()  


@protected_router.patch("/buisness/{buisness_id}")
async def update_buisness(
    buisness_id: int,
    buisness_update: BuisnessUpdate,
    authorization: Optional[str] = Depends(get_token)
):
    """
    Actualiza un negocio. Solo se modificarán los campos enviados en el payload.
    """
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{USER_SERVICE_PATH}/buisness/{buisness_id}",
            json=buisness_update.dict(),
            headers=headers
        )
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al actualizar el negocio"))
        return response.json()



@protected_router.get("/buisness_get/{buisness_id}")
async def get_buisness_by_id(
    buisness_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_PATH}/buisness_get/{buisness_id}", headers=headers)
    return response.json()     



@protected_router.delete("/buisness/{buisness_id}", response_model=None)
async def delete_buisness(
    buisness_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_PATH}/buisness/{buisness_id}", headers=headers)
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al eliminar el negocio"))
        return response.json()
    
@protected_router.delete("/licence/{licence_id}", response_model=None)
async def delete_licence(
    licence_id: int,
    authorization: Optional[str] = Depends(get_token)
):
    headers = {"Authorization": authorization} if authorization else {}
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_PATH}/licence/{licence_id}", headers=headers)
        if response.status_code >= 400:
            error_data = response.json()
            raise HTTPException(status_code=response.status_code, detail=error_data.get("detail", "Error al eliminar la licencia"))
        return response.json()


app.include_router(protected_router,prefix="/api")

    
    




