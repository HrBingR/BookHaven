from cryptography.fernet import Fernet
from models.users import Users
from functions.db import get_session
from email_validator import validate_email, EmailNotValidError
import bcrypt
import re
from flask import current_app

def check_required_envs(secret_key: str, base_url: str, cf_auth: str, cf_team: str) -> tuple[bool, str]:
    if not secret_key:
        return False, "SECRET_KEY environment variable is not set. Generate one (bash) using: openssl rand -hex 32"
    if len(secret_key) != 64:
        return False, "SECRET_KEY environment variable is invalid. Generate one (bash) using: openssl rand -hex 32"
    if not base_url:
        return False, "BASE_URL is not set. Please set this to your application's base URL"
    if cf_auth and not cf_team:
        return False, "CF_ACCESS_AUTH is enabled but no CF_ACCESS_TEAM_NAME has been provided"
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
            is_admin=True,
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