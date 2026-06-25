from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


# ===================== PROPERTY =====================

class PropertyBase(BaseModel):
    name: str
    address: str
    monthly_rent: float = 0.0
    description: Optional[str] = None


class PropertyCreate(PropertyBase):
    landlord_id: int


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    monthly_rent: Optional[float] = None
    description: Optional[str] = None


class PropertyResponse(PropertyBase):
    id: int
    landlord_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== TENANT =====================

class TenantBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    property_id: int
    rent_amount: float = 0.0
    deposit: float = 0.0
    start_date: Optional[date] = None
    notes: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    rent_amount: Optional[float] = None
    deposit: Optional[float] = None
    start_date: Optional[date] = None
    status: Optional[str] = None
    payer_status: Optional[str] = None
    notes: Optional[str] = None


class TenantResponse(TenantBase):
    id: int
    status: str
    payer_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== PAYMENT =====================

class PaymentBase(BaseModel):
    tenant_id: int
    amount: float
    payment_date: date
    method: str = "cash"
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    payment_date: Optional[date] = None
    method: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===================== CLASSIFICATION =====================

class ClassificationUpdate(BaseModel):
    payer_status: str