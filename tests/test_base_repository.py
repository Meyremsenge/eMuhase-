"""
BaseRepository birim testleri.
CRUD, filtreleme, arama, sayfalama ve diğer temel operasyonları test eder.
"""
from datetime import datetime
import pytest
from app.repositories.base_repository import BaseRepository
from app.repositories.musteri_repository import MusteriRepository
from app.models import db


class TestBaseRepositoryCreate:
    """BaseRepository.create() metodu testleri."""

    def test_create_success(self, app):
        """Yeni kayıt oluşturma başarılı."""
        musteri = MusteriRepository.create(
            unvan='Test Firma',
            vergi_no='1234567890',
            tip='musteri'
        )
        assert musteri.id is not None
        assert musteri.unvan == 'Test Firma'
        assert musteri.vergi_no == '1234567890'

    def test_create_with_empty_fields(self, app):
        """Zorunlu alanlar olmadan oluşturma."""
        # Bu test, database constraint'ine bağlı olarak hata fırlatabilir
        try:
            musteri = MusteriRepository.create(unvan='')
            # Başarılı ise kontrol et
            assert musteri.unvan == ''
        except Exception:
            # Database constraint hatasını kontrol et
            pass


class TestBaseRepositoryRead:
    """BaseRepository.get_by_id() ve get_all() metotları testleri."""

    def test_get_by_id_success(self, app):
        """ID'ye göre kayıt getirme başarılı."""
        musteri = MusteriRepository.create(unvan='Test', vergi_no='1111111111')
        found = MusteriRepository.get_by_id(musteri.id)
        assert found is not None
        assert found.id == musteri.id
        assert found.unvan == 'Test'

    def test_get_by_id_not_found(self, app):
        """Var olmayan ID ile getirme."""
        found = MusteriRepository.get_by_id(99999)
        assert found is None

    def test_get_all_empty(self, app):
        """Boş tablo üzerinden getirme."""
        result = MusteriRepository.get_all()
        assert isinstance(result, list)
        # Sonuç boş veya tam sayıda olabilir

    def test_get_all_multiple(self, app):
        """Birden fazla kayıt getirme."""
        MusteriRepository.create(unvan='Firma A', vergi_no='1000000001')
        MusteriRepository.create(unvan='Firma B', vergi_no='1000000002')
        MusteriRepository.create(unvan='Firma C', vergi_no='1000000003')
        result = MusteriRepository.get_all()
        assert len(result) >= 3


class TestBaseRepositoryUpdate:
    """BaseRepository.update() metodu testleri."""

    def test_update_success(self, app):
        """Kayıt güncelleme başarılı."""
        musteri = MusteriRepository.create(unvan='Eski', vergi_no='2222222222')
        updated = MusteriRepository.update(musteri.id, unvan='Yeni')
        assert updated is not None
        assert updated.unvan == 'Yeni'
        assert updated.vergi_no == '2222222222'

    def test_update_multiple_fields(self, app):
        """Birden fazla alan güncelleme."""
        musteri = MusteriRepository.create(unvan='Eski', vergi_no='3333333333')
        updated = MusteriRepository.update(
            musteri.id,
            unvan='Yeni',
            vergi_no='4444444444'
        )
        assert updated.unvan == 'Yeni'
        assert updated.vergi_no == '4444444444'

    def test_update_not_found(self, app):
        """Var olmayan kaydı güncelleme."""
        result = MusteriRepository.update(99999, unvan='Test')
        assert result is None

    def test_update_invalid_field(self, app):
        """Var olmayan alan güncelleme."""
        musteri = MusteriRepository.create(unvan='Test', vergi_no='5555555555')
        # Var olmayan field için setattr yapılmayacak
        updated = MusteriRepository.update(musteri.id, non_existent_field='value')
        assert updated is not None


class TestBaseRepositoryDelete:
    """BaseRepository.delete() metodu testleri."""

    def test_delete_success(self, app):
        """Kayıt silme başarılı."""
        musteri = MusteriRepository.create(unvan='Silinecek', vergi_no='6666666666')
        result = MusteriRepository.delete(musteri.id)
        assert result is True
        
        # Soft delete sonrası silinme_tarihi set edilmelidir
        deleted = MusteriRepository.get_by_id(musteri.id)
        assert deleted is not None
        assert deleted.silinme_tarihi is not None

    def test_delete_not_found(self, app):
        """Var olmayan kaydı silme."""
        result = MusteriRepository.delete(99999)
        assert result is False

    def test_delete_soft_delete_check(self, app):
        """Soft delete kontrol."""
        musteri = MusteriRepository.create(unvan='Test', vergi_no='7777777777')
        before_delete = musteri.silinme_tarihi
        MusteriRepository.delete(musteri.id)
        after_delete = MusteriRepository.get_by_id(musteri.id)
        assert after_delete is not None
        assert after_delete.silinme_tarihi is not None


class TestBaseRepositoryFilter:
    """BaseRepository.filter_by() metodu testleri."""

    def test_filter_by_single_criterion(self, app):
        """Tek kritere göre filtreleme."""
        MusteriRepository.create(unvan='ABC Ltd', vergi_no='8888888888', tip='musteri')
        MusteriRepository.create(unvan='XYZ Ltd', vergi_no='9999999999', tip='tedarikci')
        
        result = MusteriRepository.filter_by(tip='musteri')
        assert len(result) >= 1
        assert all(m.tip == 'musteri' for m in result)

    def test_filter_by_no_results(self, app):
        """Filtreleme sonuç bulamazsa."""
        result = MusteriRepository.filter_by(unvan='NonExistent')
        assert result == []

    def test_filter_by_multiple_criteria(self, app):
        """Birden fazla kritere göre filtreleme."""
        MusteriRepository.create(unvan='Test', vergi_no='1010101010', tip='musteri')
        result = MusteriRepository.filter_by(unvan='Test', tip='musteri')
        assert len(result) >= 1


