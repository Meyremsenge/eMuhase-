"""
Alış Fatura Repository - Alış faturası verisi erişim katmanı
"""
from decimal import Decimal
from types import SimpleNamespace
from sqlalchemy.orm import joinedload
from app.models import AlisFatura, AlisFaturaKalem, Urun, db
from app.repositories.base_repository import BaseRepository


class AlisFaturaRepository(BaseRepository):
    """Alış faturası tablosuna yönelik veri erişim metotları."""

    model = AlisFatura

    @classmethod
    def get_by_id(cls, id_):
        return cls.model.query.filter_by(id=id_, silinme_tarihi=None).first()

    @classmethod
    def get_by_fatura_no(cls, fatura_no):
        """Fatura numarasına göre tekil kayıt getirir."""
        return cls.model.query.filter_by(fatura_no=fatura_no, silinme_tarihi=None).first()

    @classmethod
    def get_by_tedarikci(cls, tedarikci_id):
        """Tedarikçiye ait faturaları döndürür."""
        return cls.filter_by(tedarikci_id=tedarikci_id)

    @classmethod
    def get_by_durum(cls, durum):
        """Duruma göre filtreler (beklemede, odendi, iptal)."""
        return cls.filter_by(durum=durum)

    @classmethod
    def create_with_kalemler(cls, fatura_data, kalemler_data):
        """Fatura ve kalemlerini birlikte oluşturur."""
        try:
            fatura = AlisFatura(**fatura_data)
            db.session.add(fatura)
            db.session.flush()  # ID atanması için

            for kalem_data in kalemler_data:
                kalem_data['fatura_id'] = fatura.id
                kalem = AlisFaturaKalem(**kalem_data)
                db.session.add(kalem)
                urun = Urun.query.filter_by(id=kalem.urun_id, silinme_tarihi=None).first() if kalem.urun_id else None
                if urun is not None:
                    urun.stok_miktari = (urun.stok_miktari or Decimal('0')) + Decimal(str(kalem.miktar))

            fatura.hesapla()
            db.session.commit()
            return fatura
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def soft_delete(cls, fatura_id):
        fatura = cls.get_by_id(fatura_id)
        if not fatura:
            return None
        for kalem in list(fatura.kalemler):
            urun = Urun.query.filter_by(id=kalem.urun_id, silinme_tarihi=None).first() if kalem.urun_id else None
            if urun is not None:
                urun.stok_miktari = (urun.stok_miktari or Decimal('0')) - Decimal(str(kalem.miktar))
        from datetime import datetime, timezone

        fatura.silinme_tarihi = fatura.silinme_tarihi or datetime.now(timezone.utc)
        db.session.add(fatura)
        db.session.commit()
        return fatura

    @classmethod
    def paginate_with_kalemler(cls, page=1, per_page=20):
        q = cls.model.query.filter(cls.model.silinme_tarihi == None).options(  # noqa: E711
            joinedload(cls.model.kalemler)
        )
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return SimpleNamespace(total=total, page=page, per_page=per_page, items=items)
