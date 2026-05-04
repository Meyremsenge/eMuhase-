"""
eMuhasebe Pro - API Blueprint
REST API endpoint'leri — ORM + Repository + Service katmanlı mimarisi kullanır.
Frontend (Firebase) ile paralel çalışır; backend tarafında da tam CRUD desteği sağlar.
"""
import os
from sqlalchemy import text
from flask import Blueprint, jsonify, request
from app.models import db
from app.services.musteri_service import MusteriService
from app.services.urun_service import UrunService
from app.services.fatura_service import FaturaService
from app import limiter

api_bp = Blueprint('api', __name__)


def _build_openapi_spec():
    return {
        'openapi': '3.0.3',
        'info': {
            'title': 'eMuhasebe Pro API',
            'version': os.environ.get('APP_VERSION', '1.0.0'),
            'description': 'eMuhasebe Pro için mevcut REST API yüzeyi',
        },
        'servers': [
            {'url': '/api'}
        ],
        'paths': {
            '/health': {
                'get': {
                    'summary': 'Healthcheck',
                    'responses': {
                        '200': {'description': 'Uygulama ve veritabanı sağlıklı'},
                        '503': {'description': 'Veritabanı erişilemedi'},
                    },
                }
            },
            '/config/firebase': {
                'get': {
                    'summary': 'Firebase configuration',
                    'responses': {
                        '200': {'description': 'Firebase yapılandırması'},
                    },
                }
            },
            '/v1/auth/login': {
                'post': {
                    'summary': 'Login',
                    'responses': {
                        '200': {'description': 'Access ve refresh token'},
                        '401': {'description': 'Geçersiz kimlik bilgileri'},
                    },
                }
            },
            '/v1/auth/register': {
                'post': {
                    'summary': 'Register',
                    'responses': {
                        '201': {'description': 'Kullanıcı oluşturuldu'},
                        '400': {'description': 'Geçersiz rol veya eksik alan'},
                        '403': {'description': 'Yetki yok'},
                    },
                }
            },
            '/v1/auth/me': {
                'get': {
                    'summary': 'Current user',
                    'responses': {
                        '200': {'description': 'Aktif kullanıcı'},
                    },
                }
            },
            '/v1/auth/refresh': {
                'post': {
                    'summary': 'Refresh token',
                    'responses': {
                        '200': {'description': 'Yeni access token'},
                    },
                }
            },
            '/v1/auth/logout': {
                'post': {
                    'summary': 'Logout',
                    'responses': {
                        '200': {'description': "Token blocklist'e eklendi"},
                    },
                }
            },
            '/v1/musteriler': {
                'get': {'summary': 'Müşteri listesi'},
                'post': {'summary': 'Müşteri oluşturma'},
            },
            '/v1/urunler': {
                'get': {'summary': 'Ürün listesi'},
                'post': {'summary': 'Ürün oluşturma'},
            },
            '/v1/faturalar/ozet': {
                'get': {'summary': 'Fatura özeti'},
            },
            '/v1/faturalar/alis': {
                'get': {'summary': 'Alış faturaları'},
                'post': {'summary': 'Alış faturası oluşturma'},
            },
            '/v1/faturalar/satis': {
                'get': {'summary': 'Satış faturaları'},
                'post': {'summary': 'Satış faturası oluşturma'},
            },
            '/v1/faturalar/iade': {
                'get': {'summary': 'İade faturaları'},
                'post': {'summary': 'İade faturası oluşturma'},
            },
        },
    }


@api_bp.route('/health', methods=['GET'])
def healthcheck():
    try:
        db.session.execute(text('SELECT 1'))
        db_status = 'ok'
        status_code = 200
        overall = 'ok'
    except Exception:
        db_status = 'error'
        status_code = 503
        overall = 'degraded'

    return jsonify({
        'status': overall,
        'db': db_status,
        'version': os.environ.get('APP_VERSION', '1.0.0')
    }), status_code


