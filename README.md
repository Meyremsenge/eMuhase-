# eMuhasebe Pro

Yapay zeka destekli, gerçek zamanlı (realtime) ön muhasebe yönetim sistemi. Okul projesi amacıyla geliştirilmiştir.

Canlı: https://emuhasebe.onrender.com

## Öne Çıkan Özellikler

- **Yapay Zeka Finansal Asistan:** Tek tıkla kapsamlı finansal rapor üretir:
  - 4 sağlık skoru (Kârlılık / Likidite / Büyüme / Risk) ve genel finansal sağlık göstergesi
  - Güçlü yönler, riskler, öneriler, müşteri & pazar, nakit & likidite, anomali & kontrol başlıklı yorumlar
  - Aylık ortalama ciro, tahsilat oranı, müşteri konsantrasyonu gibi metrikler
  - **Alacak yaşlandırma** (0–30 / 31–60 / 60+ gün) ve vadesi geçmiş en büyük cariler
  - **Z-score tabanlı anomali tespiti** ve **nakit akışı tahmini**
- **Zengin Dashboard:** KPI kartları, aylık gelir-gider grafiği, fatura dağılımı, kritik stok, son aktiviteler, en çok satan ürünler, **Alacak/Borç özeti** ve **KDV özeti** (hesaplanan / indirilecek / devreden).
- **Kapsamlı Muhasebe Modülleri:** Müşteri/Tedarikçi yönetimi, Ürün/Stok takibi, Alış / Satış / İade faturaları. Fatura hesaplamaları tam matematiksel hassasiyetle (KDV/indirim) yapılır; satış/alış faturaları stok hareketlerini otomatik günceller.
- **Fatura Dışa Aktarma:** Türkçe karakter destekli **PDF** çıktısı ve **e-Fatura (UBL-TR) XML** üretimi. Fatura kalemlerini **Excel'den içe aktarma** desteği.
- **Firebase Gerçek Zamanlı Veritabanı:** Veriler Firebase Realtime Database üzerinde tutulur. Firebase yoksa otomatik olarak `localStorage` moduna düşer. Sayfalar açılışta önbellekten anında boyanır, ardından taze veri arka planda güncellenir (stale-while-revalidate).
- **Güvenli Mimari (Auth & API):** Flask-JWT-Extended ile JWT tabanlı oturum yönetimi, şifrelenmiş parolalar ve Rate Limiting korumalı RESTful API.
- **Katmanlı Mimari:** Blueprint tabanlı yapı, Service katmanı, Repository kalıbı, SQLAlchemy ORM; Soft Delete (silinen kayıtlar arşivlenir) ve AuditLog ile izlenebilirlik.
- **PWA:** `manifest.json` ve service worker ile uygulama gibi yüklenebilir / çevrimdışı destek.

## Teknolojiler

- **Backend:** Python 3.11+, Flask 3, SQLAlchemy 2, Flask-Migrate, Flask-JWT-Extended, Flask-Limiter (Redis destekli), Flask-WTF, Pydantic
- **Frontend:** Vanilla JS (ES Modules), CSS3, HTML5 (Jinja2), Chart.js, jsPDF + AutoTable, SheetJS
- **Veritabanı:** SQLite (kullanıcı/oturum), Firebase Realtime Database (uygulama verisi)
- **Yapay Zeka:** Google Gemini (varsayılan `gemini-2.0-flash`; kota dolarsa `gemini-2.5-flash-lite`, `gemini-1.5-flash` gibi alternatiflere otomatik geçer) ve OpenRouter ücretsiz modelleri
- **Dağıtım:** Gunicorn, Docker / docker-compose, Procfile (Render üzerinde yayında)

## Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleyin
Proje dizininde bir sanal ortam oluşturun ve bağımlılıkları yükleyin:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini Ayarlayın
Proje ana dizininde bir `.env` dosyası oluşturun ve alanları kendi bilgilerinizle doldurun:

```env
# Flask
FLASK_ENV=development
SECRET_KEY=gizli-bir-anahtar-belirleyin

# Yapay Zeka (opsiyonel — UI'daki "AI Kurulum" ekranından da girilebilir)
GEMINI_API_KEY=AIzaSy...
# veya OpenRouter:
# OPENROUTER_API_KEY=sk-or-...

# Firebase (opsiyonel — yoksa localStorage modu çalışır)
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=projeniz.firebaseapp.com
FIREBASE_DATABASE_URL=https://projeniz-default-rtdb.firebaseio.com
FIREBASE_PROJECT_ID=projeniz
FIREBASE_STORAGE_BUCKET=projeniz.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abcdef
```

> **Not (Gemini ücretsiz katman):** Bazı bölgelerde Gemini ücretsiz kotası 0 olabilir (`limit: 0`). Bu durumda OpenRouter anahtarı kullanmanız önerilir; uygulama `AIzaSy` ile başlamayan anahtarları otomatik olarak OpenRouter'a yönlendirir.

### 3. Veritabanını Başlatın ve Uygulamayı Çalıştırın
```powershell
flask db upgrade
python run.py
```
Uygulama `http://127.0.0.1:5000` adresinde çalışır. İlk kayıt olan kullanıcı otomatik olarak admin olur.

### Docker ile (opsiyonel)
```powershell
docker compose up --build
```

## Faydalı CLI Komutları
`run.py` içinde tanımlı kullanıcı yönetimi komutları:

```powershell
flask --app run.py list-users
flask --app run.py reset-password <email> <yeni_sifre>
flask --app run.py create-admin <kullanici_adi> <email> <sifre>
```

## Testler
```powershell
python -m pytest tests/ -v --tb=short
```

## Notlar
- Firebase ve Yapay Zeka entegrasyonlarını arayüzdeki ayarlar / "AI Kurulum" ekranından kontrol edebilir ve API anahtarlarınızı güncelleyebilirsiniz.
- Silinen kayıtlar kalıcı olarak silinmez; Soft Delete ile arşivlenir ve işlemler AuditLog ile kayıt altına alınır.
- Yapay zeka çıktısındaki skorlar, yaşlandırma, KDV ve tahsilat metrikleri tamamen gerçek verilerden **istemci tarafında** hesaplanır; metin yorumu için yapay zeka kullanılır.
