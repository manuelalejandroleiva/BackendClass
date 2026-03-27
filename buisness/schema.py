from pydantic import BaseModel, Field, EmailStr
from typing import Optional



class BuisnessBase(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    capital_money: Optional[int] = Field(None, ge=0)
    categoria: Optional[int] = None
    address: Optional[str] = Field(None, min_length=5)
    phone: Optional[str] = Field(None, min_length=7, max_length=15)
    email: Optional[EmailStr] = None
    user_id:Optional[int]=Field(None,ge=0)
    image_path:Optional[str]=None
    business_type: Optional[str] = Field("general", description="Tipo: restaurant | store | general")
    class Config:
        orm_mode = True


class BuisnessCreate(BuisnessBase):
    name: str
    capital_money: int
    business_type: str = "general"


class BuisnessUpdate(BuisnessBase):
    """Modelo usado solo para actualizaciones (parciales)."""
    pass


class LicenciaCreate(BaseModel):
    
    name:str= Field(..., min_length=7, max_length=15)   # Este sigue siendo obligatorio

    class Config:
        orm_mode = True