@api_bp.route('/openapi.json', methods=['GET'])
def openapi_spec():
    return jsonify(_build_openapi_spec())


# ══════════════════════ KONFIGÜRASYON ══════════════════════

@api_bp.route('/config/firebase', methods=['GET'])
def get_firebase_config():
    """
    Frontend'in Firebase config'ini güvenli şekilde al.
    Config ortam değişkenlerinden yüklenir, code'da hardcode edilmez.
    """
    
    # Eğer Firebase devre dışıysa null döndür (localStorage modunda çalışacak)
    if os.environ.get('FIREBASE_DISABLED') == 'true':
        return jsonify({'config': None})
    
    # Firebase config'i env var'lardan yükle
    firebase_config = {
        'apiKey': os.environ.get('VITE_FIREBASE_API_KEY'),
        'authDomain': os.environ.get('VITE_FIREBASE_AUTH_DOMAIN'),
        'databaseURL': os.environ.get('VITE_FIREBASE_DATABASE_URL'),
        'projectId': os.environ.get('VITE_FIREBASE_PROJECT_ID'),
        'storageBucket': os.environ.get('VITE_FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': os.environ.get('VITE_FIREBASE_MESSAGING_SENDER_ID'),
        'appId': os.environ.get('VITE_FIREBASE_APP_ID'),
    }
    
    # Zorunlu alanlar kontrol et
    required_fields = ['apiKey', 'authDomain', 'databaseURL', 'projectId']
    missing_fields = [f for f in required_fields if not firebase_config.get(f)]
    
    if missing_fields:
        # Eksik config varsa, demo modunda çalış
        return jsonify({
            'config': None,
            'warning': f'Firebase config eksik: {", ".join(missing_fields)}'
        })
    
    return jsonify({'config': firebase_config})


# ══════════════════════ MÜŞTERİLER ══════════════════════

@api_bp.route('/musteriler', methods=['GET'])
@limiter.limit("30 per minute")
def musteriler_list():
    """Tüm müşterileri listeler. ?q= ile arama destekler."""
    keyword = request.args.get('q', '').strip()
    if keyword:
        musteriler = MusteriService.search(keyword)
    else:
        musteriler = MusteriService.get_all()
    return jsonify([_musteri_to_dict(m) for m in musteriler])


@api_bp.route('/musteriler/<int:musteri_id>', methods=['GET'])
@limiter.limit("60 per minute")
def musteriler_detail(musteri_id):
    """Tekil müşteri detayı."""
    musteri = MusteriService.get_by_id(musteri_id)
    if musteri is None:
        return jsonify({'error': 'Müşteri bulunamadı'}), 404
    return jsonify(_musteri_to_dict(musteri))


@api_bp.route('/musteriler', methods=['POST'])
@limiter.limit("10 per minute")
def musteriler_create():
    """Yeni müşteri oluşturur."""
    data = request.get_json()
    if not data or not data.get('unvan'):
        return jsonify({'error': 'Ünvan zorunludur'}), 400
    try:
        musteri = MusteriService.create(data)
        return jsonify(_musteri_to_dict(musteri)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/musteriler/<int:musteri_id>', methods=['PUT'])
@limiter.limit("20 per minute")
def musteriler_update(musteri_id):
    """Müşteriyi günceller."""
    data = request.get_json()
    try:
        musteri = MusteriService.update(musteri_id, data)
        return jsonify(_musteri_to_dict(musteri))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/musteriler/<int:musteri_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
def musteriler_delete(musteri_id):
    """Müşteriyi siler."""
    try:
        MusteriService.delete(musteri_id)
        return jsonify({'message': 'Müşteri silindi'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# ══════════════════════ ÜRÜNLER ══════════════════════

@api_bp.route('/urunler', methods=['GET'])
@limiter.limit("30 per minute")
def urunler_list():
    """Tüm ürünleri listeler. ?q= ile arama destekler."""
    keyword = request.args.get('q', '').strip()
    if keyword:
        urunler = UrunService.search(keyword)
    else:
        urunler = UrunService.get_all()
    return jsonify([_urun_to_dict(u) for u in urunler])


@api_bp.route('/urunler/<int:urun_id>', methods=['GET'])
@limiter.limit("60 per minute")
def urunler_detail(urun_id):
    """Tekil ürün detayı."""
    urun = UrunService.get_by_id(urun_id)
    if urun is None:
        return jsonify({'error': 'Ürün bulunamadı'}), 404
    return jsonify(_urun_to_dict(urun))


@api_bp.route('/urunler', methods=['POST'])
@limiter.limit("10 per minute")
def urunler_create():
    """Yeni ürün oluşturur."""
    data = request.get_json()
    if not data or not data.get('kod') or not data.get('ad'):
        return jsonify({'error': 'Kod ve ad zorunludur'}), 400
    try:
        urun = UrunService.create(data)
        return jsonify(_urun_to_dict(urun)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/urunler/<int:urun_id>', methods=['PUT'])
@limiter.limit("20 per minute")
def urunler_update(urun_id):
    """Ürünü günceller."""
    data = request.get_json()
    try:
        urun = UrunService.update(urun_id, data)
        return jsonify(_urun_to_dict(urun))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/urunler/<int:urun_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
def urunler_delete(urun_id):
    """Ürünü siler."""
    try:
        UrunService.delete(urun_id)
        return jsonify({'message': 'Ürün silindi'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# ══════════════════════ FATURALAR ══════════════════════

@api_bp.route('/faturalar/ozet', methods=['GET'])
@limiter.limit("60 per minute")
def faturalar_summary():
    """Dashboard için fatura özet istatistikleri."""
    return jsonify(FaturaService.get_summary())


@api_bp.route('/faturalar/alis', methods=['GET'])
@limiter.limit("30 per minute")
def alis_list():
    """Tüm alış faturalarını listeler."""
    faturalar = FaturaService.get_alis_all()
    return jsonify([_fatura_to_dict(f) for f in faturalar])


@api_bp.route('/faturalar/satis', methods=['GET'])
@limiter.limit("30 per minute")
def satis_list():
    """Tüm satış faturalarını listeler."""
    faturalar = FaturaService.get_satis_all()
    return jsonify([_fatura_to_dict(f) for f in faturalar])


@api_bp.route('/faturalar/iade', methods=['GET'])
@limiter.limit("30 per minute")
def iade_list():
    """Tüm iade faturalarını listeler."""
    faturalar = FaturaService.get_iade_all()
    return jsonify([_fatura_to_dict(f) for f in faturalar])


# ══════════════════════ HELPERS ══════════════════════

def _musteri_to_dict(m):
    return {
        'id': m.id,
        'unvan': m.unvan,
        'vergi_no': m.vergi_no,
        'vergi_dairesi': m.vergi_dairesi,
        'adres': m.adres,
        'telefon': m.telefon,
        'email': m.email,
        'tip': m.tip,
        'aktif': m.aktif,
    }


def _urun_to_dict(u):
    return {
        'id': u.id,
        'kod': u.kod,
        'ad': u.ad,
        'aciklama': u.aciklama,
        'birim': u.birim,
        'alis_fiyat': u.alis_fiyat,
        'satis_fiyat': u.satis_fiyat,
        'kdv_orani': u.kdv_orani,
        'stok_miktari': u.stok_miktari,
        'aktif': u.aktif,
    }


def _fatura_to_dict(f):
    return {
        'id': f.id,
        'fatura_no': f.fatura_no,
        'fatura_tarihi': str(f.fatura_tarihi) if f.fatura_tarihi else None,
        'ara_toplam': f.ara_toplam,
        'kdv_toplam': f.kdv_toplam,
        'genel_toplam': f.genel_toplam,
        'durum': f.durum,
        'aciklama': f.aciklama,
    }
