"""
eMuhasebe Pro - Alış Faturaları Modülü (Firebase Realtime Database)
"""
from flask import Blueprint, render_template

alis_bp = Blueprint('alis', __name__)


@alis_bp.route('/')
def liste():
    """Alış faturaları listesi - Firebase'den client-side yüklenecek"""
    return render_template('faturalar/alis/liste_firebase.html')


@alis_bp.route('/yeni', methods=['GET'])
def yeni():
    """Yeni alış faturası formu"""
    return render_template('faturalar/alis/form_firebase.html', fatura_id=None)


@alis_bp.route('/duzenle/<id>', methods=['GET'])
def duzenle(id):
    """Alış faturası düzenleme formu"""
    return render_template('faturalar/alis/form_firebase.html', fatura_id=id)


@alis_bp.route('/detay/<id>')
def detay(id):
    """Alış faturası detay sayfası"""
    return render_template('faturalar/alis/detay_firebase.html', fatura_id=id)

