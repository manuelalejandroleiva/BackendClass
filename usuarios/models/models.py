from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from usuarios.connection.database import Base







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
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    is_verified = Column(Integer, default=0)  # 0 for not verified, 1 for verified
    image=Column(String, index=True)