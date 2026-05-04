"""
API v1 Endpoint Tests
Pagination, Validation, Response Format testleri
"""
import pytest
import json
from decimal import Decimal


def _register_and_login(client, email='api-v1@example.com', password='Password123!'):
    register_payload = {
        'username': 'api-v1',
        'email': email,
        'password': password,
        'role': 'admin'
    }
    client.post('/api/v1/auth/register', data=json.dumps(register_payload), content_type='application/json')
    login_response = client.post(
        '/api/v1/auth/login',
        data=json.dumps({'email': email, 'password': password}),
        content_type='application/json'
    )
    assert login_response.status_code == 200
    login_data = json.loads(login_response.data)
    return login_data['access_token']


@pytest.fixture
def auth_headers(client):
    access_token = _register_and_login(client)
    return {'Authorization': f'Bearer {access_token}'}


class TestMusteriEndpoints:
    """Müşteri endpoint testleri."""

    def test_list_musteriler_empty(self, client):
        """Boş müşteri listesi."""
        response = client.get('/api/v1/musteriler')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data'] == []
        assert data['pagination']['total'] == 0

    def test_list_musteriler_with_pagination(self, client, multiple_musteriler):
        """Sayfalama ile müşteri listesi."""
        # Sayfa 1
        response = client.get('/api/v1/musteriler?page=1&per_page=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['total'] == 25
        assert data['pagination']['total_pages'] == 3
        assert data['pagination']['has_next'] is True
        assert data['pagination']['has_prev'] is False
        
        # Sayfa 2
        response = client.get('/api/v1/musteriler?page=2&per_page=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 10
        assert data['pagination']['page'] == 2
        assert data['pagination']['has_prev'] is True
        
        # Son sayfa
        response = client.get('/api/v1/musteriler?page=3&per_page=10')
        data = json.loads(response.data)
        assert len(data['data']) == 5
        assert data['pagination']['has_next'] is False

    def test_list_musteriler_with_search(self, client, sample_musteri):
        """Arama ile müşteri listesi."""
        response = client.get('/api/v1/musteriler?q=Test')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 1
        assert data['data'][0]['unvan'] == 'Test Müşteri Ltd'
        assert 'search' in data
        assert data['search']['keyword'] == 'Test'
        assert data['search']['count'] == 1

    def test_search_no_results(self, client, sample_musteri):
        """Arama sonucu bulunamadığında."""
        response = client.get('/api/v1/musteriler?q=NonExistent')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 0
        assert data['search']['count'] == 0

    def test_get_musteri_detail(self, client, sample_musteri):
        """Müşteri detayı."""
        response = client.get(f'/api/v1/musteriler/{sample_musteri.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == sample_musteri.id
        assert data['data']['unvan'] == sample_musteri.unvan

    def test_get_musteri_not_found(self, client):
        """Müşteri bulunamadığında."""
        response = client.get('/api/v1/musteriler/999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'NOT_FOUND'

    def test_create_musteri_valid(self, client, auth_headers):
        """Geçerli müşteri oluştur."""
        payload = {
            'unvan': 'Yeni Müşteri',
            'vergi_no': '9876543210',
            'email': 'yeni@example.com'
        }
        response = client.post(
            '/api/v1/musteriler',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['unvan'] == 'Yeni Müşteri'
        assert data['message'] == 'Kayıt başarıyla oluşturuldu'

    def test_create_musteri_validation_error(self, client, auth_headers):
        """Validation hatası ile müşteri oluştururken."""
        payload = {
            'unvan': '',  # Boş - hatır
            'vergi_no': 'ABC',  # Geçersiz format
        }
        response = client.post(
            '/api/v1/musteriler',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert len(data['error']['details']['validation_errors']) > 0

    def test_create_musteri_duplicate_vergi_no(self, client, sample_musteri, auth_headers):
        """Çift vergi numarasında müşteri oluşturma."""
        payload = {
            'unvan': 'Başka Müşteri',
            'vergi_no': sample_musteri.vergi_no  # Aynısı
        }
        response = client.post(
            '/api/v1/musteriler',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error']['code'] == 'DUPLICATE_ENTRY'

    def test_update_musteri(self, client, sample_musteri, auth_headers):
        """Müşteri güncelle."""
        payload = {
            'unvan': 'Güncellenmiş Ad',
            'email': 'newemail@example.com'
        }
        response = client.put(
            f'/api/v1/musteriler/{sample_musteri.id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['unvan'] == 'Güncellenmiş Ad'
        assert data['data']['email'] == 'newemail@example.com'

    def test_update_musteri_partial(self, client, sample_musteri, auth_headers):
        """Müşteri kısmı güncelle."""
        payload = {'unvan': 'Yalnız Ad Değişti'}
        response = client.put(
            f'/api/v1/musteriler/{sample_musteri.id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        # Değiştirilmeyenleri gözle
        assert data['data']['email'] == sample_musteri.email

    def test_delete_musteri(self, client, sample_musteri, auth_headers):
        """Müşteri sil."""
        response = client.delete(f'/api/v1/musteriler/{sample_musteri.id}', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Müşteri başarıyla silindi'
        
        # Silindikten sonra kontrol et (soft delete)
        response = client.get(f'/api/v1/musteriler/{sample_musteri.id}')
        # Soft delete implementasyonuna gore 200 veya 404 olabilir
        assert response.status_code in (200, 404)


class TestUrunEndpoints:
    """Ürün endpoint testleri."""

    def test_list_urunler_empty(self, client):
        """Boş ürün listesi."""
        response = client.get('/api/v1/urunler')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 0

    def test_list_urunler_with_pagination(self, client, multiple_urunler):
        """Sayfalama ile ürün listesi."""
        response = client.get('/api/v1/urunler?page=1&per_page=15')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 15
        assert data['pagination']['total'] == 25

    def test_get_urun_detail(self, client, sample_urun):
        """Ürün detayı."""
        response = client.get(f'/api/v1/urunler/{sample_urun.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['kod'] == 'TEST-001'

    def test_create_urun_valid(self, client, auth_headers):
        """Geçerli ürün oluştur."""
        payload = {
            'ad': 'Yeni Ürün',
            'kod': 'YEN-001',
            'alis_fiyat': 100.00,
            'satis_fiyat': 150.00,
            'stok_miktari': 50
        }
        response = client.post(
            '/api/v1/urunler',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['ad'] == 'Yeni Ürün'

    def test_create_urun_negative_price(self, client, auth_headers):
        """Negatif fiyatla ürün oluşturma."""
        payload = {
            'ad': 'Bad Ürün',
            'kod': 'BAD-001',
            'alis_fiyat': -100.00,  # Negatif - hatı
            'satis_fiyat': 150.00,
        }
        response = client.post(
            '/api/v1/urunler',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_urun(self, client, sample_urun, auth_headers):
        """Ürün güncelle."""
        payload = {
            'satis_fiyat': 200.00
        }
        response = client.put(
            f'/api/v1/urunler/{sample_urun.id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['satis_fiyat'] == 200.0


class TestPaginationParams:
    """Sayfalama parametreleri testleri."""

    def test_invalid_page_number(self, client, multiple_musteriler):
        """Geçersiz sayfa numarası."""
        response = client.get('/api/v1/musteriler?page=abc&per_page=20')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_page_exceeds_max(self, client, sample_musteri):
        """Sayfa max değerini aşarsa."""
        response = client.get('/api/v1/musteriler?page=999&per_page=20')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 0
        assert data['pagination']['page'] == 999

    def test_per_page_max_limit(self, client, multiple_musteriler):
        """per_page max 100'de sınırlandırılacak."""
        response = client.get('/api/v1/musteriler?page=1&per_page=1000')
        data = json.loads(response.data)
        assert data['pagination']['per_page'] == 100

    def test_default_pagination_values(self, client, multiple_musteriler):
        """Default sayfalama değerleri."""
        response = client.get('/api/v1/musteriler')
        data = json.loads(response.data)
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 20


class TestResponseFormat:
    """Response format testleri."""

    def test_success_response_structure(self, client, sample_musteri):
        """Başarılı response yapısı."""
        response = client.get(f'/api/v1/musteriler/{sample_musteri.id}')
        data = json.loads(response.data)
        
        # Gerekli alanları kontrol et
        assert 'success' in data
        assert 'data' in data
        assert data['success'] is True

    def test_error_response_structure(self, client):
        """Error response yapısı."""
        response = client.get('/api/v1/musteriler/999')
        data = json.loads(response.data)
        
        assert 'success' in data
        assert 'error' in data
        assert data['success'] is False
        assert 'message' in data['error']
        assert 'code' in data['error']

    def test_paginated_response_structure(self, client, multiple_musteriler):
        """Paginated response yapısı."""
        response = client.get('/api/v1/musteriler?page=1&per_page=10')
        data = json.loads(response.data)
        
        assert 'pagination' in data
        required_fields = ['page', 'per_page', 'total', 'total_pages', 'has_next', 'has_prev']
        for field in required_fields:
            assert field in data['pagination']
