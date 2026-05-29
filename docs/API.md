# API

Bu doküman, depodaki mevcut REST API durumunu özetler.

## Genel

- Baz yol: `/api`
- Sürüm baz yolu: `/api/v1`
- Healthcheck: `/api/health`
- Auth: `/api/v1/auth/*`

## Authentication

JWT tabanlı kimlik doğrulama kullanılır.

Login örneği:

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Password123!"}'
```

Yanıt `access_token` ve `refresh_token` döndürür. Korunan endpoint'ler için:

```bash
-H "Authorization: Bearer <access_token>"
```

## Endpointler

| Method | URL | Auth | Açıklama |
|---|---|---:|---|
| GET | `/api/health` | Hayır | DB bağlantısı ve uygulama sürümü |
| GET | `/api/config/firebase` | Hayır | Firebase config okumak için |
| GET | `/api/v1/musteriler` | Hayır | Müşteri listesi |
| GET | `/api/v1/musteriler/<id>` | Hayır | Müşteri detayı |
| POST | `/api/v1/musteriler` | Evet | Müşteri oluştur |
| PUT | `/api/v1/musteriler/<id>` | Evet | Müşteri güncelle |
| DELETE | `/api/v1/musteriler/<id>` | Evet | Müşteri soft delete |
| GET | `/api/v1/urunler` | Hayır | Ürün listesi |
| GET | `/api/v1/urunler/<id>` | Hayır | Ürün detayı |
| POST | `/api/v1/urunler` | Evet | Ürün oluştur |
| PUT | `/api/v1/urunler/<id>` | Evet | Ürün güncelle |
| DELETE | `/api/v1/urunler/<id>` | Evet | Ürün soft delete |
| GET | `/api/v1/faturalar/ozet` | Hayır | Fatura özetleri |
| GET | `/api/v1/faturalar/alis` | Hayır | Alış faturaları |
| POST | `/api/v1/faturalar/alis` | Evet | Alış faturası oluştur |
| DELETE | `/api/v1/faturalar/alis/<id>` | Evet | Alış faturası soft delete |
| GET | `/api/v1/faturalar/satis` | Hayır | Satış faturaları |
| POST | `/api/v1/faturalar/satis` | Evet | Satış faturası oluştur |
| DELETE | `/api/v1/faturalar/satis/<id>` | Evet | Satış faturası soft delete |
| GET | `/api/v1/faturalar/iade` | Hayır | İade faturaları |
| POST | `/api/v1/faturalar/iade` | Evet | İade faturası oluştur |
| DELETE | `/api/v1/faturalar/iade/<id>` | Evet | İade faturası soft delete |
| POST | `/api/v1/auth/refresh` | Refresh token | Yeni access token |
| GET | `/api/v1/auth/me` | Evet | Aktif kullanıcı bilgisi |
| POST | `/api/v1/auth/logout` | Evet | Token blocklist’e ekle |
| POST | `/api/v1/auth/register` | Admin önerilir | Kullanıcı oluştur |

## Stok Etkisi

| İşlem | Stok |
|---|---:|
| Alış faturası oluştur | Artar |
| Satış faturası oluştur | Azalır |
| Satış faturası sil | Artar |
| Alış faturası sil | Azalır |
| İade faturası, `satis_iade` | Artar |
| İade faturası, `alis_iade` | Azalır |

## KDV Kuralları

Geçerli KDV oranları: `0, 1, 8, 10, 18, 20`

Fatura indirimi, KDV matrahını düşürür.

## Hata Kodları

| Kod | Anlam |
|---|---|
| `NOT_FOUND` | Kayıt bulunamadı |
| `BAD_REQUEST` | Geçersiz istek |
| `VALIDATION_ERROR` | Girdi doğrulama hatası |
| `DUPLICATE_ENTRY` | Çift kayıt |
| `BUSINESS_RULE_VIOLATION` | İş kuralı ihlali |
| `RATE_LIMIT_EXCEEDED` | Rate limit aşıldı |
| `UNAUTHORIZED` | Kimlik doğrulama eksik/hatalı |
| `FORBIDDEN` | Yetki yok |

## cURL Örnekleri

Müşteri listesi:

```bash
curl http://localhost:5000/api/v1/musteriler
```

Satış faturası oluşturma:

```bash
curl -X POST http://localhost:5000/api/v1/faturalar/satis \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "musteri_id": 1,
    "fatura_no": "S-001",
    "fatura_tarihi": "2026-05-01",
    "indirim_toplam": "0",
    "kalemler": [
      {
        "urun_id": 1,
        "miktar": "2",
        "birim_fiyat": "100.00",
        "kdv_orani": 18,
        "indirim_orani": 0
      }
    ]
  }'
```

Sağlık kontrolü:

```bash
curl http://localhost:5000/api/health
```
