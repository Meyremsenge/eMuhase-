"""
eMuhasebe Pro - Ürünler Modülü (Firebase Realtime Database)
"""
from flask import Blueprint, render_template

urunler_bp = Blueprint('urunler', __name__)


@urunler_bp.route('/')
def liste():
    """Ürün listesi - Firebase'den client-side yüklenecek"""
    return render_template('urunler/liste_firebase.html')


@urunler_bp.route('/yeni', methods=['GET'])
def yeni():
    """Yeni ürün formu"""
    return render_template('urunler/form_firebase.html', urun_id=None)


@urunler_bp.route('/duzenle/<id>', methods=['GET'])
def duzenle(id):
    """Ürün düzenleme formu"""
    return render_template('urunler/form_firebase.html', urun_id=id)

