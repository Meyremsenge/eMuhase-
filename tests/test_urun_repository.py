"""
Ürün Repository birim testleri.
"""
from app.repositories.urun_repository import UrunRepository


class TestUrunRepository:
    """UrunRepository CRUD testleri."""

    def test_create(self, app):
        urun = UrunRepository.create(
            kod='URN001',
            ad='Test Ürün',
            birim='Adet',
            alis_fiyat=100.0,
            satis_fiyat=150.0,
            kdv_orani=20
        )
        assert urun.id is not None
        assert urun.kod == 'URN001'
        assert urun.satis_fiyat == 150.0

    def test_get_by_kod(self, app):
        UrunRepository.create(kod='KOD01', ad='Ürün A')
        found = UrunRepository.get_by_kod('KOD01')
        assert found is not None
        assert found.ad == 'Ürün A'

    def test_search_by_ad(self, app):
        UrunRepository.create(kod='K1', ad='Laptop Bilgisayar')
        UrunRepository.create(kod='K2', ad='Mouse Pad')
        result = UrunRepository.search_by_ad('laptop')
        assert len(result) == 1
        assert result[0].ad == 'Laptop Bilgisayar'

    def test_get_aktif(self, app):
        UrunRepository.create(kod='A1', ad='Aktif Ürün', aktif=True)
        UrunRepository.create(kod='P1', ad='Pasif Ürün', aktif=False)
        result = UrunRepository.get_aktif()
        assert len(result) == 1

    def test_update(self, app):
        urun = UrunRepository.create(kod='UP1', ad='Eski Ad')
        updated = UrunRepository.update(urun.id, ad='Yeni Ad')
        assert updated.ad == 'Yeni Ad'

    def test_delete(self, app):
        urun = UrunRepository.create(kod='DEL1', ad='Silinecek')
        assert UrunRepository.delete(urun.id) is True
        deleted = UrunRepository.get_by_id(urun.id)
        assert deleted is not None
        assert deleted.silinme_tarihi is not None

    def test_count(self, app):
        assert UrunRepository.count() == 0
        UrunRepository.create(kod='CNT1', ad='Sayım')
        assert UrunRepository.count() == 1
