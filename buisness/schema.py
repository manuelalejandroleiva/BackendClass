from pydantic import BaseModel, Field, EmailStr
from typing import Optional



class BuisnessBase(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    capital_money: Optional[int] = Field(None, ge=0)
    licencia_id: Optional[int] = None
    permisos: Optional[str] = None
    categoria: Optional[int] = None
    address: Optional[str] = Field(None, min_length=5)
    phone: Optional[str] = Field(None, min_length=7, max_length=15)
    email: Optional[EmailStr] = None

    class Config:
        orm_mode = True


class BuisnessCreate(BuisnessBase):
    # si tienes campos obligatorios para creación, defínelos aquí
    name: str
    capital_money: int


class BuisnessUpdate(BuisnessBase):
    """Modelo usado solo para actualizaciones (parciales)."""
    pass


class LicenciaCreate(BaseModel):
    
    name:str= Field(..., min_length=7, max_length=15)   # Este sigue siendo obligatorio

    class Config:
        orm_mode = True