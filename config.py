import os
import secrets
from datetime import timedelta

class Config:
    """Uygulama yapılandırma ayarları"""
    
    # ━━━ SECRET_KEY Güvenliği ━━━
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Üretimde hata, geliştirmede random oluştur
        if os.environ.get('FLASK_ENV') == 'production':
            raise ValueError(
                '❌ CRITICAL: SECRET_KEY ortam değişkeni set edilmemiş!\n'
                'Üretim ortamında SECRET_KEY zorunludur.\n'
                '.env dosyasını kontrol edin: SECRET_KEY=<32-char-key>'
            )
        # Geliştirmede random oluştur (her restart'ta değişir ama sorun değil)
        SECRET_KEY = secrets.token_hex(32)
    
    # ━━━ Veritabanı Ayarları ━━━
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASEDIR, 'instance', 'muhasebe.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 1800)),
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 5)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 10)),
    }
    
    # ━━━ Session Güvenliği ━━━
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True  # JavaScript erişimini engelle
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF koruması
    PERMANENT_SESSION_LIFETIME = 86400  # 24 saat
    
    # ━━━ Uygulama Ayarları ━━━
    APP_NAME = 'eMuhasebe Pro'
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    MAX_ITEMS_PER_PAGE = int(os.environ.get('MAX_ITEMS_PER_PAGE', 100))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    JWT_ACCESS_TOKEN_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_MINUTES', 60))
    JWT_REFRESH_TOKEN_DAYS = int(os.environ.get('JWT_REFRESH_TOKEN_DAYS', 30))
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    STRICT_TRANSPORT_SECURITY = os.environ.get('STRICT_TRANSPORT_SECURITY', 'True') == 'True'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=JWT_ACCESS_TOKEN_MINUTES)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=JWT_REFRESH_TOKEN_DAYS)

    # ━━━ JWT Cookie Ayarları ━━━
    # JWT hem cookie hem header'dan kabul ediyor. Cookie tercih edilir (XSS dirençli);
    # header geri uyumluluk için.
    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_COOKIE_SECURE = os.environ.get('JWT_COOKIE_SECURE', 'False') == 'True'
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_ACCESS_COOKIE_NAME = 'emuhasebe_access_token'
    JWT_REFRESH_COOKIE_NAME = 'emuhasebe_refresh_token'
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_REFRESH_COOKIE_PATH = '/api/v1/auth/refresh'
    # CSRF korumasını şimdilik kapalı (header'lı testler için). Browser-only
    # flow'da etkinleştirmek istersen True yapıp X-CSRF-TOKEN header'ı gönder.
    JWT_COOKIE_CSRF_PROTECT = False

    # ━━━ Rate Limit ━━━
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_STRATEGY = os.environ.get('RATELIMIT_STRATEGY', 'fixed-window')

    # ━━━ JWT Blocklist ━━━
    JWT_BLOCKLIST_REDIS_URL = os.environ.get('JWT_BLOCKLIST_REDIS_URL')
    
    # ━━━ Para Birimi ━━━
    CURRENCY = 'TL'
    CURRENCY_SYMBOL = '₺'


class DevelopmentConfig(Config):
    """Geliştirme ortamı ayarları"""
    DEBUG = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    TESTING = False


class ProductionConfig(Config):
    """Üretim ortamı ayarları"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS only
    PREFERRED_URL_SCHEME = 'https'
    
    # Üretimde zorunlu validasyonlar
    def __init__(self):
        """Üretim başlangıcında güvenlik kontrolleri"""
        super().__init__()
        
        # DATABASE_URL kontrol et
        if not os.environ.get('DATABASE_URL'):
            raise ValueError(
                '❌ CRITICAL: DATABASE_URL ortam değişkeni set edilmemiş!\n'
                'Üretim ortamında DATABASE_URL zorunludur.'
            )

        if str(self.RATELIMIT_STORAGE_URI).startswith('memory://'):
            raise ValueError('❌ CRITICAL: RATELIMIT_STORAGE_URI memory:// olamaz, üretimde Redis zorunludur')

        jwt_blocklist_url = self.JWT_BLOCKLIST_REDIS_URL or ''
        rl_uri = str(self.RATELIMIT_STORAGE_URI)
        if not jwt_blocklist_url and (rl_uri.startswith('redis://') or rl_uri.startswith('rediss://')):
            jwt_blocklist_url = self.RATELIMIT_STORAGE_URI
            self.JWT_BLOCKLIST_REDIS_URL = jwt_blocklist_url

        blk = str(jwt_blocklist_url)
        if not (blk.startswith('redis://') or blk.startswith('rediss://')):
            raise ValueError('❌ CRITICAL: JWT_BLOCKLIST_REDIS_URL Redis olmalı')
        
        print('✅ Production config: Tüm güvenlik kontrolleri geçildi')


class TestingConfig(Config):
    """Test ortamı ayarları"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key-for-testing-only'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
