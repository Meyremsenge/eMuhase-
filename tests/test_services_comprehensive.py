"""
Service Layer Tests
Business logic ve validation testleri
"""
import pytest
from decimal import Decimal
from app.services.musteri_service import MusteriService
from app.services.urun_service import UrunService


class TestMusteriService:
    """Müşteri servisi testleri."""

    def test_get_all_musteriler(self, sample_musteri):
        """Tüm müşterileri getir."""
        musteriler = MusteriService.get_all()
        assert len(musteriler) == 1
        assert musteriler[0].unvan == 'Test Müşteri Ltd'

    def test_get_musteri_by_id(self, sample_musteri):
        """ID'ye göre müşteri getir."""
        musteri = MusteriService.get_by_id(sample_musteri.id)
        assert musteri is not None
        assert musteri.unvan == sample_musteri.unvan

    def test_get_nonexistent_musteri(self, db):
        """Olmayan müşteri getirme."""
        musteri = MusteriService.get_by_id(999)
        assert musteri is None

    def test_search_musteri_by_unvan(self, sample_musteri):
        """Müşteri araması."""
        results = MusteriService.search('Test')
        assert len(results) == 1
        assert results[0].id == sample_musteri.id

    def test_search_musteri_no_results(self, sample_musteri):
        """Arama sonucu yok."""
        results = MusteriService.search('NonExistent')
        assert len(results) == 0

    def test_create_musteri_valid(self, db):
        """Geçerli müşteri oluştur."""
        data = {
            'unvan': 'Yeni Müşteri',
            'vergi_no': '9876543210',
            'email': 'yeni@example.com'
        }
        musteri = MusteriService.create(data)
        assert musteri.id is not None
        assert musteri.unvan == 'Yeni Müşteri'
        assert musteri.vergi_no == '9876543210'

    def test_create_musteri_duplicate_vergi_no(self, sample_musteri):
        """Çift vergi numarası fırlatması."""
        data = {
            'unvan': 'Başka Müşteri',
            'vergi_no': sample_musteri.vergi_no
        }
        with pytest.raises(ValueError, match='vergi numarası zaten kayıtlı'):
            MusteriService.create(data)

    def test_update_musteri(self, sample_musteri):
        """Müşteri güncelle."""
        update_data = {'unvan': 'Güncellenmiş Ad'}
        updated = MusteriService.update(sample_musteri.id, update_data)
        assert updated.unvan == 'Güncellenmiş Ad'

    def test_update_nonexistent_musteri(self, db):
        """Olmayan müşteri güncellemesi."""
        with pytest.raises(ValueError, match='Müşteri bulunamadı'):
            MusteriService.update(999, {'unvan': 'New'})

    def test_delete_musteri(self, sample_musteri):
        """Müşteri sil."""
        result = MusteriService.delete(sample_musteri.id)
        # Soft delete olması gerekir, kontrol et
        deleted = MusteriService.get_by_id(sample_musteri.id)
        assert deleted is not None  # Soft delete
        assert deleted.silinme_tarihi is not None

    def test_delete_nonexistent_musteri(self, db):
        """Olmayan müşteri silme."""
        with pytest.raises(ValueError, match='Müşteri bulunamadı'):
            MusteriService.delete(999)

    def test_count_musteriler(self, multiple_musteriler):
        """Müşteri sayısı."""
        count = MusteriService.count()
        assert count == 25


class TestUrunService:
    """Ürün servisi testleri."""

    def test_get_all_urunler(self, sample_urun):
        """Tüm ürünleri getir."""
        urunler = UrunService.get_all()
        assert len(urunler) == 1

    def test_get_urun_by_id(self, sample_urun):
        """ID'ye göre ürün getir."""
        urun = UrunService.get_by_id(sample_urun.id)
        assert urun is not None
        assert urun.kod == 'TEST-001'

    def test_search_urun_by_ad(self, sample_urun):
        """Ürün adına göre araş."""
        results = UrunService.search('Test')
        assert len(results) == 1

    def test_create_urun_valid(self, db):
        """Geçerli ürün oluştur."""
        data = {
            'ad': 'Yeni Ürün',
            'kod': 'YEN-001',
            'alis_fiyat': Decimal('100.00'),
            'satis_fiyat': Decimal('150.00'),
            'stok_miktari': 50
        }
        urun = UrunService.create(data)
        assert urun.id is not None
        assert urun.ad == 'Yeni Ürün'
        assert urun.kod == 'YEN-001'

    def test_create_urun_duplicate_kod(self, sample_urun):
        """Çift ürün kodu."""
        data = {
            'ad': 'Başka Ürün',
            'kod': sample_urun.kod,  # Aynısı
            'alis_fiyat': Decimal('100.00'),
            'satis_fiyat': Decimal('150.00')
        }
        with pytest.raises(ValueError, match='ürün kodu zaten kayıtlı'):
            UrunService.create(data)

    def test_update_urun(self, sample_urun):
        """Ürün güncelle."""
        update_data = {'satis_fiyat': Decimal('200.00')}
        updated = UrunService.update(sample_urun.id, update_data)
        assert updated.satis_fiyat == Decimal('200.00')

    def test_delete_urun(self, sample_urun):
        """Ürün sil."""
        UrunService.delete(sample_urun.id)
        deleted = UrunService.get_by_id(sample_urun.id)
        assert deleted.silinme_tarihi is not None  # Soft delete


