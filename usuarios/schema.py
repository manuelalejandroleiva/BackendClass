from pydantic import BaseModel, EmailStr
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



class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    role_id: Optional[int] = None
    is_active: bool
    is_verified: bool

    class Config:
        orm_mode = True


class UserCreateDTO(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None
    phone: Optional[str] = None
    password: str
    role_id: int
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False


class UserResponseOne(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[UserSchema] = None
