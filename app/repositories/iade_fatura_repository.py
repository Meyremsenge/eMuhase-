"""
İade Fatura Repository - İade faturası verisi erişim katmanı
"""
from decimal import Decimal
from types import SimpleNamespace
from sqlalchemy.orm import joinedload
from app.models import IadeFatura, IadeFaturaKalem, Urun, db
from app.repositories.base_repository import BaseRepository


class IadeFaturaRepository(BaseRepository):
    """İade faturası tablosuna yönelik veri erişim metotları."""

    model = IadeFatura

    @classmethod
    def get_by_id(cls, id_):
        return cls.model.query.filter_by(id=id_, silinme_tarihi=None).first()

    @classmethod
    def get_by_fatura_no(cls, fatura_no):
        """Fatura numarasına göre tekil kayıt getirir."""
        return cls.model.query.filter_by(fatura_no=fatura_no, silinme_tarihi=None).first()

    @classmethod
    def get_by_firma(cls, firma_id):
        """Firmaya ait iade faturalarını döndürür."""
        return cls.filter_by(firma_id=firma_id)

    @classmethod
    def get_by_iade_turu(cls, iade_turu):
        """İade türüne göre filtreler (alis_iade, satis_iade)."""
        return cls.filter_by(iade_turu=iade_turu)

    @classmethod
    def create_with_kalemler(cls, fatura_data, kalemler_data):
        """Fatura ve kalemlerini birlikte oluşturur."""
        try:
            fatura = IadeFatura(**fatura_data)
            db.session.add(fatura)
            db.session.flush()

            for kalem_data in kalemler_data:
                kalem_data['fatura_id'] = fatura.id
                kalem = IadeFaturaKalem(**kalem_data)
                db.session.add(kalem)
                urun = Urun.query.filter_by(id=kalem.urun_id, silinme_tarihi=None).first() if kalem.urun_id else None
                if urun is not None:
                    if fatura.iade_turu == 'satis_iade':
                        urun.stok_miktari = (urun.stok_miktari or Decimal('0')) + Decimal(str(kalem.miktar))
                    else:
                        urun.stok_miktari = (urun.stok_miktari or Decimal('0')) - Decimal(str(kalem.miktar))

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
                if fatura.iade_turu == 'satis_iade':
                    urun.stok_miktari = (urun.stok_miktari or Decimal('0')) - Decimal(str(kalem.miktar))
                else:
                    urun.stok_miktari = (urun.stok_miktari or Decimal('0')) + Decimal(str(kalem.miktar))
        from datetime import datetime, timezone

        fatura.silinme_tarihi = fatura.silinme_tarihi or datetime.now(timezone.utc)
        db.session.add(fatura)
        db.session.commit()
        return fatura

    @classmethod
    def paginate_with_kalemler(cls, page=1, per_page=20):
        q = cls.model.query.filter(cls.model.silinme_tarihi == None).options(joinedload(cls.model.kalemler))
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return SimpleNamespace(total=total, page=page, per_page=per_page, items=items)
