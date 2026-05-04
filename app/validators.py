"""
Pydantic Validators - API input validation
JSON request'leri doğrula ve type hints ile API endpoints'ini güvenli hale getir.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date


GECERLI_KDV_ORANLARI = {0, 1, 8, 10, 18, 20}
GECERLI_BIRIMLER = {'Adet', 'Kg', 'Litre', 'Metre'}
GECERLI_MUSTERI_TIPLERI = {'musteri', 'tedarikci', 'her_ikisi'}


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, 'isoformat') and not isinstance(value, str):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d').date()
    return value


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MÜŞTERİ VALIDATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MusteriCreateRequest(BaseModel):
    """Yeni müşteri oluşturma endpoint'i için validation."""
    unvan: str = Field(..., min_length=2, max_length=255, description="Müşteri ünvanı")
    vergi_no: Optional[str] = Field(None, min_length=10, max_length=11, description="Vergi numarası")
    email: Optional[EmailStr] = Field(None, description="E-mail adresi")
    telefon: Optional[str] = Field(None, max_length=20, description="Telefon numarası")
    adres: Optional[str] = Field(None, max_length=500, description="Adres")
    tip: Optional[str] = Field('musteri', description="Müşteri tipi")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "unvan": "ABC Ltd Şti",
                "vergi_no": "1234567890",
                "email": "info@abc.com",
                "telefon": "+90 532 123 4567",
                "adres": "İstanbul, Türkiye"
            }
        }
    )
    
    @field_validator('unvan')
    @classmethod
    def unvan_not_blank(cls, v):
        """Ünvan boş olamaz."""
        if not v or not v.strip():
            raise ValueError('Ünvan boş olamaz')
        return v.strip()
    
    @field_validator('vergi_no')
    @classmethod
    def vergi_no_format(cls, v):
        """Vergi numarası sadece rakam olmalı."""
        if v and not v.isdigit():
            raise ValueError('Vergi numarası sadece rakam içerebilir')
        return v

    @field_validator('tip')
    @classmethod
    def validate_tip(cls, v):
        if v not in GECERLI_MUSTERI_TIPLERI:
            raise ValueError("Geçersiz müşteri tipi")
        return v


class MusteriUpdateRequest(BaseModel):
    """Müşteri güncelleme endpoint'i için validation."""
    unvan: Optional[str] = Field(None, min_length=2, max_length=255)
    vergi_no: Optional[str] = Field(None, min_length=10, max_length=11)
    email: Optional[EmailStr] = None
    telefon: Optional[str] = Field(None, max_length=20)
    adres: Optional[str] = Field(None, max_length=500)
    tip: Optional[str] = Field(None, description="Müşteri tipi")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "unvan": "ABC Inc Şti",
                "email": "newemail@abc.com"
            }
        }
    )
    
    @field_validator('vergi_no')
    @classmethod
    def vergi_no_format(cls, v):
        if v and not v.isdigit():
            raise ValueError('Vergi numarası sadece rakam içerebilir')
        return v

    @field_validator('tip')
    @classmethod
    def validate_tip(cls, v):
        if v is not None and v not in GECERLI_MUSTERI_TIPLERI:
            raise ValueError("Geçersiz müşteri tipi")
        return v


