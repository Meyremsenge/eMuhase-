"""
eMuhasebe Pro - Müşteriler Modülü (Firebase Realtime Database)
"""
from flask import Blueprint, render_template

musteriler_bp = Blueprint('musteriler', __name__)


@musteriler_bp.route('/')
def liste():
    """Müşteri listesi - Firebase'den client-side yüklenecek"""
    return render_template('musteriler/liste_firebase.html')


@musteriler_bp.route('/yeni', methods=['GET'])
def yeni():
    """Yeni müşteri/tedarikçi formu"""
    return render_template('musteriler/form_firebase.html', musteri_id=None)


@musteriler_bp.route('/duzenle/<id>', methods=['GET'])
def duzenle(id):
    """Müşteri düzenleme formu"""
    return render_template('musteriler/form_firebase.html', musteri_id=id)

