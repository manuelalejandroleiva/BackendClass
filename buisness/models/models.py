from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, declarative_base
from common.database import Base






# Licencia sanitaria
# Licencia de arrendamiento





class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    buisnesses = relationship("Buisness", back_populates="category")  # ✅ plural y coincide con Buisness

        


class Buisness(Base):
    __tablename__ = "buisness"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capital_money = Column(Integer, index=True)
    categoria = Column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="buisnesses")  # ✅ coincide con Category.buisnesses
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)
    user_id = Column(Integer, index=True) # referencia logica hacia los usuarios
    address = Column(String, index=True)
    image_path = Column(String, nullable=True)
    business_type = Column(String, default="general", index=True)  # restaurant | store | general









class Tables(Base):
    __tablename__ = "Tables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 
    capacity=Column(Integer,index=True)
    buisness_id = Column(Integer, ForeignKey("buisness.id"))  # clave foránea
    buisness = relationship("Buisness")
    status=Column(String,index=True,nullable=True)  # libre, ocupada, reservada
    location=Column(String,index=True,nullable=True)  # interior, exterior, barra   
    
        

class Product(Base):
    __tablename__ = "Product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 
    price=Column(Integer,index=True)
    sold=Column(Integer,index=True)
    stock=Column(Integer,index=True)
    buisness_id = Column(Integer, index=True)  # clave foránea


class Sale(Base):
    __tablename__ = "sale"
    id = Column(Integer, primary_key=True, index=True)
    total = Column(Integer, default=0)
    payment_method = Column(String, default="cash")
    business_id = Column(Integer, index=True)
    cashier_id = Column(Integer, nullable=True)
    discount = Column(Integer, default=0)
    created_at = Column(String, index=True)  # Se guardará como string ISO
    