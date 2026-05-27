"""
Logging Configuration Module
Uygulamanın tüm logging ihtiyaçlarını merkezi olarak yönetir.
- Console logging (development)
- File logging with rotation (production)
- SQL query logging (SQLAlchemy DEBUG)
- API request/response logging (middleware)
- Error/exception tracking
"""

import json
import logging
import logging.handlers
import os
from pathlib import Path
from flask import has_request_context, g


_PII_FIELDS = {
    'password', 'sifre', 'password_hash', 'sifre_hash', 'token', 'refresh_token',
    'email', 'telefon', 'phone', 'adres', 'address'
}


def setup_logging(app):
    """
    Flask uygulaması için logging'i yapılandırır.

    Args:
        app: Flask application instance

    Environment Variables:
        FLASK_ENV: development|production (default: development)
        LOG_LEVEL: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
        LOG_DIR: Log dosyalarının dizini (default: ./logs)
    """

    # Log dizini oluştur
    log_dir = Path(os.environ.get('LOG_DIR', 'logs'))
    log_dir.mkdir(exist_ok=True)

    # Log seviyesi ayarla
    log_level = app.config.get('LOG_LEVEL', os.environ.get('LOG_LEVEL', 'INFO')).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Root logger'ı yapılandır
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Mevcut handler'ları temizle (multiple initialization'den kaçın)
    root_logger.handlers.clear()

    class PIIMaskFilter(logging.Filter):
        def filter(self, record):
            message = record.getMessage()
            lowered = message.lower()
            if any(field in lowered for field in _PII_FIELDS):
                record.msg = '[MASKED] Sensitive data suppressed'
                record.args = ()
            return True

    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            if has_request_context():
                record.request_id = getattr(g, "request_id", "-")
            else:
                record.request_id = "-"
            return True

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            payload = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "request_id": getattr(record, "request_id", "-"),
                "message": record.getMessage(),
                "file": record.filename,
                "line": record.lineno,
            }
            return json.dumps(payload)

    # Formatter - detaylı format
    log_format = app.config.get('LOG_FORMAT', os.environ.get('LOG_FORMAT', 'plain')).lower()
    json_log_file = app.config.get('LOG_JSON_FILE', os.environ.get('LOG_JSON_FILE'))
    if log_format == 'json':
        detailed_formatter = JsonFormatter(datefmt='%Y-%m-%d %H:%M:%S')
    else:
        detailed_formatter = logging.Formatter(
            fmt=(
                '%(asctime)s - %(name)s - %(levelname)s - '
                '[req=%(request_id)s] - [%(filename)s:%(lineno)d] - %(message)s'
            ),
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console Handler (her zaman ekrana yazı)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(detailed_formatter)
    console_handler.addFilter(RequestIdFilter())
    console_handler.addFilter(PIIMaskFilter())
    root_logger.addHandler(console_handler)

    # File Handler - RotatingFileHandler (production)
    main_log_file = log_dir / 'app.log'
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(main_log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,  # 10 backup file
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    file_handler.addFilter(RequestIdFilter())
    file_handler.addFilter(PIIMaskFilter())
    root_logger.addHandler(file_handler)

    # Erro-specific File Handler
    error_log_file = log_dir / 'errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        filename=str(error_log_file),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    error_handler.addFilter(RequestIdFilter())
    error_handler.addFilter(PIIMaskFilter())
    root_logger.addHandler(error_handler)

    if json_log_file:
        json_handler = logging.handlers.RotatingFileHandler(
            filename=str(json_log_file),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        json_handler.setLevel(numeric_level)
        json_handler.setFormatter(JsonFormatter(datefmt='%Y-%m-%d %H:%M:%S'))
        json_handler.addFilter(RequestIdFilter())
        json_handler.addFilter(PIIMaskFilter())
        root_logger.addHandler(json_handler)

    # SQL Query Logging (SQLAlchemy)
    if os.environ.get('FLASK_ENV') == 'development':
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    else:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # Flask internal logger
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return root_logger


def get_logger(name):
    """
    Adlandırılmış logger döndürür. Tüm modüllerde kullan:

    Example:
        logger = get_logger(__name__)
        logger.info("User login: %s", username)
        logger.error("Database error occurred", exc_info=True)
    """
    return logging.getLogger(name)


# Audit Log Helper Functions
def log_audit_action(logger, user_id, action, tablo_adi, kayit_id, eski_veriler=None, yeni_veriler=None):
    """
    Muhasebe işlemlerini audit trail olarak kaydetir.

    Args:
        logger: Logger instance
        user_id: İşlemi yapan kullanıcı ID'si
        action: CREATE|UPDATE|DELETE
        tablo_adi: Tablo adı (e.g., musteriler, urunler)
        kayit_id: Kayıt ID'si
        eski_veriler: Eski değerler (UPDATE/DELETE için)
        yeni_veriler: Yeni değerler (CREATE/UPDATE için)

    Example:
        log_audit_action(
            logger,
            user_id=1,
            action='UPDATE',
            tablo_adi='musteriler',
            kayit_id=5,
            eski_veriler={'unvan': 'ABC Ltd'},
            yeni_veriler={'unvan': 'ABC Inc'}
        )
    """
    message = f"AUDIT: [{action}] {tablo_adi} (ID: {kayit_id}) by user {user_id}"
    if eski_veriler or yeni_veriler:
        message += f" | Old: {eski_veriler} | New: {yeni_veriler}"
    logger.info(message)


def log_api_call(logger, method, endpoint, user_id=None, ip_address=None, response_code=None, duration_ms=None):
    """
    API çağrılarını kaydeder.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (/api/musteriler, etc.)
        user_id: İsteği yapan kullanıcı ID'si
        ip_address: İstemci IP adresi
        response_code: HTTP response kodu
        duration_ms: İsteğin süresi (milisaniye)

    Example:
        log_api_call(
            logger,
            method='POST',
            endpoint='/api/musteriler',
            user_id=1,
            ip_address='192.168.1.1',
            response_code=201,
            duration_ms=245
        )
    """
    log_parts = [f"API: {method} {endpoint}"]
    if user_id:
        log_parts.append(f"user={user_id}")
    if ip_address:
        log_parts.append(f"ip={ip_address}")
    if response_code:
        log_parts.append(f"status={response_code}")
    if duration_ms:
        log_parts.append(f"duration={duration_ms}ms")

    logger.info(" | ".join(log_parts))


def log_error_context(logger, error_type, error_msg, context=None):
    """
    Hatalar için context bilgisi ile log kaydı oluşturur.

    Args:
        logger: Logger instance
        error_type: Hata sınıfı adı
        error_msg: Hata mesajı
        context: İlgili context bilgisi (dict)

    Example:
        log_error_context(
            logger,
            error_type='DatabaseError',
            error_msg='Connection failed',
            context={'host': 'localhost', 'port': 5432}
        )
    """
    context_str = " | ".join([f"{k}={v}" for k, v in context.items()]) if context else ""
    message = f"ERROR [{error_type}]: {error_msg}"
    if context_str:
        message += f" | {context_str}"
    logger.error(message, exc_info=True)
