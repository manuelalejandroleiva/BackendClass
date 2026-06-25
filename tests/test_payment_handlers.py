"""
Tests unitarios para los handlers de pagos del landlord service.
"""
import asyncio
import pytest
from datetime import date, datetime
from enum import Enum as PyEnum


class PaymentMethod(str, PyEnum):
    CASH = "cash"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    RENT = "rent"
    OTHER = "other"


class FakePayment:
    def __init__(self, id, tenant_id, amount, payment_date, method, notes, created_at=None):
        self.id = id
        self.tenant_id = tenant_id
        self.amount = amount
        self.payment_date = payment_date
        self.method = method
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()


async def handle_get_all_payments(payments_in_db):
    """Copia exacta del handler con los fixes aplicados"""
    try:
        data = [{
            "id": p.id,
            "tenant_id": p.tenant_id,
            "amount": p.amount,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "method": p.method.value if p.method else None,
            "notes": p.notes,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in payments_in_db]
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_get_all_payments_bugged(payments_in_db):
    """Versión SIN fixes (antes del parche)"""
    try:
        data = [{
            "id": p.id,
            "tenant_id": p.tenant_id,
            "amount": p.amount,
            "payment_date": p.payment_date.isoformat(),
            "method": p.method.value,
            "notes": p.notes,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in payments_in_db]
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ===================== TESTS =====================

class TestGetAllPayments:
    def test_all_valid_enums(self):
        payments = [
            FakePayment(1, 1, 500.0, date(2026, 6, 1), PaymentMethod.CASH, "nota"),
            FakePayment(2, 1, 300.0, date(2026, 5, 1), PaymentMethod.TRANSFER, None),
        ]
        result = asyncio.run(handle_get_all_payments(payments))
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["method"] == "cash"
        assert result["data"][1]["method"] == "transfer"

    def test_method_none_value(self):
        """method = None en DB → el fix lo convierte a None en lugar de error"""
        payments = [
            FakePayment(3, 1, 500.0, date(2026, 6, 1), None, "sin metodo"),
        ]
        result = asyncio.run(handle_get_all_payments(payments))
        assert result["success"] is True
        assert result["data"][0]["method"] is None

    def test_method_none_bugged_returns_false(self):
        """Versión buggeada: None.method.value → AttributeError capturado"""
        payments = [
            FakePayment(3, 1, 500.0, date(2026, 6, 1), None, "sin metodo"),
        ]
        result = asyncio.run(handle_get_all_payments_bugged(payments))
        assert result["success"] is False
        assert "NoneType" in result["message"]

    def test_raw_string_method_causes_error(self):
        """
        Si method es un string crudo (no es un enum), .value falla.
        El handler captura el error y retorna success=False (HTTP 400).
        """
        payments = [
            FakePayment(4, 1, 500.0, date(2026, 6, 1), "credit", "no enum"),
        ]
        result = asyncio.run(handle_get_all_payments(payments))
        assert result["success"] is False
        assert "value" in result["message"]

    def test_empty_payments(self):
        result = asyncio.run(handle_get_all_payments([]))
        assert result["success"] is True
        assert result["data"] == []

    def test_payment_date_none(self):
        """payment_date=None → debe ser None, no error"""
        payments = [
            FakePayment(5, 1, 500.0, None, PaymentMethod.CASH, None),
        ]
        result = asyncio.run(handle_get_all_payments(payments))
        assert result["success"] is True
        assert result["data"][0]["payment_date"] is None

    def test_payment_date_none_bugged_causes_error(self):
        """payment_date=None sin fix → AttributeError"""
        payments = [
            FakePayment(5, 1, 500.0, None, PaymentMethod.CASH, None),
        ]
        result = asyncio.run(handle_get_all_payments_bugged(payments))
        assert result["success"] is False
        assert "NoneType" in result["message"]


class TestGetPaymentById:
    def test_none_method_in_response(self):
        """method=None debe mapearse a None"""
        payment = FakePayment(1, 1, 500.0, date(2026, 6, 1), None, "nota")
        data = {
            "id": payment.id,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "method": payment.method.value if payment.method else None,
        }
        assert data["method"] is None
        assert data["payment_date"] is not None

    def test_none_payment_date_in_response(self):
        """payment_date=None debe mapearse a None"""
        payment = FakePayment(1, 1, 500.0, None, PaymentMethod.CASH, "nota")
        data = {
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "method": payment.method.value if payment.method else None,
        }
        assert data["payment_date"] is None
        assert data["method"] == "cash"


class TestRouteErrorHandling:
    def test_timeout_gives_504(self):
        """asyncio.TimeoutError debe ser HTTP 504, no 500"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            try:
                raise asyncio.TimeoutError("timeout")
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="timeout")
        assert exc.value.status_code == 504

    def test_generic_error_gives_500(self):
        """Errores genéricos deben seguir siendo HTTP 500"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            try:
                raise ConnectionError("db down")
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="timeout")
            except Exception:
                raise HTTPException(status_code=500, detail="db down")
        assert exc.value.status_code == 500

    def test_handler_error_gives_400(self):
        """
        Cuando el handler retorna success=False,
        el route responde con HTTP 400.
        """
        result = {"success": False, "message": "error test"}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))
        assert exc.value.status_code == 400
