from __future__ import annotations
from typing import Any, Iterable, List, Optional, Type
from types import SimpleNamespace
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from app.models import db
import logging

logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self, model: Type, session: Session):
        self.model = model
        self.session = session

    def _base_query(self):
        stmt = select(self.model).where(getattr(self.model, 'silinme_tarihi', None) == None)
        return stmt

    def get_all(self, eager_load: Optional[Iterable] = None) -> List[Any]:
        stmt = self._base_query()
        if eager_load:
            for rel in eager_load:
                stmt = stmt.options(joinedload(getattr(self.model, rel)))
        items = list(self.session.execute(stmt).scalars().all())
        logger.debug("%s.get_all returned %s rows", self.model.__name__, len(items))
        return items

    def get_by_id(self, id_) -> Optional[Any]:
        stmt = select(self.model).where(self.model.id == id_)
        item = self.session.execute(stmt).scalars().first()
        logger.debug("%s.get_by_id(%s) -> %s", self.model.__name__, id_, bool(item))
        return item

    def exists(self, *args, **filters) -> bool:
        stmt = select(func.count()).select_from(self.model).where(self.model.silinme_tarihi == None)
        if args:
            if len(args) != 1:
                raise ValueError('exists() tek bir pozisyonel arguman kabul eder')
            stmt = stmt.where(self.model.id == args[0])
        for k, v in filters.items():
            stmt = stmt.where(getattr(self.model, k) == v)
        count = self.session.execute(stmt).scalar_one()
        return count > 0

    def count(self, **filters) -> int:
        stmt = select(func.count()).select_from(self.model).where(self.model.silinme_tarihi == None)
        for k, v in filters.items():
            stmt = stmt.where(getattr(self.model, k) == v)
        return int(self.session.execute(stmt).scalar_one())

    def filter_by(self, **filters) -> List[Any]:
        stmt = self._base_query()
        for k, v in filters.items():
            stmt = stmt.where(getattr(self.model, k) == v)
        return list(self.session.execute(stmt).scalars().all())

    def search(self, *clauses, eager_load: Optional[Iterable] = None) -> List[Any]:
        stmt = self._base_query()
        for c in clauses:
            stmt = stmt.where(c)
        if eager_load:
            for rel in eager_load:
                stmt = stmt.options(joinedload(getattr(self.model, rel)))
        return list(self.session.execute(stmt).scalars().all())

    def paginate(self, page: int = 1, per_page: int = 20, eager_load: Optional[Iterable] = None):
        stmt = self._base_query()
        if eager_load:
            for rel in eager_load:
                stmt = stmt.options(joinedload(rel))
        total = self.session.execute(select(func.count()).select_from(self.model).where(self.model.silinme_tarihi == None)).scalar_one()
        items = list(self.session.execute(stmt.offset((page - 1) * per_page).limit(per_page)).scalars().all())
        return {
            'total': int(total),
            'page': page,
            'per_page': per_page,
            'items': items,
        }

    def create(self, obj: Any) -> Any:
        self.session.add(obj)
        self.session.flush()
        logger.info("%s.create(%s)", self.model.__name__, getattr(obj, 'id', None))
        return obj

    def update(self, obj: Any, **changes) -> Any:
        for k, v in changes.items():
            setattr(obj, k, v)
        self.session.add(obj)
        self.session.flush()
        logger.info("%s.update(%s)", self.model.__name__, getattr(obj, 'id', None))
        return obj

    def delete(self, obj: Any) -> None:
        # soft delete if field exists
        if hasattr(obj, 'silinme_tarihi'):
            from datetime import datetime, timezone

            obj.silinme_tarihi = datetime.now(timezone.utc)
            self.session.add(obj)
        else:
            self.session.delete(obj)
        self.session.flush()
        logger.info("%s.delete(%s)", self.model.__name__, getattr(obj, 'id', None))

    def hard_delete(self, obj: Any) -> None:
        self.session.delete(obj)
        self.session.flush()
        logger.info("%s.hard_delete(%s)", self.model.__name__, getattr(obj, 'id', None))

    def restore(self, obj: Any) -> Any:
        if hasattr(obj, 'silinme_tarihi'):
            obj.silinme_tarihi = None
            self.session.add(obj)
            self.session.flush()
            logger.info("%s.restore(%s)", self.model.__name__, getattr(obj, 'id', None))
        return obj

    # --- Classmethod-style helpers for existing repo classes that use class methods ---
    @classmethod
    def _base_query_cls(cls):
        stmt = select(cls.model).where(getattr(cls.model, 'silinme_tarihi', None) == None)
        return stmt

    @classmethod
    def get_all(cls, eager_load: Optional[Iterable] = None):
        stmt = cls._base_query_cls()
        if eager_load:
            for rel in eager_load:
                stmt = stmt.options(joinedload(rel))
        items = list(db.session.execute(stmt).scalars().all())
        logger.debug("%s.get_all returned %s rows", cls.model.__name__, len(items))
        return items

    @classmethod
    def get_by_id(cls, id_):
        item = cls.model.query.filter_by(id=id_).first()
        logger.debug("%s.get_by_id(%s) -> %s", cls.model.__name__, id_, bool(item))
        return item

    @classmethod
    def filter_by(cls, **filters):
        q = cls.model.query.filter_by(**filters)
        if hasattr(cls.model, 'silinme_tarihi'):
            q = q.filter(cls.model.silinme_tarihi == None)
        return q.all()

    @classmethod
    def count(cls, **filters):
        q = db.session.query(func.count()).select_from(cls.model)
        if hasattr(cls.model, 'silinme_tarihi'):
            q = q.filter(cls.model.silinme_tarihi == None)
        for k, v in filters.items():
            q = q.filter(getattr(cls.model, k) == v)
        return int(q.scalar())

    @classmethod
    def exists(cls, *args, **filters):
        if args:
            if len(args) != 1:
                raise ValueError('exists() tek bir pozisyonel arguman kabul eder')
            return cls.count(id=args[0]) > 0
        return cls.count(**filters) > 0

    @classmethod
    def search(cls, *clauses, eager_load: Optional[Iterable] = None):
        stmt = cls._base_query_cls()
        for clause in clauses:
            stmt = stmt.where(clause)
        if eager_load:
            for rel in eager_load:
                stmt = stmt.options(joinedload(rel))
        return list(db.session.execute(stmt).scalars().all())

    @classmethod
    def paginate(cls, page: int = 1, per_page: int = 20, eager_load: Optional[Iterable] = None):
        q = cls.model.query.filter(cls.model.silinme_tarihi == None)
        if eager_load:
            for rel in eager_load:
                q = q.options(joinedload(getattr(cls.model, rel)))
        total = q.count()
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return SimpleNamespace(total=total, page=page, per_page=per_page, items=items)

    @classmethod
    def create(cls, **data):
        obj = cls.model(**data)
        db.session.add(obj)
        db.session.flush()
        db.session.commit()
        logger.info("%s.create(%s)", cls.model.__name__, getattr(obj, 'id', None))
        return obj

    @classmethod
    def update(cls, obj_or_id, **changes):
        obj = obj_or_id
        if not isinstance(obj_or_id, cls.model):
            obj = cls.get_by_id(obj_or_id)
        if obj is None:
            raise ValueError('Kayıt bulunamadı')
        for key, value in changes.items():
            setattr(obj, key, value)
        db.session.add(obj)
        db.session.flush()
        db.session.commit()
        logger.info("%s.update(%s)", cls.model.__name__, getattr(obj, 'id', None))
        return obj

    @classmethod
    def delete(cls, obj_or_id):
        obj = obj_or_id
        if not isinstance(obj_or_id, cls.model):
            obj = cls.get_by_id(obj_or_id)
        if obj is None:
            return False
        if hasattr(obj, 'silinme_tarihi'):
            from datetime import datetime, timezone

            obj.silinme_tarihi = datetime.now(timezone.utc)
            db.session.add(obj)
        else:
            db.session.delete(obj)
        db.session.flush()
        db.session.commit()
        logger.info("%s.delete(%s)", cls.model.__name__, getattr(obj, 'id', None))
        return True

    @classmethod
    def hard_delete(cls, obj_or_id):
        obj = obj_or_id
        if not isinstance(obj_or_id, cls.model):
            obj = cls.get_by_id(obj_or_id)
        if obj is None:
            raise ValueError('Kayıt bulunamadı')
        db.session.delete(obj)
        db.session.flush()
        db.session.commit()
        logger.info("%s.hard_delete(%s)", cls.model.__name__, getattr(obj, 'id', None))
        return obj

    @classmethod
    def restore(cls, obj_or_id):
        obj = obj_or_id
        if not isinstance(obj_or_id, cls.model):
            obj = cls.get_by_id(obj_or_id)
        if obj is None:
            raise ValueError('Kayıt bulunamadı')
        if hasattr(obj, 'silinme_tarihi'):
            obj.silinme_tarihi = None
            db.session.add(obj)
            db.session.flush()
            db.session.commit()
            logger.info("%s.restore(%s)", cls.model.__name__, getattr(obj, 'id', None))
        return obj
