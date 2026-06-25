from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class BuisnessBase(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    capital_money: Optional[int] = Field(None, ge=0)
    categoria: Optional[int] = None
    address: Optional[str] = Field(None, min_length=5)
    phone: Optional[str] = Field(None, min_length=7, max_length=15)
    email: Optional[EmailStr] = None
    user_id: Optional[int] = Field(None, ge=0)
    image_path: Optional[str] = None
    class Config:
        from_attributes = True


class BuisnessCreate(BuisnessBase):
    name: str
    capital_money: int


class BuisnessUpdate(BuisnessBase):
    pass


class LicenciaCreate(BaseModel):
    name: str = Field(..., min_length=7, max_length=15)

    class Config:
        from_attributes = True


class TableCreate(BaseModel):
    name: str
    capacity: int = 4
    buisness_id: int
    status: str = "available"
    location: Optional[str] = None
    tipo_id: Optional[int] = None
    precio_wash: Optional[int] = None


class TableStatusUpdate(BaseModel):
    status: str


class TableUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    location: Optional[str] = None
    tipo_id: Optional[int] = None
    precio_wash: Optional[int] = None
    cantidad_lavados: Optional[int] = None


class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: int
    category: Optional[str] = None
    available: bool = True
    business_id: int
    image: Optional[str] = None


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    category: Optional[str] = None
    available: Optional[bool] = None
    image: Optional[str] = None


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = 1
    notes: Optional[str] = None


class OrderCreate(BaseModel):
    table_id: int
    business_id: int
    items: List[OrderItemCreate]
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str


class OrderUpdate(BaseModel):
    notes: Optional[str] = None


class SaleCreate(BaseModel):
    business_id: int
    total: int
    payment_method: str = "cash"
    cashier_id: Optional[int] = None
    discount: int = 0


class MonthlyClosingCreate(BaseModel):
    business_id: int
    month: int
    year: int


class CreatePaymentIntentRequest(BaseModel):
    order_id: int


class CreatePaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str


class StripeWebhookEvent(BaseModel):
    type: str
    data: dict


class MenuItemPublic(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: int
    category: Optional[str] = None
    image: Optional[str] = None


class MenuCategoryGroup(BaseModel):
    category: str
    items: List[MenuItemPublic]


class PublicMenuResponse(BaseModel):
    business_id: int
    business_name: str
    categories: List[MenuCategoryGroup]
