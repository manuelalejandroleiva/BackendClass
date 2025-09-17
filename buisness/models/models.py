from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, declarative_base
from database.database import Base




# Licencia sanitaria
# Licencia de arrendamiento

class Licencia(Base):
    __tablename__ = "Licencia"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 
    buisnesses = relationship("Buisness", back_populates="licencia")
    
class Buisness(Base):
    __tablename__ = "Buisness"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 
    capital_money=Column(Integer,index=True)
    licencia_id = Column(Integer, ForeignKey("Licencia.id"))  # clave foránea
    licencia = relationship("Licencia", back_populates="buisnesses")
    permisos=Column(String, index=True)
    categoria=Column(Integer, index=True)
    address=Column(String, index=True)
    phone=Column(String, index=True)
    email=Column(String, unique=True, index=True)       