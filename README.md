# eMuhasebe Pro

Küçük ve orta ölçekli işletmeler için geliştirilmiş **ön muhasebe web uygulaması**.

## Özellikler

- **Müşteri/Tedarikçi Yönetimi** – Kayıt, düzenleme, gelişmiş arama ve filtreleme
- **Ürün/Hizmet Yönetimi** – Stok takibi, dinamik fiyatlandırma, kategorilendirme
- **Fatura Yönetimi** – Alış, satış ve iade faturaları, özet raporlar
- **Yapay Zeka Modülü** – Nakit akışı tahmini, anomali tespiti, akıllı ürün önerisi
- **REST API** – Tam CRUD desteği (`/api/musteriler`, `/api/urunler`, `/api/faturalar`)
- **Karanlık/Aydınlık Tema** – Kullanıcı tercihine göre geçiş
- **Gelişmiş Raporlama** – Özet istatistikler ve veri analizi

## Mimari

```
Route → Service → Repository → ORM (SQLAlchemy)
```

| Katman | Açıklama |
|--------|----------|
| **Route / API** | HTTP isteklerini karşılar |
| **Service** | İş kurallarını uygular |
| **Repository** | Veritabanı sorgularını yönetir (BaseRepository) |
| **ORM** | SQLAlchemy modelleri (8 tablo, 6 ilişki) |

### Tasarım Desenleri

- **Factory Pattern** – `create_app()` ile uygulama oluşturma
- **Repository Pattern** – Veri erişim katmanı soyutlaması
- **Service Layer** – İş mantığı katmanı
- **Blueprint** – Modüler route yapısı

## Teknolojiler

- **Backend:** Python 3.x, Flask 3.0, SQLAlchemy, Flask-Migrate
- **Frontend:** HTML5, CSS3, JavaScript, Chart.js
- **Veritabanı:** SQLite (geliştirme), Firebase Realtime DB (istemci tarafı)
- **AI:** OpenRouter API (Mistral), yerel JS algoritmaları
- **CI/CD:** GitHub Actions, Docker, Gunicorn

## Kurulum

### Gereksinimler
- Python 3.8+
- pip (Python paket yöneticisi)
- Git

### Adım Adım

```bash
# 1. Repository'yi klonla
git clone https://github.com/Meyremsenge/eMuhasebe.git
cd eMuhasebe

# 2. Sanal ortam oluştur ve aktifleştir
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Veritabanı migration'ı çalıştır
flask db upgrade

# 5. .env dosyasını konfigüre et (varsa)
cp .env.example .env
# İçeriğini kendi ayarlarına göre düzenle

# 6. Uygulamayı başlat
python run.py
```

Uygulama **http://localhost:5000** adresinde çalışacaktır.

## Test

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Belirli test dosyasını çalıştır
python -m pytest tests/test_musteri_service.py -v

# Lint kontrolü ve kod kalitesi
python -m flake8 app/ --max-line-length=120
python -m pylint app/ --disable=all --enable=E,F

# Test kapsama raporu
python -m pytest tests/ --cov=app --cov-report=html
```

## API Kullanımı

Detaylı API dokumentasyonu için [API.md](API.md) dosyasına bakınız.

### Temel Örnekler

```bash
# Müşterileri listele
curl -X GET http://localhost:5000/api/musteriler

# Yeni müşteri oluştur
curl -X POST http://localhost:5000/api/musteriler \
  -H "Content-Type: application/json" \
  -d '{"unvan": "ABC Ltd", "vergi_no": "1234567890"}'

# Ürünleri ara
curl -X GET "http://localhost:5000/api/urunler?q=laptop"

# Fatura özeti
curl -X GET http://localhost:5000/api/faturalar/ozet
```

## Proje Yapısı

```
app/
├── api/             # REST API endpoint'leri
├── repositories/    # Veri erişim katmanı (Repository Pattern)
├── services/        # İş mantığı katmanı (Service Layer)
├── models.py        # ORM modelleri
├── faturalar/       # Fatura blueprint'leri (alış, satış, iade)
├── musteriler/      # Müşteri blueprint'i
├── urunler/         # Ürün blueprint'i
├── static/          # CSS, JS, görseller
└── templates/       # Jinja2 şablonları
tests/               # pytest birim testleri
migrations/          # Flask-Migrate (Alembic)
.github/workflows/   # CI/CD pipeline
```
