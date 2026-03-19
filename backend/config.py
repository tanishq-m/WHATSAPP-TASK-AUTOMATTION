"""
Configuration file for WhatsApp Task Manager Backend.

This file contains all configuration variables for the Flask application.
All sensitive values are loaded from environment variables via .env file.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# FLASK CONFIGURATION
# ============================================================================

# Flask environment: "development" or "production"
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

# Port number for Flask server
PORT = int(os.environ.get('FLASK_PORT', 5001))

# Enable/disable debug mode (auto-reload, detailed errors)
DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

# Frontend URL for generating submission links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# SQLite database file path (absolute path to backend/database.db)
DATABASE_PATH = os.path.join(BACKEND_DIR, "database.db")


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

# Allowed origins for CORS (React frontend URLs)
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Vite dev server (default)
    "http://localhost:5173",      # Vite dev server (alternative port)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]


# ============================================================================
# KAPSO API CONFIGURATION
# ============================================================================

# Kapso API credentials - loaded from .env file
KAPSO_API_KEY = os.environ.get('KAPSO_API_KEY', '')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID', '')
KAPSO_API_BASE = os.environ.get('KAPSO_API_BASE', 'https://api.kapso.ai/meta/whatsapp/v24.0')


# ============================================================================
# KAPSO WORKFLOW CONFIGURATION (for Stage 7)
# ============================================================================

WORKFLOW_ID = os.environ.get('WORKFLOW_ID', '')


# ============================================================================
# SCHEDULER CONFIGURATION (for Stage 7)
# ============================================================================

# Time to trigger EOD workflow (24-hour format)
EOD_TRIGGER_HOUR = int(os.environ.get('EOD_TRIGGER_HOUR', 17))
EOD_TRIGGER_MINUTE = int(os.environ.get('EOD_TRIGGER_MINUTE', 0))

# Timezone for scheduler
TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Kolkata')
