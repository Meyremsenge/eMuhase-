"""
Middleware Module - API Request/Response Logging
API çağrılarını yakala, logla ve audit trail'e ekle.
"""

import logging
import time
from functools import wraps
from uuid import uuid4
from flask import request, g, current_app

logger = logging.getLogger(__name__)

_REQUEST_ID_HEADER = "X-Request-ID"

_PII_FIELDS = {
    'password', 'sifre', 'password_hash', 'sifre_hash', 'token', 'refresh_token',
    'email', 'telefon', 'phone', 'adres', 'address'
}


def log_request_response():
    """
    Flask before_request/after_request hook olarak kullanılan middleware.
    Tüm HTTP isteklerini ve yanıtlarını loglar.

    Usage in app/__init__.py:
        @app.before_request
        def before_request():
            log_request_response.before_request()

        @app.after_request
        def after_request(response):
            return log_request_response.after_request(response)
    """

    def before_request_hook():
        """İsteğin başında bilgileri yakala."""
        g.start_time = time.time()
        header_request_id = (request.headers.get(_REQUEST_ID_HEADER) or "").strip()
        g.request_id = header_request_id if header_request_id else uuid4().hex

        # Duyarlı verileri minimize et (sadece alan adlarini logla)
        request_data = request.get_json(silent=True) or request.form.to_dict()
        data_keys = []
        if isinstance(request_data, dict):
            for key in request_data.keys():
                if key.lower() in _PII_FIELDS:
                    data_keys.append(f'{key}=[MASKED]')
                else:
                    data_keys.append(key)

        log_message = (
            f"[{g.request_id}] "
            f"{request.method} {request.path} "
            f"| IP: {request.remote_addr} "
            f"| Content-Type: {request.content_type or 'N/A'}"
        )

        if data_keys:
            log_message += f" | DataKeys: {data_keys}"

        logger.info(log_message)
        return None

    def after_request_hook(response):
        """İsteğin sonunda yanıt bilgilerini logla."""
        if hasattr(g, 'start_time'):
            duration_ms = round((time.time() - g.start_time) * 1000)
        else:
            duration_ms = 0

        response.headers[_REQUEST_ID_HEADER] = getattr(g, 'request_id', '')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('X-XSS-Protection', '1; mode=block')
        response.headers.setdefault('Referrer-Policy', 'no-referrer')

        if request.path.startswith('/api'):
            response.headers.setdefault(
                'Content-Security-Policy',
                "default-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            )

        if current_app.config.get('STRICT_TRANSPORT_SECURITY'):
            forwarded_proto = (request.headers.get('X-Forwarded-Proto') or '').lower()
            if request.is_secure or forwarded_proto == 'https':
                response.headers.setdefault(
                    'Strict-Transport-Security',
                    'max-age=63072000; includeSubDomains; preload'
                )

        log_message = (
            f"[{getattr(g, 'request_id', 'unknown')}] "
            f"{request.method} {request.path} "
            f"-> {response.status_code} "
            f"({duration_ms}ms)"
        )

        # Status koduna göre log seviyesini belirle
        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return response

    return before_request_hook, after_request_hook


before_request, after_request = log_request_response()


def log_database_operation(operation_type):
    """
    Decorator: Database operasyonlarını logla (CREATE, UPDATE, DELETE).

    Usage:
        @log_database_operation('INSERT')
        def create_musteri(self, musteri):
            # method body
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"DB {operation_type}: {func.__qualname__} | Success"
                )
                return result
            except Exception as e:
                logger.error(
                    f"DB {operation_type}: {func.__qualname__} | Error: {str(e)}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_service_operation(service_name):
    """
    Decorator: Service layer operasyonlarını logla.

    Usage:
        @log_service_operation('MusteriService')
        def validate_mustteri_data(self, data):
            # method body
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(
                f"{service_name}.{func.__name__} called with args={args[1:]} kwargs={kwargs}"
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"{service_name}.{func.__name__} completed successfully"
                )
                return result
            except Exception as e:
                logger.error(
                    f"{service_name}.{func.__name__} failed: {str(e)}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_error_handler(error_code, error_name):
    """
    Decorator: Error handler'ları logla.

    Usage:
        @app.errorhandler(404)
        @log_error_handler(404, 'NotFound')
        def handle_not_found(error):
            # error handler body
    """
    def decorator(func):
        @wraps(func)
        def wrapper(error):
            logger.warning(
                f"[{error_code}] {error_name}: {request.method} {request.path} | {str(error)}"
            )
            return func(error)
        return wrapper
    return decorator


class AuditLogContext:
    """
    Context manager: Audit log bilgilerini otomatik olarak kaydeder.

    Usage:
        with AuditLogContext('musteriler', 'UPDATE', user_id=1) as audit:
            # update operasyonu
            audit.add_change('unvan', 'old_value', 'new_value')
    """

    def __init__(self, tablo_adi, islem_tipi, user_id=None, kayit_id=None):
        self.tablo_adi = tablo_adi
        self.islem_tipi = islem_tipi
        self.user_id = user_id
        self.kayit_id = kayit_id
        self.changes = {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.debug(
            f"AUDIT START: {self.islem_tipi} on {self.tablo_adi} (ID: {self.kayit_id}) by user {self.user_id}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = round((time.time() - self.start_time) * 1000)

        if exc_type is None:
            logger.info(
                f"AUDIT SUCCESS: {self.islem_tipi} on {self.tablo_adi} (ID: {self.kayit_id}) | "
                f"Changes: {self.changes} | Duration: {duration_ms}ms"
            )
        else:
            logger.error(
                f"AUDIT FAILED: {self.islem_tipi} on {self.tablo_adi} (ID: {self.kayit_id}) | "
                f"Error: {exc_val} | Duration: {duration_ms}ms",
                exc_info=True
            )

        return False  # Exception'ı propagate et

    def add_change(self, field_name, old_value, new_value):
        """Değişkin bir alanı audit trail'e ekle."""
        self.changes[field_name] = {
            'old': old_value,
            'new': new_value
        }
        logger.debug(f"  Field '{field_name}' changed: {old_value} -> {new_value}")


def format_context_for_logging(data):
    """
    Sensitif veriler içerebilecek kontekst bilgisini format et.
    Password, token gibi alanları mask' et.

    Args:
        data: Dictionary format veri

    Returns:
        Masked version of data
    """
    sensitive_fields = ['password', 'token', 'key', 'secret', 'card', 'cvv', 'dak', 'banka', 'hesap']

    masked = {}
    for key, value in data.items():
        if any(s in key.lower() for s in sensitive_fields):
            masked[key] = '***MASKED***'
        elif isinstance(value, dict):
            masked[key] = format_context_for_logging(value)
        elif isinstance(value, list):
            masked[key] = [format_context_for_logging(item) if isinstance(item, dict) else item for item in value]
        else:
            masked[key] = value

    return masked
