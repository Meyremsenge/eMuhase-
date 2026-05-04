"""
eMuhasebe Pro - Uygulama Başlatıcı
"""
import webbrowser
import threading
import sys
import os
from app import create_app

# Varsayılan geliştirme modu: değişiklikleri otomatik algıla.
# Üretimde EMUHASEBE_ENV=production vererek production ayarlarını kullan.
env_name = os.environ.get('EMUHASEBE_ENV', 'development').lower()
config_name = 'production' if env_name == 'production' else 'development'
app = create_app(config_name)

def open_browser():
    """Uygulama başladıktan sonra tarayıcıyı aç"""
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  eMuhasebe Pro v1.0.0")
    print("  Ön Muhasebe Yönetim Sistemi")
    print("="*50)
    print("\n  Uygulama başlatılıyor...")
    print("  http://127.0.0.1:5000 adresinde çalışıyor")
    print("  Kapatmak için bu pencereyi kapatın.\n")
    
    # Tarayıcıyı 1.5 saniye sonra aç (sunucu başlayana kadar bekle)
    threading.Timer(1.5, open_browser).start()
    
    is_dev = config_name == 'development'
    app.run(
        debug=is_dev,
        host='127.0.0.1',
        port=5000,
        use_reloader=is_dev
    )
