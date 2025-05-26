# safeagree_backend/config.py

import os
from datetime import timedelta

class Config:
    """
    Centralized configuration settings for the SafeAgree application.
    Uses environment variables for sensitive data and provides sensible defaults.
    """
    # Database Configuration
    # SQLite Database URI
    # This will create a file named 'site.db' in your safeagree_backend directory
    DATABASE_URL = 'sqlite:///site.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications to save resources
    # AWS S3 / File Storage Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "safeagree")
    AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")

    SECRET_KEY = 'YOUR_FLASK_APP_SUPER_SECRET_KEY_HERE'

    # Flask-JWT-Extended Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_very_secret_jwt_key_here") # REPLACE WITH A STRONG SECRET
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # AI Model Endpoints (Conceptual/Example)
    SUMMARIZER_AI_ENDPOINT = os.getenv("SUMMARIZER_AI_ENDPOINT", "http://localhost:8000/summarize")

    # Flask Application Settings
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true" # Set to False in production
    HOST = '0.0.0.0'
    PORT = 5000
    