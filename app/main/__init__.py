"""
eMuhasebe Pro - Ana Modül
Dashboard ve genel sayfalar
Firebase Realtime Database ile çalışır
"""
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Ana sayfa - Dashboard (Firebase Realtime)"""
    return render_template('main/index_firebase.html')


@main_bp.route('/veri-sifirla')
def veri_sifirla():
    """Tarayicidaki yerel verileri sifirla"""
    return render_template('main/reset_data.html')


@main_bp.route('/bildirimler')
def bildirimler():
    """Tum bildirimler sayfasi"""
    return render_template('main/bildirimler.html')


@main_bp.route('/giris')
def giris():
    """Login sayfasi - JWT API'ye fetch ile baglanan tek sayfa form"""
    return render_template('auth/login.html')

