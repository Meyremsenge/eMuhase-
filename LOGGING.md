# Logging & Audit Trail Sistemi Dokümantasyonu

**İŞ 3 - Logging & Audit Trail Sistemi Uygulaması**

Uygulamanın tüm önemli operasyonlarını, hataları ve audit trail kayıtlarını merkezi olarak yönetir.

---

## 📋 İçindekiler

1. [Logging Mimarisi](#logging-mimarisi)
2. [Kurulum ve Konfigürasyon](#kurulum-ve-konfigürasyon)
3. [Log Seviyeleri ve Örnekler](#log-seviyeleri-ve-örnekler)
4. [Audit Trail Integration](#audit-trail-integration)
5. [API Request/Response Logging](#api-requestresponse-logging)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Logging Mimarisi

### Katmanlar

```
┌─────────────────────────────────────┐
│      Flask Application (main)       │
│  (Request başlangıcı ve bitişi)     │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Middleware (middleware.py)        │
│  (Request/Response logging)         │
│  (Error handlers)                   │
│  (Audit context management)         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│     Service Layer                   │
│  (Business logic logging)           │
│  (Validation issues)                │
│  (Fatura calculations)              │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Repository Layer                 │
│  (Database operations)              │
│  (Query execution)                  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   SQLAlchemy ORM                    │
│  (SQL query logging - DEBUG)        │
│  (Connection pooling)               │
└─────────────────────────────────────┘
```

### Logging Bileşenleri

| Bileşen | Dosya | Sorumluluk |
|---------|-------|-----------|
| **Config** | `app/logging_config.py` | Logger kurulumu, handlers, formatters |
| **Middleware** | `app/middleware.py` | API request/response, audit context, error handling |
| **Service** | `musteri_service.py` vb. | Business logic operasyonları |
| **Repository** | `*_repository.py` | (Optional) Database operasyonları |

---

## Kurulum ve Konfigürasyon

### 1. Ortam Değişkenleri

**.env** dosyasında ayarlar:

```bash
# Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log dizini (app.log ve errors.log burada tutulur)
LOG_DIR=logs

# Log formatı (plain|json)
LOG_FORMAT=plain

# JSON log dosyası (opsiyonel)
LOG_JSON_FILE=logs/app.jsonl

# Flask ortamı
FLASK_ENV=development
```

### 2. Log Dizini Oluştur

```bash
mkdir -p logs
```

### 3. Logging Modules İçer

```python
# app/__init__.py
from app.logging_config import setup_logging
from app.middleware import log_request_response

logger = setup_logging(app)
```

### 4. Flask Uygulama Başlangıcı

```python
# run.py
if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
    # Logging başlatılır ve logs/app.log'a yazılır
```

---

## Log Seviyeleri ve Örnekler

### DEBUG (En Detaylı)

**Ne zaman kullan:** Geliştirme sırasında, metodun giriş/çıkışı

```python
logger.debug("MusteriService.get_all() çağrıldı")
logger.debug(f"Müşteri bulundu: ID={musteri_id}, Ünvan={result.unvan}")
```

**Çıktı:**
```
2026-03-26 14:23:45,123 - app.services.musteri_service - DEBUG - [musteri_service.py:15] - MusteriService.get_all() çağrıldı
```

### INFO (Normal İşlemler)

**Ne zaman kullan:** Başarılı operasyonlar, önemli olaylar

```python
logger.info(f"Müşteri oluşturuldu: ID={result.id}, Ünvan={result.unvan}")
logger.info(f"Müşteriler listelendi: 25 kayıt")
```

**Çıktı:**
```
2026-03-26 14:24:10,456 - app.services.musteri_service - INFO - [musteri_service.py:65] - Müşteri oluşturuldu: ID=5, Ünvan=ABC Ltd
```

### JSON Log Formatı

`LOG_FORMAT=json` set edilirse loglar JSON olarak yazılır.

Örnek:

```json
{"timestamp": "2026-03-26 14:24:10", "level": "INFO", "logger": "app.services.musteri_service", "request_id": "abc123", "message": "Müşteri oluşturuldu", "file": "musteri_service.py", "line": 65}
```

JSON loglarını ayrı bir dosyaya yazmak için `LOG_JSON_FILE` ayarlanır.

### WARNING (Uyarılar)

**Ne zaman kullan:** Beklenmedik durumlar, veri çakışmaları

```python
logger.warning(f"Müşteri bulunamadı: ID={musteri_id}")
logger.warning(f"Vergi no çakışması: {data['vergi_no']} zaten kayıtlı (ID: {existing.id})")
```

**Çıktı:**
```
2026-03-26 14:25:30,789 - app.services.musteri_service - WARNING - [musteri_service.py:35] - Vergi no çakışması: 1234567890 zaten kayıtlı (ID: 3)
```

### ERROR (Hatalar)

**Ne zaman kullan:** Operasyon başarısız oldu

```python
logger.error(f"Müşteri güncelleme hatası (ID: {musteri_id}): {str(e)}", exc_info=True)
```

**Çıktı (app.log):**
```
2026-03-26 14:26:45,234 - app.services.musteri_service - ERROR - [musteri_service.py:88] - Müşteri güncelleme hatası (ID: 5): Database connection failed
Traceback (most recent call last):
  File "app/services/musteri_service.py", line 85, in update
    result = MusteriRepository.update(musteri_id, **data)
  ...
```

**Çıktı (errors.log):**
```
(Aynı traceback errors.log'a yazılır)
```

### CRITICAL (Kritik Hatalar)

**Ne zaman kullan:** Uygulamanın çalışması riske giren durumlar

```python
logger.critical("Veritabanı bağlantısı kaybedildi - Uygulama durdurulmalı")
```

---

## Audit Trail Integration

### AuditLogContext Manager

Tüm veritabanı değişikliklerini otomatik olarak kaydeder:

```python
from app.middleware import AuditLogContext

with AuditLogContext('musteriler', 'UPDATE', kayit_id=5) as audit:
    # Veritabanı update operasyonu
    for key, new_value in data.items():
        old_value = getattr(musteri, key, None)
        if old_value != new_value:
            audit.add_change(key, old_value, new_value)
    
    result = MusteriRepository.update(musteri_id, **data)
    # Context exit: Audit kayıt yazılır
```

### Log Örneği

```
2026-03-26 14:27:00,100 - app.middleware - DEBUG - Audit'i START: UPDATE on musteriler (ID: 5) by user None
2026-03-26 14:27:00,105 - app.middleware - DEBUG -   Field 'unvan' changed: Old Corp. -> New Corp Inc
2026-03-26 14:27:00,110 - app.middleware - DEBUG -   Field 'vergi_no' changed: 1234567890 -> 0987654321
2026-03-26 14:27:00,115 - app.middleware - INFO - AUDIT SUCCESS: UPDATE on musteriler (ID: 5) | Changes: {'unvan': {'old': 'Old Corp.', 'new': 'New Corp Inc'}, 'vergi_no': {'old': '1234567890', 'new': '0987654321'}} | Duration: 25ms
```

### Audit Log Database Integration

AuditLog tablosu her değişikliği kaydetmek için trigger veya ORM hooks kullanabilir:

```python
# app/models.py - Event listener örneği (gelecekte implemente edilecek)
@event.listens_for(Musteri, 'before_update')
def receive_before_update(mapper, connection, target):
    # Eski değerleri yakala
    # AuditLog.log_change() çağrısı yap
    pass
```

---

## API Request/Response Logging

### Request Middleware

Her HTTP isteği otomatik olarak loglanır:

```
[2026-03-26 14:28:15.234567_192.168.1.100] GET /api/musteriler | IP: 192.168.1.100 | Content-Type: application/json | Data: {'search': 'abc'}
```

### Response Middleware

Yanıt otomatik olarak loglanır (durum koduna göre):

**Başarılı (200-299):**
```
[2026-03-26 14:28:15.234567_192.168.1.100] GET /api/musteriler -> 200 (145ms)
```

**Hatalar (400-599):**
```
[2026-03-26 14:28:16.456789_192.168.1.101] GET /api/musteriler/999 -> 404 (32ms)
```

### Sensitif Veri Maskeleme

Passwords, tokens, etc. otomatik olarak maskele edilir:

```python
# Gönderilen data:
{
    'unvan': 'ABC Ltd',
    'password': 'secret123',
    'api_key': 'sk-1234567890'
}

# Log edilir:
{
    'unvan': 'ABC Ltd',
    'password': '***',
    'api_key': '***'
}
```

---

## Best Practices

### 1. ✅ Logger Adını Doğru Kullan

```python
# Modülün __name__ kütüphanesini kullan
logger = logging.getLogger(__name__)
# Sonuç: logger adı "app.services.musteri_service" olur
```

### 2. ✅ Structured Logging

```python
# İyi
logger.info(f"Müşteri oluşturuldu: ID={result.id}, Ünvan={result.unvan}, Vergi No={result.vergi_no}")

# Kötü
logger.info("Success")
logger.info(result)  # Tüm object'i loglama
```

### 3. ✅ Exception Bilgisini İnclude Et

```python
# İyi - Traceback ile
logger.error(f"Müşteri güncelleme hatası: {str(e)}", exc_info=True)

# Kötü - Traceback olmadan
logger.error(f"Müşteri güncelleme hatası: {str(e)}")
```

### 4. ✅ Audit Konteksti Kullan

```python
# İyi - Tüm operasyon loglanır
with AuditLogContext('musteriler', 'UPDATE', user_id=1, kayit_id=5) as audit:
    audit.add_change('unvan', 'Old', 'New')
    # Operasyon
    pass

# Kötü - Sığ loglama
logger.info("Updated customer")
```

### 5. ✅ Uygun Log Seviyesi Seç

```python
# DEBUG - Geliştirme sırasında debugging için
logger.debug(f"Query parameters: {request.args.to_dict()}")

# INFO - İş olayları ve başarılar
logger.info(f"Müşteri oluşturuldu: ID={id}")

# WARNING - Tahmin edilebilir ancak istenmeyen durumlar
logger.warning(f"Müşteri bulunamadı: ID={id}")

# ERROR - Operasyonlar başarısız
logger.error(f"Veritabanı hatası: {str(e)}", exc_info=True)

# CRITICAL - Sistem kritik durumda
logger.critical("Veritabanı bağlantısı kaybedildi")
```

### 6. ✅ Performance Düşüncüsü

```python
# İyi - Conditional debug logging (overhead yok)
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Processing {len(large_list)} items: {expensive_calculation()}")

# Acceptable - f-string (minimal overhead)
logger.debug(f"Processing {item_count} items")

# Kötü - String concatenation ile debug level'sinde string yaratma
logger.info("Processing " + str(large_list))  # Always executed
```

---

## Troubleshooting

### Problem 1: Loglar görünmüyor

**Nedenleri:**
- LOG_DIR dizini existisi değil
- LOG_LEVEL çok yüksek (ERROR veya CRITICAL)
- Logger adı yanlış

**Çözüm:**

```bash
# 1. Dizin oluştur
mkdir -p logs

# 2. .env'de kontrol et
LOG_LEVEL=DEBUG  # Daha düşük level seç
LOG_DIR=logs     # Doğru dizin

# 3. logs/app.log ve logs/errors.log'u kontrol et
cat logs/app.log
tail -f logs/app.log  # Real-time
```

### Problem 2: Log dosyaları çok büyük

**Nedeni:** RotatingFileHandler tarafından otomatik olarak yönetilir.

**Konfigurasyon (app/logging_config.py):**

```python
# Şu anda:
maxBytes=10 * 1024 * 1024,  # 10 MB
backupCount=10,             # 10 backup file

# Ayarlarını değiştirebilirsin:
maxBytes=5 * 1024 * 1024,   # 5 MB (daha sık rotate)
backupCount=5,              # 5 backup file (az alan kullan)
```

### Problem 3: Sensitif veri loglanıyor

**Kontrolü:** format_context_for_logging() fonksiyonunda ayarlanmış alanlar

```python
# app/middleware.py
sensitive_fields = ['password', 'token', 'key', 'secret', 'card', 'cvv', 'dak', 'banka', 'hesap']

# Alan adı bu listede varsa otomatik olarak maskele edilir
```

### Problem 4: Üretim ortamında performans düşüşü

**Çözüm:**

```bash
# .env
LOG_LEVEL=INFO       # DEBUG yerine (DEBUG çok verbose)
FLASK_ENV=production # DEBUG mode kapalı
```

---

## Log Dosyası Yapısı

### Directory Layout

```
logs/
├── app.log              # Tüm loglar (rotate)
│   ├── app.log.1
│   ├── app.log.2
│   └── app.log.10       (backup files)
└── errors.log           # Yalnız ERROR+ loglar (rotate)
    ├── errors.log.1
    ├── errors.log.2
    └── errors.log.5
```

### app.log Format

```
2026-03-26 14:35:00,123 - flask.app - INFO - [app.py:45] - Flask uygulama başlatıldı | Mode: development | Debug: True
2026-03-26 14:35:05,456 - app.middleware - INFO - [2026-03-26T14:35:05.456789_192.168.1.1] GET /api/musteriler | IP: 192.168.1.1 | Content-Type: application/json
2026-03-26 14:35:05,678 - app.services.musteri_service - INFO - Müşteriler listelendi: 15 kayıt
2026-03-26 14:35:05,789 - app.middleware - INFO - [2026-03-26T14:35:05.456789_192.168.1.1] GET /api/musteriler -> 200 (124ms)
```

---

## İntegrasyon Kontrol Listesi

- [x] `app/logging_config.py` oluşturuldu
- [x] `app/middleware.py` oluşturuldu (request/response, audit context)
- [x] `app/__init__.py` güncellendi (logging setup entegre)
- [x] `app/services/*.py` güncellendi (logging çağrıları eklendi)
- [x] `.env.example` güncellendi (logging variables)
- [ ] Database triggers/ORM hooks (future: AuditLog event listeners)
- [ ] Log analysis dashboard (future: Kibana/Splunk)
- [ ] Centralized logging (future: ELK Stack, Datadog)

---

## Sonraki Adımlar (İŞ 4 ve 5)

### İŞ 4: API'yi Geliştir
- API pagination (logging ile support)
- Input validation (logging hataları)
- Error response standardization

### İŞ 5: Test Kapsamını Genişlet
- Logging module testi
- Error handler testi
- Audit trail testi

---

## Kaynaklar

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Flask Logging](https://flask.palletsprojects.com/logging/)
- [SQLAlchemy Event System](https://docs.sqlalchemy.org/orm/events.html)

**Son Güncelleme:** 2026-03-26
**İŞ 3 Durumu:** ✅ COMPLETE
