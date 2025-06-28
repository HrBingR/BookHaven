import jwt
import pyotp
from functions.init import CustomFlask
from typing import cast
from flask import request, jsonify, make_response, redirect, Blueprint, current_app, url_for, session as oidc_session
from bcrypt import checkpw
from datetime import datetime, timezone, timedelta
from config.config import config
from config.logger import logger
from functions.roles import login_required
from functions.utils import decrypt_totp_secret, hash_password
from functions.auth import verify_token
from functions.db import get_session
from models.users import Users
from sqlalchemy import func
import secrets

auth_bp = Blueprint('auth', __name__)

def get_oauth():
    app = cast(CustomFlask, current_app)
    oauth = app.oauth
    return oauth

def create_oidc_client():
    provider_name = config.OIDC_PROVIDER
    oauth = get_oauth()
    client = oauth.create_client(provider_name)
    return client

def generate_token(user_id, user_email, user_role):
    return jwt.encode(
        {
            'token_type': "login",
            'user_id': user_id,
            'user_email':user_email,
            'user_role':user_role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        },
        config.SECRET_KEY,
        algorithm='HS256'
    )

def generate_cf_token(user_id, user_role, user_email, cf_iss):
    return jwt.encode(
        {
            'token_type': "login",
            'user_id': user_id,
            'user_role':user_role,
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
        token = generate_cf_token(user_id=cf_user.id, user_role=cf_user.role, user_email=cf_user.email, cf_iss=iss)
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
            cloudflare_login_response, cloudflare_login_status = cf_login(session)
            cloudflare_login_response_json_data = cloudflare_login_response.get_json()
            if cloudflare_login_status == 200:
                return cloudflare_login_response, cloudflare_login_status
            logger.error(f"Attempt to use CF_ACCESS_AUTH failed: {cloudflare_login_response_json_data["error"]}")
        if not username or not password:
            logger.debug(f"Username or password not submitted.")
            return make_response(jsonify({'error': 'Missing username or password'}), 400)
        user = session.query(Users).filter(Users.username == username).first()
        if not user:
            user = session.query(Users).filter(Users.email == username).first()
        if user.auth_type == "oidc":
            return jsonify({"error": "OIDC user cannot log in with username and password."}), 400
        if user and checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            if not user.mfa_enabled:
                user.last_login = datetime.now(timezone.utc)
                session.commit()
                token = generate_token(user_id=user.id, user_email=user.email, user_role=user.role)
                return jsonify({'token': token}), 200
            token = generate_totp_token(user_id=user.id)
            return jsonify({'token': token}), 200
        else:
            if user:
                user.failed_login_count += 1
                session.commit()
            ip_address = request.remote_addr
            logger.warning(f"Failed login attempt for username/email: {username} from IP: {ip_address}")
            return make_response(jsonify({'error': 'Incorrect username or password.'}), 401)
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
        token = generate_token(user_id=user.id, user_email=user.email)
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

@auth_bp.route('/login/oidc', methods=['GET'])
def oidc_login():
    client = create_oidc_client()
    if not client:
        return jsonify({'error': 'OIDC not configured'}), 400
    redirect_uri = url_for('auth.oidc_callback', _external=True)
    return client.authorize_redirect(redirect_uri)

@auth_bp.route('/login/link-oidc', methods=['GET'])
def link_oidc():
    oidc_session["link_oidc"] = True
    client = create_oidc_client()
    if not client:
        return jsonify({'error': 'OIDC not configured'}), 400
    redirect_uri = url_for('auth.oidc_callback', _external=True)
    return client.authorize_redirect(redirect_uri)

def check_oidc_user(userinfo):
    session = get_session()
    if not userinfo:
        return jsonify({"error": "No userinfo retrieved from OIDC provider"}), 400
    try:
        user_by_id = session.query(Users).filter(Users.oidc_user_id == userinfo['sub']).first()
        if not user_by_id:
            user_by_email = session.query(Users).filter(Users.email == userinfo['email']).first()
            if not user_by_email:
                if config.OIDC_AUTO_REGISTER_USER:
                    username = userinfo['email'].split('@')[0]
                    user = Users(
                        username=username,  # or generate username
                        email=userinfo['email'],
                        oidc_user_id=userinfo['sub'],
                        auth_type='oidc'
                    )
                    session.add(user)
                    session.commit()
                    new_user = session.query(Users).get(user.id)
                    token = generate_token(user_id=new_user.id, user_email=new_user.email, user_role=new_user.role)
                    return jsonify({"token": token}), 200
                return jsonify({"error": "OIDC_AUTO_REGISTER_USER is disabled. Unauthorized."}), 401
            if config.OIDC_AUTO_LINK_USER or oidc_session.get("link_oidc"):
                user_by_email.auth_type = "oidc"
                user_by_email.oidc_user_id = userinfo['sub']
                new_password = secrets.token_hex(16)
                new_password_hash = hash_password(new_password)
                user_by_email.hashed_password = new_password_hash
                session.commit()
                oidc_session.pop("link_oidc", None)
                token = generate_token(user_id=user_by_email.id, user_email=user_by_email.email, user_role=user_by_email.role)
                return jsonify({"token": token}), 200
            return jsonify({"error": "OIDC_AUTO_LINK_USER is disabled. Unauthorized."}), 401
        token = generate_token(user_id=user_by_id.id, user_email=user_by_id.email, user_role=user_by_id.role)
        return jsonify({"token": token}), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Exception checking oidc user: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

@auth_bp.route('/login/oidc/callback', methods=['GET'])
def oidc_callback():
    client = create_oidc_client()
    oidc_token = client.authorize_access_token()
    userinfo = oidc_token['userinfo']
    oidc_user_response, oidc_user_status = check_oidc_user(userinfo)
    frontend_url = url_for("react.serve_react_app", path="/login", _external=True)
    response_json = oidc_user_response.get_json()
    if oidc_user_status == 200:
        token = response_json['token']
        return redirect(f"{frontend_url}?token={token}")
    error_response = response_json['error']
    return redirect(f"{frontend_url}?error={error_response}")