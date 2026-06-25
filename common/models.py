from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from common.database import Base


class TipoMesa(Base):
    __tablename__ = "tipo_mesa"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    address = Column(String, index=True)
    phone = Column(String, index=True)
    password = Column(String, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    image = Column(String, index=True)


class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    buisnesses = relationship("Buisness", back_populates="category")


class Buisness(Base):
    __tablename__ = "buisness"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capital_money = Column(Integer, index=True)
    categoria = Column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="buisnesses")
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)
    user_id = Column(Integer, index=True)
    address = Column(String, index=True)
    image_path = Column(String, nullable=True)

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


class Tables(Base):
    __tablename__ = "Tables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer, index=True)
    buisness_id = Column(Integer, ForeignKey("buisness.id"))
    buisness = relationship("Buisness")
    status = Column(String, index=True, nullable=True)
    location = Column(String, index=True, nullable=True)
    tipo_id = Column(Integer, ForeignKey("tipo_mesa.id"), nullable=True)
    tipo = relationship("TipoMesa")
    precio_wash = Column(Integer, nullable=True)
    cantidad_lavados = Column(Integer, default=0)


class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(Integer, index=True)
    category = Column(String, index=True, nullable=True)
    available = Column(Boolean, default=True)
    business_id = Column(Integer, ForeignKey("buisness.id"), index=True)
    image = Column(String, nullable=True)


class Order(Base):
    __tablename__ = "restaurant_orders"
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("Tables.id"), index=True)
    business_id = Column(Integer, ForeignKey("buisness.id"), index=True)
    status = Column(String, default="pending", index=True)
    total = Column(Integer, default=0)
    notes = Column(String, nullable=True)
    created_at = Column(String, index=True)
    updated_at = Column(String, nullable=True)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)


class OrderItem(Base):
    __tablename__ = "restaurant_order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("restaurant_orders.id"), index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), index=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer)
    subtotal = Column(Integer)
    notes = Column(String, nullable=True)


class LegacyOrder(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, index=True)
    business_id = Column(Integer, index=True)
    status = Column(String, default="pending", index=True)
    notes = Column(String, nullable=True)
    total = Column(Integer, default=0)
    created_at = Column(String, index=True)
    updated_at = Column(String, index=True)


class LegacyOrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True)
    product_id = Column(Integer, index=True)
    product_name = Column(String, index=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    subtotal = Column(Integer, default=0)


class MonthlyClosing(Base):
    __tablename__ = "monthly_closings"
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("buisness.id"), index=True)
    month = Column(Integer, index=True)
    year = Column(Integer, index=True)
    total_sales = Column(Integer, default=0)
    total_cash = Column(Integer, default=0)
    total_card = Column(Integer, default=0)
    total_transactions = Column(Integer, default=0)
    total_discounts = Column(Integer, default=0)
    closed_at = Column(String)
    status = Column(String, default="open", index=True)
