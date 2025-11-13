from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from common.database import Base







class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # e.g., 'admin', 'user'
    users = relationship("User", back_populates="role")  # uno a muchos

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    address= Column(String, index=True)
    phone = Column(String, index=True)
    password = Column(String, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))  # clave foránea
    role = relationship("Role", back_populates="users")  # muchos a uno
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    image=Column(String, index=True)
    