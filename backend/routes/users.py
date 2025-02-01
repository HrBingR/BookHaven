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
        return jsonify({"error": f"{', '.join(missing_fields).capitalize().split("_")} field(s) required."}), 400
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
# @limiter.limit('2 per second')
def enable_mfa(token_state):
    logger.debug("Attempting to enable MFA")
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    user_id = token_state["user_id"]
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.auth_type == "oidc":
            return jsonify({"error": "Cannot enable MFA with OIDC auth type"}), 400
        if user.mfa_enabled:
            return jsonify({"error": "MFA is already enabled"}), 400
        mfa_secret = pyotp.random_base32()
        encrypted_mfa_secret = encrypt_totp_secret(mfa_secret)
        user.mfa_secret = encrypted_mfa_secret
        session.commit()
        user_totp_name = f"{user.username}/{user.email}"
        totp = pyotp.TOTP(mfa_secret)
        provisioning_url = totp.provisioning_uri(name=user_totp_name, issuer_name="BookHaven")
        mfa_secret_split = " ".join(mfa_secret[i:i + 4] for i in range(0, len(mfa_secret), 4))
    except Exception as e:
        session.rollback()
        logger.exception(f"Error enabling MFA for user ID {user_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        session.close()
    return jsonify({
        "message": "MFA setup initiated. Validate the OTP to complete setup.",
        "totp_provisioning_url": provisioning_url,
        "mfa_secret": mfa_secret_split
    }), 200


@users_bp.route('/user/disable-mfa', methods=['DELETE'])
@login_required
@limiter.limit('2 per second')
def disable_mfa(token_state):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    user_id = token_state["user_id"]
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.auth_type == "oidc":
            return jsonify({"error": "Cannot disable MFA with OIDC auth type"}), 400
        if not user.mfa_enabled:
            return jsonify({"error": "MFA is not enabled"}), 400
        user.mfa_enabled = False
        user.mfa_secret = None
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(f"Error disabling MFA for user ID {user_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        session.close()
    return jsonify({"message": "MFA successfully disabled."}), 200

@users_bp.route('/user/get-mfa-status', methods=['GET'])
@login_required
@limiter.limit('2 per second')
def get_mfa_status(token_state):
    if token_state == "no_token":
        return jsonify({"error": "Unauthenticated access is not allowed"}), 401
    user_id = token_state["user_id"]
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.mfa_enabled:
            return jsonify({"message": "true"}), 200
        else:
            return jsonify({"message": "false"}), 200
    except Exception as e:
        logger.exception(f"Error retrieving MFA status for user ID {user_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        session.close()

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