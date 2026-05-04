"""
REST API endpoint birim testleri.
Flask test client ile API isteklerini test eder.
"""
import json


class TestMusterilerAPI:
    """Müşteri API endpoint testleri."""

    def test_list_empty(self, client):
        res = client.get('/api/musteriler')
        assert res.status_code == 200
        assert res.get_json() == []

    def test_create(self, client):
        res = client.post('/api/musteriler',
                          data=json.dumps({'unvan': 'API Firma', 'vergi_no': '1234567890'}),
                          content_type='application/json')
        assert res.status_code == 201
        data = res.get_json()
        assert data['unvan'] == 'API Firma'
        assert data['id'] is not None

    def test_create_missing_unvan(self, client):
        res = client.post('/api/musteriler',
                          data=json.dumps({'vergi_no': '0000000000'}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_detail(self, client):
        # Önce oluştur
        create_res = client.post('/api/musteriler',
                                 data=json.dumps({'unvan': 'Detay Firma', 'vergi_no': '1111111111'}),
                                 content_type='application/json')
        musteri_id = create_res.get_json()['id']
        # Detay
        res = client.get(f'/api/musteriler/{musteri_id}')
        assert res.status_code == 200
        assert res.get_json()['unvan'] == 'Detay Firma'

    def test_detail_not_found(self, client):
        res = client.get('/api/musteriler/9999')
        assert res.status_code == 404

    def test_update(self, client):
        create_res = client.post('/api/musteriler',
                                 data=json.dumps({'unvan': 'Eski', 'vergi_no': '2222222222'}),
                                 content_type='application/json')
        musteri_id = create_res.get_json()['id']
        res = client.put(f'/api/musteriler/{musteri_id}',
                         data=json.dumps({'unvan': 'Yeni'}),
                         content_type='application/json')
        assert res.status_code == 200
        assert res.get_json()['unvan'] == 'Yeni'

    def test_delete(self, client):
        create_res = client.post('/api/musteriler',
                                 data=json.dumps({'unvan': 'Silinecek', 'vergi_no': '3333333333'}),
                                 content_type='application/json')
        musteri_id = create_res.get_json()['id']
        res = client.delete(f'/api/musteriler/{musteri_id}')
        assert res.status_code == 200

    def test_search(self, client):
        client.post('/api/musteriler',
                    data=json.dumps({'unvan': 'Deniz Ticaret', 'vergi_no': '4444444444'}),
                    content_type='application/json')
        client.post('/api/musteriler',
                    data=json.dumps({'unvan': 'Kara Lojistik', 'vergi_no': '5555555555'}),
                    content_type='application/json')
        res = client.get('/api/musteriler?q=deniz')
        data = res.get_json()
        assert len(data) == 1
        assert data[0]['unvan'] == 'Deniz Ticaret'


class TestUrunlerAPI:
    """Ürün API endpoint testleri."""

    def test_list_empty(self, client):
        res = client.get('/api/urunler')
        assert res.status_code == 200
        assert res.get_json() == []

    def test_create(self, client):
        res = client.post('/api/urunler',
                          data=json.dumps({'kod': 'URN01', 'ad': 'Test Ürün', 'satis_fiyat': 100}),
                          content_type='application/json')
        assert res.status_code == 201
        assert res.get_json()['kod'] == 'URN01'

    def test_create_missing_fields(self, client):
        res = client.post('/api/urunler',
                          data=json.dumps({'ad': 'Eksik Kod'}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_delete(self, client):
        create_res = client.post('/api/urunler',
                                 data=json.dumps({'kod': 'DEL01', 'ad': 'Silinecek'}),
                                 content_type='application/json')
        urun_id = create_res.get_json()['id']
        res = client.delete(f'/api/urunler/{urun_id}')
        assert res.status_code == 200


class TestFaturalarAPI:
    """Fatura API endpoint testleri."""

    def test_ozet(self, client):
        res = client.get('/api/faturalar/ozet')
        assert res.status_code == 200
        data = res.get_json()
        assert 'alis_count' in data

    def test_alis_list(self, client):
        res = client.get('/api/faturalar/alis')
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)

    def test_satis_list(self, client):
        res = client.get('/api/faturalar/satis')
        assert res.status_code == 200

    def test_iade_list(self, client):
        res = client.get('/api/faturalar/iade')
        assert res.status_code == 200


class TestOpenApiSpec:
    def test_openapi_spec(self, client):
        res = client.get('/api/openapi.json')
        assert res.status_code == 200
        data = res.get_json()
        assert data['openapi'] == '3.0.3'
        assert '/health' in data['paths']
        assert '/v1/auth/login' in data['paths']
        assert '/v1/faturalar/satis' in data['paths']
