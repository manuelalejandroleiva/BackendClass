from sqlalchemy import Column, Integer, String, ForeignKey
from common.database import Base

class Tables(Base):
    __tablename__ = "Tables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer, index=True)
    buisness_id = Column(Integer, index=True)
    status = Column(String, index=True, nullable=True)
    location = Column(String, index=True, nullable=True)

class Product(Base):
    __tablename__ = "Product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    price = Column(Integer, index=True)
    sold = Column(Integer, index=True, default=0)
    stock = Column(Integer, index=True, default=0)
    buisness_id = Column(Integer, index=True)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, index=True)
    business_id = Column(Integer, index=True)
    status = Column(String, default="pending", index=True)
    notes = Column(String, nullable=True)
    total = Column(Integer, default=0)
    created_at = Column(String, index=True)
    updated_at = Column(String, index=True)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True)
    product_id = Column(Integer, index=True)
    product_name = Column(String, index=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    subtotal = Column(Integer, default=0)