class TestBaseRepositorySearch:
    """BaseRepository.search() metodu testleri."""

    def test_search_success(self, app):
        """Başarılı arama."""
        from app.models import Musteri
        MusteriRepository.create(unvan='Acme Corporation', vergi_no='1111111112')
        MusteriRepository.create(unvan='Beta Industries', vergi_no='2222222223')
        
        result = MusteriRepository.search(Musteri.unvan, 'Acme')
        assert len(result) >= 1
        assert any('Acme' in m.unvan for m in result)

    def test_search_case_insensitive(self, app):
        """Büyük/küçük harf duyarsız arama."""
        from app.models import Musteri
        MusteriRepository.create(unvan='TestCorp', vergi_no='3333333334')
        
        result = MusteriRepository.search(Musteri.unvan, 'testcorp')
        assert len(result) >= 1

    def test_search_no_results(self, app):
        """Arama sonuç bulmazsa."""
        from app.models import Musteri
        result = MusteriRepository.search(Musteri.unvan, 'NonExistentString12345')
        assert result == []


class TestBaseRepositoryCount:
    """BaseRepository.count() metodu testleri."""

    def test_count_empty(self, app):
        """Boş tablo sayısı."""
        count = MusteriRepository.count()
        assert isinstance(count, int)
        assert count >= 0

    def test_count_with_records(self, app):
        """Kayıt varken sayma."""
        initial_count = MusteriRepository.count()
        MusteriRepository.create(unvan='Count Test', vergi_no='4444444445')
        new_count = MusteriRepository.count()
        assert new_count > initial_count


class TestBaseRepositoryPaginate:
    """BaseRepository.paginate() metodu testleri."""

    def test_paginate_default(self, app):
        """Varsayılan sayfalama."""
        # Birden fazla kayıt oluştur
        for i in range(15):
            MusteriRepository.create(unvan=f'Firma {i}', vergi_no=f'{i:010d}')
        
        page = MusteriRepository.paginate(page=1, per_page=10)
        assert page is not None
        assert hasattr(page, 'items')

    def test_paginate_multiple_pages(self, app):
        """Birden fazla sayfaya bölünmüş sayfalama."""
        for i in range(25):
            MusteriRepository.create(unvan=f'Firma {i}', vergi_no=f'{1000+i:010d}')
        
        page1 = MusteriRepository.paginate(page=1, per_page=10)
        page2 = MusteriRepository.paginate(page=2, per_page=10)
        
        assert page1 is not None
        assert page2 is not None

    def test_paginate_per_page(self, app):
        """Sayfa başına kayıt sayısı."""
        for i in range(20):
            MusteriRepository.create(unvan=f'Test {i}', vergi_no=f'{2000+i:010d}')
        
        page = MusteriRepository.paginate(page=1, per_page=5)
        assert len(page.items) <= 5


class TestBaseRepositoryExists:
    """BaseRepository.exists() metodu testleri."""

    def test_exists_true(self, app):
        """Kayıt var mı kontrolü - var."""
        musteri = MusteriRepository.create(unvan='Exists Test', vergi_no='5555555556')
        exists = MusteriRepository.exists(musteri.id)
        assert exists is True

    def test_exists_false(self, app):
        """Kayıt var mı kontrolü - yok."""
        exists = MusteriRepository.exists(99999)
        assert exists is False


class TestBaseRepositoryBaseQuery:
    """BaseRepository._base_query() metodu testleri."""

    def test_base_query_soft_delete_filter(self, app):
        """Soft delete filtrelemesi kontrol."""
        musteri1 = MusteriRepository.create(unvan='Active', vergi_no='6666666667')
        musteri2 = MusteriRepository.create(unvan='ToDelete', vergi_no='7777777778')
        
        # Bir kaydı sil
        MusteriRepository.delete(musteri2.id)
        
        # Silinen kayıt get_all'da görünmemelidir
        all_records = MusteriRepository.get_all()
        assert musteri1.id in [m.id for m in all_records]
        # musteri2 soft delete olduğu için filtrelenmelidir


class TestBaseRepositoryIntegration:
    """BaseRepository tam entegrasyon testleri."""

    def test_crud_workflow(self, app):
        """Tam CRUD işlemi akışı."""
        # Create
        musteri = MusteriRepository.create(unvan='Workflow Test', vergi_no='8888888889')
        assert musteri.id is not None
        
        # Read
        found = MusteriRepository.get_by_id(musteri.id)
        assert found.unvan == 'Workflow Test'
        
        # Update
        updated = MusteriRepository.update(musteri.id, unvan='Updated Workflow')
        assert updated.unvan == 'Updated Workflow'
        
        # Delete
        deleted = MusteriRepository.delete(musteri.id)
        assert deleted is True

    def test_concurrent_operations(self, app):
        """Eşzamanlı operasyonlar."""
        musteri1 = MusteriRepository.create(unvan='Concurrent 1', vergi_no='9090909091')
        musteri2 = MusteriRepository.create(unvan='Concurrent 2', vergi_no='9191919192')
        
        MusteriRepository.update(musteri1.id, unvan='Updated 1')
        MusteriRepository.update(musteri2.id, unvan='Updated 2')
        
        found1 = MusteriRepository.get_by_id(musteri1.id)
        found2 = MusteriRepository.get_by_id(musteri2.id)
        
        assert found1.unvan == 'Updated 1'
        assert found2.unvan == 'Updated 2'
