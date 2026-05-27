# eMuhasebe Pro

Gelişmiş, yapay zeka destekli ve gerçek zamanlı (realtime) ön muhasebe yönetim sistemi. Okul projesi amacıyla geliştirilmiştir.

## 🚀 Öne Çıkan Özellikler

- **🤖 Yapay Zeka Asistanı (Gemini API):** Finansal verilerinizi analiz eder, nakit akışı tahmini yapar ve Z-score tabanlı anomali tespiti sunar.
- **🔥 Firebase Gerçek Zamanlı Veritabanı:** Verileriniz Firebase Realtime Database üzerinde eşzamanlı olarak yedeklenir ve birden çok cihaz arasında anlık senkronize olur. Çevrimdışı durumlarda `localStorage` fallback mekanizması devreye girer.
- **💼 Kapsamlı Muhasebe Modülleri:** Müşteri/Tedarikçi yönetimi, Ürün/Stok takibi, Alış/Satış ve İade Faturası kesimi. Fatura hesaplamaları tam matematiksel hassasiyetle (Numeric KDV/İndirim) çalışır.
- **🔒 Güvenli Mimari (Auth & API):** Flask-JWT-Extended ile JWT tabanlı oturum yönetimi, şifrelenmiş parolalar ve Rate Limiting (Hız Sınırlandırması) korumalı RESTful API endpoints.
- **📂 Katmanlı Mimari (Layered Architecture):** Blueprint tabanlı yapı, Service katmanı, Repository kalıbı (Repository Pattern) ve SQLAlchemy ORM kullanımı.

## 🛠️ Teknolojiler

- **Backend:** Python 3.12+, Flask, SQLAlchemy, Flask-JWT-Extended, Flask-Limiter, Pydantic
- **Frontend:** Vanilla JS, CSS3, HTML5 (Jinja2)
- **Veritabanı:** SQLite (Yerel), Firebase Realtime Database (Bulut)
- **Yapay Zeka:** Google Gemini 1.5/2.5 Flash API & OpenRouter desteği

## ⚙️ Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleyin
Proje dizininde bir sanal ortam oluşturun ve bağımlılıkları yükleyin:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini (Environment Variables) Ayarlayın
Proje ana dizininde bir `.env` dosyası oluşturun (veya mevcut `.env` dosyasını düzenleyin) ve aşağıdaki alanları kendi bilgilerinizle doldurun:

```env
# Flask Ayarları
FLASK_ENV=development
SECRET_KEY=gizli-bir-anahtar-belirleyin

# Yapay Zeka (Gemini API)
GEMINI_API_KEY=AIzaSy...

# Firebase Konfigürasyonu
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=projeniz.firebaseapp.com
FIREBASE_DATABASE_URL=https://projeniz-default-rtdb.firebaseio.com
FIREBASE_PROJECT_ID=projeniz
FIREBASE_STORAGE_BUCKET=projeniz.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abcdef
```

### 3. Veritabanını Başlatın ve Uygulamayı Çalıştırın
```powershell
flask db upgrade
python run.py
```
Uygulama `http://127.0.0.1:5000` adresinde çalışmaya başlayacaktır.

## 🧪 Testleri Çalıştırma
Projede yer alan kapsamlı test senaryolarını çalıştırmak için:
```powershell
python -m pytest tests/ -v --tb=short
```

## 📝 Notlar
- Uygulama ilk kez başlatıldığında sağ alt köşedeki mod butonlarından Firebase ve Yapay Zeka entegrasyonlarınızın durumunu kontrol edebilir, arayüz üzerinden de API anahtarlarınızı güncelleyebilirsiniz.
- Silinen kayıtlar veritabanından kalıcı olarak silinmez, "Soft Delete" yöntemi ile arşivlenir. Tüm işlemler AuditLog ile kayıt altına alınır.
