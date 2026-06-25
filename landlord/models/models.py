from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, Date
from sqlalchemy.orm import relationship
from common.database import Base
from datetime import datetime
import enum


class PayerStatus(str, enum.Enum):
    GOOD = "good_payer"
    BAD = "bad_payer"
    REGULAR = "regular"


class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    RENT = "rent"
    OTHER = "other"


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    landlord_id = Column(Integer, nullable=False, index=True)
    monthly_rent = Column(Float, default=0.0)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenants = relationship("Tenant", back_populates="property", cascade="all, delete")


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    rent_amount = Column(Float, nullable=False, default=0.0)
    deposit = Column(Float, default=0.0)
    start_date = Column(Date)
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.ACTIVE, nullable=False)
    payer_status = Column(SQLEnum(PayerStatus), default=PayerStatus.REGULAR, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="tenants")
    payments = relationship("Payment", back_populates="tenant", cascade="all, delete")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.CASH)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="payments")