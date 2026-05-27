from __future__ import annotations
import os
from flask import Flask
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from .models import db
from .logging_config import setup_logging

migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
jwt = JWTManager()


def register_extensions(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    jwt.init_app(app)


def register_blueprints(app: Flask):
    # Import inside to avoid circular imports at module import time
    from .api import api_bp
    from .api.v1 import api_v1
    try:
        from .main import main_bp
    except Exception:
        main_bp = None
    try:
        from .musteriler import musteriler_bp
    except Exception:
        musteriler_bp = None
    try:
        from .urunler import urunler_bp
    except Exception:
        urunler_bp = None
    try:
        from .faturalar.alis import alis_bp
    except Exception:
        alis_bp = None
    try:
        from .faturalar.satis import satis_bp
    except Exception:
        satis_bp = None
    try:
        from .faturalar.iade import iade_bp
    except Exception:
        iade_bp = None
    try:
        from .auth import auth_bp
    except Exception:
        auth_bp = None

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(api_v1, url_prefix="/api/v1")
    csrf.exempt(api_bp)
    csrf.exempt(api_v1)
    if main_bp:
        app.register_blueprint(main_bp)
    if musteriler_bp:
        app.register_blueprint(musteriler_bp, url_prefix="/musteriler")
    if urunler_bp:
        app.register_blueprint(urunler_bp, url_prefix="/urunler")
    if alis_bp:
        app.register_blueprint(alis_bp, url_prefix="/alis")
    if satis_bp:
        app.register_blueprint(satis_bp, url_prefix="/satis")
    if iade_bp:
        app.register_blueprint(iade_bp, url_prefix="/iade")
    if auth_bp:
        app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
        csrf.exempt(auth_bp)


def register_errorhandlers(app: Flask):
    from flask import jsonify

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Too Many Requests"}), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal Server Error"}), 500


def register_jwt_callbacks(app: Flask):
    from flask import jsonify
    from .auth import register_jwt_callbacks as register_auth_jwt_callbacks

    @jwt.expired_token_loader
    def expired_callback(jwt_header, jwt_payload):
        return jsonify({"msg": "Token expired"}), 401

    @jwt.invalid_token_loader
    def invalid_callback(reason):
        return jsonify({"msg": "Invalid token", "reason": reason}), 422

    @jwt.unauthorized_loader
    def missing_callback(reason):
        return jsonify({"msg": "Missing token", "reason": reason}), 401

    register_auth_jwt_callbacks(jwt)


def register_audit_listeners(app: Flask):
    # Import here to avoid heavy imports at module level
    from .models import register_audit_listeners as _reg

    _reg(db)


def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    # Load config from env or provided object
    cfg = config_object or os.environ.get("FLASK_CONFIG", "config.Config")
    if isinstance(cfg, str) and "." not in cfg:
        try:
            from config import config as config_map

            cfg = config_map.get(cfg, cfg)
        except Exception:
            pass

    try:
        app.config.from_object(cfg)
    except Exception:
        if config_object not in {"testing", "default"}:
            raise

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    if str(app.config.get("SQLALCHEMY_DATABASE_URI", "")).startswith("sqlite"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", app.config.get("JWT_ACCESS_TOKEN_EXPIRES"))
    app.config.setdefault("JWT_REFRESH_TOKEN_EXPIRES", app.config.get("JWT_REFRESH_TOKEN_EXPIRES"))

    register_extensions(app)
    setup_logging(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_jwt_callbacks(app)
    register_audit_listeners(app)

    # Attach before/after request middleware if provided
    try:
        from .middleware import before_request, after_request

        app.before_request(before_request)
        app.after_request(after_request)
    except Exception:
        pass

    return app
