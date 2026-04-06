"""
Müşteri Servisi - Müşteri iş mantığı katmanı
Route'lardan çağrılır; veri erişimi Repository üzerinden yapılır.
"""
import logging
from app.repositories.musteri_repository import MusteriRepository
from app.middleware import log_service_operation, AuditLogContext

logger = logging.getLogger(__name__)


class MusteriService:
    """Müşteri/Tedarikçi iş kurallarını yöneten servis sınıfı."""

    @staticmethod
    def get_all():
        """Tüm müşterileri döndürür."""
        logger.debug("MusteriService.get_all() çağrıldı")
        try:
            result = MusteriRepository.get_all()
            logger.info(f"Müşteriler listelendi: {len(result) if result else 0} kayıt")
            return result
        except Exception as e:
            logger.error(f"Müşteri listesi alınırken hata: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_by_id(musteri_id):
        """ID'ye göre müşteri getirir."""
        try:
            result = MusteriRepository.get_by_id(musteri_id)
            if result:
                logger.debug(f"Müşteri bulundu: ID={musteri_id}, Ünvan={result.unvan}")
            else:
                logger.warning(f"Müşteri bulunamadı: ID={musteri_id}")
            return result
        except Exception as e:
            logger.error(f"Müşteri getirme hatası (ID: {musteri_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def search(keyword):
        """Ünvana göre arama yapar."""
        logger.debug(f"Müşteri araması: keyword='{keyword}'")
        try:
            result = MusteriRepository.search_by_unvan(keyword)
            logger.info(f"Arama sonucu: {len(result) if result else 0} müşteri bulundu")
            return result
        except Exception as e:
            logger.error(f"Müşteri araması hatası (keyword: {keyword}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def create(data):
        """Yeni müşteri oluşturur. Vergi no kontrolü yapar."""
        logger.info(f"Yeni müşteri oluşturma talep: Ünvan={data.get('unvan')}")
        
        try:
            with AuditLogContext('musteriler', 'CREATE', kayit_id='NEW') as audit:
                if data.get('vergi_no'):
                    existing = MusteriRepository.get_by_vergi_no(data['vergi_no'])
                    if existing:
                        logger.warning(f"Vergi no çakışması: {data['vergi_no']} zaten kayıtlı (ID: {existing.id})")
                        raise ValueError('Bu vergi numarası zaten kayıtlı.')
                
                result = MusteriRepository.create(**data)
                audit.add_change('unvan', 'N/A', result.unvan)
                audit.add_change('vergi_no', 'N/A', result.vergi_no)
                logger.info(f"Müşteri oluşturuldu: ID={result.id}, Ünvan={result.unvan}")
                return result
        except Exception as e:
            logger.error(f"Müşteri oluşturma hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def update(musteri_id, data):
        """Müşteriyi günceller."""
        logger.info(f"Müşteri güncelleme talep: ID={musteri_id}")
        
        try:
            musteri = MusteriRepository.get_by_id(musteri_id)
            if musteri is None:
                logger.error(f"Güncellenecek müşteri bulunamadı: ID={musteri_id}")
                raise ValueError('Müşteri bulunamadı.')
            
            if data.get('vergi_no') and data['vergi_no'] != musteri.vergi_no:
                existing = MusteriRepository.get_by_vergi_no(data['vergi_no'])
                if existing:
                    logger.warning(f"Vergi no çakışması güncellemede: {data['vergi_no']} zaten başka müşteriye ait")
                    raise ValueError('Bu vergi numarası başka bir müşteriye ait.')
            
            with AuditLogContext('musteriler', 'UPDATE', kayit_id=musteri_id) as audit:
                for key, new_value in data.items():
                    old_value = getattr(musteri, key, None)
                    if old_value != new_value:
                        audit.add_change(key, old_value, new_value)
                
                result = MusteriRepository.update(musteri_id, **data)
                logger.info(f"Müşteri güncellendi: ID={musteri_id}")
                return result
        except Exception as e:
            logger.error(f"Müşteri güncelleme hatası (ID: {musteri_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def delete(musteri_id):
        """Müşteriyi siler."""
        logger.info(f"Müşteri silme talep: ID={musteri_id}")
        
        try:
            if not MusteriRepository.exists(musteri_id):
                logger.error(f"Silinecek müşteri bulunamadı: ID={musteri_id}")
                raise ValueError('Müşteri bulunamadı.')
            
            with AuditLogContext('musteriler', 'DELETE', kayit_id=musteri_id) as audit:
                audit.add_change('silinme_tarihi', 'NULL', 'datetime.utcnow()')
                result = MusteriRepository.delete(musteri_id)
                logger.info(f"Müşteri silindi: ID={musteri_id}")
                return result
        except Exception as e:
            logger.error(f"Müşteri silme hatası (ID: {musteri_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_aktif():
        """Aktif müşterileri döndürür."""
        logger.debug("Aktif müşteriler getiriliyor")
        try:
            result = MusteriRepository.get_aktif()
            logger.info(f"Aktif müşteri sayısı: {len(result) if result else 0}")
            return result
        except Exception as e:
            logger.error(f"Aktif müşteri getirme hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def count():
        """Toplam müşteri sayısını döndürür."""
        try:
            result = MusteriRepository.count()
            logger.debug(f"Müşteri sayısı: {result}")
            return result
        except Exception as e:
            logger.error(f"Müşteri sayısı alınırken hata: {str(e)}", exc_info=True)
            raise
