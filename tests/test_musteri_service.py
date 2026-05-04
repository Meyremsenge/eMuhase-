"""
Müşteri Servisi birim testleri.
İş kurallarını (validasyon, uniqueness) test eder.
"""
import pytest
from app.services.musteri_service import MusteriService
from app.repositories.musteri_repository import MusteriRepository


class TestMusteriService:
    """MusteriService iş kuralı testleri."""

    def test_create_success(self, app):
        musteri = MusteriService.create({
            'unvan': 'Servis Test',
            'vergi_no': '1234567890',
            'tip': 'musteri'
        })
        assert musteri.id is not None
        assert musteri.unvan == 'Servis Test'

    def test_create_duplicate_vergi_no(self, app):
        MusteriService.create({'unvan': 'İlk', 'vergi_no': '1111111111'})
        with pytest.raises(ValueError, match='vergi numarası zaten kayıtlı'):
            MusteriService.create({'unvan': 'İkinci', 'vergi_no': '1111111111'})

    def test_update_success(self, app):
        musteri = MusteriService.create({'unvan': 'Eski', 'vergi_no': '2222222222'})
        updated = MusteriService.update(musteri.id, {'unvan': 'Yeni'})
        assert updated.unvan == 'Yeni'

    def test_update_not_found(self, app):
        with pytest.raises(ValueError, match='bulunamadı'):
            MusteriService.update(9999, {'unvan': 'Yok'})

    def test_update_duplicate_vergi_no(self, app):
        MusteriService.create({'unvan': 'A', 'vergi_no': '3333333333'})
        m2 = MusteriService.create({'unvan': 'B', 'vergi_no': '4444444444'})
        with pytest.raises(ValueError, match='başka bir müşteriye ait'):
            MusteriService.update(m2.id, {'vergi_no': '3333333333'})

    def test_delete_success(self, app):
        musteri = MusteriService.create({'unvan': 'Sil', 'vergi_no': '5555555555'})
        result = MusteriService.delete(musteri.id)
        assert result is True

    def test_delete_not_found(self, app):
        with pytest.raises(ValueError, match='bulunamadı'):
            MusteriService.delete(9999)

    def test_get_aktif(self, app):
        MusteriService.create({'unvan': 'Aktif', 'vergi_no': '6666666666', 'aktif': True})
        result = MusteriService.get_aktif()
        assert len(result) >= 1

    def test_count(self, app):
        assert MusteriService.count() == 0
        MusteriService.create({'unvan': 'Count', 'vergi_no': '7777777777'})
        assert MusteriService.count() == 1
