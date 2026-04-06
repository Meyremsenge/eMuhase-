"""
Müşteri/Tedarikçi Repository - Müşteri verisi erişim katmanı
"""
from app.models import Musteri
from app.repositories.base_repository import BaseRepository


class MusteriRepository(BaseRepository):
    """Müşteri tablosuna yönelik veri erişim metotları."""

    model = Musteri

    @classmethod
    def search_by_unvan(cls, keyword):
        """Ünvana göre arama yapar."""
        return cls.search(Musteri.unvan, keyword)

    @classmethod
    def get_by_vergi_no(cls, vergi_no):
        """Vergi numarasına göre müşteri getirir."""
        return Musteri.query.filter_by(vergi_no=vergi_no).first()

    @classmethod
    def get_aktif(cls):
        """Yalnızca aktif müşterileri döndürür."""
        return cls.filter_by(aktif=True)

    @classmethod
    def get_by_tip(cls, tip):
        """Tipe göre müşterileri filtreler (musteri, tedarikci, her_ikisi)."""
        return cls.filter_by(tip=tip)
