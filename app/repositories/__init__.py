"""
eMuhasebe Pro - Repository Katmanı
Tüm veri erişim işlemleri bu modül üzerinden yürütülür.
Repository Pattern ile veri erişim kodu iş mantığından ayrılır.
"""
from app.repositories.musteri_repository import MusteriRepository
from app.repositories.urun_repository import UrunRepository
from app.repositories.alis_fatura_repository import AlisFaturaRepository
from app.repositories.satis_fatura_repository import SatisFaturaRepository
from app.repositories.iade_fatura_repository import IadeFaturaRepository

__all__ = [
    'MusteriRepository',
    'UrunRepository',
    'AlisFaturaRepository',
    'SatisFaturaRepository',
    'IadeFaturaRepository',
]
