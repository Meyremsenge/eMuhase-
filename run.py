"""
eMuhasebe Pro - Uygulama Başlatıcı
"""
import webbrowser
import threading
import sys
import os
import click
from app import create_app
from app.models import db, User

# Varsayılan geliştirme modu: değişiklikleri otomatik algıla.
# Üretimde EMUHASEBE_ENV=production vererek production ayarlarını kullan.
env_name = os.environ.get('EMUHASEBE_ENV', 'development').lower()
config_name = 'production' if env_name == 'production' else 'development'
app = create_app(config_name)


# ══════════════════ CLI Komutları (Şifre Yönetimi) ══════════════════
# Kullanım:
#   flask --app run.py reset-password <email> <yeni_sifre>
#   flask --app run.py reset-users
#   flask --app run.py list-users
#   flask --app run.py create-admin <username> <email> <sifre>

@app.cli.command('reset-password')
@click.argument('email')
@click.argument('new_password')
def reset_password_cmd(email, new_password):
    """Bir kullanıcının şifresini sıfırla. Şifreyi unutursan bunu çalıştır."""
    if len(new_password) < 6:
        click.echo('❌ Şifre en az 6 karakter olmalı.')
        sys.exit(1)
    user = User.query.filter_by(email=email).first()
    if not user:
        click.echo(f'❌ Kullanıcı bulunamadı: {email}')
        sys.exit(1)
    user.set_password(new_password)
    db.session.commit()
    click.echo(f'✅ {email} kullanıcısının şifresi güncellendi.')


@app.cli.command('reset-users')
def reset_users_cmd():
    """Tüm kullanıcıları sil. Yeniden ilk kayıt = admin olur."""
    if not click.confirm('⚠️  TÜM kullanıcı hesaplarını silmek istediğine emin misin?'):
        click.echo('İptal edildi.')
        return
    count = User.query.delete()
    db.session.commit()
    click.echo(f'✅ {count} kullanıcı silindi. Bir sonraki kayıt otomatik admin olur.')


@app.cli.command('list-users')
def list_users_cmd():
    """Mevcut kullanıcıları listele."""
    users = User.query.all()
    if not users:
        click.echo('Hiç kullanıcı yok. /giris sayfasından ilk admin\'i oluştur.')
        return
    for u in users:
        click.echo(f'  • {u.email}  ({u.username})  rol={u.role}  aktif={u.aktif}')


@app.cli.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_admin_cmd(username, email, password):
    """Doğrudan admin kullanıcı oluştur (zaten varsa hata)."""
    if len(password) < 6:
        click.echo('❌ Şifre en az 6 karakter olmalı.')
        sys.exit(1)
    if User.query.filter((User.username == username) | (User.email == email)).first():
        click.echo(f'❌ Aynı kullanıcı adı/email zaten var.')
        sys.exit(1)
    u = User(username=username, email=email, role='admin')
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    click.echo(f'✅ Admin oluşturuldu: {email}')


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
