"""
eMuhasebe Pro - Flask Uygulama Fabrikası (Factory Pattern)
Katmanlı Mimari: Route → Service → Repository → ORM
"""
import logging
from flask import Flask
from flask_migrate import Migrate
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
from app.models import db
from app.logging_config import setup_logging
from app.middleware import log_request_response, log_error_handler

migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name='default'):
    """Flask uygulama fabrikası"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    if app.config.get('DEBUG'):
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # ━━━ Logging Setup ━━━
    logger = setup_logging(app)
    logger.info(f"Flask uygulama başlatıldı | Mode: {config_name} | Debug: {app.config.get('DEBUG')}")
    
    # ━━━ Güvenlik Setup ━━━
    # 1. HTTP Security Headers (Talisman) - Test'TE DEAKTIVE
    if not app.config.get('TESTING'):
        Talisman(app, 
            force_https=app.config.get('SESSION_COOKIE_SECURE', False),
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 year
            content_security_policy={
                'default-src': "'self'",
                'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.gstatic.com",
                'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
                'img-src': "'self' data: https:",
                'font-src': "'self' https://fonts.gstatic.com",
                'connect-src': "'self' https://*.firebaseio.com"
            }
        )
    
    # 2. Rate Limiting - Test'TE DEAKTIVE
    if not app.config.get('TESTING'):
        limiter.init_app(app)
    
    # 3. Request/Response Logging Middleware
    before_req_hook, after_req_hook = log_request_response()
    
    @app.before_request
    def before_request():
        before_req_hook()

    @app.after_request
    def after_request(response):
        response = after_req_hook(response)
        # CORS Headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    
    # 4. Global Error Handler'ları
    @app.errorhandler(404)
    @log_error_handler(404, 'NotFound')
    def handle_404(error):
        from app.api_utils import not_found_response
        return not_found_response('Kaynak')
    
    @app.errorhandler(500)
    @log_error_handler(500, 'InternalServerError')
    def handle_500(error):
        logger.error("Internal server error occurred", exc_info=True)
        from app.api_utils import internal_error_response
        return internal_error_response('Sunucu hatası')
    
    # ━━━ Veritabanı ve Migration ━━━
    db.init_app(app)
    migrate.init_app(app, db)
    
    # ━━━ Blueprint'leri Kaydet ━━━
    from app.main import main_bp
    from app.faturalar.alis import alis_bp
    from app.faturalar.satis import satis_bp
    from app.faturalar.iade import iade_bp
    from app.musteriler import musteriler_bp
    from app.urunler import urunler_bp
    from app.api import api_bp
    from app.api.v1 import api_v1
    
    app.register_blueprint(main_bp)
    app.register_blueprint(alis_bp, url_prefix='/faturalar/alis')
    app.register_blueprint(satis_bp, url_prefix='/faturalar/satis')
    app.register_blueprint(iade_bp, url_prefix='/faturalar/iade')
    app.register_blueprint(musteriler_bp, url_prefix='/musteriler')
    app.register_blueprint(urunler_bp, url_prefix='/urunler')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(api_v1)  # /api/v1 preconfigured
    
    logger.info("✅ Tüm blueprint'ler kayıt edildi: main, faturalar (alis/satis/iade), musteriler, urunler, api, api/v1")
    
    return app
