"""
eMuhasebe Pro - API Blueprint
REST API endpoint'leri — ORM + Repository + Service katmanlı mimarisi kullanır.
Frontend (Firebase) ile paralel çalışır; backend tarafında da tam CRUD desteği sağlar.
"""
import os
import json
import time
import urllib.request
import urllib.error
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
        'apiKey': os.environ.get('FIREBASE_API_KEY') or os.environ.get('VITE_FIREBASE_API_KEY'),
        'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN') or os.environ.get('VITE_FIREBASE_AUTH_DOMAIN'),
        'databaseURL': os.environ.get('FIREBASE_DATABASE_URL') or os.environ.get('VITE_FIREBASE_DATABASE_URL'),
        'projectId': os.environ.get('FIREBASE_PROJECT_ID') or os.environ.get('VITE_FIREBASE_PROJECT_ID'),
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET') or os.environ.get('VITE_FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': (
            os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
            or os.environ.get('VITE_FIREBASE_MESSAGING_SENDER_ID')
        ),
        'appId': os.environ.get('FIREBASE_APP_ID') or os.environ.get('VITE_FIREBASE_APP_ID'),
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


# ══════════════════════ AI ANALYSIS (proxy) ══════════════════════

@api_bp.route('/ai/ping', methods=['POST', 'GET'])
@limiter.limit("30 per minute")
def ai_ping():
    """
    AI anahtarını DOĞRULA (token harcamadan).

    Eğer anahtar AIzaSy ile başlıyorsa resmi Google Gemini API'ye,
    aksi takdirde OpenRouter'a doğrulama isteği gönderir.
    """
    client_key = (request.headers.get('X-OpenRouter-Key') or '').strip()
    api_key = client_key or os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({'ok': False, 'error': 'Anahtar yok'}), 400

    if api_key.startswith('AIzaSy'):
        # Google Gemini API Anahtar Doğrulaması
        req = urllib.request.Request(
            f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}',
            method='GET',
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode('utf-8') or '{}')
                models = payload.get('models') or []
                if models:
                    return jsonify({
                        'ok': True,
                        'label': 'Google Gemini API',
                        'usage': 0,
                        'limit': None,
                        'is_free_tier': True,
                    })
                return jsonify({'ok': False, 'error': 'Model listesi alınamadı'}), 200
        except urllib.error.HTTPError as e:
            return jsonify({'ok': False, 'error': f'Geçersiz Gemini anahtarı ({e.code})'}), 200
        except Exception as e:
            return jsonify({'ok': False, 'error': f'Gemini API\'ye bağlanılamadı: {str(e)}'}), 200

    # Varsayılan OpenRouter Doğrulaması
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/auth/key',
        headers={
            'Authorization': f'Bearer {api_key}',
            'X-Title': 'eMuhasebe Pro',
        },
        method='GET',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode('utf-8') or '{}')
            data = payload.get('data') or {}
            return jsonify({
                'ok': True,
                'label': data.get('label'),
                'usage': data.get('usage'),
                'limit': data.get('limit'),
                'is_free_tier': data.get('is_free_tier'),
            })
    except urllib.error.HTTPError as e:
        return jsonify({'ok': False, 'error': f'Geçersiz anahtar ({e.code})'}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': f'Bağlanılamadı: {str(e)}'}), 200


@api_bp.route('/ai/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def ai_analyze():
    """
    Yapay Zeka Analiz Endpoint'i.

    Anahtar öncelik sırası:
      1) İstemcinin gönderdiği `X-OpenRouter-Key` header'ı (UI'daki AI Kurulum modal)
      2) Backend `GEMINI_API_KEY` veya `OPENROUTER_API_KEY` env değişkeni

    Model öncelik sırası:
      1) İstek body'sindeki `model` alanı
      2) İstemcinin `X-OpenRouter-Model` header'ı
      3) Backend `OPENROUTER_MODEL` env değişkeni
      4) Varsayılan: google/gemini-2.5-flash:free (veya native için gemini-1.5-flash)
    """
    client_key = (request.headers.get('X-OpenRouter-Key') or '').strip()
    api_key = client_key or os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI servisi yapılandırılmamış. AI Kurulum ekranından anahtar ekleyin.'}), 503

    data = request.get_json(silent=True) or {}
    prompt = (data.get('prompt') or data.get('summary') or '').strip()
    if not prompt:
        return jsonify({'error': 'prompt zorunludur'}), 400

    # Varsayılan: gemini-2.0-flash — ücretsiz katmanda en cömert kota
    # (~1500 istek/gün, 15 istek/dk). 2.5-flash çok daha düşük limitli
    # (~250/gün) olduğu için az kullanımda bile çabuk doluyordu.
    model = (data.get('model')
             or request.headers.get('X-OpenRouter-Model')
             or os.environ.get('OPENROUTER_MODEL')
             or 'google/gemini-2.0-flash-exp:free')

    # 1) Google Gemini NATIVE API Çağrısı
    if api_key.startswith('AIzaSy'):
        gemini_model = 'gemini-2.0-flash'  # varsayılan
        ml = model.lower()
        if 'gemini-2.5' in ml:
            gemini_model = 'gemini-2.5-flash'
        elif 'gemini-1.5' in ml:
            gemini_model = 'gemini-1.5-flash'
        elif 'gemini-2.0' in ml:
            gemini_model = 'gemini-2.0-flash'

        # Kota sıfır/aşılmış (RESOURCE_EXHAUSTED) durumunda sırayla denenecek
        # alternatifler — bazı bölgelerde belirli modellerin ücretsiz kotası 0.
        adaylar = [gemini_model]
        for alt in ('gemini-2.5-flash-lite', 'gemini-2.0-flash-lite',
                    'gemini-1.5-flash-8b', 'gemini-1.5-flash'):
            if alt not in adaylar:
                adaylar.append(alt)

        body = json.dumps({'contents': [{'parts': [{'text': prompt}]}]}).encode('utf-8')

        def _gemini_call(m):
            """Tek model çağrısı. (text, None) ya da (None, (code, status, msg)) döner.
               500/503 geçici hatalarda kısa beklemeyle 3 kez dener."""
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}'
            for deneme in range(3):
                req = urllib.request.Request(
                    url, data=body,
                    headers={'Content-Type': 'application/json'}, method='POST')
                try:
                    with urllib.request.urlopen(req, timeout=90) as resp:
                        payload = json.loads(resp.read().decode('utf-8'))
                        return payload['candidates'][0]['content']['parts'][0]['text'], None
                except urllib.error.HTTPError as e:
                    try:
                        eb = e.read().decode('utf-8')
                    except Exception:
                        eb = ''
                    st, msg = '', ''
                    try:
                        ge = (json.loads(eb) or {}).get('error', {})
                        st, msg = ge.get('status', ''), ge.get('message', '')
                    except Exception:
                        pass
                    if e.code in (500, 503) and deneme < 2:
                        time.sleep(2 * (deneme + 1))
                        continue
                    return None, (e.code, st, msg)
                except Exception as e:
                    if deneme < 2:
                        time.sleep(2 * (deneme + 1))
                        continue
                    return None, (0, '', str(e))
            return None, (503, '', 'Yanıt alınamadı')

        son = None
        for m in adaylar:
            text_out, err = _gemini_call(m)
            if text_out is not None:
                return jsonify({'text': text_out, 'model': m})
            code, st, msg = err
            son = (m, code, st, msg)
            detail = f'{m} | {st} {msg}'.strip()[:400]
            # Kota / model-yok dışındaki hatalarda hemen dur (gerçek sebep bu)
            if code == 429 and st == 'RESOURCE_EXHAUSTED':
                continue          # sıradaki modeli dene
            if code == 404:
                continue          # model yoksa sıradakini dene
            if code in (401, 403):
                return jsonify({'error': (
                    'Gemini API anahtarı geçersiz, yetkisiz veya bu model/bölge için '
                    'erişim yok. AI Kurulum ekranından anahtarı kontrol edin.'
                ), 'detail': detail}), 401
            if code == 400:
                if st == 'FAILED_PRECONDITION' and 'location' in (msg or '').lower():
                    continue      # konum kısıtlaması — sıradaki modeli dene
                return jsonify({'error': f'Gemini isteği reddedildi: {msg or st or "400"}',
                                'detail': detail}), 400
            if code == 429:       # 429 ama RESOURCE_EXHAUSTED değil
                return jsonify({'error': f'Gemini 429: {msg or st}', 'detail': detail}), 429
            if code == 503:
                return jsonify({'error': (
                    'Gemini modeli şu an çok yoğun (geçici). Birkaç dakika sonra deneyin.'
                ), 'detail': detail}), 503
            if code == 0:
                return jsonify({'error': f'Gemini API\'ye ulaşılamadı: {msg}'}), 502
            return jsonify({'error': f'Gemini API hatası: {code}', 'detail': detail}), 502

        # Tüm modeller başarısız → konum kısıtlaması veya kota sorunu
        m, code, st, msg = son or ('', 0, '', '')
        detail = f'{m} | {st} {msg}'.strip()[:400]
        if st == 'FAILED_PRECONDITION' and 'location' in (msg or '').lower():
            return jsonify({'error': (
                'Google Gemini API bu sunucu konumundan erişilemiyor '
                '(User location is not supported). Çözüm: openrouter.ai adresinden '
                'ücretsiz bir anahtar alıp AI Kurulum ekranına girin — '
                'uygulama OpenRouter ücretsiz modellerini otomatik kullanır.'
            ), 'detail': detail}), 400
        return jsonify({'error': (
            'Bu Gemini anahtarının ücretsiz kotası 0 (free tier bu bölge/hesap için '
            'kapalı). Çözüm: ya Google AI Studio\'da faturalandırma açın, ya da ÜCRETSİZ '
            'alternatif için openrouter.ai\'den bir anahtar alıp AI Kurulum ekranına girin '
            '— uygulama OpenRouter ücretsiz modellerini otomatik kullanır.'
        ), 'detail': detail}), 429

    # 2) OpenRouter API Çağrısı
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 2500,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'X-Title': 'eMuhasebe Pro',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            text_out = (payload.get('choices') or [{}])[0].get('message', {}).get('content', '')
            return jsonify({'text': text_out, 'model': model})
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
        except Exception:
            err_body = ''
        if e.code == 429:
            return jsonify({'error': (
                'AI servisi kotası/hız limiti aşıldı. Birkaç dakika bekleyip tekrar '
                'deneyin veya AI Kurulum ekranından farklı bir anahtar/model seçin.'
            )}), 429
        if e.code in (401, 403):
            return jsonify({'error': (
                'AI API anahtarı geçersiz veya yetkisiz. '
                'AI Kurulum ekranından anahtarı kontrol edin.'
            )}), 401
        return jsonify({'error': f'AI servisi hata: {e.code}',
                        'detail': err_body[:300]}), 502
    except Exception as e:
        return jsonify({'error': f'AI servisine ulaşılamadı: {str(e)}'}), 502


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

def _iso(dt):
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def _num(v):
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


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
        'olusturma_tarihi': _iso(getattr(m, 'olusturma_tarihi', None)),
        'guncelleme_tarihi': _iso(getattr(m, 'guncelleme_tarihi', None)),
    }


def _urun_to_dict(u):
    return {
        'id': u.id,
        'kod': u.kod,
        'ad': u.ad,
        'aciklama': u.aciklama,
        'birim': u.birim,
        'alis_fiyat': _num(u.alis_fiyat),
        'satis_fiyat': _num(u.satis_fiyat),
        'kdv_orani': u.kdv_orani,
        'stok_miktari': _num(u.stok_miktari),
        'aktif': u.aktif,
        'olusturma_tarihi': _iso(getattr(u, 'olusturma_tarihi', None)),
        'guncelleme_tarihi': _iso(getattr(u, 'guncelleme_tarihi', None)),
    }


def _fatura_to_dict(f):
    return {
        'id': f.id,
        'fatura_no': f.fatura_no,
        'fatura_tarihi': _iso(getattr(f, 'fatura_tarihi', None)),
        'ara_toplam': _num(getattr(f, 'ara_toplam', None)),
        'kdv_toplam': _num(getattr(f, 'kdv_toplam', None)),
        'genel_toplam': _num(getattr(f, 'genel_toplam', None)),
        'durum': getattr(f, 'durum', None),
        'aciklama': getattr(f, 'aciklama', None),
    }
