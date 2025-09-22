from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, declarative_base
from database.database import Base




# Licencia sanitaria
# Licencia de arrendamiento


class Licencia(Base):
    __tablename__ = "licencia"   # 👈 en minúsculas siempre
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    buisnesses = relationship("Buisness", back_populates="licencia")


class Buisness(Base):
    __tablename__ = "buisness"   # 👈 en minúsculas también
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capital_money = Column(Integer, index=True)

    licencia_id = Column(Integer, ForeignKey("licencia.id"))  # 👈 apunta a tabla en minúscula
    licencia = relationship("Licencia", back_populates="buisnesses")

    permisos = Column(String, index=True)
    categoria = Column(Integer)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)
    address = Column(String, index=True)






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
    stock=Column(Integer,index=True)
    buisness_id = Column(Integer, ForeignKey("buisness.id"))  # clave foránea
    buisness = relationship("Buisness")   