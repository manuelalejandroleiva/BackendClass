from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: str
    address: str
    phone: str
    password: str
    role_id: int  # <- usa este nombre
    is_active: int
    is_verified: int            

class UserCreate(UserBase):
    pass

class   UserSchema(BaseModel):
    id: Optional[int] = None
    name: str  # Este sigue siendo obligatorio
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False
   

    class Config:
        orm_mode = True
