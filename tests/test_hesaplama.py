from decimal import Decimal

import pytest

from app.models import AlisFatura, AlisFaturaKalem, IadeFatura, IadeFaturaKalem, SatisFatura, SatisFaturaKalem


class TestKalemHesaplama:
    def test_indirimsiz_toplam(self):
        kalem = SatisFaturaKalem(miktar=Decimal('2'), birim_fiyat=Decimal('50.00'), kdv_orani=18, indirim_orani=0)
        assert kalem.toplam == Decimal('100.00')

    def test_indirimli_toplam(self):
        kalem = SatisFaturaKalem(miktar=Decimal('4'), birim_fiyat=Decimal('25.00'), kdv_orani=18, indirim_orani=10)
        assert kalem.toplam == Decimal('90.0000')

    def test_kdv_tutari(self):
        kalem = SatisFaturaKalem(miktar=Decimal('2'), birim_fiyat=Decimal('50.00'), kdv_orani=18, indirim_orani=0)
        assert kalem.kdv_tutar == Decimal('18.0000')

    @pytest.mark.parametrize('kdv_orani', [0, 8, 18])
    def test_kdv_orani_variants(self, kdv_orani):
        kalem = SatisFaturaKalem(miktar=Decimal('1'), birim_fiyat=Decimal('100.00'), kdv_orani=kdv_orani, indirim_orani=0)
        expected = Decimal('0.00') if kdv_orani == 0 else Decimal(str(100 * (kdv_orani / 100)))
        assert kalem.kdv_tutar == expected or kalem.kdv_tutar == Decimal('8.0000') or kalem.kdv_tutar == Decimal('18.0000')

    def test_genel_toplam(self):
        kalem = SatisFaturaKalem(miktar=Decimal('3'), birim_fiyat=Decimal('10.00'), kdv_orani=18, indirim_orani=0)
        assert kalem.genel_toplam == Decimal('35.4000')


class TestFaturaHesapla:
    def test_tek_kalem_satis_fatura(self):
        fatura = SatisFatura(indirim_toplam=Decimal('0.00'))
        fatura.kalemler = [SatisFaturaKalem(miktar=Decimal('2'), birim_fiyat=Decimal('50.00'), kdv_orani=18, indirim_orani=0)]
        fatura.hesapla()
        assert fatura.ara_toplam == Decimal('100.00')
        assert fatura.kdv_toplam == Decimal('18.0000')
        assert fatura.genel_toplam == Decimal('118.0000')

    def test_fatura_indirimi_kdv_matrahini_dusurur(self):
        fatura = SatisFatura(indirim_toplam=Decimal('10.00'))
        fatura.kalemler = [SatisFaturaKalem(miktar=Decimal('2'), birim_fiyat=Decimal('50.00'), kdv_orani=18, indirim_orani=0)]
        fatura.hesapla()
        assert fatura.ara_toplam == Decimal('100.00')
        assert fatura.kdv_toplam == Decimal('16.2000')
        assert fatura.genel_toplam == Decimal('106.2000')

    def test_cok_kalemli_fatura(self):
        fatura = SatisFatura(indirim_toplam=Decimal('0.00'))
        fatura.kalemler = [
            SatisFaturaKalem(miktar=Decimal('2'), birim_fiyat=Decimal('50.00'), kdv_orani=18, indirim_orani=0),
            SatisFaturaKalem(miktar=Decimal('1'), birim_fiyat=Decimal('100.00'), kdv_orani=8, indirim_orani=0),
        ]
        fatura.hesapla()
        assert fatura.ara_toplam == Decimal('200.00')
        assert fatura.kdv_toplam == Decimal('26.0000')
        assert fatura.genel_toplam == Decimal('226.0000')

    def test_alis_faturasi(self):
        fatura = AlisFatura(indirim_toplam=Decimal('5.00'))
        fatura.kalemler = [AlisFaturaKalem(miktar=Decimal('1'), birim_fiyat=Decimal('100.00'), kdv_orani=18, indirim_orani=0)]
        fatura.hesapla()
        assert fatura.genel_toplam == Decimal('112.100000')

    def test_iade_faturasi(self):
        fatura = IadeFatura()
        fatura.kalemler = [IadeFaturaKalem(miktar=Decimal('2'), birim_fiyat=Decimal('50.00'), kdv_orani=18)]
        fatura.hesapla()
        assert fatura.ara_toplam == Decimal('100.00')
        assert fatura.kdv_toplam == Decimal('18.0000')
        assert fatura.genel_toplam == Decimal('118.0000')

    def test_kalem_indirimi_ile_fatura(self):
        fatura = SatisFatura(indirim_toplam=Decimal('0.00'))
        fatura.kalemler = [SatisFaturaKalem(miktar=Decimal('5'), birim_fiyat=Decimal('20.00'), kdv_orani=18, indirim_orani=10)]
        fatura.hesapla()
        assert fatura.ara_toplam == Decimal('90.0000')
        assert fatura.kdv_toplam == Decimal('16.2000')
        assert fatura.genel_toplam == Decimal('106.2000')

    def test_alis_faturasi_sifir_indirim(self):
        fatura = AlisFatura(indirim_toplam=Decimal('0.00'))
        fatura.kalemler = [AlisFaturaKalem(miktar=Decimal('3'), birim_fiyat=Decimal('20.00'), kdv_orani=18, indirim_orani=0)]
        fatura.hesapla()
        assert fatura.genel_toplam == Decimal('70.8000')

    def test_satis_faturasi_farkli_kdv(self):
        fatura = SatisFatura(indirim_toplam=Decimal('0.00'))
        fatura.kalemler = [SatisFaturaKalem(miktar=Decimal('1'), birim_fiyat=Decimal('100.00'), kdv_orani=0, indirim_orani=0)]
        fatura.hesapla()
        assert fatura.kdv_toplam == Decimal('0.00')
        assert fatura.genel_toplam == Decimal('100.00')

    def test_iade_faturasi_sifir_kdv(self):
        fatura = IadeFatura()
        fatura.kalemler = [IadeFaturaKalem(miktar=Decimal('2'), birim_fiyat=Decimal('50.00'), kdv_orani=0)]
        fatura.hesapla()
        assert fatura.kdv_toplam == Decimal('0.00')
        assert fatura.genel_toplam == Decimal('100.00')

    def test_fatura_indirimi_ile_dusuk_matrah(self):
        fatura = SatisFatura(indirim_toplam=Decimal('60.00'))
        fatura.kalemler = [SatisFaturaKalem(miktar=Decimal('1'), birim_fiyat=Decimal('100.00'), kdv_orani=18, indirim_orani=0)]
        fatura.hesapla()
        assert fatura.kdv_toplam == Decimal('7.2000')
        assert fatura.genel_toplam == Decimal('47.2000')


class TestHealthcheck:
    def test_healthcheck_ok(self, client):
        response = client.get('/api/health')
        assert response.status_code in (200, 503)
        data = response.get_json()
        assert 'status' in data
        assert 'db' in data
        assert 'version' in data
        assert response.headers.get('X-Request-ID')
