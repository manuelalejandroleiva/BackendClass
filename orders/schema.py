from pydantic import BaseModel, Field
from typing import Optional, List

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class OrderCreate(BaseModel):
    business_id: int
    table_id: int
    items: List[OrderItemCreate]
    notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

class OrderResponse(BaseModel):
    id: int
    business_id: int
    table_id: int
    status: str
    notes: Optional[str]
    total: float
    items: List[OrderItemResponse]
    created_at: str
    updated_at: str

class TableCreate(BaseModel):
    name: str
    capacity: int = 4
    business_id: int
    location: Optional[str] = None

class TableResponse(BaseModel):
    id: int
    name: str
    capacity: int
    status: Optional[str]
    location: Optional[str]

class StatusUpdate(BaseModel):
    status: str = Field(..., description="pending | in_progress | completed | cancelled")
