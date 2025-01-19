import bcrypt
import pyotp
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from config.logger import logger
from functions.book_management import login_required
from functions.db import get_session
from functions.utils import hash_password, check_pw_complexity, encrypt_totp_secret
from functions.extensions import limiter
from models.users import Users

users_bp = Blueprint('users', __name__, url_prefix='/api')

@users_bp.route('/user/change-password', methods=['PATCH'])
@login_required
@limiter.limit('2 per second')
def change_password(token_state):
    data = request.get_json(silent=True)
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    user_id = token_state["user_id"]
    if data is None:
        return jsonify({"error": "No data submitted"}), 400
    required_fields = ["new_password", "old_password"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"{', '.join(missing_fields).capitalize()} field(s) are required."}), 400
    new_password = data.get("new_password")
    old_password = data.get("old_password")
    if not new_password.strip() or not old_password.strip():
        return jsonify({"error": "Password fields cannot be empty."}), 400
    valid_pw, message = check_pw_complexity(new_password)
    if not valid_pw:
        return jsonify({"error": message}), 400
    session = get_session()
    try:
        user_record = session.query(Users).filter_by(id=user_id).first()
        if user_record.auth_type == "oidc":
            return jsonify({"error": "Unable to change your password while connected to OIDC. Please revert to a local account to change your password."}), 400
        current_hashed_password = user_record.password_hash
        valid_old_pw = bcrypt.checkpw(old_password.encode('utf-8'), current_hashed_password.encode('utf-8'))
        if not valid_old_pw:
            return jsonify({"error": "Current password is incorrect."}), 401
        if bcrypt.checkpw(new_password.encode('utf-8'), current_hashed_password.encode('utf-8')):
            return jsonify({"error": "The new password cannot be the same as the current password."}), 400
        user_record.password_hash = hash_password(new_password)
        session.commit()
        return jsonify({"message": "Password changed successfully."}), 200
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Failed to update password: {e}")
        return jsonify({"error": "An unexpected database error occurred. Please try again later."}), 500
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to update password: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500
    finally:
        session.close()

@users_bp.route('/user/enable-mfa', methods=['POST'])
@login_required
@limiter.limit('2 per second')
def enable_mfa(token_state):
    # IMPLEMENT HMAC OTP AFTER EMAIL SETUP
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    user_id = token_state["user_id"]
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if user.auth_type == "oidc":
            return jsonify({"error" : "Cannot enable MFA with OIDC auth type"}), 400
        if user.mfa_enabled or user.mfa_secret is not None:
            return jsonify({"error": "User already has MFA enabled."}), 400
        mfa_secret = pyotp.random_base32()
        encrypted_mfa_secret = encrypt_totp_secret(mfa_secret)
        user.mfa_enabled = True
        user.mfa_secret = encrypted_mfa_secret
        session.commit()
        user_username = user.username
        user_email = user.email
        user_totp_name = f"{user_username}/{user_email}"
        totp = pyotp.TOTP(mfa_secret)
        provisioning_url = totp.provisioning_uri(name=user_totp_name,issuer_name="BookHaven")
        mfa_secret_split = " ".join(mfa_secret[i:i + 4] for i in range(0, len(mfa_secret), 4))
    except Exception as e:
        session.rollback()
        logger.exception(f"Error enabling MFA for user ID {user_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        session.close()
    return jsonify({
        "message": "MFA Successfully Enabled",
        "totp_provisioning_url": provisioning_url,
        "mfa_secret": mfa_secret_split
    }), 200


### TO BE IMPLEMENTED AFTER EMAIL/SMTP:

# @users_bp.route('/user/change-email', methods=['PATCH'])
# @login_required
# def change_email(token_state):
#     data = request.get_json(silent=True)
#     if token_state == "no_token":
#         return jsonify({"error": "Unauthenticated access is not allowed"}), 401
#     user_id = token_state["user_id"]
#     if data is None:
#         return jsonify({"error": "No data submitted"}), 400
#     required_fields = [""]