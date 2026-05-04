"""
Test Yapılandırması - pytest fixture'ları
Her test in-memory SQLite veritabanı kullanır.
"""
import pytest
from decimal import Decimal
import os


# Test öncesi environment variables ayarla
os.environ['FLASK_ENV'] = 'testing'

from app import create_app
from app.models import db as _db, Musteri, Urun, AlisFatura, SatisFatura, IadeFatura


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key-please-use-32-bytes!!'
    JWT_SECRET_KEY = SECRET_KEY
    SESSION_COOKIE_SECURE = False  # Test'te HTTPS'e gerek yok
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    PROPAGATE_EXCEPTIONS = True


@pytest.fixture
def app():
    """Test Flask uygulaması oluşturur."""
    try:
        # Test config'den app oluştur
        test_app = create_app('testing')
        test_app.config.from_object(TestConfig)
    except KeyError:
        # Eğer 'testing' config yoksa 'default' kullan ve override et
        test_app = create_app('default')
        test_app.config.from_object(TestConfig)

    # Rate limiter'ı test'te varsayılan olarak deaktive et
    if os.environ.get('ENABLE_RATELIMIT_TESTS') == '1':
        test_app.config['RATELIMIT_ENABLED'] = True
    else:
        test_app.config['RATELIMIT_ENABLED'] = False
    test_app.config['WTF_CSRF_ENABLED'] = False

    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()


@pytest.fixture
def client(app):
    """Flask test client'ı döndürür."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Veritabanı oturumunu döndürür."""
    with app.app_context():
        yield _db


@pytest.fixture
def sample_musteri(db):
    """Test müşteri oluşturur."""
    musteri = Musteri(
        unvan='Test Müşteri Ltd',
        vergi_no='1234567890',
        email='test@example.com',
        telefon='+90 532 123 4567',
        adres='Test Adres, İstanbul'
    )
    db.session.add(musteri)
    db.session.commit()
    return musteri


@pytest.fixture
def sample_urun(db):
    """Test ürün oluşturur."""
    urun = Urun(
        ad='Test Ürün',
        kod='TEST-001',
        birim='Adet',
        alis_fiyat=Decimal('100.00'),
        satis_fiyat=Decimal('150.00'),
        stok_miktari=100
    )
    db.session.add(urun)
    db.session.commit()
    return urun


@pytest.fixture
def multiple_musteriler(db):
    """Birden fazla müşteri oluşturur."""
    musteriler = [
        Musteri(unvan=f'Müşteri {i}', vergi_no=f'{1000000000+i}', email=f'test{i}@example.com')
        for i in range(1, 26)  # 25 müşteri
    ]
    db.session.add_all(musteriler)
    db.session.commit()
    return musteriler


@pytest.fixture
def multiple_urunler(db):
    """Birden fazla ürün oluşturur."""
    urunler = [
        Urun(
            ad=f'Ürün {i}',
            kod=f'URN-{i:03d}',
            alis_fiyat=Decimal(100 + i),
            satis_fiyat=Decimal(150 + i),
            stok_miktari=100 + i
        )
        for i in range(1, 26)
    ]
    db.session.add_all(urunler)
    db.session.commit()
    return urunler


@pytest.fixture
def invalid_data():
    """Geçersiz test verisi."""
    return {
        'unvan': '',  # Boş
        'vergi_no': 'ABC',  # Sadece rakam olmalı
        'email': 'not-an-email',  # Geçersiz format
    }

