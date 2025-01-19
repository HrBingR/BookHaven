from flask import request, jsonify, make_response
from bcrypt import checkpw
import jwt
from datetime import datetime, timezone, timedelta
from flask import Blueprint
from config.config import config
from config.logger import logger
from functions.book_management import login_required
from functions.utils import decrypt_totp_secret
from models.users import Users
from functions.db import get_session
import pyotp

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

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    session = get_session()
    try:
        if not username or not password:
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
    otp = int(data["otp"])
    session = get_session()
    try:
        if config.ENVIRONMENT != "test":
            user = session.query(Users).filter_by(id=user_id).with_for_update.first() # pragma: no cover
        else:
            user = session.query(Users).filter_by(id=user_id).first()
        if user.last_used_otp == otp:
            return jsonify({"error": "This one time pin has already been used."}), 400
        encrypted_totp_secret = user.mfa_secret
        mfa_secret = decrypt_totp_secret(encrypted_totp_secret)
        totp = pyotp.TOTP(mfa_secret)
        verified_otp = totp.verify(str(otp), valid_window=1)
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