from typing import Optional, Dict, Any
from app.models import db, Musteri
from app.repositories.musteri_repository import MusteriRepository


class MusteriService:
    @staticmethod
    def get_all():
        return MusteriRepository.get_all()

    @staticmethod
    def get_by_id(musteri_id: int) -> Optional[Musteri]:
        return MusteriRepository.get_by_id(musteri_id)

    @staticmethod
    def search(keyword: str):
        return MusteriRepository.search_full(keyword)

    @staticmethod
    def create(data: Dict[str, Any]) -> Musteri:
        # duplicate checks
        if data.get('vergi_no') and MusteriRepository.get_by_vergi_no(data.get('vergi_no')):
            raise ValueError('vergi numarası zaten kayıtlı')
        if data.get('email') and MusteriRepository.get_by_email(data.get('email')):
            raise ValueError('Email zaten kayıtlı')

        musteri = Musteri(**data)
        db.session.add(musteri)
        db.session.commit()
        return musteri

    @staticmethod
    def update(musteri_or_id, changes: Dict[str, Any]) -> Musteri:
        """Müşteri günceller. İlk argüman ID veya Musteri instance olabilir."""
        if isinstance(musteri_or_id, Musteri):
            musteri = musteri_or_id
        else:
            musteri = MusteriRepository.get_by_id(musteri_or_id)
        if musteri is None:
            raise ValueError('Müşteri bulunamadı')

        # duplicate checks
        if changes.get('vergi_no'):
            existing = MusteriRepository.get_by_vergi_no(changes['vergi_no'])
            if existing and existing.id != musteri.id:
                raise ValueError('Vergi numarası başka bir müşteriye ait')
        if changes.get('email'):
            existing = MusteriRepository.get_by_email(changes['email'])
            if existing and existing.id != musteri.id:
                raise ValueError('Email başka bir kayıtta mevcut')

        for k, v in changes.items():
            setattr(musteri, k, v)
        db.session.add(musteri)
        db.session.commit()
        return musteri

    @staticmethod
    def delete(musteri_or_id) -> bool:
        """Müşteri soft-delete eder. İlk argüman ID veya Musteri instance olabilir."""
        if isinstance(musteri_or_id, Musteri):
            musteri = musteri_or_id
        else:
            musteri = MusteriRepository.get_by_id(musteri_or_id)
        if musteri is None:
            raise ValueError('Müşteri bulunamadı')
        musteri.soft_delete()
        db.session.add(musteri)
        db.session.commit()
        return True

    @staticmethod
    def get_aktif():
        return MusteriRepository.get_aktif()

    @staticmethod
    def count():
        return MusteriRepository.count()
