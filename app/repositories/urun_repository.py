"""
Ürün Repository - Ürün verisi erişim katmanı
"""
from app.models import Urun
from app.repositories.base_repository import BaseRepository


class UrunRepository(BaseRepository):
    """Ürün tablosuna yönelik veri erişim metotları."""

    model = Urun

    @classmethod
    def search_by_ad(cls, keyword):
        """Ürün adına göre arama yapar."""
        if not keyword:
            return []
        return cls.search(Urun.ad.ilike(f"%{keyword}%"))

    @classmethod
    def get_by_kod(cls, kod):
        """Ürün koduna göre tekil kayıt getirir."""
        return Urun.query.filter_by(kod=kod, silinme_tarihi=None).first()

    @classmethod
    def get_aktif(cls):
        """Yalnızca aktif ürünleri döndürür."""
        return cls.filter_by(aktif=True)

    @classmethod
    def get_stoklu(cls):
        """Stok miktarı sıfırdan büyük ürünleri döndürür."""
        return Urun.query.filter(Urun.silinme_tarihi == None, Urun.stok_miktari > 0).all()
