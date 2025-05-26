# safeagree_backend/routes/__init__.py
# This file makes the 'routes' directory a Python package.

from flask import Blueprint

# Define blueprints for different route categories
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
policy_bp = Blueprint('policy', __name__, url_prefix='/policy')

# Import route definitions to register them with the blueprints
from . import auth_routes
from . import policy_routes
