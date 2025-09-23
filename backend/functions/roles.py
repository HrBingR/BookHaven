from flask import request, jsonify
from functions.db import get_session
from models.users import Users
from config.logger import logger
from functions.auth import verify_token
from functools import wraps
from config.config import config
import inspect

def user_logged_in():
    session = get_session()
    try:
        auth_header = request.headers.get('Authorization')
        no_token = "no_token"
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            decoded_token = verify_token(token)
            if not decoded_token:
                return False, "Invalid or expired token.", no_token
            user_id = decoded_token.get("user_id")
            user_record = session.query(Users).filter_by(id=user_id).first()
            if not user_record:
                return False, "User not found.", no_token
            return True, "User token validated.", decoded_token
        return True, "Unauthenticated session in progress.", no_token
    finally:
        session.close()


def get_user_role(user_id):
    """Get the current role for a user from the database"""
    session = get_session()
    try:
        user_record = session.query(Users).filter_by(id=user_id).first()
        if not user_record:
            return None
        return user_record.role
    finally:
        session.close()


def login_required(func=None, totp=False, required_roles=None):
    """
    Decorator to check login status, enforce token type, and validate user roles:
    - Allows optional token validation based on config.ALLOW_UNAUTHENTICATED.
    - Updates token_state if token type is invalid or missing.
    - Checks user roles against required_roles if specified.

    Parameters:
        func (function): The wrapped function.
        totp (bool): Set to True to allow TOTP tokens specifically for the route.
        required_roles (list): List of roles that can access this endpoint. If None, any authenticated user can access.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_login_status, message, token_state = user_logged_in()
            if not user_login_status:
                logger.debug(message)
            
            # Handle unauthenticated access
            if not config.ALLOW_UNAUTHENTICATED and token_state == "no_token":
                logger.debug("Unauthenticated access denied.")
                return jsonify({
                    "error": "Unauthenticated access is not allowed. Please see ALLOW_UNAUTHENTICATED environment variable"
                }), 401

            # Handle TOTP requirements
            if totp and token_state == "no_token":
                return jsonify({
                    "error": "TOTP verification requires authentication."
                }), 401
            
            # Handle token type validation
            if token_state != "no_token":
                token_type = token_state.get("token_type", None)
                if token_type == "totp" and not totp:
                    logger.debug("TOTP token detected, marking as no_token.")
                    token_state = "no_token"

            # Handle role-based access control
            if required_roles and token_state != "no_token":
                user_id = token_state.get("user_id")
                if user_id:
                    user_role = get_user_role(user_id)
                    if not user_role or user_role not in required_roles:
                        logger.warning(f"User {user_id} with role '{user_role}' attempted to access endpoint requiring roles: {required_roles}")
                        return jsonify({
                            "error": "Forbidden. Insufficient permissions."
                        }), 403
                else:
                    logger.warning("Token missing user_id for role validation")
                    return jsonify({
                        "error": "Invalid token format."
                    }), 401
            elif required_roles and token_state == "no_token":
                logger.debug(f"Unauthenticated user attempted to access endpoint requiring roles: {required_roles}")
                return jsonify({
                    "error": "Authentication required for this endpoint."
                }), 401

            # Call the function with token_state if it accepts it
            func_params = inspect.signature(func).parameters
            if 'token_state' in func_params:
                return func(*args, token_state=token_state, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    if func:
        return decorator(func)
    return decorator
