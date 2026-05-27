from __future__ import annotations

import os
import time
from typing import Optional

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    current_user,
    create_access_token,
    create_refresh_token,
    get_jwt,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from app.models import db, User

auth_bp = Blueprint("auth", __name__)

_TOKEN_BLOCKLIST: set[str] = set()
_ALLOWED_ROLES = {"user", "admin"}
_BLOCKLIST_REDIS = None


def _get_blocklist_backend():
    global _BLOCKLIST_REDIS
    if _BLOCKLIST_REDIS is not None:
        return _BLOCKLIST_REDIS

    redis_url = os.environ.get("JWT_BLOCKLIST_REDIS_URL")
    if not redis_url:
        redis_url = os.environ.get("RATELIMIT_STORAGE_URI")

    if redis_url and (redis_url.startswith("redis://") or redis_url.startswith("rediss://")):
        try:
            import redis

            _BLOCKLIST_REDIS = redis.Redis.from_url(redis_url, decode_responses=True)
        except Exception:
            _BLOCKLIST_REDIS = None
    return _BLOCKLIST_REDIS


def _store_blocked_token(jti: str, exp: Optional[int]):
    backend = _get_blocklist_backend()
    if backend is None:
        _TOKEN_BLOCKLIST.add(jti)
        return

    ttl = None
    if isinstance(exp, int):
        ttl = max(0, exp - int(time.time()))

    key = f"jwt_blocklist:{jti}"
    if ttl is None or ttl == 0:
        backend.set(key, "1")
    else:
        backend.setex(key, ttl, "1")


def token_iptal_edildi_mi(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    if not jti:
        return False

    backend = _get_blocklist_backend()
    if backend is None:
        return jti in _TOKEN_BLOCKLIST

    return backend.exists(f"jwt_blocklist:{jti}") == 1


def _user_lookup(jwt_header, jwt_data):
    user_id = jwt_data.get("sub")
    if user_id is None:
        return None
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    return User.query.filter_by(id=user_id, aktif=True).first()


def register_jwt_callbacks(jwt_manager):
    jwt_manager.token_in_blocklist_loader(token_iptal_edildi_mi)
    jwt_manager.user_lookup_loader(_user_lookup)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email ve password zorunludur"}), 400

    user = User.query.filter_by(email=email, aktif=True).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Geçersiz kimlik bilgileri"}), 401

    identity = str(user.id)
    access_token = create_access_token(identity=identity, additional_claims={"role": user.role, "email": user.email})
    refresh_token = create_refresh_token(identity=identity, additional_claims={"role": user.role, "email": user.email})
    # Cookie ve JSON body birlikte döner — header-bazlı eski istemciler de
    # cookie'siz erişimini sürdürebilir.
    response = jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    })
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user = current_user
    if user is None:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email}
    )
    response = jsonify({"access_token": access_token})
    set_access_cookies(response, access_token)
    return response, 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = current_user
    if user is None:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "aktif": user.aktif,
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jwt_data = get_jwt()
    _store_blocked_token(jwt_data["jti"], jwt_data.get("exp"))
    response = jsonify({"message": "Çıkış yapıldı"})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.route("/register", methods=["POST"])
@jwt_required(optional=True)
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = str(data.get("role", "user")).strip().lower()

    if not username or not email or not password:
        return jsonify({"error": "username, email ve password zorunludur"}), 400

    if role not in _ALLOWED_ROLES:
        return jsonify({"error": "Geçersiz rol"}), 400

    existing_users = User.query.count()
    if existing_users > 0:
        if current_user is None or getattr(current_user, "role", None) != "admin":
            return jsonify({"error": "Sadece admin kullanıcı oluşturabilir"}), 403

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Kullanıcı zaten kayıtlı"}), 409

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }), 201