class MusteriResponse(BaseModel):
    """Müşteri response format."""
    id: int
    unvan: str
    vergi_no: Optional[str]
    email: Optional[str]
    telefon: Optional[str]
    adres: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ÜRÜN VALIDATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UrunCreateRequest(BaseModel):
    """Yeni ürün oluşturma endpoint'i için validation."""
    ad: str = Field(..., min_length=2, max_length=255, description="Ürün adı")
    kod: Optional[str] = Field(None, min_length=1, max_length=50, description="Ürün kodu")
    birim: Optional[str] = Field("Adet", max_length=20, description="Ölçü birimi")
    alis_fiyat: Decimal = Field(..., gt=0, description="Alış fiyatı (>0)")
    satis_fiyat: Decimal = Field(..., gt=0, description="Satış fiyatı (>0)")
    stok_miktari: int = Field(0, ge=0, description="Stok miktarı (≥0)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ad": "Laptop",
                "kod": "LT-001",
                "birim": "Adet",
                "alis_fiyat": 5000.00,
                "satis_fiyat": 6500.00,
                "stok_miktari": 10
            }
        }
    )
    
    @field_validator('alis_fiyat', 'satis_fiyat', mode='before')
    @classmethod
    def parse_decimal(cls, v):
        """String'den Decimal'e çevir."""
        if isinstance(v, str):
            return Decimal(v)
        return v
    
    @field_validator('kod')
    @classmethod
    def kod_not_empty_if_provided(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Kod boş olamaz')
        return v.strip() if v else None

    @field_validator('birim')
    @classmethod
    def validate_birim(cls, v):
        if v is not None and v not in GECERLI_BIRIMLER:
            raise ValueError('Geçersiz birim')
        return v


class UrunUpdateRequest(BaseModel):
    """Ürün güncelleme endpoint'i için validation."""
    ad: Optional[str] = Field(None, min_length=2, max_length=255)
    kod: Optional[str] = Field(None, min_length=1, max_length=50)
    birim: Optional[str] = Field(None, max_length=20)
    alis_fiyat: Optional[Decimal] = Field(None, gt=0)
    satis_fiyat: Optional[Decimal] = Field(None, gt=0)
    stok_miktari: Optional[int] = Field(None, ge=0)
    
    @field_validator('alis_fiyat', 'satis_fiyat', mode='before')
    @classmethod
    def parse_decimal(cls, v):
        if v and isinstance(v, str):
            return Decimal(v)
        return v

    @field_validator('birim')
    @classmethod
    def validate_birim(cls, v):
        if v is not None and v not in GECERLI_BIRIMLER:
            raise ValueError('Geçersiz birim')
        return v


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FATURA VALIDATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FaturaKalemRequest(BaseModel):
    """Fatura satır kalemi."""
    urun_id: int = Field(..., gt=0, description="Ürün ID")
    miktar: Decimal = Field(..., gt=0, description="Miktar (>0)")
    birim_fiyat: Decimal = Field(..., ge=0, description="Birim fiyat")
    kdv_orani: int = Field(18, ge=0, le=100, description="KDV oranı (0-100%)")
    indirim_orani: int = Field(0, ge=0, le=100, description="İndirim oranı (0-100%)")
    
    @field_validator('miktar', 'birim_fiyat', mode='before')
    @classmethod
    def parse_decimal(cls, v):
        if v and isinstance(v, str):
            return Decimal(v)
        return v

    @field_validator('kdv_orani')
    @classmethod
    def validate_kdv_orani(cls, v):
        if v not in GECERLI_KDV_ORANLARI:
            raise ValueError(f'Geçersiz KDV oranı: {v}')
        return v

    @field_validator('indirim_orani')
    @classmethod
    def validate_indirim_orani(cls, v):
        if v < 0 or v > 100:
            raise ValueError('İndirim oranı 0-100 aralığında olmalı')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "urun_id": 1,
                "miktar": 5,
                "birim_fiyat": 100.00,
                "kdv_orani": 18,
                "indirim_orani": 10
            }
        }
    )


class FaturaCreateRequest(BaseModel):
    """Fatura oluşturma request."""
    musteri_id: int = Field(..., gt=0, description="Müşteri ID")
    fatura_no: str = Field(..., min_length=1, max_length=50, description="Fatura numarası")
    fatura_tarihi: date = Field(..., description="Fatura tarihi (YYYY-MM-DD)")
    kalemler: list[FaturaKalemRequest] = Field(..., min_length=1, description="Fatura kalemoleri (en az 1)")
    notlar: Optional[str] = Field(None, max_length=500, description="Notlar")
    
    @field_validator('kalemler')
    @classmethod
    def validate_kalemler(cls, v):
        """En az 1 kalem olmalı."""
        if not v or len(v) == 0:
            raise ValueError('Fatura en az 1 kalem içermeli')
        return v

    @field_validator('fatura_tarihi')
    @classmethod
    def validate_fatura_tarihi(cls, v):
        parsed = _parse_date(v)
        if parsed is None:
            return v
        if parsed > datetime.now().date():
            raise ValueError('Fatura tarihi gelecek bir tarih olamaz')
        return parsed
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "musteri_id": 1,
                "fatura_no": "2026/001",
                "fatura_tarihi": "2026-03-26",
                "kalemler": [
                    {
                        "urun_id": 1,
                        "miktar": 5,
                        "birim_fiyat": 100.00,
                        "kdv_orani": 18,
                        "indirim_orani": 0
                    }
                ],
                "notlar": "Ürünlerin kalitesi kontrol edilmiştir"
            }
        }
    )


class AlisFaturaKalemRequest(FaturaKalemRequest):
    pass


