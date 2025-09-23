from pydantic import BaseModel, Field, EmailStr
from typing import Optional



class BuisnessBase(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    capital_money: Optional[int] = Field(None, ge=0)  # Obligatorio y >= 0
    licencia_id: Optional[int] = None  # clave foránea
    permisos: Optional[str] = None
    categoria: Optional[int] = None
    address: Optional[str] = Field(None, min_length=5)
    phone: Optional[str] = Field(None, min_length=7, max_length=15) 
    email: Optional[EmailStr] = None  # Validación de email
    class Config:
        orm_mode = True

class BuisnessCreate(BuisnessBase):
    pass


class LicenciaCreate(BaseModel):
    
    name:str= Field(..., min_length=7, max_length=15)   # Este sigue siendo obligatorio

    class Config:
        orm_mode = True