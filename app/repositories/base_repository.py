"""
Temel Repository sınıfı - Tüm repository'ler bu sınıftan türer.
CRUD, filtreleme, listeleme ve arama gibi ortak veri erişim metotlarını sağlar.
"""
from datetime import datetime
from app.models import db


class BaseRepository:
    """Genel CRUD ve sorgulama metotlarını barındıran temel repository."""

    model = None  # Alt sınıflar tarafından atanır

    @classmethod
    def _base_query(cls):
        """Soft delete destekli temel sorgu."""
        query = cls.model.query
        if hasattr(cls.model, 'silinme_tarihi'):
            query = query.filter(cls.model.silinme_tarihi.is_(None))
        return query

    @classmethod
    def get_by_id(cls, record_id):
        """ID'ye göre tekil kayıt getirir."""
        return cls.model.query.get(record_id)

    @classmethod
    def get_all(cls):
        """Tüm kayıtları döndürür."""
        return cls._base_query().all()

    @classmethod
    def filter_by(cls, **kwargs):
        """Verilen kriterlere göre filtreler."""
        return cls._base_query().filter_by(**kwargs).all()

    @classmethod
    def search(cls, column, keyword):
        """Belirli bir sütunda LIKE araması yapar."""
        return cls._base_query().filter(column.ilike(f'%{keyword}%')).all()

    @classmethod
    def create(cls, **kwargs):
        """Yeni kayıt oluşturur ve döndürür."""
        instance = cls.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def update(cls, record_id, **kwargs):
        """Mevcut kaydı günceller."""
        instance = cls.get_by_id(record_id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        db.session.commit()
        return instance

    @classmethod
    def delete(cls, record_id):
        """Kaydı siler. Başarılıysa True döndürür."""
        instance = cls.get_by_id(record_id)
        if instance is None:
            return False
        # Soft delete destekleyen modellerde silinme_tarihi set edilir
        if hasattr(instance, 'silinme_tarihi'):
            instance.silinme_tarihi = datetime.utcnow()
            db.session.commit()
            return True

        db.session.delete(instance)
        db.session.commit()
        return True

    @classmethod
    def count(cls):
        """Toplam kayıt sayısını döndürür."""
        return cls._base_query().count()

    @classmethod
    def paginate(cls, page=1, per_page=10):
        """Sayfalama ile kayıtları döndürür."""
        return cls._base_query().paginate(page=page, per_page=per_page, error_out=False)

    @classmethod
    def exists(cls, record_id):
        """Kayıt var mı kontrol eder."""
        if hasattr(cls.model, 'id'):
            return cls._base_query().filter_by(id=record_id).first() is not None
        return cls.get_by_id(record_id) is not None
