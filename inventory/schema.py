from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class SaleCreate(BaseModel):
    business_id: int
    items: List[SaleItemCreate]
    payment_method: str = "cash"
    cashier_id: Optional[int] = None
    discount: int = 0

class SaleItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

class SaleResponse(BaseModel):
    id: int
    total: float
    payment_method: str
    cashier_id: Optional[int]
    discount: int
    items: List[SaleItemResponse]
    created_at: str

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    stock: Optional[int] = None
    price: Optional[int] = None

class ReportPeriodResponse(BaseModel):
    daily: dict
    weekly: dict
    monthly: dict

class TopProductResponse(BaseModel):
    product_id: int
    product_name: str
    total_sold: int
    revenue: float

class SummaryResponse(BaseModel):
    total: float
    total_cash: float
    total_card: float
    total_transactions: int
