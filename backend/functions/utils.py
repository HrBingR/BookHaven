from cryptography.fernet import Fernet
from models.users import Users
from functions.db import get_session
from email_validator import validate_email, EmailNotValidError
import bcrypt
import re
from flask import current_app, jsonify, request
from config.config import config
from config.logger import logger

def check_required_envs(secret_key: str, base_url: str, oidc_enabled: bool) -> tuple[bool, str]:
    if not secret_key:
        return False, "SECRET_KEY environment variable is not set. Generate one (bash) using: openssl rand -hex 32"
    if len(secret_key) != 64:
        return False, "SECRET_KEY environment variable is invalid. Generate one (bash) using: openssl rand -hex 32"
    if not base_url:
        return False, "BASE_URL is not set. Please set this to your application's base URL"
    if oidc_enabled:
        if not config.OIDC_PROVIDER:
            return False, "OIDC_ENABLED is True but OIDC_PROVIDER is not configured."
        if not config.OIDC_CLIENT_ID:
            return False, "OIDC_ENABLED is True but OIDC_CLIENT_ID is not configured."
        if not config.OIDC_CLIENT_SECRET:
            return False, "OIDC_ENABLED is True but OIDC_CLIENT_SECRET is not configured."
        if not config.OIDC_METADATA_ENDPOINT:
            return False, "OIDC_ENABLED is True but OIDC_METADATA_ENDPOINT is not configured."
    return True, "Required environment variables are set."


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_pw_complexity(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "Password complexity requirements have been met."


def check_admin_user(password: str, email: str) -> tuple[bool, str]:
    session = get_session()
    try:
        admin_user = session.query(Users).filter_by(username='admin').first()
        if admin_user:
            return True, "Admin user already exists. Skipping initial setup."
        if not password or not email:
            return False, "Missing admin credentials. Please set ADMIN_PASS and ADMIN_EMAIL in environment variables. These variables can be unset after initial setup."
        try:
            email_address = validate_email(email, check_deliverability=False)
            email = email_address.normalized
        except EmailNotValidError as e:
            return False, f"Email validation error: {str(e)}"
        valid_pw, message = check_pw_complexity(password)
        if not valid_pw:
            return False, message
        hashed_password = hash_password(password)
        new_admin_user = Users(
            username='admin',
            email=email,
            password_hash=hashed_password,
            role='admin',
            auth_type='local'
        )
        session.add(new_admin_user)
        session.commit()
        return True, "Admin user created successfully."
    except Exception as e:
        return False, str(e)
    finally:
        session.close()


def reset_admin_user_password(password: str) -> tuple[bool, str]:
    if not password:
        return False, "Missing password for admin user password reset. Please set ADMIN_PASS in environment variables."
    session = get_session()
    try:
        admin_user = session.query(Users).filter_by(username='admin').first()
        if admin_user:
            hashed_password = hash_password(password)
            admin_user.password_hash = hashed_password
            if admin_user.mfa_enabled:
                admin_user.mfa_secret = None
                admin_user.mfa_enabled = False
            session.commit()
            return True, "Admin password and MFA reset successfully."
        else:
            return False, "Admin user not found in the database."
    except Exception as e:
        return False, str(e)
    finally:
        session.close()


def encrypt_totp_secret(secret):
    fernet = Fernet(current_app.config["FERNET_KEY"])
    encrypted_secret = fernet.encrypt(secret.encode('utf-8')).decode('utf-8')
    return encrypted_secret


def decrypt_totp_secret(secret):
    fernet = Fernet(current_app.config["FERNET_KEY"])
    decrypted_secret = fernet.decrypt(secret.encode('utf-8')).decode('utf-8')
    return decrypted_secret


def unlink_oidc(user_id):
    data = request.get_json(silent=True)
    if data is None or "new_password" not in data:
        return jsonify({"error": "No password submitted"}), 400
    new_password = data.get('new_password')
    valid_pw, message = check_pw_complexity(new_password)
    if not valid_pw:
        return jsonify({"error": message}), 400
    hashed_password = hash_password(new_password)
    session = get_session()
    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        user.oidc_user_id = None
        user.auth_type = "local"
        user.password_hash = hashed_password
        user.mfa_enabled = False
        user.mfa_secret = None
        user.last_used_otp = None
        session.commit()
        return jsonify({"message": "Successfully un-linked OIDC"}), 200
    except Exception as e:
        logger.exception(f"Exception occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()
