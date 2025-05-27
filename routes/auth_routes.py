# safeagree_backend/routes/auth_routes.py
# Defines API endpoints for user authentication and account management.

from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from utils.form_validator import validate_request_data
from utils.error import Error, ErrorType
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# --- User Account Management Endpoints ---


# Import the blueprint defined in __init__.py
from routes import auth_bp
# We'll need to pass the db_manager instance to these routes from app.py
db_manager_instance = None # This will be set by app.py

def set_auth_db_manager(db_manager):
    global db_manager_instance
    db_manager_instance = db_manager


@auth_bp.route("/register", methods=["POST"])
def register_user():    
    """Endpoint for user registration."""
    
    required_fields = {"email":str, "password":str}
    data = request.get_json()

    is_valid, error = validate_request_data(data, required_fields)

    email = data.get("email")
    password = data.get("password")


    if not is_valid:
        return jsonify(Error(ErrorType.SYNTACTIC, error).serialize()), 400
    existing_user = db_manager_instance.get_user_by_email(email)
    if existing_user:
        return jsonify(Error(ErrorType.SYNTACTIC, "This account already exists.").serialize()), 409

    try:
        new_user = db_manager_instance.add_user(email, password)
        if new_user:
            return jsonify({"message": "User registered successfully"}), 201
        
    except Exception as e:
        return jsonify({"message": "User registration failed"}), 500

@auth_bp.route("/login", methods=["POST"])
def login_user():
    """Endpoint for user login, returns JWT access token."""
    required_fields = {"email":str, "password":str}

    data = request.get_json()

    is_valid, error = validate_request_data(data, required_fields)

    if not is_valid:
        return jsonify(Error(ErrorType.SYNTACTIC, error).serialize()), 400
    
    email = data.get("email")
    password = data.get("password")

    user = db_manager_instance.get_user_by_email(email)
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)  # Optional refresh token
        return jsonify(access_token=access_token,
                       refresh_token=refresh_token,
                        user_id=user.id), 200
    return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route("/refresh", methods=["POST"])
def refresh_token_controller():
    """Endpoint to refresh JWT access token."""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token), 200


@auth_bp.route("/change_password", methods=["POST"])
@jwt_required()
def change_password():
    """Endpoint to change user's password."""
    user_id = get_jwt_identity()
    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not all([old_password, new_password]):
        return jsonify({"message": "Missing old or new password"}), 400

    user = db_manager_instance.get_user_by_id(user_id)
    if not user:
        return jsonify({"message": "User does not exist"}), 404
    elif not user.check_password(old_password):
        return jsonify({"message": "Invalid old password"}), 401

    if db_manager_instance.update_user_password(user_id, new_password):
        return jsonify({"message": "Password updated successfully"}), 200
    return jsonify({"message": "Failed to update password"}), 500

@auth_bp.route("/delete_account", methods=["DELETE"])
@jwt_required()
def delete_account():
    """Endpoint to delete user account."""
    user_id = get_jwt_identity()
    if db_manager_instance.delete_user(user_id):
        return jsonify({"message": "Account deleted successfully"}), 200
    return jsonify({"message": "Failed to delete account or account not found"}), 404

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout_user():
    """Endpoint to log out user (optional, depending on JWT strategy)."""
    # For JWT, logout can be handled by client-side token deletion
    return jsonify({"message": "User logged out successfully"}), 200