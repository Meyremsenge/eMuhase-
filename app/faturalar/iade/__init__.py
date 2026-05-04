"""
eMuhasebe Pro - İade Faturaları Modülü (Firebase Realtime Database)
"""
from flask import Blueprint, render_template

iade_bp = Blueprint('iade', __name__)


@iade_bp.route('/')
def liste():
    """İade faturaları listesi - Firebase'den client-side yüklenecek"""
    return render_template('faturalar/iade/liste_firebase.html')


@iade_bp.route('/yeni', methods=['GET'])
def yeni():
    """Yeni iade faturası formu"""
    return render_template('faturalar/iade/form_firebase.html', fatura_id=None)


@iade_bp.route('/duzenle/<id>', methods=['GET'])
def duzenle(id):
    """İade faturası düzenleme formu"""
    return render_template('faturalar/iade/form_firebase.html', fatura_id=id)


@iade_bp.route('/detay/<id>')
def detay(id):
    """İade faturası detay sayfası"""
    return render_template('faturalar/iade/detay_firebase.html', fatura_id=id)

