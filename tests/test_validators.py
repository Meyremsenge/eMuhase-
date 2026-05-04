"""
Validator Tests
Pydantic input validation testleri
"""
import pytest
from pydantic import ValidationError
from app.validators import (
    MusteriCreateRequest, MusteriUpdateRequest,
    UrunCreateRequest, UrunUpdateRequest,
    PaginationParams
)


class TestMusteriValidators:
    """Müşteri validator testleri."""

    def test_musteri_create_valid(self):
        """Geçerli müşteri request."""
        data = {
            'unvan': 'ABC Ltd',
            'vergi_no': '1234567890',
            'email': 'test@example.com'
        }
        request = MusteriCreateRequest(**data)
        assert request.unvan == 'ABC Ltd'
        assert request.vergi_no == '1234567890'

    def test_musteri_create_unvan_required(self):
        """Ünvan zorunlu."""
        data = {'vergi_no': '1234567890'}
        with pytest.raises(ValidationError) as exc_info:
            MusteriCreateRequest(**data)
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('unvan',) for e in errors)

    def test_musteri_create_unvan_min_length(self):
        """Ünvan min 2 karakter."""
        data = {'unvan': 'A'}  # 1 karakter
        with pytest.raises(ValidationError) as exc_info:
            MusteriCreateRequest(**data)
        errors = exc_info.value.errors()
        assert any('at least 2 characters' in str(e) for e in errors)

    def test_musteri_create_unvan_max_length(self):
        """Ünvan max 255 karakter."""
        data = {'unvan': 'A' * 300}
        with pytest.raises(ValidationError):
            MusteriCreateRequest(**data)

    def test_musteri_create_vergi_no_format(self):
        """Vergi numarası sadece rakam."""
        data = {
            'unvan': 'Test',
            'vergi_no': 'ABC123'  # Harf içeriyor
        }
        with pytest.raises(ValidationError):
            MusteriCreateRequest(**data)

    def test_musteri_create_vergi_no_length(self):
        """Vergi numarası 10-11 karakter."""
        # Çok kısa
        with pytest.raises(ValidationError):
            MusteriCreateRequest(unvan='Test', vergi_no='123')
        
        # Çok uzun
        with pytest.raises(ValidationError):
            MusteriCreateRequest(unvan='Test', vergi_no='123456789012')

    def test_musteri_create_email_valid(self):
        """Geçerli email."""
        data = {
            'unvan': 'Test',
            'email': 'valid@example.com'
        }
        request = MusteriCreateRequest(**data)
        assert request.email == 'valid@example.com'

    def test_musteri_create_email_invalid(self):
        """Geçersiz email."""
        data = {
            'unvan': 'Test',
            'email': 'not-an-email'
        }
        with pytest.raises(ValidationError):
            MusteriCreateRequest(**data)

    def test_musteri_update_all_optional(self):
        """Update'te tüm alanlar opsiyonel."""
        data = {}
        request = MusteriUpdateRequest(**data)
        assert request.unvan is None
        assert request.email is None

    def test_musteri_update_partial(self):
        """Update'te kısmi alan."""
        data = {'unvan': 'Updated Name'}
        request = MusteriUpdateRequest(**data)
        assert request.unvan == 'Updated Name'
        assert request.email is None


class TestUrunValidators:
    """Ürün validator testleri."""

    def test_urun_create_valid(self):
        """Geçerli ürün request."""
        data = {
            'ad': 'Laptop',
            'kod': 'LT-001',
            'alis_fiyat': 100.00,
            'satis_fiyat': 150.00,
            'stok_miktari': 50
        }
        request = UrunCreateRequest(**data)
        assert request.ad == 'Laptop'
        assert request.alis_fiyat == 100.00

    def test_urun_create_ad_required(self):
        """Ürün adı zorunlu."""
        data = {
            'alis_fiyat': 100.00,
            'satis_fiyat': 150.00
        }
        with pytest.raises(ValidationError):
            UrunCreateRequest(**data)

    def test_urun_create_prices_required(self):
        """Fiyatlar zorunlu."""
        data = {
            'ad': 'Test',
            'alis_fiyat': 100.00
            # satis_fiyat eksik
        }
        with pytest.raises(ValidationError):
            UrunCreateRequest(**data)

    def test_urun_create_negative_price(self):
        """Negatif fiyat."""
        data = {
            'ad': 'Test',
            'alis_fiyat': -100.00,
            'satis_fiyat': 150.00
        }
        with pytest.raises(ValidationError):
            UrunCreateRequest(**data)

    def test_urun_create_zero_price(self):
        """Sıfır fiyat (gt=0 constraint)."""
        data = {
            'ad': 'Test',
            'alis_fiyat': 0.00,
            'satis_fiyat': 150.00
        }
        with pytest.raises(ValidationError):
            UrunCreateRequest(**data)

    def test_urun_create_string_prices(self):
        """String'ten Decimal'e çevrim."""
        data = {
            'ad': 'Test',
            'alis_fiyat': '100.00',
            'satis_fiyat': '150.00'
        }
        request = UrunCreateRequest(**data)
        assert request.alis_fiyat == 100.00

    def test_urun_create_negative_stock(self):
        """Negatif stok (ge=0 constraint)."""
        data = {
            'ad': 'Test',
            'alis_fiyat': 100.00,
            'satis_fiyat': 150.00,
            'stok_miktari': -5
        }
        with pytest.raises(ValidationError):
            UrunCreateRequest(**data)

    def test_urun_update_optional_prices(self):
        """Update'te fiyatlar opsiyonel."""
        data = {'ad': 'Updated'}
        request = UrunUpdateRequest(**data)
        assert request.ad == 'Updated'
        assert request.alis_fiyat is None


