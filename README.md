# eMuhasebe Pro (dev)

Basit ön muhasebe uygulaması - bu depo okul projesi amaçlıdır. README bu çalışma dizinindeki güncel durum ve hızlı çalışma talimatlarını içerir.

Öne çıkan değişiklikler (kritik düzeltmeler):
- `app/__init__.py` eklenerek `create_app()` factory oluşturuldu
- Model audit log (AuditLog) için SQLAlchemy listener'ları eklendi
- `app/repositories/base_repository.py` yeniden düzenlendi; repository class'ları çalışır durumda
- `app/services/musteri_service.py` ve `app/repositories/musteri_repository.py` eklendi
- `app/api_utils.py` içinde `fatura_to_dict` hatası düzeltildi (kalem iterasyonu) ve serializer alanları güncellendi

Çalıştırma ortamı
- Python 3.14 önerilir

Hızlı başlangıç

```powershell
# Windows (repo kökünde)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Ortam değişkenleri (örnek):
set FLASK_APP=run.py
set FLASK_ENV=development

# DB migration ve başlatma
flask db upgrade
python run.py
```

Testler

```powershell
python -m pytest -q
```

Notlar
- Projede eksik veya kısmi implementasyonlar bulunabilir (özellikle frontend ve bazı blueprint'ler).
- Kritik olarak çalışmayan import hataları düzeltildi; testlere çalıştırıp doğrulamanız önerilir.
