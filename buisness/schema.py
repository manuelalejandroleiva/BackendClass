from pydantic import BaseModel
from typing import Optional



class BuisnessBase(BaseModel):
    name: Optional[str] = None
    capital_money: Optional[int] = None
    licencia_id: Optional[int] = None  # clave foránea
    permisos: Optional[str] = None
    categoria: Optional[int] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    class Config:
        orm_mode = True

class BuisnessCreate(BuisnessBase):
    pass


class LicenciaCreate(BaseModel):
    
    name: str  # Este sigue siendo obligatorio

    class Config:
        orm_mode = True