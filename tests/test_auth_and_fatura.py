import json
from decimal import Decimal

import pytest

from app.models import db, Musteri, Urun, SatisFatura


ALLOWED_KDV = [0, 1, 8, 10, 18, 20]


def _json(response):
    return json.loads(response.data)


def _register_and_login(client, email='admin@example.com', password='Password123!'):
    register_payload = {
        'username': 'admin',
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
    login_data = _json(login_response)
    return login_data['access_token'], login_data['refresh_token']


def _auth_headers(access_token):
    return {'Authorization': f'Bearer {access_token}'}


def _create_sample_sales_invoice(client, access_token, musteri_id, urun_id, fatura_no='S-001', miktar=2, birim_fiyat='100.00', kdv_orani=18):
    payload = {
        'musteri_id': musteri_id,
        'fatura_no': fatura_no,
        'fatura_tarihi': '2026-05-01',
        'vade_tarihi': '2026-05-15',
        'indirim_toplam': '0',
        'kalemler': [
            {
                'urun_id': urun_id,
                'miktar': str(miktar),
                'birim_fiyat': birim_fiyat,
                'kdv_orani': kdv_orani,
                'indirim_orani': 0,
            }
        ],
        'aciklama': 'Test satış faturası'
    }
    return client.post('/api/v1/faturalar/satis', data=json.dumps(payload), content_type='application/json', headers=_auth_headers(access_token))


class TestAuth:
    def test_public_get_is_open(self, client, sample_musteri):
        response = client.get(f'/api/v1/musteriler/{sample_musteri.id}')
        assert response.status_code == 200

    def test_register_rejects_invalid_role(self, client):
        response = client.post(
            '/api/v1/auth/register',
            data=json.dumps({
                'username': 'bad-role',
                'email': 'bad-role@example.com',
                'password': 'Password123!',
                'role': 'superadmin',
            }),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_register_and_login(self, client):
        access_token, refresh_token = _register_and_login(client)
        assert access_token
        assert refresh_token

    def test_me_endpoint(self, client):
        access_token, _ = _register_and_login(client, email='me@example.com')
        response = client.get('/api/v1/auth/me', headers=_auth_headers(access_token))
        assert response.status_code == 200
        data = _json(response)
        assert data['email'] == 'me@example.com'

    def test_refresh_endpoint(self, client):
        access_token, refresh_token = _register_and_login(client, email='refresh@example.com')
        response = client.post('/api/v1/auth/refresh', headers={'Authorization': f'Bearer {refresh_token}'})
        assert response.status_code == 200
        data = _json(response)
        assert 'access_token' in data

    def test_logout_blocks_token(self, client):
        access_token, _ = _register_and_login(client, email='logout@example.com')
        response = client.post('/api/v1/auth/logout', headers=_auth_headers(access_token))
        assert response.status_code == 200
        blocked = client.get('/api/v1/auth/me', headers=_auth_headers(access_token))
        assert blocked.status_code in (401, 422)


class TestMusteriEmailUnique:
    def test_create_duplicate_email_is_rejected(self, client, sample_musteri):
        access_token, _ = _register_and_login(client, email='dup-create@example.com')
        payload = {
            'unvan': 'Yeni Müşteri',
            'vergi_no': '9876543210',
            'email': sample_musteri.email,
        }
        response = client.post('/api/v1/musteriler', data=json.dumps(payload), content_type='application/json', headers=_auth_headers(access_token))
        assert response.status_code == 409

    def test_update_duplicate_email_is_rejected(self, client, sample_musteri, db):
        other = Musteri(unvan='Other', vergi_no='1111111111', email='other@example.com')
        db.session.add(other)
        db.session.commit()
        access_token, _ = _register_and_login(client, email='dup-update@example.com')
        payload = {'email': other.email}
        response = client.put(f'/api/v1/musteriler/{sample_musteri.id}', data=json.dumps(payload), content_type='application/json', headers=_auth_headers(access_token))
        assert response.status_code == 409


class TestKdvValidasyon:
    @pytest.mark.parametrize('kdv_orani', ALLOWED_KDV)
    def test_allowed_kdv_rates_are_accepted(self, client, sample_musteri, sample_urun, kdv_orani):
        access_token, _ = _register_and_login(client, email=f'kdv-{kdv_orani}@example.com')
        response = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no=f'S-{kdv_orani}', kdv_orani=kdv_orani)
        assert response.status_code == 201

    def test_invalid_kdv_rate_is_rejected(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='bad-kdv@example.com')
        response = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-BAD-KDV', kdv_orani=7)
        assert response.status_code == 422


class TestFaturaCrud:
    def test_create_list_delete_sales_invoice(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='crud@example.com')
        create_response = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-CRUD-1')
        assert create_response.status_code == 201
        created = _json(create_response)['data']
        list_response = client.get('/api/v1/faturalar/satis')
        assert list_response.status_code == 200
        listed = _json(list_response)['data']
        assert any(item['fatura_no'] == 'S-CRUD-1' for item in listed)
        delete_response = client.delete(f"/api/v1/faturalar/satis/{created['id']}", headers=_auth_headers(access_token))
        assert delete_response.status_code == 200

    def test_duplicate_invoice_number_is_rejected(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='dup-invoice@example.com')
        first = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-DUP-1')
        assert first.status_code == 201
        second = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-DUP-1')
        assert second.status_code == 409

    def test_future_invoice_date_is_rejected(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='future@example.com')
        payload = {
            'musteri_id': sample_musteri.id,
            'fatura_no': 'S-FUTURE-1',
            'fatura_tarihi': '2999-01-01',
            'kalemler': [
                {'urun_id': sample_urun.id, 'miktar': '1', 'birim_fiyat': '100', 'kdv_orani': 18, 'indirim_orani': 0}
            ],
        }
        response = client.post('/api/v1/faturalar/satis', data=json.dumps(payload), content_type='application/json', headers=_auth_headers(access_token))
        assert response.status_code == 422

    def test_create_purchase_and_return_invoices(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='mixed@example.com')
        alis_payload = {
            'tedarikci_id': sample_musteri.id,
            'fatura_no': 'A-CRUD-1',
            'fatura_tarihi': '2026-05-01',
            'vade_tarihi': '2026-05-15',
            'indirim_toplam': '0',
            'kalemler': [
                {'urun_id': sample_urun.id, 'miktar': '3', 'birim_fiyat': '50.00', 'kdv_orani': 18, 'indirim_orani': 0}
            ]
        }
        alis_response = client.post('/api/v1/faturalar/alis', data=json.dumps(alis_payload), content_type='application/json', headers=_auth_headers(access_token))
        assert alis_response.status_code == 201

        iade_payload = {
            'firma_id': sample_musteri.id,
            'iade_turu': 'satis_iade',
            'referans_fatura_no': 'S-REF-1',
            'fatura_no': 'I-CRUD-1',
            'fatura_tarihi': '2026-05-02',
            'kalemler': [
                {'urun_id': sample_urun.id, 'miktar': '1', 'birim_fiyat': '100.00', 'kdv_orani': 18}
            ]
        }
        iade_response = client.post('/api/v1/faturalar/iade', data=json.dumps(iade_payload), content_type='application/json', headers=_auth_headers(access_token))
        assert iade_response.status_code == 201


class TestStokHareketi:
    def test_sales_invoice_decreases_stock(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='stock1@example.com')
        before = Decimal(str(sample_urun.stok_miktari))
        response = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-STOCK-1', miktar=2)
        assert response.status_code == 201
        db.session.refresh(sample_urun)
        assert Decimal(str(sample_urun.stok_miktari)) == before - Decimal('2')

    def test_purchase_invoice_increases_stock(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='stock2@example.com')
        before = Decimal(str(sample_urun.stok_miktari))
        payload = {
            'tedarikci_id': sample_musteri.id,
            'fatura_no': 'A-STOCK-1',
            'fatura_tarihi': '2026-05-01',
            'vade_tarihi': '2026-05-15',
            'indirim_toplam': '0',
            'kalemler': [
                {'urun_id': sample_urun.id, 'miktar': '4', 'birim_fiyat': '50.00', 'kdv_orani': 18, 'indirim_orani': 0}
            ]
        }
        response = client.post('/api/v1/faturalar/alis', data=json.dumps(payload), content_type='application/json', headers=_auth_headers(access_token))
        assert response.status_code == 201
        db.session.refresh(sample_urun)
        assert Decimal(str(sample_urun.stok_miktari)) == before + Decimal('4')

    def test_insufficient_stock_is_rejected(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='stock3@example.com')
        payload = {
            'musteri_id': sample_musteri.id,
            'fatura_no': 'S-STOCK-BAD',
            'fatura_tarihi': '2026-05-01',
            'kalemler': [
                {'urun_id': sample_urun.id, 'miktar': '9999', 'birim_fiyat': '100.00', 'kdv_orani': 18, 'indirim_orani': 0}
            ]
        }
        response = client.post('/api/v1/faturalar/satis', data=json.dumps(payload), content_type='application/json', headers=_auth_headers(access_token))
        assert response.status_code == 409

    def test_delete_sales_invoice_restores_stock(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='stock4@example.com')
        before = Decimal(str(sample_urun.stok_miktari))
        create_response = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-STOCK-DEL', miktar=3)
        assert create_response.status_code == 201
        invoice_id = _json(create_response)['data']['id']
        db.session.refresh(sample_urun)
        mid = Decimal(str(sample_urun.stok_miktari))
        assert mid == before - Decimal('3')
        delete_response = client.delete(f'/api/v1/faturalar/satis/{invoice_id}', headers=_auth_headers(access_token))
        assert delete_response.status_code == 200
        db.session.refresh(sample_urun)
        assert Decimal(str(sample_urun.stok_miktari)) == before

    def test_return_invoice_adjusts_stock(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='stock5@example.com')
        before = Decimal(str(sample_urun.stok_miktari))
        payload = {
            'firma_id': sample_musteri.id,
            'iade_turu': 'satis_iade',
            'referans_fatura_no': 'S-REF-STOCK',
            'fatura_no': 'I-STOCK-1',
            'fatura_tarihi': '2026-05-02',
            'kalemler': [
                {'urun_id': sample_urun.id, 'miktar': '2', 'birim_fiyat': '100.00', 'kdv_orani': 18}
            ]
        }
        response = client.post('/api/v1/faturalar/iade', data=json.dumps(payload), content_type='application/json', headers=_auth_headers(access_token))
        assert response.status_code == 201
        db.session.refresh(sample_urun)
        assert Decimal(str(sample_urun.stok_miktari)) == before + Decimal('2')


class TestSoftDelete:
    def test_deleted_sales_invoice_is_hidden_from_list(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='soft1@example.com')
        create_response = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-SOFT-1')
        assert create_response.status_code == 201
        invoice_id = _json(create_response)['data']['id']
        delete_response = client.delete(f'/api/v1/faturalar/satis/{invoice_id}', headers=_auth_headers(access_token))
        assert delete_response.status_code == 200
        list_response = client.get('/api/v1/faturalar/satis')
        data = _json(list_response)
        assert all(item['id'] != invoice_id for item in data['data'])

    def test_deleted_sales_invoice_returns_404(self, client, sample_musteri, sample_urun):
        access_token, _ = _register_and_login(client, email='soft2@example.com')
        create_response = _create_sample_sales_invoice(client, access_token, sample_musteri.id, sample_urun.id, fatura_no='S-SOFT-2')
        invoice_id = _json(create_response)['data']['id']
        client.delete(f'/api/v1/faturalar/satis/{invoice_id}', headers=_auth_headers(access_token))
        response = client.get(f'/api/v1/faturalar/satis/{invoice_id}')
        assert response.status_code == 404
