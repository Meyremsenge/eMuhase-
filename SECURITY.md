# 🔐 eMuhasebe Pro - Güvenlik Rehberi

## Yapılan Güvenlik Iyileştirmeleri (İşletme 1)

### 1. ✅ Firebase Credentials Güvenlik

**PROBLEM (Daha Önceki):**
```javascript
// ❌ Hardcoded credentials - ASLA YAPMA!
const firebaseConfig = {
    apiKey: "AIzaSyByvscNxJM..."  // PUBLIC - HERKESİN ERİŞEBİLECEĞİ
};
```

**ÇÖZÜM:**
- Firebase config'i backend'den `/api/config/firebase` endpoint'ine taşındı
- Config ortam değişkenlerinden yüklenir (`.env` dosyasından)
- `.env` dosyası `.gitignore`'a eklendi (asla Git'e commit edilmez)

**Uygulama:**
```bash
# .env dosyasını ayarla
VITE_FIREBASE_API_KEY=your-actual-key-here
VITE_FIREBASE_PROJECT_ID=your-project-id
# ... diğer config variables
```

```javascript
// ✅ Güvenli - Backend'den yüklenir
const response = await fetch('/api/config/firebase');
const { config } = await response.json();
const app = initializeApp(config);
```

---

### 2. ✅ SECRET_KEY Güvenliği

**PROBLEM:**
```python
# ❌ Hardcoded secret - Tahmin edilebilir
SECRET_KEY = os.environ.get('SECRET_KEY') or 'muhasebe-gizli-anahtar-2024'
```

**ÇÖZÜM:**
- Üretimde `SECRET_KEY` zorunlu env var'dır
- Geliştirmede random key otomatik oluşturulur
- `.env.example` template dosyası sunulur (gerçek değerler yok)

**Uygulama:**
```python
# config.py - Üretim kontrolü
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if os.environ.get('FLASK_ENV') == 'production':
        raise ValueError('SECRET_KEY zorunludur!')
```

---

### 3. ✅ HTTP Security Headers

**Eklenen Header'lar:**
- `X-Content-Type-Options: nosniff` - MIME sniffing saldırılarını engelle
- `X-Frame-Options: DENY` - Clickjacking saldırılarını engelle
- `X-XSS-Protection: 1; mode=block` - XSS saldırılarını engelle
- `Strict-Transport-Security` - HTTPS'i zorunlu kıl
- `Content-Security-Policy` - İçerik kaynaki sınırlaması

**Uygulama:** Flask-Talisman middleware'i kullanılıyor:
```python
from flask_talisman import Talisman

Talisman(app, force_https=True)
```

---

### 4. ✅ Session Cookie Güvenliği

**Yapılandırma:**
```python
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # XSS'ten koruma (JS erişimi yok)
SESSION_COOKIE_SAMESITE = 'Lax'   # CSRF koruması
```

---

### 5. ✅ Rate Limiting

**Uygulanan Limitler:**
```
GET Listeleme:     30 request / dakika
GET Detay:         60 request / dakika
POST Oluştur:      10 request / dakika
PUT Güncelle:      20 request / dakika
DELETE Sil:        10 request / dakika
```

**Kullanım:**
```python
@api_bp.route('/musteriler', methods=['GET'])
@limiter.limit("30 per minute")
def musteriler_list():
    ...
```

---

## 🚀 Dağıtım Öncesi Kontrol Listesi

### Üretim Ortamında ZORUNLU

- [ ] `.env` dosyasını oluştur (`.env.example`'dan kopyala)
- [ ] `FLASK_ENV=production` ayarla
- [ ] `SECRET_KEY` - 32 karakterli random string yap:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] `VITE_FIREBASE_API_KEY` ve diğer Firebase env var'larını doldur
- [ ] `DATABASE_URL` set et (PostgreSQL önerilen)
- [ ] `SESSION_COOKIE_SECURE=True` ayarla
- [ ] HTTPS sertifikası yap

### Güvenlik Kontrolleri

- [ ] `.env` dosyası `.gitignore`'da (commit edilmeyecek)
- [ ] `firebase-config.js` asla hardcoded credentials tutmıyor
- [ ] Tüm API endpoint'leri rate limited (DoS koruması)
- [ ] CORS header'ları aktif
- [ ] Debug modu kapalı (`DEBUG=False`)

---

## 🔒 Ek Güvenlik Önerileri (İleride)

1. **API Authentication & Authorization**
   - JWT token'lar
   - Role-based access control (RBAC)
   - Permission system

2. **Input Validation**
   - WTForms veya Pydantic validation
   - Format checking (vergi no, email, etc.)
   - Length/type constraints

3. **Database Security**
   - Parameterized queries (already done ✅)
   - Encryption at rest
   - Backup encryption

4. **Logging & Monitoring**
   - Audit trail for all data changes
   - Security event logging
   - Anomaly detection

5. **Deployment Security**
   - WAF (Web Application Firewall)
   - DDoS protection
   - Regular security audits
   - Penetration testing

---

## 📖 Referanslar

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

---

**Son Güncelleme:** 26 Mart 2026  
**Güvenlik Seviyesi:** ⭐⭐⭐⭐ (4/5)