class AlisFaturaCreateRequest(BaseModel):
    tedarikci_id: int = Field(..., gt=0)
    fatura_no: str = Field(..., min_length=1, max_length=50)
    fatura_tarihi: date = Field(...)
    vade_tarihi: Optional[date] = None
    indirim_toplam: Decimal = Field(Decimal('0'), ge=0)
    kalemler: List[AlisFaturaKalemRequest] = Field(..., min_length=1)
    aciklama: Optional[str] = Field(None, max_length=500)

    @field_validator('fatura_tarihi', 'vade_tarihi', mode='before')
    @classmethod
    def parse_dates(cls, v):
        return _parse_date(v)

    @field_validator('fatura_tarihi')
    @classmethod
    def validate_fatura_tarihi(cls, v):
        if v and v > datetime.now().date():
            raise ValueError('Fatura tarihi gelecek bir tarih olamaz')
        return v


class SatisFaturaKalemRequest(FaturaKalemRequest):
    pass


class SatisFaturaCreateRequest(BaseModel):
    musteri_id: int = Field(..., gt=0)
    fatura_no: str = Field(..., min_length=1, max_length=50)
    fatura_tarihi: date = Field(...)
    vade_tarihi: Optional[date] = None
    indirim_toplam: Decimal = Field(Decimal('0'), ge=0)
    kalemler: List[SatisFaturaKalemRequest] = Field(..., min_length=1)
    aciklama: Optional[str] = Field(None, max_length=500)

    @field_validator('fatura_tarihi', 'vade_tarihi', mode='before')
    @classmethod
    def parse_dates(cls, v):
        return _parse_date(v)

    @field_validator('fatura_tarihi')
    @classmethod
    def validate_fatura_tarihi(cls, v):
        if v and v > datetime.now().date():
            raise ValueError('Fatura tarihi gelecek bir tarih olamaz')
        return v


class IadeFaturaKalemRequest(BaseModel):
    urun_id: int = Field(..., gt=0)
    miktar: Decimal = Field(..., gt=0)
    birim_fiyat: Decimal = Field(..., ge=0)
    kdv_orani: int = Field(18, ge=0, le=100)

    @field_validator('miktar', 'birim_fiyat', mode='before')
    @classmethod
    def parse_decimal(cls, v):
        if v and isinstance(v, str):
            return Decimal(v)
        return v

    @field_validator('kdv_orani')
    @classmethod
    def validate_kdv_orani(cls, v):
        if v not in GECERLI_KDV_ORANLARI:
            raise ValueError(f'Geçersiz KDV oranı: {v}')
        return v

    @field_validator('miktar')
    @classmethod
    def validate_miktar(cls, v):
        if v <= 0:
            raise ValueError('Miktar sıfırdan büyük olmalı')
        return v


class IadeFaturaCreateRequest(BaseModel):
    firma_id: int = Field(..., gt=0)
    iade_turu: str = Field(..., min_length=1, max_length=20)
    referans_fatura_no: str = Field(..., min_length=1, max_length=50)
    fatura_no: str = Field(..., min_length=1, max_length=50)
    fatura_tarihi: date = Field(...)
    iade_nedeni: Optional[str] = Field(None, max_length=500)
    kalemler: List[IadeFaturaKalemRequest] = Field(..., min_length=1)

    @field_validator('fatura_tarihi', mode='before')
    @classmethod
    def parse_date(cls, v):
        return _parse_date(v)

    @field_validator('fatura_tarihi')
    @classmethod
    def validate_fatura_tarihi(cls, v):
        if v and v > datetime.now().date():
            raise ValueError('Fatura tarihi gelecek bir tarih olamaz')
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Optional[str] = Field('user', max_length=20)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGINATION REQUEST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PaginationParams(BaseModel):
    """Sayfalama parametreleri."""
    page: int = Field(1, ge=1, description="Sayfa numarası (≥1)")
    per_page: int = Field(20, ge=1, le=100, description="Sayfa başına kayıt (1-100)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "per_page": 20
            }
        }
    )


def validate_pagination_params(request_args):
    """Query parametrelerden pagination params'ı extract et."""
    try:
        page = int(request_args.get('page', 1))
        per_page = int(request_args.get('per_page', 20))
        
        # Validation
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
        if per_page > 100:
            per_page = 100
        
        return page, per_page, None  # (page, per_page, error)
    except (ValueError, TypeError) as e:
        return 1, 20, f"Geçersiz sayfalama parametreleri: {str(e)}"
