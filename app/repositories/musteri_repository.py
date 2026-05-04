"""
Müşteri repository - müşteri/tedarikçi veri erişimi
"""
from sqlalchemy import or_
from app.models import Musteri
from app.repositories.base_repository import BaseRepository


class MusteriRepository(BaseRepository):
    model = Musteri

    @classmethod
    def search_by_unvan(cls, keyword: str):
        if not keyword:
            return []
        return cls.search(Musteri.unvan.ilike(f"%{keyword}%"))

    @classmethod
    def get_by_vergi_no(cls, vergi_no: str):
        return Musteri.query.filter_by(vergi_no=vergi_no, silinme_tarihi=None).first()

    @classmethod
    def get_by_email(cls, email: str):
        return Musteri.query.filter_by(email=email, silinme_tarihi=None).first()

    @classmethod
    def get_by_tip(cls, tip: str):
        return cls.filter_by(tip=tip)

    @classmethod
    def get_aktif(cls):
        return cls.filter_by(aktif=True)

    @classmethod
    def search_full(cls, keyword: str):
        if not keyword:
            return []
        pattern = f"%{keyword}%"
        return Musteri.query.filter(
            Musteri.silinme_tarihi == None,
            or_(
                Musteri.unvan.ilike(pattern),
                Musteri.vergi_no.ilike(pattern),
                Musteri.email.ilike(pattern),
                Musteri.telefon.ilike(pattern),
            )
        ).all()
