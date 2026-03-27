from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from common.database import Base

class Product(Base):
    __tablename__ = "Product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 
    price = Column(Integer, index=True)
    sold = Column(Integer, index=True, default=0)
    stock = Column(Integer, index=True, default=0)
    buisness_id = Column(Integer, index=True)

class Sale(Base):
    __tablename__ = "sale"
    id = Column(Integer, primary_key=True, index=True)
    total = Column(Integer, default=0)
    payment_method = Column(String, default="cash")
    business_id = Column(Integer, index=True)
    cashier_id = Column(Integer, nullable=True)
    discount = Column(Integer, default=0)
    created_at = Column(String, index=True)
