"""
eMuhasebe Pro - Veritabanı Modelleri
Tüm veritabanı tablolarının tanımları

Finansal Veri İntegritysi:
- Numeric(12,2) para hassasiyeti için (Float yerine)
- CHECK constraints saatler ve yüzdeler için
- NOT NULL kritik alanlar için
- Audit Trail tüm değişiklikler için
- Soft Delete muhasebe kayıtları delete yerine işaretle
"""
from datetime import datetime, timezone
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, event, inspect

db = SQLAlchemy()


# ════════════════════════════════════════════════════════════════
# AUDIT TRAIL - Tüm değişiklikleri logla
# ════════════════════════════════════════════════════════════════

class AuditLog(db.Model):
    """Veritabanı audit trail - kim, ne zaman, ne yaptı"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    tablo_adi = db.Column(db.String(100), nullable=False, index=True)
    kayit_id = db.Column(db.Integer, nullable=True, index=True)
    islem_tipi = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE
    eski_veriler = db.Column(db.JSON)  # Eski değerler JSON olarak
    yeni_veriler = db.Column(db.JSON)  # Yeni değerler JSON olarak
    degisen_alanlar = db.Column(db.JSON)  # Hangi alanlar değişti
    olusturma_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.islem_tipi} {self.tablo_adi}:{self.kayit_id}>'


# ════════════════════════════════════════════════════════════════
# MIXIN - Soft Delete ve Audit Trail desteği
# ════════════════════════════════════════════════════════════════

class SoftDeleteMixin:
    """Soft delete mixin - silinmiş ama veri kalır"""
    silinme_tarihi = db.Column(db.DateTime(timezone=True), nullable=True)  # NULL = aktif
    
    def soft_delete(self):
        """Mantıksal silme (veri kaldırma değil)"""
        self.silinme_tarihi = datetime.now(timezone.utc)
        db.session.commit()
    
    def restore(self):
        """Silinen kaydı geri al"""
        self.silinme_tarihi = None
        db.session.commit()
    
    @classmethod
    def get_active(cls):
        """Sadece silinmemiş kayıtları getir"""
        return cls.query.filter_by(silinme_tarihi=None)


# ════════════════════════════════════════════════════════════════
# MÜŞTERI / TEDARİKÇİ
# ════════════════════════════════════════════════════════════════

class Musteri(db.Model, SoftDeleteMixin):
    """Müşteri/Tedarikçi bilgileri"""
    __tablename__ = 'musteriler'
    __table_args__ = (
        CheckConstraint("tip IN ('musteri','tedarikci','her_ikisi')", name='check_musteri_tip'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    unvan = db.Column(db.String(200), nullable=False)
    vergi_no = db.Column(db.String(11), unique=True, nullable=True)
    vergi_dairesi = db.Column(db.String(100))
    adres = db.Column(db.Text)
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, index=True, nullable=True)
    tip = db.Column(db.String(20), default='musteri', nullable=False)  # musteri, tedarikci, her_ikisi
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    
    # Soft delete
    silinme_tarihi = db.Column(db.DateTime(timezone=True), nullable=True)

    olusturma_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    guncelleme_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # İlişkiler
    alis_faturalari = db.relationship('AlisFatura', backref='tedarikci', lazy='select')
    satis_faturalari = db.relationship('SatisFatura', backref='musteri', lazy='select')
    iade_faturalari = db.relationship('IadeFatura', backref='firma', lazy='select')
    
    def __repr__(self):
        return f'<Musteri {self.unvan}>'


# ════════════════════════════════════════════════════════════════
# ÜRÜN / HİZMET
# ════════════════════════════════════════════════════════════════

class Urun(db.Model, SoftDeleteMixin):
    """Ürün/Hizmet tanımları"""
    __tablename__ = 'urunler'
    __table_args__ = (
        CheckConstraint('kdv_orani >= 0 AND kdv_orani <= 100', name='check_kdv_orani'),
        CheckConstraint('alis_fiyat >= 0', name='check_alis_fiyat'),
        CheckConstraint('satis_fiyat >= 0', name='check_satis_fiyat'),
        CheckConstraint('stok_miktari >= 0', name='check_stok_miktari'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(50), unique=True, nullable=False)
    ad = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    birim = db.Column(db.String(20), default='Adet', nullable=False)
    
    # ✅ Numeric(12,2) - Para hassasiyeti (Float yerine)
    alis_fiyat = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    satis_fiyat = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    kdv_orani = db.Column(db.Integer, default=20, nullable=False)  # % olarak
    stok_miktari = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    
    # Soft delete
    silinme_tarihi = db.Column(db.DateTime(timezone=True), nullable=True)

    olusturma_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    guncelleme_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<Urun {self.kod} - {self.ad}>'


# ════════════════════════════════════════════════════════════════
# ALIŞ FATURALARI
# ════════════════════════════════════════════════════════════════

class AlisFatura(db.Model, SoftDeleteMixin):
    """Alış faturaları"""
    __tablename__ = 'alis_faturalari'
    __table_args__ = (
        CheckConstraint('ara_toplam >= 0', name='check_alis_ara_toplam'),
        CheckConstraint('kdv_toplam >= 0', name='check_alis_kdv_toplam'),
        CheckConstraint('indirim_toplam >= 0', name='check_alis_indirim_toplam'),
        CheckConstraint('genel_toplam >= 0', name='check_alis_genel_toplam'),
        CheckConstraint("durum IN ('beklemede','odendi','iptal')", name='check_alis_durum'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fatura_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fatura_tarihi = db.Column(db.Date, nullable=False)
    vade_tarihi = db.Column(db.Date)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'), nullable=False)
    
    # ✅ Numeric(12,2) - Para hassasiyeti
    ara_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    kdv_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    indirim_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    genel_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Durum bilgileri
    durum = db.Column(db.String(20), default='beklemede', nullable=False)  # beklemede, odendi, iptal
    aciklama = db.Column(db.Text)
    
    # Soft delete
    silinme_tarihi = db.Column(db.DateTime(timezone=True), nullable=True)

    olusturma_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    guncelleme_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # İlişkiler
    kalemler = db.relationship('AlisFaturaKalem', backref='fatura', lazy='select', cascade='all, delete-orphan')
    
    def hesapla(self):
        """Fatura toplamlarını hesapla (Numeric doğruluğu).

        İndirim, KDV matrahını orantısal olarak düşürür (iskontonun KDV
        tabanını etkilediği varsayımı). assert yerine ValueError fırlatır.
        """
        indirim = getattr(self, 'indirim_toplam', None) or Decimal('0.00')
        self.ara_toplam = sum((k.toplam for k in self.kalemler), Decimal('0.00'))
        brut_kdv = sum((k.kdv_tutar for k in self.kalemler), Decimal('0.00'))
        kdv_matrahi = max(self.ara_toplam - indirim, Decimal('0.00'))
        oran = (kdv_matrahi / self.ara_toplam) if self.ara_toplam else Decimal('0.00')
        self.kdv_toplam = brut_kdv * oran
        self.genel_toplam = kdv_matrahi + self.kdv_toplam

        if self.genel_toplam < Decimal('0.00'):
            raise ValueError(f'Geçersiz total: {self.genel_toplam}')
    
    def __repr__(self):
        return f'<AlisFatura {self.fatura_no}>'


class AlisFaturaKalem(db.Model):
    """Alış fatura kalemleri"""
    __tablename__ = 'alis_fatura_kalemleri'
    __table_args__ = (
        CheckConstraint('miktar > 0', name='check_alis_kalem_miktar'),
        CheckConstraint('birim_fiyat >= 0', name='check_alis_kalem_fiyat'),
        CheckConstraint('kdv_orani >= 0 AND kdv_orani <= 100', name='check_alis_kalem_kdv'),
        CheckConstraint('indirim_orani >= 0 AND indirim_orani <= 100', name='check_alis_kalem_indirim'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('alis_faturalari.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urunler.id'))
    
    aciklama = db.Column(db.String(300))
    miktar = db.Column(db.Numeric(12, 2), default=Decimal('1'), nullable=False)
    birim = db.Column(db.String(20), default='Adet', nullable=False)
    birim_fiyat = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    kdv_orani = db.Column(db.Integer, default=20, nullable=False)
    indirim_orani = db.Column(db.Integer, default=0, nullable=False)  # % olarak
    
    @property
    def toplam(self):
        """Kalem toplamı (KDV hariç)"""
        tutar = self.miktar * self.birim_fiyat
        indirim = tutar * (Decimal(self.indirim_orani) / Decimal('100'))
        return tutar - indirim
    
    @property
    def kdv_tutar(self):
        """KDV tutarı"""
        return self.toplam * (Decimal(self.kdv_orani) / Decimal('100'))
    
    @property
    def genel_toplam(self):
        """KDV dahil toplam"""
        return self.toplam + self.kdv_tutar


# ════════════════════════════════════════════════════════════════
# SATIŞ FATURALARI
# ════════════════════════════════════════════════════════════════

class SatisFatura(db.Model, SoftDeleteMixin):
    """Satış faturaları"""
    __tablename__ = 'satis_faturalari'
    __table_args__ = (
        CheckConstraint('ara_toplam >= 0', name='check_satis_ara_toplam'),
        CheckConstraint('kdv_toplam >= 0', name='check_satis_kdv_toplam'),
        CheckConstraint('indirim_toplam >= 0', name='check_satis_indirim_toplam'),
        CheckConstraint('genel_toplam >= 0', name='check_satis_genel_toplam'),
        CheckConstraint("durum IN ('beklemede','tahsil_edildi','iptal')", name='check_satis_durum'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fatura_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fatura_tarihi = db.Column(db.Date, nullable=False)
    vade_tarihi = db.Column(db.Date)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'), nullable=False)
    
    # ✅ Numeric(12,2) - Para hassasiyeti
    ara_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    kdv_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    indirim_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    genel_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Durum bilgileri
    durum = db.Column(db.String(20), default='beklemede', nullable=False)  # beklemede, tahsil_edildi, iptal
    aciklama = db.Column(db.Text)
    
    # Soft delete
    silinme_tarihi = db.Column(db.DateTime(timezone=True), nullable=True)

    olusturma_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    guncelleme_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # İlişkiler
    kalemler = db.relationship('SatisFaturaKalem', backref='fatura', lazy='select', cascade='all, delete-orphan')
    
    def hesapla(self):
        """Fatura toplamlarını hesapla (Numeric doğruluğu).

        İndirim, KDV matrahını orantısal olarak düşürür (iskontonun KDV
        tabanını etkilediği varsayımı). assert yerine ValueError fırlatır.
        """
        indirim = getattr(self, 'indirim_toplam', None) or Decimal('0.00')
        self.ara_toplam = sum((k.toplam for k in self.kalemler), Decimal('0.00'))
        brut_kdv = sum((k.kdv_tutar for k in self.kalemler), Decimal('0.00'))
        kdv_matrahi = max(self.ara_toplam - indirim, Decimal('0.00'))
        oran = (kdv_matrahi / self.ara_toplam) if self.ara_toplam else Decimal('0.00')
        self.kdv_toplam = brut_kdv * oran
        self.genel_toplam = kdv_matrahi + self.kdv_toplam

        if self.genel_toplam < Decimal('0.00'):
            raise ValueError(f'Geçersiz total: {self.genel_toplam}')
    
    def __repr__(self):
        return f'<SatisFatura {self.fatura_no}>'


class SatisFaturaKalem(db.Model):
    """Satış fatura kalemleri"""
    __tablename__ = 'satis_fatura_kalemleri'
    __table_args__ = (
        CheckConstraint('miktar > 0', name='check_satis_kalem_miktar'),
        CheckConstraint('birim_fiyat >= 0', name='check_satis_kalem_fiyat'),
        CheckConstraint('kdv_orani >= 0 AND kdv_orani <= 100', name='check_satis_kalem_kdv'),
        CheckConstraint('indirim_orani >= 0 AND indirim_orani <= 100', name='check_satis_kalem_indirim'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('satis_faturalari.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urunler.id'))
    
    aciklama = db.Column(db.String(300))
    miktar = db.Column(db.Numeric(12, 2), default=Decimal('1'), nullable=False)
    birim = db.Column(db.String(20), default='Adet', nullable=False)
    birim_fiyat = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    kdv_orani = db.Column(db.Integer, default=20, nullable=False)
    indirim_orani = db.Column(db.Integer, default=0, nullable=False)  # % olarak
    
    @property
    def toplam(self):
        """Kalem toplamı (KDV hariç)"""
        tutar = self.miktar * self.birim_fiyat
        indirim = tutar * (Decimal(self.indirim_orani) / Decimal('100'))
        return tutar - indirim
    
    @property
    def kdv_tutar(self):
        """KDV tutarı"""
        return self.toplam * (Decimal(self.kdv_orani) / Decimal('100'))
    
    @property
    def genel_toplam(self):
        """KDV dahil toplam"""
        return self.toplam + self.kdv_tutar


# ════════════════════════════════════════════════════════════════
# İADE FATURALARI
# ════════════════════════════════════════════════════════════════

class IadeFatura(db.Model, SoftDeleteMixin):
    """İade faturaları"""
    __tablename__ = 'iade_faturalari'
    __table_args__ = (
        CheckConstraint('ara_toplam >= 0', name='check_iade_ara_toplam'),
        CheckConstraint('kdv_toplam >= 0', name='check_iade_kdv_toplam'),
        CheckConstraint('genel_toplam >= 0', name='check_iade_genel_toplam'),
        CheckConstraint("iade_turu IN ('alis_iade','satis_iade')", name='check_iade_turu'),
        CheckConstraint("durum IN ('beklemede','tamamlandi','iptal')", name='check_iade_durum'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fatura_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    fatura_tarihi = db.Column(db.Date, nullable=False)
    firma_id = db.Column(db.Integer, db.ForeignKey('musteriler.id'), nullable=False)
    
    # İade türü
    iade_turu = db.Column(db.String(20), nullable=False)  # alis_iade, satis_iade
    referans_fatura_no = db.Column(db.String(50))  # İlişkili orijinal fatura
    
    # ✅ Numeric(12,2) - Para hassasiyeti
    ara_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    kdv_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    genel_toplam = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Durum bilgileri
    durum = db.Column(db.String(20), default='beklemede', nullable=False)  # beklemede, tamamlandi, iptal
    iade_nedeni = db.Column(db.Text)
    aciklama = db.Column(db.Text)
    
    # Soft delete
    silinme_tarihi = db.Column(db.DateTime(timezone=True), nullable=True)

    olusturma_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    guncelleme_tarihi = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # İlişkiler
    kalemler = db.relationship('IadeFaturaKalem', backref='fatura', lazy='select', cascade='all, delete-orphan')
    
    def hesapla(self):
        """Fatura toplamlarını hesapla (Numeric doğruluğu)"""
        self.ara_toplam = sum((k.toplam for k in self.kalemler), Decimal('0.00'))
        self.kdv_toplam = sum((k.kdv_tutar for k in self.kalemler), Decimal('0.00'))
        self.genel_toplam = self.ara_toplam + self.kdv_toplam
        
        # Negatif olmadığını verify et
        assert self.genel_toplam >= Decimal('0.00'), f'Geçersiz total: {self.genel_toplam}'
    
    def __repr__(self):
        return f'<IadeFatura {self.fatura_no}>'


class IadeFaturaKalem(db.Model):
    """İade fatura kalemleri"""
    __tablename__ = 'iade_fatura_kalemleri'
    __table_args__ = (
        CheckConstraint('miktar > 0', name='check_iade_kalem_miktar'),
        CheckConstraint('birim_fiyat >= 0', name='check_iade_kalem_fiyat'),
        CheckConstraint('kdv_orani >= 0 AND kdv_orani <= 100', name='check_iade_kalem_kdv'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('iade_faturalari.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urunler.id'))
    
    aciklama = db.Column(db.String(300))
    miktar = db.Column(db.Numeric(12, 2), default=Decimal('1'), nullable=False)
    birim = db.Column(db.String(20), default='Adet', nullable=False)
    birim_fiyat = db.Column(db.Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    kdv_orani = db.Column(db.Integer, default=20, nullable=False)
    
    @property
    def toplam(self):
        """Kalem toplamı (KDV hariç)"""
        return self.miktar * self.birim_fiyat
    
    @property
    def kdv_tutar(self):
        """KDV tutarı"""
        return self.toplam * (Decimal(self.kdv_orani) / Decimal('100'))
    
    @property
    def genel_toplam(self):
        """KDV dahil toplam"""
        return self.toplam + self.kdv_tutar


# ════════════════════════════════════════════════════════════════
# AUDIT TRACKING HOOKS
# ════════════════════════════════════════════════════════════════

def _serialize_model_state(obj):
    data = {}
    try:
        for col in obj.__table__.columns:
            val = getattr(obj, col.name)
            # Convert non-serializables
            if isinstance(val, datetime):
                data[col.name] = val.isoformat()
            else:
                try:
                    data[col.name] = str(val) if val is not None else None
                except Exception:
                    data[col.name] = None
    except Exception:
        return {}
    return data


# Event listeners kaydet - After flush'ta audit kaydedilir
def register_audit_listeners(db_instance):
    """Register listeners that create AuditLog entries for create/update/delete operations."""

    @event.listens_for(db_instance.session, 'before_flush')
    def before_flush(session, flush_context, instances):
        # New objects -> CREATE
        for obj in list(session.new):
            if isinstance(obj, AuditLog):
                continue
            audit = AuditLog(
                tablo_adi=getattr(obj.__class__, '__tablename__', obj.__class__.__name__),
                kayit_id=getattr(obj, 'id', None) or None,
                islem_tipi='CREATE',
                eski_veriler=None,
                yeni_veriler=_serialize_model_state(obj),
                degisen_alanlar=None
            )
            session.add(audit)

        # Dirty objects -> UPDATE
        for obj in list(session.dirty):
            if isinstance(obj, AuditLog):
                continue
            state = inspect(obj)
            if not state.attrs:
                continue
            changed = []
            old_vals = {}
            new_vals = {}
            for attr in state.attrs:
                if attr.history.has_changes():
                    name = attr.key
                    changed.append(name)
                    old = attr.history.deleted[0] if attr.history.deleted else None
                    new = getattr(obj, name)
                    old_vals[name] = str(old) if old is not None else None
                    new_vals[name] = str(new) if new is not None else None

            if changed:
                audit = AuditLog(
                    tablo_adi=getattr(obj.__class__, '__tablename__', obj.__class__.__name__),
                    kayit_id=getattr(obj, 'id', None),
                    islem_tipi='UPDATE',
                    eski_veriler=old_vals,
                    yeni_veriler=new_vals,
                    degisen_alanlar=changed
                )
                session.add(audit)

        # Deleted -> DELETE (hard deletes only)
        for obj in list(session.deleted):
            if isinstance(obj, AuditLog):
                continue
            audit = AuditLog(
                tablo_adi=getattr(obj.__class__, '__tablename__', obj.__class__.__name__),
                kayit_id=getattr(obj, 'id', None),
                islem_tipi='DELETE',
                eski_veriler=_serialize_model_state(obj),
                yeni_veriler=None,
                degisen_alanlar=None
            )
            session.add(audit)


# Basit User modeli
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'kullanicilar'
    __table_args__ = (
        CheckConstraint("role IN ('user','admin')", name='check_user_role'),
    )
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    aktif = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

