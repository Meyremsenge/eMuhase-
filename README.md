# eMuhasebe Pro

Küçük ve orta ölçekli işletmeler için geliştirilmiş **ön muhasebe web uygulaması**.

## Özellikler

- **Müşteri/Tedarikçi Yönetimi** – Kayıt, düzenleme, arama
- **Ürün/Hizmet Yönetimi** – Stok takibi, fiyatlandırma
- **Fatura Yönetimi** – Alış, satış ve iade faturaları
- **Yapay Zeka Modülü** – Nakit akışı tahmini, anomali tespiti, akıllı ürün önerisi
- **REST API** – Tam CRUD desteği (`/api/musteriler`, `/api/urunler`, `/api/faturalar`)
- **Karanlık/Aydınlık Tema** – Kullanıcı tercihine göre geçiş

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

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Veritabanı migration
flask db upgrade

# Uygulamayı çalıştır
python run.py
```

## Test

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Lint kontrolü
python -m flake8 app/ --max-line-length=120
```

## API Kullanımı

```bash
# Müşterileri listele
GET /api/musteriler

# Yeni müşteri oluştur
POST /api/musteriler
Content-Type: application/json
{"unvan": "ABC Ltd", "vergi_no": "1234567890"}

# Ürünleri ara
GET /api/urunler?q=laptop

# Fatura özeti
GET /api/faturalar/ozet
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