class TestPaginationValidators:
    """Sayfalama validator testleri."""

    def test_pagination_defaults(self):
        """Default değerler."""
        from app.validators import validate_pagination_params
        page, per_page, error = validate_pagination_params({})
        assert page == 1
        assert per_page == 20
        assert error is None

    def test_pagination_valid_params(self):
        """Geçerli parametreler."""
        from app.validators import validate_pagination_params
        class MockArgs:
            def get(self, key, default=None):
                if key == 'page':
                    return '2'
                elif key == 'per_page':
                    return '50'
                return default
        
        mock_args = MockArgs()
        page, per_page, error = validate_pagination_params(mock_args)
        assert page == 2
        assert per_page == 50
        assert error is None

    def test_pagination_page_min(self):
        """Sayfa minimum 1."""
        from app.validators import validate_pagination_params
        class MockArgs:
            def get(self, key, default=None):
                return '0' if key == 'page' else default
        
        page, _, _ = validate_pagination_params(MockArgs())
        assert page == 1  # 0'dan 1'e ayarlandı

    def test_pagination_per_page_max(self):
        """per_page maximum 100."""
        from app.validators import validate_pagination_params
        class MockArgs:
            def get(self, key, default=None):
                return '1000' if key == 'per_page' else default
        
        _, per_page, _ = validate_pagination_params(MockArgs())
        assert per_page == 100  # 1000'den 100'e ayarlandı

    def test_pagination_invalid_input(self):
        """Geçersiz input."""
        from app.validators import validate_pagination_params
        class MockArgs:
            def get(self, key, default=None):
                return 'invalid' if key == 'page' else default
        
        _, _, error = validate_pagination_params(MockArgs())
        assert error is not None


class TestValidatorEdgeCases:
    """Validator edge case testleri."""

    def test_musteri_unvan_whitespace(self):
        """Ünvan whitespace'lerle."""
        data = {'unvan': '  Test Company  '}
        # Trim edilmeli veya hata
        try:
            request = MusteriCreateRequest(**data)
            # Whitespace'ler kalmışsa test edilir
            assert request.unvan.strip() == 'Test Company'
        except ValidationError:
            pass

    def test_urun_decimal_precision(self):
        """Ürün fiyat precision."""
        from decimal import Decimal
        data = {
            'ad': 'Test',
            'alis_fiyat': Decimal('99.99'),  # 2 decimal places (standard for currency)
            'satis_fiyat': Decimal('150.50')
        }
        request = UrunCreateRequest(**data)
        # Decimal precision kontrol
        assert request.alis_fiyat == Decimal('99.99')

    def test_urun_very_large_stock(self):
        """Çok büyük stok."""
        data = {
            'ad': 'Test',
            'alis_fiyat': 100.00,
            'satis_fiyat': 150.00,
            'stok_miktari': 999999999
        }
        request = UrunCreateRequest(**data)
        assert request.stok_miktari == 999999999

    def test_musteri_special_characters(self):
        """Özel karakterler."""
        data = {
            'unvan': 'Test & Co. Ltd™',
            'email': 'test+tag@example.com'
        }
        try:
            request = MusteriCreateRequest(**data)
            # Özel karakter kabul edildi
            assert '&' in request.unvan
            assert '+' in request.email
        except ValidationError:
            pass  # Reddedilebilir
