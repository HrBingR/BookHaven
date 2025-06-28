from flask import Blueprint, jsonify, request, g
from functions.db import get_session
import random
import string
from functions.utils import hash_password, check_pw_complexity, unlink_oidc
from functions.roles import login_required
from models.users import Users
from config.logger import logger
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import SQLAlchemyError

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for _ in range(length))

@admin_bp.route('/users', methods=['GET'])
@login_required(required_roles=["admin"])
def get_all_users(token_state):
    """Fetch a list of all users"""
    session = get_session()
    try:
        users = session.query(Users).all()
        result = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "auth_type": user.auth_type,
                "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for user in users
        ]
        logger.info(f"Admin UID {token_state["user_id"]} successfully retrieved {len(result)} users.")
        return jsonify(result), 200
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/role', methods=['PATCH'])
@login_required(required_roles=["admin"])
def change_user_role(user_id, token_state):
    """Change the role for a user"""
    session = get_session()
    data = request.get_json()
    if "role" not in data or not isinstance(data["role"], str):
        return jsonify({"error": "Invalid role value provided."}), 400
    current_user_id = token_state["user_id"]
    role = data["role"].lower()
    valid_roles = ["admin", "editor", "user"]
    if role not in valid_roles:
        return jsonify({"error": f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}"}), 400
    if current_user_id == user_id and role != "admin":
        return jsonify({"error": "Admins cannot remove their own admin status."}), 400
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        user.role = role
        session.commit()
        logger.info(f"Admin UID {current_user_id} successfully changed UID {user_id} role.")
        return jsonify({
            "success": True,
            "message": "User role updated successfully."
        }), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to change user role: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required(required_roles=["admin"])
def reset_user_password(user_id, token_state):
    """Reset a user's password (local-auth users only)"""
    data = request.get_json(silent=True)
    if data is None or "new_password" not in data:
        return jsonify({"error": "No password submitted"})
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
        logger.info(f"Admin UID {token_state["user_id"]} successfully reset UID {user_id} password.")
        return jsonify({"success": True}), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to reset user password: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/reset-mfa', methods=['POST'])
@login_required(required_roles=["admin"])
def reset_user_mfa(user_id, token_state):
    session = get_session()
    try:
        user = session.query(Users).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        if user.auth_type != "local":
            return jsonify({"error": "Cannot reset MFA for OIDC-authenticated users."}), 400
        if not user.mfa_enabled:
            return jsonify({"error": "User does not have MFA enabled."}), 400
        user.mfa_enabled = False
        user.mfa_secret = None
        session.commit()
        logger.info(f"Admin UID {token_state["user_id"]} successfully reset UID {user_id} MFA.")
        return jsonify({"message": f"MFA successfully reset for user-id {user_id}"})
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to reset user MFA: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()


@admin_bp.route('/users/<int:user_id>/change-email', methods=['PATCH'])
@login_required(required_roles=["admin"])
def change_email(user_id, token_state):
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
        logger.info(f"Admin UID {token_state["user_id"]} successfully changed UID {user_id} email address.")
        return jsonify({"message": "Email address successfully updated."}), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to update user email address: {str(e)}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/register', methods=['POST'])
@login_required(required_roles=["admin"])
def register_user(token_state):
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "No data submitted."}), 400
    required_fields = ["username", "password", "email"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"{', '.join(missing_fields).capitalize()} field(s) are required."}), 400
    role = (data.get('role', 'user'))
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
            role=role
        )
        session.add(new_user)
        logger.info(f"Admin UID {token_state["user_id"]} successfully registered user {username}.")
        session.commit()
        return jsonify({"message": f"User {username} added successfully."}), 200
    except Exception as e:
        session.rollback()
        logger.exception(f"Failed to register user: {e}")
        return jsonify({"error": "Internal server error. See logs for details."}), 500
    finally:
        session.close()

@admin_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@login_required(required_roles=["admin"])
def delete_user(user_id, token_state):
    if user_id <= 0:
        return jsonify({"error": "Invalid user ID."}), 400
    session = get_session()
    current_user_id = token_state["user_id"]
    if current_user_id == user_id:
        return jsonify({"error": "You cannot delete your own account."}), 400
    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404
        session.delete(user)
        session.commit()
        logger.info(f"Admin UID {current_user_id} successfully deleted UID {user_id}.")
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

@admin_bp.route('/users/<int:user_id>/unlink-oidc', methods=['PATCH'])
@login_required(required_roles=["admin"])
def unlink_oidc_admin(user_id):
    if user_id <= 0:
        return jsonify({"error": "Invalid user ID."}), 400
    unlink_response, unlink_status = unlink_oidc(user_id)

    return unlink_response, unlink_status