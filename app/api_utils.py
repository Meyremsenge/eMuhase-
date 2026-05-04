"""
API Utilities - Response standardization, pagination, error handling
"""

from flask import jsonify
from typing import Any, Dict, List, Optional
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ERROR RESPONSE STANDARDIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class APIError(Exception):
    """Standart API error."""
    
    def __init__(
        self,
        message: str,
        code: str = 'UNKNOWN_ERROR',
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


def error_response(
    message: str,
    code: str = 'UNKNOWN_ERROR',
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
):
    """
    Standart API error response döndür.
    
    Örnek:
        return error_response('Müşteri bulunamadı', 'NOT_FOUND', 404)
    """
    response = {
        'success': False,
        'error': {
            'message': message,
            'code': code,
        }
    }
    
    if details:
        response['error']['details'] = details
    
    logger.warning(f"API Error [{code}]: {message} (Status: {status_code})")
    
    return jsonify(response), status_code


def validation_error_response(validation_errors: List[Dict[str, Any]]):
    """
    Validation error'larını format et.
    
    Örnek:
        errors = [
            {'field': 'unvan', 'message': 'Min 2 karakter gerekli'},
            {'field': 'email', 'message': 'Geçersiz email'}
        ]
        return validation_error_response(errors)
    """
    response = {
        'success': False,
        'error': {
            'message': 'Validation hatası',
            'code': 'VALIDATION_ERROR',
            'details': {
                'validation_errors': validation_errors
            }
        }
    }
    
    logger.warning(f"Validation Error: {validation_errors}")
    
    return jsonify(response), 422  # 422 Unprocessable Entity


def pydantic_error_to_list(pydantic_errors):
    """
    Pydantic validation error'larını liste formatına çevir.
    
    Входные данные: pydantic ValidationError.errors()
    Çıktı: [{'field': str, 'message': str, 'type': str}, ...]
    """
    errors = []
    for error in pydantic_errors:
        loc = '.'.join(str(x) for x in error['loc'])
        errors.append({
            'field': loc,
            'message': error['msg'],
            'type': error['type']
        })
    return errors


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGINATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def paginated_response(
    items: List[Any],
    page: int,
    per_page: int,
    total: int,
    serialize_func=None
):
    """
    Sayfalanmış yanıt döndür.
    
    Args:
        items: Sayfa içindeki items
        page: Şu anki sayfa numarası
        per_page: Sayfa başına kayıt sayısı
        total: Toplam kayıt sayısı
        serialize_func: Item'ı dict'e çevirme fonksiyonu (opsiyonel)
    
    Çıktı Örneği:
        {
            "success": true,
            "data": [...],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 150,
                "total_pages": 8,
                "has_next": true,
                "has_prev": false
            }
        }
    """
    import math
    
    total_pages = math.ceil(total / per_page) if per_page > 0 else 1
    
    # Items'ı serialize et
    serialized_items = items
    if serialize_func:
        serialized_items = [serialize_func(item) for item in items]
    
    response = {
        'success': True,
        'data': serialized_items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    logger.debug(f"Paginated response: page={page}, per_page={per_page}, total={total}")
    
    return jsonify(response), 200


def list_response(items: List[Any], serialize_func=None):
    """
    Sayfalanmamış list yanıt döndür (backward compatibility için).
    
    Çıktı Örneği:
        {
            "success": true,
            "data": [...]
        }
    """
    # Items'ı serialize et
    serialized_items = items
    if serialize_func:
        serialized_items = [serialize_func(item) for item in items]
    
    response = {
        'success': True,
        'data': serialized_items
    }
    
    return jsonify(response), 200


def single_response(item: Any, serialize_func=None):
    """
    Tekil item yanıt döndür.
    
    Çıktı Örneği:
        {
            "success": true,
            "data": {...}
        }
    """
    # Item'ı serialize et
    serialized_item = item
    if serialize_func:
        serialized_item = serialize_func(item)
    
    response = {
        'success': True,
        'data': serialized_item
    }
    
    return jsonify(response), 200


def created_response(item: Any, serialize_func=None):
    """
    Yeni oluşturulan item yanıt döndür (201 Created).
    """
    # Item'ı serialize et
    serialized_item = item
    if serialize_func:
        serialized_item = serialize_func(item)
    
    response = {
        'success': True,
        'data': serialized_item,
        'message': 'Kayıt başarıyla oluşturuldu'
    }
    
    logger.info(f"Resource created: {type(item).__name__}")
    
    return jsonify(response), 201


def deleted_response(item_id: int, item_type: str = 'Kayıt'):
    """
    Silinen item için yanıt döndür.
    
    Çıktı Örneği:
        {
            "success": true,
            "message": "Kayıt başarıyla silindi"
        }
    """
    response = {
        'success': True,
        'message': f'{item_type} başarıyla silindi',
        'data': {'id': item_id}
    }
    
    logger.info(f"{item_type} deleted: ID={item_id}")
    
    return jsonify(response), 200


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMON ERROR RESPONSES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def not_found_response(resource: str = 'Kaynak', resource_id: Optional[Any] = None):
    """Kaynak bulunamadı (404)."""
    message = f'{resource} bulunamadı'
    if resource_id:
        message += f' (ID: {resource_id})'
    
    return error_response(message, 'NOT_FOUND', 404)


def bad_request_response(message: str, details: Optional[Dict] = None):
    """Kötü istek (400)."""
    return error_response(message, 'BAD_REQUEST', 400, details)


def unauthorized_response(message: str = 'Yetkilendirme gerekli'):
    """Yetkilendirme hatası (401)."""
    return error_response(message, 'UNAUTHORIZED', 401)


def forbidden_response(message: str = 'Bu operasyon yapma izni yok'):
    """Yasak (403)."""
    return error_response(message, 'FORBIDDEN', 403)


def conflict_response(message: str, code: str = 'CONFLICT'):
    """Çakışma (409) - örn: duplicate entry."""
    return error_response(message, code, 409)


def internal_error_response(message: str = 'Sunucu hatası'):
    """Sunucu hatası (500)."""
    logger.error(f"Internal Server Error: {message}")
    return error_response(message, 'INTERNAL_ERROR', 500)


def too_many_requests_response():
    """Rate limit hatası (429)."""
    return error_response(
        'Çok fazla istek gönderdiniz. Lütfen daha sonra tekrar deneyiniz.',
        'RATE_LIMIT_EXCEEDED',
        429
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SERIALIZERS - Model'den dict'e çevir
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def musteri_to_dict(musteri):
    """Musteri model'ini dict'e çevir."""
    if not musteri:
        return None
    return {
        'id': musteri.id,
        'unvan': musteri.unvan,
        'vergi_no': musteri.vergi_no,
        'vergi_dairesi': getattr(musteri, 'vergi_dairesi', None),
        'email': musteri.email,
        'telefon': musteri.telefon,
        'adres': musteri.adres,
        'tip': getattr(musteri, 'tip', None),
        'aktif': getattr(musteri, 'aktif', None),
        'olusturma_tarihi': _isoformat_or_none(getattr(musteri, 'olusturma_tarihi', None)),
    }


def urun_to_dict(urun):
    """Urun model'ini dict'e çevir."""
    if not urun:
        return None
    return {
        'id': urun.id,
        'ad': urun.ad,
        'kod': urun.kod,
        'birim': urun.birim,
        'alis_fiyat': _decimal_or_none(getattr(urun, 'alis_fiyat', None)),
        'satis_fiyat': _decimal_or_none(getattr(urun, 'satis_fiyat', None)),
        'stok_miktari': _decimal_or_none(getattr(urun, 'stok_miktari', None)),
        'kdv_orani': getattr(urun, 'kdv_orani', None),
        'aciklama': getattr(urun, 'aciklama', None),
        'aktif': getattr(urun, 'aktif', None),
        'olusturma_tarihi': _isoformat_or_none(getattr(urun, 'olusturma_tarihi', None)),
    }


def fatura_to_dict(fatura):
    """Fatura model'ini dict'e çevir (kalemler ile)."""
    if not fatura:
        return None
    kalemler = []
    if hasattr(fatura, 'kalemler') and fatura.kalemler:
        for k in fatura.kalemler:
            kalemler.append({
                'id': k.id,
                'urun_id': getattr(k, 'urun_id', None),
                'miktar': _decimal_or_none(getattr(k, 'miktar', None)),
                'birim_fiyat': _decimal_or_none(getattr(k, 'birim_fiyat', None)),
                'kdv_orani': getattr(k, 'kdv_orani', None),
                'indirim_orani': getattr(k, 'indirim_orani', None),
                'toplam': _decimal_or_none(getattr(k, 'toplam', None)),
                'kdv_tutar': _decimal_or_none(getattr(k, 'kdv_tutar', None)),
            })

    # Determine related partner id
    partner_id = None
    for attr in ('tedarikci_id', 'musteri_id', 'firma_id'):
        if hasattr(fatura, attr):
            partner_id = getattr(fatura, attr)
            break

    musteri_adi = getattr(getattr(fatura, 'musteri', None), 'unvan', None)
    tedarikci_adi = getattr(getattr(fatura, 'tedarikci', None), 'unvan', None)
    firma_adi = getattr(getattr(fatura, 'firma', None), 'unvan', None)

    result = {
        'id': fatura.id,
        'fatura_no': fatura.fatura_no,
        'fatura_tarihi': _isoformat_or_none(getattr(fatura, 'fatura_tarihi', None)),
        'vade_tarihi': _isoformat_or_none(getattr(fatura, 'vade_tarihi', None)),
        'tedarikci_id': getattr(fatura, 'tedarikci_id', None),
        'musteri_id': getattr(fatura, 'musteri_id', partner_id),
        'firma_id': getattr(fatura, 'firma_id', None),
        'partner_id': partner_id,
        'musteri_adi': musteri_adi,
        'tedarikci_adi': tedarikci_adi,
        'firma_adi': firma_adi,
        'cari_adi': musteri_adi or tedarikci_adi or firma_adi,
        'iade_turu': getattr(fatura, 'iade_turu', None),
        'iade_nedeni': getattr(fatura, 'iade_nedeni', None),
        'ara_toplam': _decimal_or_none(getattr(fatura, 'ara_toplam', None)),
        'kdv_toplam': _decimal_or_none(getattr(fatura, 'kdv_toplam', None)),
        'indirim_toplam': _decimal_or_none(getattr(fatura, 'indirim_toplam', None)),
        'genel_toplam': _decimal_or_none(getattr(fatura, 'genel_toplam', None)),
        'kalemler': kalemler,
        'notlar': getattr(fatura, 'notlar', None),
        'olusturma_tarihi': _isoformat_or_none(getattr(fatura, 'olusturma_tarihi', None)),
    }

    return result


def _isoformat_or_none(dt):
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def _decimal_or_none(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except Exception:
        return None
