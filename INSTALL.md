# 📦 eMuhasebe Pro - Kurulum Rehberi

## 1️⃣ Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

**Yeni eklenen paketler:**
- `Flask-Talisman` - HTTP Security Headers
- `Flask-Limiter` - Rate Limiting
- `python-dotenv` - Environment variables (zaten var ama verify et)

---

## 2️⃣ Ortam Değişkenlerini Konfigüre Et

### `.env` Dosyasını Oluştur

```bash
# .env.example'dan başla
cp .env.example .env
```

### `.env` Dosyasını Doldur

```env
# Flask Ayarları
FLASK_ENV=development
SECRET_KEY=your-random-32-char-secret-key

# Veritabanı (development = SQLite)
DATABASE_URL=sqlite:///instance/muhasebe.db

# Firebase Config (İsteğe Bağlı - Demo modunda çalışır)
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

> **ÖNEMLİ:** `.env` dosyası asla Git'e commit edilmemeli!
> `.gitignore` zaten bunu engeller.

---

## 3️⃣ Veritabanı Kurulum

```bash
# Veritabanı migrate et
flask db upgrade

# Veya baştan oluştur:
# flask db init
# flask db migrate
# flask db upgrade
```

---

## 4️⃣ Demo Verileri Yükle (Opsiyonel)

Tarayıcıda açınız:
```
http://localhost:5000/demo-yukle
```

Veya komut satırından:
```bash
python demo_data.py
```

---

## 5️⃣ Uygulamayı Başlat

```bash
python run.py
```

Otomatik olarak `http://localhost:5000` açılacaktır.

---

## 🔐 Güvenlik Kurulu Kontrol Listesi

```
✅ .env dosyası oluşturuldu
✅ SECRET_KEY ayarlandı
✅ Firebase config env var'larından yükleniyor
✅ Rate limiting aktif
✅ HTTP Security Headers aktif
✅ Session cookies güvenli (HTTPONLY, SECURE)
```

---

## 🚀 Üretim Dağıtımı

### Ortam Değişkenlerini Kur

```bash
export FLASK_ENV=production
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export DATABASE_URL=postgresql://user:pass@localhost/emuhasebe
export VITE_FIREBASE_API_KEY=...
# ... diğerleri
```

### HTTPS ile Çalıştır

```bash
gunicorn --ssl-version TLSv1_2 \
         --certfile=/path/to/cert.pem \
         --keyfile=/path/to/key.pem \
         --bind 0.0.0.0:443 \
         run:app
```

### Docker Dağıtımı

```bash
docker build -t emuhasebe:latest .
docker run -e FLASK_ENV=production \
           -e SECRET_KEY=... \
           -e DATABASE_URL=... \
           -p 443:5000 \
           emuhasebe:latest
```

---

## 🧪 Test Çalıştır

```bash
# Tüm testleri çalıştır
pytest

# Coverage raporu ile
pytest --cov=app tests/
```

---

## 📱 Troubleshooting

### "SECRET_KEY ortam değişkeni set edilmemiş"
```bash
# .env dosyasını kontrol et
cat .env | grep SECRET_KEY

# Yoksa ekle
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env
```

### Firebase konfigürasyonu yüklemiyor
```bash
# Firebase env var'larını kontrol et
env | grep VITE_FIREBASE

# Veya API'den kontrol et
curl http://localhost:5000/api/config/firebase
```

### Rate limit hataları
API'den çok fazla request yollandıysa 429 (Too Many Requests) hatası alınır.
```
Retry-After header'ına bakarak beklemeyi oku.
```

---

## 📚 İlgili Dosyalar

- [SECURITY.md](SECURITY.md) - Güvenlik detayları
- [README.md](README.md) - Proje açıklaması
- [config.py](config.py) - Konfigürasyon
- [.env.example](.env.example) - Environment template

---

**Son Güncelleme:** 26 Mart 2026  
**Geçerli Versiyon:** 1.0.0
