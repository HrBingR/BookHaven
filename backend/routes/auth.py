import base64

from flask import request, jsonify, make_response
from bcrypt import checkpw
import jwt
from datetime import datetime, timezone, timedelta
from flask import Blueprint
from config.config import config
from config.logger import logger
from functions.book_management import login_required
from functions.utils import decrypt_totp_secret, hash_password
from functions.auth import verify_token
from models.users import Users
from functions.db import get_session
import pyotp
from urllib.parse import urlparse
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__)

def generate_token(user_id, user_is_admin, user_email):
    return jwt.encode(
        {
            'token_type': "login",
            'user_id': user_id,
            'user_is_admin':user_is_admin,
            'user_email':user_email,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        },
        config.SECRET_KEY,
        algorithm='HS256'
    )

def generate_cf_token(user_id, user_is_admin, user_email, cf_iss):
    return jwt.encode(
        {
            'token_type': "login",
            'user_id': user_id,
            'user_is_admin':user_is_admin,
            'user_email':user_email,
            'iss':cf_iss,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        },
        config.SECRET_KEY,
        algorithm='HS256'
    )

def generate_totp_token(user_id):
    return jwt.encode(
        {
            'token_type': 'totp',
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(minutes=10)
        },
        config.SECRET_KEY,
        algorithm='HS256'
    )

def cf_login(session):
    cf_cookie = request.cookies.get('CF_Authorization')
    if not cf_cookie:
        return jsonify({"error": "No data in CF_Authorization cookie, of CF_Authorization cookie missing"}), 400
    try:
        decoded_payload = jwt.decode(cf_cookie, options={"verify_signature": False})
        cf_email = decoded_payload.get("email")
        iss = decoded_payload.get("iss")
        cf_password = decoded_payload.get("identity_nonce")
        netloc = urlparse(iss).netloc
        cf_username = cf_email.split('@')[0]
        cf_user = session.query(Users).filter(func.lower(Users.username) == func.lower(cf_username)).first()
        if not cf_user:
            cf_user = session.query(Users).filter(func.lower(Users.email) == func.lower(cf_email)).first()
            if not cf_user:
                hashed_password = hash_password(cf_password)
                cf_user = Users(
                    username=cf_username,
                    email=cf_email,
                    password_hash=hashed_password
                )
                session.add(cf_user)
                session.commit()
        token = generate_cf_token(user_id=cf_user.id, user_is_admin=cf_user.is_admin, user_email=cf_user.email, cf_iss=iss)
        return jsonify({'token': token}), 200
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        session.rollback()
        return make_response(jsonify({'error': 'Internal server error'}), 500)
    finally:
        session.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    session = get_session()
    try:
        if config.CF_ACCESS_AUTH:
            return cf_login(session)
        if not username or not password:
            logger.debug(f"Username or password not submitted.")
            return make_response(jsonify({'error': 'Missing username or password'}), 400)
        user = session.query(Users).filter(Users.username == username).first()
        if not user:
            user = session.query(Users).filter(Users.email == username).first()
        if user and checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            if not user.mfa_enabled:
                user.last_login = datetime.now(timezone.utc)
                session.commit()
                token = generate_token(user_id=user.id, user_is_admin=user.is_admin, user_email=user.email)
                return jsonify({'token': token}), 200
            token = generate_totp_token(user_id=user.id)
            return jsonify({'token': token}), 200
        else:
            if user:
                user.failed_login_count += 1
                session.commit()
            ip_address = request.remote_addr
            logger.warning(f"Failed login attempt for username/email: {username} from IP: {ip_address}")
            logger.debug(f"{password} was the PW used, result of checkpw: {checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))}")
            return make_response(jsonify({'error': 'Invalid credentials'}), 401)
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return make_response(jsonify({'error': 'Internal server error'}), 500)
    finally:
        session.close()

@auth_bp.route('/login/check-otp', methods=['POST'])
@login_required(totp=True)
def check_otp(token_state):
    data = request.get_json(silent=True)
    if data is None or "otp" not in data:
        return jsonify({"error": "No one time pin submitted"}), 400
    user_id = token_state["user_id"]
    otp = data["otp"]
    session = get_session()
    try:
        if config.ENVIRONMENT != "test":
            user = session.query(Users).filter_by(id=user_id).with_for_update().first() # pragma: no cover
        else:
            user = session.query(Users).filter_by(id=user_id).first()
        if user.last_used_otp == otp:
            return jsonify({"error": "This one time pin has already been used."}), 400
        encrypted_totp_secret = user.mfa_secret
        mfa_secret = decrypt_totp_secret(encrypted_totp_secret)
        totp = pyotp.TOTP(mfa_secret)
        verified_otp = totp.verify(otp, valid_window=1)
        if not verified_otp:
            return jsonify({"error": "Incorrect one time pin entered."}), 403
        user.last_used_otp = otp
        user.last_login = datetime.now(timezone.utc)
        session.commit()
        token = generate_token(user_id=user.id, user_is_admin=user.is_admin, user_email=user.email)
        return jsonify({'token': token}), 200
    except Exception as e:
        session.rollback()
        logger.error(f"Error during login: {str(e)}")
        return jsonify({"error": "Internal server error."}), 500
    finally:
        session.close()

@auth_bp.route('/validate-otp', methods=['POST'])
def validate_otp():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header with Bearer token is required"}), 401
    token = auth_header.split(" ")[1]
    decoded_token = verify_token(token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401
    user_id = decoded_token.get("user_id")
    if not user_id:
        return jsonify({"error": "Token does not contain user_id"}), 400
    data = request.get_json(silent=True)
    if not data or "otp" not in data:
        return jsonify({"error": "Missing OTP"}), 400
    otp = data["otp"]
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        encrypted_totp_secret = user.mfa_secret
        if not encrypted_totp_secret:
            return jsonify({"error": "MFA setup was not initiated for this user"}), 400
        mfa_secret = decrypt_totp_secret(encrypted_totp_secret)
        totp = pyotp.TOTP(mfa_secret)
        verified_otp = totp.verify(otp, valid_window=1)
        if not verified_otp:
            return jsonify({"error": "Incorrect one-time PIN entered"}), 403
        user.mfa_enabled = True
        # user.last_used_otp = otp
        user.last_login = datetime.now(timezone.utc)
        session.commit()
        return jsonify({"success": "OTP validated and MFA enabled"}), 200
    except Exception as e:
        session.rollback()
        logger.error(f"Error during OTP validation: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()