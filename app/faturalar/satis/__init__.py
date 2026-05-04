"""
eMuhasebe Pro - Satış Faturaları Modülü (Firebase Realtime Database)
"""
from flask import Blueprint, render_template

satis_bp = Blueprint('satis', __name__)


@satis_bp.route('/')
def liste():
    """Satış faturaları listesi - Firebase'den client-side yüklenecek"""
    return render_template('faturalar/satis/liste_firebase.html')


@satis_bp.route('/yeni', methods=['GET'])
def yeni():
    """Yeni satış faturası formu"""
    return render_template('faturalar/satis/form_firebase.html', fatura_id=None)


@satis_bp.route('/duzenle/<id>', methods=['GET'])
def duzenle(id):
    """Satış faturası düzenleme formu"""
    return render_template('faturalar/satis/form_firebase.html', fatura_id=id)


@satis_bp.route('/detay/<id>')
def detay(id):
    """Satış faturası detay sayfası"""
    return render_template('faturalar/satis/detay_firebase.html', fatura_id=id)

