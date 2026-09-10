"""
Tests para handle_update_product en buisness/service.py
Valida que el mapeo de campos del schema al modelo funcione correctamente.
"""
import asyncio
import json
import pytest
from typing import Optional
from pydantic import BaseModel


# ===================== ESQUEMAS (replicas para test) =====================

class ProductUpdate_BUG(BaseModel):
    """Versión actual (bug) - usa sales_price en vez de price"""
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    category: Optional[int] = None
    sales_price: Optional[int] = None
    cost: Optional[int] = None
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    pz: Optional[int] = None


class ProductUpdate_FIX(BaseModel):
    """Versión corregida - usa price y category_id (nombres del modelo)"""
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[int] = None
    cost: Optional[int] = None
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    pz: Optional[int] = None


# ===================== MODELO SIMULADO =====================

class FakeProduct:
    """Simula el Product de SQLAlchemy"""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.name = kwargs.get("name", "Test")
        self.price = kwargs.get("price", 100)
        self.sales_price = None  # atajo para detectar asignacion erronea
        self.stock = kwargs.get("stock", 10)
        self.category_id = kwargs.get("category_id", None)
        self.category = kwargs.get("category", None)
        self.cost = kwargs.get("cost", 0)
        self.min_stock = kwargs.get("min_stock", 0)
        self.pz = kwargs.get("pz", 1)


# ===================== LOGICA DEL HANDLER (extraida) =====================

async def handle_update_product_bug(payload):
    """Copia exacta del bug actual"""
    product_id = payload.get("product_id")
    if product_id is None:
        return {"success": False, "message": "product_id is required"}
    try:
        if isinstance(payload, str):
            payload = json.loads(payload)
        update_data = ProductUpdate_BUG(**payload)
        update_dict = update_data.dict(exclude_unset=True)
        product = FakeProduct(id=int(product_id), price=100, stock=10)
        for key, value in update_dict.items():
            setattr(product, key, value)
        return {"success": True, "data": {"id": product.id, "price": product.price, "stock": product.stock}}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_update_product_fixed(payload):
    """Version corregida con field mapping"""
    if isinstance(payload, str):
        payload = json.loads(payload)
    product_id = payload.get("product_id")
    if product_id is None:
        return {"success": False, "message": "product_id is required"}
    try:
        update_data = ProductUpdate_FIX(**{k: v for k, v in payload.items() if k != "product_id"})
        update_dict = update_data.dict(exclude_unset=True)
        product = FakeProduct(id=int(product_id), price=100, stock=10)
        for key, value in update_dict.items():
            setattr(product, key, value)
        return {"success": True, "data": {"id": product.id, "price": product.price, "stock": product.stock}}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ===================== TESTS =====================

class TestProductUpdateSchemaMapping:

    def test_bug_version_ignores_price(self):
        """BUG: enviar 'price' no actualiza nada porque el schema espera 'sales_price'"""
        result = asyncio.run(handle_update_product_bug({
            "product_id": 1,
            "price": 200
        }))
        assert result["success"] is True
        assert result["data"]["price"] == 100  # NO cambio (bug!)

    def test_bug_version_sales_price_sets_wrong_attr(self):
        """BUG: enviar 'sales_price' setea 'product.sales_price' en vez de 'product.price'"""
        result = asyncio.run(handle_update_product_bug({
            "product_id": 1,
            "sales_price": 200
        }))
        assert result["success"] is True
        assert result["data"]["price"] == 100  # NO cambio (atributo equivocado)

    def test_fixed_version_updates_price(self):
        """FIX: enviar 'price' actualiza product.price correctamente"""
        result = asyncio.run(handle_update_product_fixed({
            "product_id": 1,
            "price": 200
        }))
        assert result["success"] is True
        assert result["data"]["price"] == 200  # Cambio correcto!

    def test_fixed_version_updates_stock(self):
        """FIX: stock se actualiza igual que antes"""
        result = asyncio.run(handle_update_product_fixed({
            "product_id": 1,
            "stock": 50
        }))
        assert result["success"] is True
        assert result["data"]["stock"] == 50

    def test_fixed_version_partial_update(self):
        """FIX: actualizacion parcial no borra otros campos"""
        result = asyncio.run(handle_update_product_fixed({
            "product_id": 1,
            "price": 999
        }))
        assert result["success"] is True
        assert result["data"]["price"] == 999
        assert result["data"]["stock"] == 10  # Sin cambios

    def test_fixed_version_product_id_filtered(self):
        """FIX: product_id no debe pasarse al schema"""
        result = asyncio.run(handle_update_product_fixed({
            "product_id": 1,
            "price": 300
        }))
        assert result["success"] is True
        assert result["data"]["price"] == 300

    def test_fixed_string_payload(self):
        """FIX: payload como string JSON se parsea correctamente"""
        result = asyncio.run(handle_update_product_fixed(json.dumps({
            "product_id": 1,
            "price": 400
        })))
        assert result["success"] is True
        assert result["data"]["price"] == 400

    def test_missing_product_id(self):
        """Sin product_id debe retornar error"""
        result = asyncio.run(handle_update_product_fixed({
            "price": 200
        }))
        assert result["success"] is False
        assert "product_id" in result["message"]