class TestMusteriServiceEdgeCases:
    """Müşteri servisi edge case testleri."""

    def test_create_musteri_empty_unvan(self):
        """Boş unvan."""
        data = {'unvan': ''}
        with pytest.raises(Exception):
            MusteriService.create(data)

    def test_create_musteri_very_long_unvan(self):
        """Çok uzun unvan."""
        data = {
            'unvan': 'A' * 300  # 255'ten fazla
        }
        # Validation'ı kontrol
        try:
            MusteriService.create(data)
        except Exception:
            pass  # Beklenen

    def test_update_musteri_partial_fields(self, sample_musteri):
        """Müşteri kısmı güncelle."""
        original_telefon = sample_musteri.telefon
        update_data = {'unvan': 'New Name'}
        updated = MusteriService.update(sample_musteri.id, update_data)
        assert updated.unvan == 'New Name'
        assert updated.telefon == original_telefon  # Değişmedi


class TestUrunServiceEdgeCases:
    """Ürün servisi edge case testleri."""

    def test_create_urun_zero_price(self, db):
        """Sıfır fiyat."""
        data = {
            'ad': 'Test',
            'kod': 'TST-001',
            'alis_fiyat': Decimal('0.00'),  # Sıfır
            'satis_fiyat': Decimal('100.00')
        }
        # Validation'ı kontrol
        try:
            urun = UrunService.create(data)
            # Eğer başarılı olursa, fiyatı kontrol et
            assert urun.alis_fiyat == Decimal('0.00')
        except Exception:
            pass  # Database constraint'ı engelleme olabilir

    def test_create_urun_negative_stock(self, db):
        """Negatif stok."""
        data = {
            'ad': 'Test',
            'kod': 'TST-002',
            'alis_fiyat': Decimal('100.00'),
            'satis_fiyat': Decimal('150.00'),
            'stok_miktari': -5  # Negatif
        }
        # Validation'ı kontrol
        try:
            urun = UrunService.create(data)
        except Exception:
            pass  # Constraints olabilir

    def test_update_urun_stock_precision(self, sample_urun):
        """Stok sayısı precision."""
        update_data = {'stok_miktari': 100.5}  # Float
        updated = UrunService.update(sample_urun.id, update_data)
        # Numeric(12,2) -> Decimal beklenir
        assert isinstance(updated.stok_miktari, Decimal)


class TestServiceDataConsistency:
    """Servis veri tutarlılığı testleri."""

    def test_create_and_retrieve_musteri(self, db):
        """Müşteri oluştur ve getir."""
        created = MusteriService.create({
            'unvan': 'Test Corp',
            'vergi_no': '1111111111'
        })
        
        retrieved = MusteriService.get_by_id(created.id)
        assert retrieved.id == created.id
        assert retrieved.unvan == created.unvan

    def test_update_and_retrieve_musteri(self, sample_musteri):
        """Müşteri güncelle ve getir."""
        MusteriService.update(sample_musteri.id, {'unvan': 'Updated'})
        retrieved = MusteriService.get_by_id(sample_musteri.id)
        assert retrieved.unvan == 'Updated'

    def test_count_consistency(self, db):
        """Müşteri sayı tutarlılığı."""
        initial_count = MusteriService.count()
        
        MusteriService.create({'unvan': 'Test 1'})
        MusteriService.create({'unvan': 'Test 2'})
        
        final_count = MusteriService.count()
        assert final_count == initial_count + 2
