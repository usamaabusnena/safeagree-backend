# --- 4. app.py (Flask WebBack Application) ---
# This file sets up the Flask application, defines API endpoints, and handles
# user authentication, authorization, and routing requests to the Communicator.
from dotenv import load_dotenv
load_dotenv()
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity, create_refresh_token

from flask_cors import CORS # Import CORS

from database.crud import DatabaseManager
from services.file_storage_service import FilebaseManager
from services.scraper_service import ScraperService
from services.communicator import Communicator

# Import blueprints for routes
from routes import auth_bp, policy_bp
from routes.auth_routes import set_auth_db_manager # Import setter function
from routes.policy_routes import set_policy_communicator, set_policy_managers # Import setter function for communicator and managers
# Import configuration
from config import Config

app = Flask(__name__)

# Initialize Flask-JWT-Extended
jwt = JWTManager(app)

# Initialize CORS
# Allow requests from your React development server.
# In production, specify your frontend's actual domain(s)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}) # <--- ADD THIS LINE

# If you want to allow all origins during development (less secure, but easy for testing):
# CORS(app)

# Load configuration
app.config.from_object(Config)

# Initialize database
db = SQLAlchemy(app) # Initialize SQLAlchemy with your app

# Initialize Flask-Migrate with your app and db object
migrate = Migrate(app, db) # <--- THIS LINE IS CRUCIAL FOR 'db' COMMAND

# Initialize database, filebase, and communicator managers
db_manager = DatabaseManager(Config.DATABASE_URL)
filebase_manager = FilebaseManager(Config.AWS_ACCESS_KEY_ID, Config.AWS_SECRET_ACCESS_KEY, Config.S3_BUCKET_NAME, Config.AWS_REGION)
communicator = Communicator(db_manager, filebase_manager)

# Pass initialized managers/communicator to routes via setter functions
# This avoids circular imports if routes directly import managers
set_auth_db_manager(db_manager)
set_policy_communicator(communicator)
set_policy_managers(db_manager, filebase_manager)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(policy_bp)

# Create database tables on application startup (or run migrations separately)
with app.app_context():
    db_manager.create_tables()

@app.route("/")
def health_check():
    """Basic health check endpoint."""
    return jsonify({"status": "ok", "message": "SafeAgree Backend is running!"}), 200



# To run the Flask app:
if __name__ == "__main__":
# Set environment variables for development/testing.
    # Environment variables are ideally set before running the app.
    # For local development, you can set them here or in a .env file.
    # Run the Flask application
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)