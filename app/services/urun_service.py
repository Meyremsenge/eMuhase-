"""
Ürün Servisi - Ürün iş mantığı katmanı
"""
import logging
from app.repositories.urun_repository import UrunRepository
from app.middleware import AuditLogContext

logger = logging.getLogger(__name__)


class UrunService:
    """Ürün iş kurallarını yöneten servis sınıfı."""

    @staticmethod
    def get_all():
        """Tüm ürünleri döndürür."""
        logger.debug("UrunService.get_all() çağrıldı")
        try:
            result = UrunRepository.get_all()
            logger.info(f"Ürünler listelendi: {len(result) if result else 0} kayıt")
            return result
        except Exception as e:
            logger.error(f"Ürün listesi alınırken hata: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_by_id(urun_id):
        """ID'ye göre ürün getirir."""
        try:
            result = UrunRepository.get_by_id(urun_id)
            if result:
                logger.debug(f"Ürün bulundu: ID={urun_id}, Ad={result.ad}")
            else:
                logger.warning(f"Ürün bulunamadı: ID={urun_id}")
            return result
        except Exception as e:
            logger.error(f"Ürün getirme hatası (ID: {urun_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def search(keyword):
        """Ürün adına göre arama yapar."""
        logger.debug(f"Ürün araması: keyword='{keyword}'")
        try:
            result = UrunRepository.search_by_ad(keyword)
            logger.info(f"Arama sonucu: {len(result) if result else 0} ürün bulundu")
            return result
        except Exception as e:
            logger.error(f"Ürün araması hatası (keyword: {keyword}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def create(data):
        """Yeni ürün oluşturur. Kod benzersizlik kontrolü yapar."""
        logger.info(f"Yeni ürün oluşturma talep: Ad={data.get('ad')}, Kod={data.get('kod')}")

        try:
            with AuditLogContext('urunler', 'CREATE', kayit_id='NEW') as audit:
                if data.get('kod'):
                    existing = UrunRepository.get_by_kod(data['kod'])
                    if existing:
                        logger.warning(f"Ürün kodu çakışması: {data['kod']} zaten kayıtlı (ID: {existing.id})")
                        raise ValueError('Bu ürün kodu zaten kayıtlı.')

                result = UrunRepository.create(**data)
                audit.add_change('ad', 'N/A', result.ad)
                audit.add_change('kod', 'N/A', result.kod)
                logger.info(f"Ürün oluşturuldu: ID={result.id}, Ad={result.ad}")
                return result
        except Exception as e:
            logger.error(f"Ürün oluşturma hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def update(urun_id, data):
        """Ürünü günceller."""
        logger.info(f"Ürün güncelleme talep: ID={urun_id}")

        try:
            urun = UrunRepository.get_by_id(urun_id)
            if urun is None:
                logger.error(f"Güncellenecek ürün bulunamadı: ID={urun_id}")
                raise ValueError('Ürün bulunamadı.')

            if data.get('kod') and data['kod'] != urun.kod:
                existing = UrunRepository.get_by_kod(data['kod'])
                if existing:
                    logger.warning(f"Ürün kodu çakışması güncellemede: {data['kod']} zaten başka ürüne ait")
                    raise ValueError('Bu ürün kodu başka bir ürüne ait.')

            with AuditLogContext('urunler', 'UPDATE', kayit_id=urun_id) as audit:
                for key, new_value in data.items():
                    old_value = getattr(urun, key, None)
                    if old_value != new_value:
                        audit.add_change(key, old_value, new_value)

                result = UrunRepository.update(urun_id, **data)
                logger.info(f"Ürün güncellendi: ID={urun_id}")
                return result
        except Exception as e:
            logger.error(f"Ürün güncelleme hatası (ID: {urun_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def delete(urun_id):
        """Ürünü siler."""
        logger.info(f"Ürün silme talep: ID={urun_id}")

        try:
            if not UrunRepository.get_by_id(urun_id):
                logger.error(f"Silinecek ürün bulunamadı: ID={urun_id}")
                raise ValueError('Ürün bulunamadı.')

            with AuditLogContext('urunler', 'DELETE', kayit_id=urun_id) as audit:
                audit.add_change('silinme_tarihi', 'NULL', 'datetime.now(timezone.utc)')
                result = UrunRepository.delete(urun_id)
                logger.info(f"Ürün silindi: ID={urun_id}")
                return result
        except Exception as e:
            logger.error(f"Ürün silme hatası (ID: {urun_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_aktif():
        """Aktif ürünleri döndürür."""
        logger.debug("Aktif ürünler getiriliyor")
        try:
            result = UrunRepository.get_aktif()
            logger.info(f"Aktif ürün sayısı: {len(result) if result else 0}")
            return result
        except Exception as e:
            logger.error(f"Aktif ürün getirme hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def count():
        """Toplam ürün sayısını döndürür."""
        try:
            result = UrunRepository.count()
            logger.debug(f"Ürün sayısı: {result}")
            return result
        except Exception as e:
            logger.error(f"Ürün sayısı alınırken hata: {str(e)}", exc_info=True)
            raise
