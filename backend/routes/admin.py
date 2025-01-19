from flask import Blueprint, jsonify, request, g
from functions.db import get_session
from functools import wraps
import random
import string
from functions.utils import hash_password, check_pw_complexity  # Assuming you implemented this function
from functions.auth import verify_token  # Import the verify_token method from auth.py
from models.users import Users
from config.logger import logger
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import SQLAlchemyError

# Create the Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Middleware to ensure user is an admin
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Warning: User attempted Admin action without a valid auth header.")
            return jsonify({"error": "Missing or invalid Authorization header."}), 401

        token = auth_header.split(" ")[1]

        # Verify the token
        decoded_token = verify_token(token)
        if not decoded_token:
            logger.warning("Warning: User attempted Admin action with an invalid or expired token.")
            return jsonify({"error": "Invalid or expired token."}), 401

        # Ensure the user is an admin
        if not decoded_token.get("user_is_admin", False):
            logger.warning(f"Warning: Non-Admin UID {decoded_token.get("user_id")} attempted to access admin-function.")
            return jsonify({"error": "Forbidden. Admin access only."}), 403

        # Pass the decoded_token to the route function
        g.user = decoded_token
        return func(*args, **kwargs)

    return wrapper

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for _ in range(length))

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Fetch a list of all users"""
    session = get_session()
    try:
        users = session.query(Users).all()
        result = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "auth_type": user.auth_type,
                "created_at": user.created_at,
                "last_login": user.last_login,
            }
            for user in users
        ]
        logger.info(f"Admin UID {g.user["user_id"]} successfully retrieved {len(result)} users.")
        return jsonify(result), 200
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/admin-status', methods=['PATCH'])
@admin_required
def change_user_admin_status(user_id):
    """Change the admin's status for a user"""
    session = get_session()
    data = request.get_json()

    # Validate input
    if "is_admin" not in data or not isinstance(data["is_admin"], bool):
        return jsonify({"error": "Invalid is_admin value provided. Must be a boolean."}), 400

    # Prevent downgrading own admin status
    current_user_id = g.user["user_id"]
    if current_user_id == user_id and not data["is_admin"]:
        return jsonify({"error": "Admins cannot remove their own admin status."}), 400

    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        user.is_admin = data["is_admin"]
        session.commit()
        logger.info(f"Admin UID {current_user_id} successfully changed UID {user_id} admin status.")
        return jsonify({
            "success": True,
            "message": f"User admin status {'granted' if user.is_admin else 'revoked'} successfully."
        }), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to change admin status: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """Reset a user's password (local-auth users only)"""
    data = request.get_json(silent=True)
    if data is None or "new_password" not in data:
        new_password = generate_random_password()
    else:
        new_password = data.get('new_password', None)
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        if user.auth_type != "local":
            return jsonify({"error": "Cannot reset passwords for OIDC-authenticated users."}), 400
        user.password_hash = hash_password(new_password)
        session.commit()
        logger.info(f"Admin UID {g.user["user_id"]} successfully reset UID {user_id} password.")
        return jsonify({"success": True}), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to reset user password: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/reset-mfa', methods=['POST'])
@admin_required
def reset_user_mfa(user_id):
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        if user.auth_type != "local":
            return jsonify({"error": "Cannot reset MFA for OIDC-authenticated users."}), 400
        user.mfa_enabled = False
        user.mfa_secret = None
        session.commit()
        logger.info(f"Admin UID {g.user["user_id"]} successfully reset UID {user_id} MFA.")
        return jsonify({"message": f"MFA successfully reset for user-id {user_id}"})
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to reset user MFA: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()


@admin_bp.route('/users/<int:user_id>/change-email', methods=['PATCH'])
@admin_required
def change_email(user_id):
    data = request.get_json(silent=True)
    if data is None or "new_email" not in data:
        return jsonify({"error": "New email address required."}), 400
    new_email_address = data["new_email"]
    try:
        email = validate_email(new_email_address, check_deliverability=False)
        new_email_address = email.normalized
    except EmailNotValidError as e:
        return jsonify({"error": f"Email validation error: {str(e)}"}), 400
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        if user.auth_type != "local":
            return jsonify({"error": "Unlink OIDC before changing user's email address."}), 400
        user.email = new_email_address
        session.commit()
        logger.info(f"Admin UID {g.user["user_id"]} successfully changed UID {user_id} email address.")
        return jsonify({"message": "Email address successfully updated."}), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to update user email address: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/register', methods=['POST'])
@admin_required
def register_user():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "No data submitted."}), 400
    required_fields = ["username", "password", "email"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"{', '.join(missing_fields).capitalize()} field(s) are required."}), 400
    is_admin = bool(data.get('is_admin', False))
    username = data.get('username')
    password = data.get('password')
    valid_pw, message = check_pw_complexity(password)
    if not valid_pw:
        return jsonify({"error": message}), 400
    email_address = data.get('email')
    hashed_password = hash_password(password)
    try:
        email = validate_email(email_address, check_deliverability=False)
        email_address = email.normalized
    except EmailNotValidError as e:
        return jsonify({"error": f"Email validation error: {str(e)}"}), 400
    session = get_session()
    try:
        existing_user = session.query(Users).filter((Users.username == username) | (Users.email == email_address)).first()
        if existing_user:
            if existing_user.username == username:
                return jsonify({"error": f"Username {username} is already registered."}), 400
            if existing_user.email == email_address:
                return jsonify({"error": f"Email address {email_address} is already registered."}), 400
        new_user = Users(
            username=username,
            email=email_address,
            password_hash=hashed_password,
            is_admin=is_admin
        )
        session.add(new_user)
        logger.info(f"Admin UID {g.user["user_id"]} successfully registered user {username}.")
        session.commit()
        return jsonify({"message": f"User {username} added successfully."}), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to register user: {e}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id <= 0:
        return jsonify({"error": "Invalid user ID."}), 400
    session = get_session()
    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        session.delete(user)
        session.commit()
        logger.info(f"Admin UID {g.user["user_id"]} successfully deleted UID {user_id}.")
        return jsonify({"message": "User successfully deleted."}), 200
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Failed to delete user: {e}")
        return jsonify({"error": "Internal database error. See logs for details."}), 500
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to delete user: {e}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()