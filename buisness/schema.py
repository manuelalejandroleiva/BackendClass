from pydantic import BaseModel
from typing import Optional



class BuisnessBase(BaseModel):
    
    name: str 
    capital_money:int
    licencia_id : int  # clave foránea
    
    permisos:str
    categoria:int
    address:str
    phone:str
    email:str    
                

class BuisnessCreate(BuisnessBase):
    pass


class LicenciaCreate(BaseModel):
    
    name: str  # Este sigue siendo obligatorio

    class Config:
        orm_mode = True