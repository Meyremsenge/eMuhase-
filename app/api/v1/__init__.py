"""
eMuhasebe Pro - API v1
REST API v1 endpoint'leri - Pagination, Validation, Standardized Responses
"""
import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.services.musteri_service import MusteriService
from app.services.urun_service import UrunService
from app.services.fatura_service import FaturaService
from app.validators import (
    MusteriCreateRequest, MusteriUpdateRequest,
    UrunCreateRequest, UrunUpdateRequest,
    AlisFaturaCreateRequest, SatisFaturaCreateRequest, IadeFaturaCreateRequest,
    validate_pagination_params
)
from app.api_utils import (
    paginated_response, single_response, created_response,
    deleted_response, not_found_response, bad_request_response,
    conflict_response, internal_error_response,
    validation_error_response, pydantic_error_to_list,
    musteri_to_dict, urun_to_dict, fatura_to_dict
)
from app import limiter

logger = logging.getLogger(__name__)

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


# ══════════════════════ MÜŞTERİLER ══════════════════════

@api_v1.route('/musteriler', methods=['GET'])
@limiter.limit("30 per minute")
def list_musteriler():
    """
    Müşterileri sayfalama ile listele.

    Query Parameters:
        - page: int (default: 1, min: 1)
        - per_page: int (default: 20, min: 1, max: 100)
        - q: str (arama keyword'ü)

    Örnek: GET /api/v1/musteriler?page=2&per_page=50&q=abc
    """
    try:
        # Pagination parametrelerini parse et
        page, per_page, error = validate_pagination_params(request.args)
        if error:
            logger.warning(f"Pagination error: {error}")
            return bad_request_response(error)

        # Arama keyword'ü kontrol  et
        keyword = request.args.get('q', '').strip()

        if keyword:
            # Arama sonucunu da sayfala
            logger.debug(f"Searching musteriler with keyword: {keyword}")
            musteriler = MusteriService.search(keyword)
            data = [musteri_to_dict(m) for m in (musteriler or [])]
            total = len(data)
            start = (page - 1) * per_page
            end = start + per_page
            paged = data[start:end]
            total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

            from flask import jsonify
            return jsonify({
                'success': True,
                'data': paged,
                'search': {
                    'keyword': keyword,
                    'count': total
                },
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }), 200
        else:
            # Get paginated musteriler
            from app.repositories.musteri_repository import MusteriRepository
            pagination = MusteriRepository.paginate(page=page, per_page=per_page)

            total = pagination.total
            items = pagination.items

            logger.info(f"Listed musteriler: page={page}, per_page={per_page}, total={total}")

            return paginated_response(
                items=items,
                page=page,
                per_page=per_page,
                total=total,
                serialize_func=musteri_to_dict
            )

    except Exception as e:
        logger.error(f"Error listing musteriler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/musteriler/<int:musteri_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_musteri(musteri_id):
    """
    Müşteri detayını al.

    Örnek: GET /api/v1/musteriler/5
    """
    try:
        musteri = MusteriService.get_by_id(musteri_id)
        if not musteri:
            logger.warning(f"Musteri not found: ID={musteri_id}")
            return not_found_response('Müşteri', musteri_id)

        logger.debug(f"Retrieved musteri: ID={musteri_id}")
        return single_response(musteri, serialize_func=musteri_to_dict)

    except Exception as e:
        logger.error(f"Error getting musteri {musteri_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/musteriler', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
def create_musteri():
    """
    Yeni müşteri oluştur.

    Request Body:
        {
            "unvan": "ABC Ltd",
            "vergi_no": "1234567890",
            "email": "info@abc.com",
            "telefon": "+90 532 123 4567",
            "adres": "İstanbul, Türkiye"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body boş')

        # Validation ile request'i parse et
        validated_data = MusteriCreateRequest(**data)

        # Service'e converted dict gönder
        musteri = MusteriService.create(validated_data.model_dump())

        logger.info(f"Created musteri: ID={musteri.id}")
        return created_response(musteri, serialize_func=musteri_to_dict)

    except ValidationError as e:
        logger.warning(f"Validation error creating musteri: {str(e)}")
        errors = pydantic_error_to_list(e.errors())
        return validation_error_response(errors)

    except ValueError as e:
        logger.warning(f"Business logic error creating musteri: {str(e)}")
        return conflict_response(str(e), 'DUPLICATE_ENTRY')

    except Exception as e:
        logger.error(f"Error creating musteri: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/musteriler/<int:musteri_id>', methods=['PUT'])
@limiter.limit("20 per minute")
@jwt_required()
def update_musteri(musteri_id):
    """
    Müşteri güncelle.

    Request Body (tüm alanlar opsiyonel):
        {
            "unvan": "ABC Inc",
            "email": "newemail@abc.com"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body boş')

        # Müşteri var mı kontrol et
        if not MusteriService.get_by_id(musteri_id):
            logger.warning(f"Musteri not found for update: ID={musteri_id}")
            return not_found_response('Müşteri', musteri_id)

        # Validation ile request'i parse et
        validated_data = MusteriUpdateRequest(**data)

        # Null olmayan alanları filter et
        update_data = {k: v for k, v in validated_data.model_dump().items() if v is not None}

        # Service'e gönder
        musteri = MusteriService.update(musteri_id, update_data)

        logger.info(f"Updated musteri: ID={musteri_id}")
        return single_response(musteri, serialize_func=musteri_to_dict)

    except ValidationError as e:
        logger.warning(f"Validation error updating musteri {musteri_id}: {str(e)}")
        errors = pydantic_error_to_list(e.errors())
        return validation_error_response(errors)

    except ValueError as e:
        logger.warning(f"Business logic error updating musteri {musteri_id}: {str(e)}")
        return conflict_response(str(e), 'DUPLICATE_ENTRY')

    except Exception as e:
        logger.error(f"Error updating musteri {musteri_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/musteriler/<int:musteri_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
@jwt_required()
def delete_musteri(musteri_id):
    """Müşteri sil (soft delete)."""
    try:
        if not MusteriService.get_by_id(musteri_id):
            logger.warning(f"Musteri not found for delete: ID={musteri_id}")
            return not_found_response('Müşteri', musteri_id)

        MusteriService.delete(musteri_id)

        logger.info(f"Deleted musteri: ID={musteri_id}")
        return deleted_response(musteri_id, 'Müşteri')

    except Exception as e:
        logger.error(f"Error deleting musteri {musteri_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


# ══════════════════════ ÜRÜNLER ══════════════════════

@api_v1.route('/urunler', methods=['GET'])
@limiter.limit("30 per minute")
def list_urunler():
    """Ürünleri sayfalama ile listele."""
    try:
        page, per_page, error = validate_pagination_params(request.args)
        if error:
            return bad_request_response(error)

        keyword = request.args.get('q', '').strip()

        if keyword:
            logger.debug(f"Searching urunler with keyword: {keyword}")
            urunler = UrunService.search(keyword)
            data = [urun_to_dict(u) for u in (urunler or [])]
            total = len(data)
            start = (page - 1) * per_page
            end = start + per_page
            paged = data[start:end]
            total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

            from flask import jsonify
            return jsonify({
                'success': True,
                'data': paged,
                'search': {'keyword': keyword, 'count': total},
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }), 200
        else:
            from app.repositories.urun_repository import UrunRepository
            pagination = UrunRepository.paginate(page=page, per_page=per_page)

            logger.info(f"Listed urunler: page={page}, per_page={per_page}, total={pagination.total}")

            return paginated_response(
                items=pagination.items,
                page=page,
                per_page=per_page,
                total=pagination.total,
                serialize_func=urun_to_dict
            )

    except Exception as e:
        logger.error(f"Error listing urunler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/urunler/<int:urun_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_urun(urun_id):
    """Ürün detayını al."""
    try:
        urun = UrunService.get_by_id(urun_id)
        if not urun:
            logger.warning(f"Urun not found: ID={urun_id}")
            return not_found_response('Ürün', urun_id)

        logger.debug(f"Retrieved urun: ID={urun_id}")
        return single_response(urun, serialize_func=urun_to_dict)

    except Exception as e:
        logger.error(f"Error getting urun {urun_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/urunler', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
def create_urun():
    """Yeni ürün oluştur."""
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body boş')

        validated_data = UrunCreateRequest(**data)
        urun = UrunService.create(validated_data.model_dump())

        logger.info(f"Created urun: ID={urun.id}")
        return created_response(urun, serialize_func=urun_to_dict)

    except ValidationError as e:
        logger.warning(f"Validation error creating urun: {str(e)}")
        errors = pydantic_error_to_list(e.errors())
        return validation_error_response(errors)

    except ValueError as e:
        logger.warning(f"Business logic error creating urun: {str(e)}")
        return conflict_response(str(e), 'DUPLICATE_ENTRY')

    except Exception as e:
        logger.error(f"Error creating urun: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/urunler/<int:urun_id>', methods=['PUT'])
@limiter.limit("20 per minute")
@jwt_required()
def update_urun(urun_id):
    """Ürün güncelle."""
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body boş')

        if not UrunService.get_by_id(urun_id):
            logger.warning(f"Urun not found for update: ID={urun_id}")
            return not_found_response('Ürün', urun_id)

        validated_data = UrunUpdateRequest(**data)
        update_data = {k: v for k, v in validated_data.model_dump().items() if v is not None}

        urun = UrunService.update(urun_id, update_data)

        logger.info(f"Updated urun: ID={urun_id}")
        return single_response(urun, serialize_func=urun_to_dict)

    except ValidationError as e:
        logger.warning(f"Validation error updating urun {urun_id}: {str(e)}")
        errors = pydantic_error_to_list(e.errors())
        return validation_error_response(errors)

    except ValueError as e:
        logger.warning(f"Business logic error updating urun {urun_id}: {str(e)}")
        return conflict_response(str(e), 'DUPLICATE_ENTRY')

    except Exception as e:
        logger.error(f"Error updating urun {urun_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/urunler/<int:urun_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
@jwt_required()
def delete_urun(urun_id):
    """Ürün sil."""
    try:
        if not UrunService.get_by_id(urun_id):
            logger.warning(f"Urun not found for delete: ID={urun_id}")
            return not_found_response('Ürün', urun_id)

        UrunService.delete(urun_id)

        logger.info(f"Deleted urun: ID={urun_id}")
        return deleted_response(urun_id, 'Ürün')

    except Exception as e:
        logger.error(f"Error deleting urun {urun_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


# ══════════════════════ FATURALAR ══════════════════════

@api_v1.route('/faturalar/ozet', methods=['GET'])
@limiter.limit("60 per minute")
def get_faturalar_summary():
    """Dashboard için fatura özet istatistikleri."""
    try:
        summary = FaturaService.get_summary()
        logger.debug("Retrieved faturalar summary")

        from flask import jsonify
        return jsonify({
            'success': True,
            'data': summary
        }), 200

    except Exception as e:
        logger.error(f"Error getting faturalar summary: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/alis', methods=['GET'])
@limiter.limit("30 per minute")
def list_alis_faturalari():
    """Alış faturalarını listele."""
    try:
        page, per_page, error = validate_pagination_params(request.args)
        if error:
            return bad_request_response(error)

        from app.repositories.alis_fatura_repository import AlisFaturaRepository
        pagination = AlisFaturaRepository.paginate_with_kalemler(page=page, per_page=per_page)

        logger.info(f"Listed alis faturalari: page={page}, total={pagination.total}")

        return paginated_response(
            items=pagination.items,
            page=page,
            per_page=per_page,
            total=pagination.total,
            serialize_func=fatura_to_dict
        )

    except Exception as e:
        logger.error(f"Error listing alis faturalari: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/alis/<int:fatura_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_alis_faturasi(fatura_id):
    """Alış faturası detayını al."""
    try:
        fatura = FaturaService.get_alis_by_id(fatura_id)
        if not fatura:
            logger.warning(f"Alis fatura not found: ID={fatura_id}")
            return not_found_response('Alış Faturası', fatura_id)

        logger.debug(f"Retrieved alis faturasi: ID={fatura_id}")
        return single_response(fatura, serialize_func=fatura_to_dict)

    except Exception as e:
        logger.error(f"Error getting alis faturasi {fatura_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/satis', methods=['GET'])
@limiter.limit("30 per minute")
def list_satis_faturalari():
    """Satış faturalarını listele."""
    try:
        page, per_page, error = validate_pagination_params(request.args)
        if error:
            return bad_request_response(error)

        from app.repositories.satis_fatura_repository import SatisFaturaRepository
        pagination = SatisFaturaRepository.paginate_with_kalemler(page=page, per_page=per_page)

        logger.info(f"Listed satis faturalari: page={page}, total={pagination.total}")

        return paginated_response(
            items=pagination.items,
            page=page,
            per_page=per_page,
            total=pagination.total,
            serialize_func=fatura_to_dict
        )

    except Exception as e:
        logger.error(f"Error listing satis faturalari: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/satis/<int:fatura_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_satis_faturasi(fatura_id):
    """Satış faturası detayını al."""
    try:
        fatura = FaturaService.get_satis_by_id(fatura_id)
        if not fatura:
            logger.warning(f"Satis fatura not found: ID={fatura_id}")
            return not_found_response('Satış Faturası', fatura_id)

        logger.debug(f"Retrieved satis faturasi: ID={fatura_id}")
        return single_response(fatura, serialize_func=fatura_to_dict)

    except Exception as e:
        logger.error(f"Error getting satis faturasi {fatura_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/iade', methods=['GET'])
@limiter.limit("30 per minute")
def list_iade_faturalari():
    """İade faturalarını listele."""
    try:
        page, per_page, error = validate_pagination_params(request.args)
        if error:
            return bad_request_response(error)

        from app.repositories.iade_fatura_repository import IadeFaturaRepository
        pagination = IadeFaturaRepository.paginate_with_kalemler(page=page, per_page=per_page)

        logger.info(f"Listed iade faturalari: page={page}, total={pagination.total}")

        return paginated_response(
            items=pagination.items,
            page=page,
            per_page=per_page,
            total=pagination.total,
            serialize_func=fatura_to_dict
        )

    except Exception as e:
        logger.error(f"Error listing iade faturalari: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/iade/<int:fatura_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_iade_faturasi(fatura_id):
    """İade faturası detayını al."""
    try:
        fatura = FaturaService.get_iade_by_id(fatura_id)
        if not fatura:
            logger.warning(f"Iade fatura not found: ID={fatura_id}")
            return not_found_response('İade Faturası', fatura_id)

        logger.debug(f"Retrieved iade faturasi: ID={fatura_id}")
        return single_response(fatura, serialize_func=fatura_to_dict)

    except Exception as e:
        logger.error(f"Error getting iade faturasi {fatura_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/alis', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
def create_alis_faturasi():
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body boş')
        validated = AlisFaturaCreateRequest(**data)
        payload = validated.model_dump()
        kalemler = payload.pop('kalemler')
        fatura = FaturaService.create_alis(payload, kalemler)
        return created_response(fatura, serialize_func=fatura_to_dict)
    except ValidationError as e:
        return validation_error_response(pydantic_error_to_list(e.errors()))
    except ValueError as e:
        return conflict_response(str(e), 'BUSINESS_RULE_VIOLATION')
    except Exception as e:
        logger.error(f"Error creating alis faturasi: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/alis/<int:fatura_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
@jwt_required()
def delete_alis_faturasi(fatura_id):
    try:
        if not FaturaService.get_alis_by_id(fatura_id):
            return not_found_response('Alış Faturası', fatura_id)
        FaturaService.delete_alis(fatura_id)
        return deleted_response(fatura_id, 'Alış Faturası')
    except ValueError as e:
        return conflict_response(str(e), 'BUSINESS_RULE_VIOLATION')
    except Exception as e:
        logger.error(f"Error deleting alis faturasi {fatura_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/satis', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
def create_satis_faturasi():
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body boş')
        validated = SatisFaturaCreateRequest(**data)
        payload = validated.model_dump()
        kalemler = payload.pop('kalemler')
        fatura = FaturaService.create_satis(payload, kalemler)
        return created_response(fatura, serialize_func=fatura_to_dict)
    except ValidationError as e:
        return validation_error_response(pydantic_error_to_list(e.errors()))
    except ValueError as e:
        return conflict_response(str(e), 'BUSINESS_RULE_VIOLATION')
    except Exception as e:
        logger.error(f"Error creating satis faturasi: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/satis/<int:fatura_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
@jwt_required()
def delete_satis_faturasi(fatura_id):
    try:
        if not FaturaService.get_satis_by_id(fatura_id):
            return not_found_response('Satış Faturası', fatura_id)
        FaturaService.delete_satis(fatura_id)
        return deleted_response(fatura_id, 'Satış Faturası')
    except ValueError as e:
        return conflict_response(str(e), 'BUSINESS_RULE_VIOLATION')
    except Exception as e:
        logger.error(f"Error deleting satis faturasi {fatura_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/iade', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
def create_iade_faturasi():
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body boş')
        validated = IadeFaturaCreateRequest(**data)
        payload = validated.model_dump()
        kalemler = payload.pop('kalemler')
        fatura = FaturaService.create_iade(payload, kalemler)
        return created_response(fatura, serialize_func=fatura_to_dict)
    except ValidationError as e:
        return validation_error_response(pydantic_error_to_list(e.errors()))
    except ValueError as e:
        return conflict_response(str(e), 'BUSINESS_RULE_VIOLATION')
    except Exception as e:
        logger.error(f"Error creating iade faturasi: {str(e)}", exc_info=True)
        return internal_error_response(str(e))


@api_v1.route('/faturalar/iade/<int:fatura_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
@jwt_required()
def delete_iade_faturasi(fatura_id):
    try:
        if not FaturaService.get_iade_by_id(fatura_id):
            return not_found_response('İade Faturası', fatura_id)
        FaturaService.delete_iade(fatura_id)
        return deleted_response(fatura_id, 'İade Faturası')
    except ValueError as e:
        return conflict_response(str(e), 'BUSINESS_RULE_VIOLATION')
    except Exception as e:
        logger.error(f"Error deleting iade faturasi {fatura_id}: {str(e)}", exc_info=True)
        return internal_error_response(str(e))
