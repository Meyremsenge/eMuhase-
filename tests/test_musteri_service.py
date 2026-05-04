"""Tests for MusteriService."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import app.services.musteri_service as musteri_service_module
from app.services.musteri_service import MusteriService


@contextmanager
def _noop_audit(*args, **kwargs):
    """Mock audit context manager."""
    class _Audit:
        def add_change(self, *a, **k):
            pass

    yield _Audit()


class TestMusteriServiceCreate:
    def test_create_fails_when_vergi_no_exists(self, monkeypatch):
        """Test that create fails if vergi_no already exists."""
        monkeypatch.setattr(musteri_service_module, "AuditLogContext", _noop_audit)

        monkeypatch.setattr(
            musteri_service_module.MusteriRepository,
            "get_by_vergi_no",
            staticmethod(lambda vergi_no: SimpleNamespace(id=99)),
        )

        with pytest.raises(ValueError, match="vergi numarası"):
            MusteriService.create({"unvan": "ABC", "vergi_no": "123"})


class TestMusteriServiceUpdate:
    def test_update_fails_when_not_found(self, monkeypatch):
        """Test that update fails if musteri not found."""
        monkeypatch.setattr(musteri_service_module, "AuditLogContext", _noop_audit)
        monkeypatch.setattr(
            musteri_service_module.MusteriRepository,
            "get_by_id",
            staticmethod(lambda _id: None),
        )

        with pytest.raises(ValueError, match="Müşteri bulunamadı"):
            MusteriService.update(10, {"unvan": "Yeni"})

    def test_update_fails_when_vergi_no_belongs_to_another(self, monkeypatch):
        """Test that update fails if new vergi_no belongs to another customer."""
        monkeypatch.setattr(musteri_service_module, "AuditLogContext", _noop_audit)

        existing = SimpleNamespace(id=1, vergi_no="111")
        monkeypatch.setattr(
            musteri_service_module.MusteriRepository,
            "get_by_id",
            staticmethod(lambda _id: existing),
        )
        monkeypatch.setattr(
            musteri_service_module.MusteriRepository,
            "get_by_vergi_no",
            staticmethod(lambda vergi_no: SimpleNamespace(id=2)),
        )

        with pytest.raises(ValueError, match="vergi numarası"):
            MusteriService.update(1, {"vergi_no": "222"})


class TestMusteriServiceDelete:
    def test_delete_fails_when_not_exists(self, monkeypatch):
        """Test that delete fails if musteri not found."""
        monkeypatch.setattr(musteri_service_module, "AuditLogContext", _noop_audit)
        monkeypatch.setattr(
            musteri_service_module.MusteriRepository,
            "exists",
            staticmethod(lambda _id: False),
        )

        with pytest.raises(ValueError, match="Müşteri bulunamadı"):
            MusteriService.delete(123)


class TestMusteriServiceGet:
    def test_get_all_delegates_to_repository(self, monkeypatch):
        """Test that get_all delegates to repository."""
        expected = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        monkeypatch.setattr(
            musteri_service_module.MusteriRepository,
            "get_all",
            staticmethod(lambda: expected),
        )

        assert MusteriService.get_all() == expected
