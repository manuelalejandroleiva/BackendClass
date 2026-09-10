from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from common.database import Base


class TipoProducto(Base):
    __tablename__ = "tipo_producto"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)


class Product(Base):
    __tablename__ = "Product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    sku = Column(String, nullable=True, index=True)
    description = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True, index=True)
    category = relationship("Category")
    tipo_id = Column(Integer, ForeignKey("tipo_producto.id"), nullable=True, index=True)
    tipo = relationship("TipoProducto")
    price = Column(Integer, index=True)
    cost = Column(Integer, nullable=True, default=0)
    sold = Column(Integer, index=True, default=0)
    stock = Column(Integer, index=True, default=0)
    min_stock = Column(Integer, nullable=True, default=0)
    pz = Column(Integer, nullable=True, default=1)
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
