"""
Müşteri Repository birim testleri.
CRUD, arama ve filtreleme operasyonlarını test eder.
"""
from app.repositories.musteri_repository import MusteriRepository


class TestMusteriRepository:
    """MusteriRepository CRUD testleri."""

    def test_create(self, app):
        musteri = MusteriRepository.create(
            unvan='Test Firma',
            vergi_no='1234567890',
            tip='musteri'
        )
        assert musteri.id is not None
        assert musteri.unvan == 'Test Firma'
        assert musteri.vergi_no == '1234567890'

    def test_get_by_id(self, app):
        musteri = MusteriRepository.create(unvan='ABC Ltd', vergi_no='1111111111')
        found = MusteriRepository.get_by_id(musteri.id)
        assert found is not None
        assert found.unvan == 'ABC Ltd'

    def test_get_by_id_not_found(self, app):
        found = MusteriRepository.get_by_id(9999)
        assert found is None

    def test_get_all(self, app):
        MusteriRepository.create(unvan='Firma A', vergi_no='1000000001')
        MusteriRepository.create(unvan='Firma B', vergi_no='1000000002')
        result = MusteriRepository.get_all()
        assert len(result) == 2

    def test_update(self, app):
        musteri = MusteriRepository.create(unvan='Eski İsim', vergi_no='2222222222')
        updated = MusteriRepository.update(musteri.id, unvan='Yeni İsim')
        assert updated.unvan == 'Yeni İsim'

    def test_delete(self, app):
        musteri = MusteriRepository.create(unvan='Silinecek', vergi_no='3333333333')
        result = MusteriRepository.delete(musteri.id)
        assert result is True
        deleted = MusteriRepository.get_by_id(musteri.id)
        assert deleted is not None
        assert deleted.silinme_tarihi is not None

    def test_delete_not_found(self, app):
        result = MusteriRepository.delete(9999)
        assert result is False

    def test_search_by_unvan(self, app):
        MusteriRepository.create(unvan='Deniz Ticaret', vergi_no='4444444444')
        MusteriRepository.create(unvan='Kara Lojistik', vergi_no='5555555555')
        result = MusteriRepository.search_by_unvan('deniz')
        assert len(result) == 1
        assert result[0].unvan == 'Deniz Ticaret'

    def test_get_by_vergi_no(self, app):
        MusteriRepository.create(unvan='VN Firma', vergi_no='6666666666')
        found = MusteriRepository.get_by_vergi_no('6666666666')
        assert found is not None
        assert found.unvan == 'VN Firma'

    def test_get_aktif(self, app):
        MusteriRepository.create(unvan='Aktif', vergi_no='7777777777', aktif=True)
        MusteriRepository.create(unvan='Pasif', vergi_no='8888888888', aktif=False)
        result = MusteriRepository.get_aktif()
        assert len(result) == 1
        assert result[0].unvan == 'Aktif'

    def test_count(self, app):
        assert MusteriRepository.count() == 0
        MusteriRepository.create(unvan='Sayım', vergi_no='9999999999')
        assert MusteriRepository.count() == 1

    def test_exists(self, app):
        musteri = MusteriRepository.create(unvan='Var mı', vergi_no='1010101010')
        assert MusteriRepository.exists(musteri.id) is True
        assert MusteriRepository.exists(9999) is False
