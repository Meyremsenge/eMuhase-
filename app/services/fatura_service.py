"""
Fatura Servisi - Fatura iş mantığı katmanı (alış, satış, iade)
"""
import logging
from app.repositories.alis_fatura_repository import AlisFaturaRepository
from app.repositories.satis_fatura_repository import SatisFaturaRepository
from app.repositories.iade_fatura_repository import IadeFaturaRepository
from app.middleware import AuditLogContext

logger = logging.getLogger(__name__)


class FaturaService:
    """Fatura iş kurallarını yöneten servis sınıfı."""

    # ── Alış Faturaları ──

    @staticmethod
    def get_alis_all():
        logger.debug("FaturaService.get_alis_all() çağrıldı")
        try:
            result = AlisFaturaRepository.get_all()
            logger.info(f"Alış faturaları listelendi: {len(result) if result else 0} kayıt")
            return result
        except Exception as e:
            logger.error(f"Alış faturası listesi alınırken hata: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_alis_by_id(fatura_id):
        try:
            result = AlisFaturaRepository.get_by_id(fatura_id)
            if result:
                logger.debug(f"Alış faturası bulundu: ID={fatura_id}, No={result.fatura_no}")
            else:
                logger.warning(f"Alış faturası bulunamadı: ID={fatura_id}")
            return result
        except Exception as e:
            logger.error(f"Alış faturası getirme hatası (ID: {fatura_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def create_alis(fatura_data, kalemler_data):
        logger.info("Yeni alış faturası oluşturma talep: No=%s, Müşteri=%s",
                    fatura_data.get('fatura_no'), fatura_data.get('musteri_unvan'))

        try:
            with AuditLogContext('alis_faturalari', 'CREATE', kayit_id='NEW') as audit:
                if AlisFaturaRepository.get_by_fatura_no(fatura_data.get('fatura_no')):
                    logger.warning(f"Alış fatura numarası çakışması: {fatura_data.get('fatura_no')} zaten kayıtlı")
                    raise ValueError('Bu fatura numarası zaten kayıtlı.')

                result = AlisFaturaRepository.create_with_kalemler(fatura_data, kalemler_data)
                audit.add_change('fatura_no', 'N/A', result.fatura_no)
                audit.add_change('kalem_sayı', '0', len(kalemler_data))
                logger.info("Alış faturası oluşturuldu: ID=%s, No=%s, Kalem Sayı=%s",
                            result.id, result.fatura_no, len(kalemler_data))
                return result
        except Exception as e:
            logger.error(f"Alış faturası oluşturma hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def delete_alis(fatura_id):
        logger.info(f"Alış faturası silme talep: ID={fatura_id}")

        try:
            if not AlisFaturaRepository.get_by_id(fatura_id):
                logger.error(f"Silinecek alış faturası bulunamadı: ID={fatura_id}")
                raise ValueError('Alış faturası bulunamadı.')

            with AuditLogContext('alis_faturalari', 'DELETE', kayit_id=fatura_id) as audit:
                audit.add_change('silinme_tarihi', 'NULL', 'datetime.now(timezone.utc)')
                result = AlisFaturaRepository.soft_delete(fatura_id)
                logger.info(f"Alış faturası silindi: ID={fatura_id}")
                return result
        except Exception as e:
            logger.error(f"Alış faturası silme hatası (ID: {fatura_id}): {str(e)}", exc_info=True)
            raise

    # ── Satış Faturaları ──

    @staticmethod
    def get_satis_all():
        logger.debug("FaturaService.get_satis_all() çağrıldı")
        try:
            result = SatisFaturaRepository.get_all()
            logger.info(f"Satış faturaları listelendi: {len(result) if result else 0} kayıt")
            return result
        except Exception as e:
            logger.error(f"Satış faturası listesi alınırken hata: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_satis_by_id(fatura_id):
        try:
            result = SatisFaturaRepository.get_by_id(fatura_id)
            if result:
                logger.debug(f"Satış faturası bulundu: ID={fatura_id}, No={result.fatura_no}")
            else:
                logger.warning(f"Satış faturası bulunamadı: ID={fatura_id}")
            return result
        except Exception as e:
            logger.error(f"Satış faturası getirme hatası (ID: {fatura_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def create_satis(fatura_data, kalemler_data):
        logger.info("Yeni satış faturası oluşturma talep: No=%s, Müşteri=%s",
                    fatura_data.get('fatura_no'), fatura_data.get('musteri_unvan'))

        try:
            with AuditLogContext('satis_faturalari', 'CREATE', kayit_id='NEW') as audit:
                if SatisFaturaRepository.get_by_fatura_no(fatura_data.get('fatura_no')):
                    logger.warning(f"Satış fatura numarası çakışması: {fatura_data.get('fatura_no')} zaten kayıtlı")
                    raise ValueError('Bu fatura numarası zaten kayıtlı.')

                result = SatisFaturaRepository.create_with_kalemler(fatura_data, kalemler_data)
                audit.add_change('fatura_no', 'N/A', result.fatura_no)
                audit.add_change('kalem_sayı', '0', len(kalemler_data))
                logger.info("Satış faturası oluşturuldu: ID=%s, No=%s, Kalem Sayı=%s",
                            result.id, result.fatura_no, len(kalemler_data))
                return result
        except Exception as e:
            logger.error(f"Satış faturası oluşturma hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def delete_satis(fatura_id):
        logger.info(f"Satış faturası silme talep: ID={fatura_id}")

        try:
            if not SatisFaturaRepository.get_by_id(fatura_id):
                logger.error(f"Silinecek satış faturası bulunamadı: ID={fatura_id}")
                raise ValueError('Satış faturası bulunamadı.')

            with AuditLogContext('satis_faturalari', 'DELETE', kayit_id=fatura_id) as audit:
                audit.add_change('silinme_tarihi', 'NULL', 'datetime.now(timezone.utc)')
                result = SatisFaturaRepository.soft_delete(fatura_id)
                logger.info(f"Satış faturası silindi: ID={fatura_id}")
                return result
        except Exception as e:
            logger.error(f"Satış faturası silme hatası (ID: {fatura_id}): {str(e)}", exc_info=True)
            raise

    # ── İade Faturaları ──

    @staticmethod
    def get_iade_all():
        logger.debug("FaturaService.get_iade_all() çağrıldı")
        try:
            result = IadeFaturaRepository.get_all()
            logger.info(f"İade faturaları listelendi: {len(result) if result else 0} kayıt")
            return result
        except Exception as e:
            logger.error(f"İade faturası listesi alınırken hata: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_iade_by_id(fatura_id):
        try:
            result = IadeFaturaRepository.get_by_id(fatura_id)
            if result:
                logger.debug(f"İade faturası bulundu: ID={fatura_id}, No={result.fatura_no}")
            else:
                logger.warning(f"İade faturası bulunamadı: ID={fatura_id}")
            return result
        except Exception as e:
            logger.error(f"İade faturası getirme hatası (ID: {fatura_id}): {str(e)}", exc_info=True)
            raise

    @staticmethod
    def create_iade(fatura_data, kalemler_data):
        logger.info("Yeni İade faturası oluşturma talep: No=%s, Müşteri=%s",
                    fatura_data.get('fatura_no'), fatura_data.get('musteri_unvan'))

        try:
            with AuditLogContext('iade_faturalari', 'CREATE', kayit_id='NEW') as audit:
                if IadeFaturaRepository.get_by_fatura_no(fatura_data.get('fatura_no')):
                    logger.warning(f"İade fatura numarası çakışması: {fatura_data.get('fatura_no')} zaten kayıtlı")
                    raise ValueError('Bu fatura numarası zaten kayıtlı.')

                result = IadeFaturaRepository.create_with_kalemler(fatura_data, kalemler_data)
                audit.add_change('fatura_no', 'N/A', result.fatura_no)
                audit.add_change('kalem_sayı', '0', len(kalemler_data))
                logger.info("İade faturası oluşturuldu: ID=%s, No=%s, Kalem Sayı=%s",
                            result.id, result.fatura_no, len(kalemler_data))
                return result
        except Exception as e:
            logger.error(f"İade faturası oluşturma hatası: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def delete_iade(fatura_id):
        logger.info(f"İade faturası silme talep: ID={fatura_id}")

        try:
            if not IadeFaturaRepository.get_by_id(fatura_id):
                logger.error(f"Silinecek İade faturası bulunamadı: ID={fatura_id}")
                raise ValueError('İade faturası bulunamadı.')

            with AuditLogContext('iade_faturalari', 'DELETE', kayit_id=fatura_id) as audit:
                audit.add_change('silinme_tarihi', 'NULL', 'datetime.now(timezone.utc)')
                result = IadeFaturaRepository.soft_delete(fatura_id)
                logger.info(f"İade faturası silindi: ID={fatura_id}")
                return result
        except Exception as e:
            logger.error(f"İade faturası silme hatası (ID: {fatura_id}): {str(e)}", exc_info=True)
            raise

    # ── Özet İstatistikler ──

    @staticmethod
    def get_summary():
        """Dashboard için fatura özetleri."""
        logger.debug("Dashboard özetleri getiriliyor")
        try:
            summary = {
                'alis_count': AlisFaturaRepository.count(),
                'satis_count': SatisFaturaRepository.count(),
                'iade_count': IadeFaturaRepository.count(),
            }
            logger.debug(f"Dashboard özeti: {summary}")
            return summary
        except Exception as e:
            logger.error(f"Dashboard özeti alınırken hata: {str(e)}", exc_info=True)
            raise
