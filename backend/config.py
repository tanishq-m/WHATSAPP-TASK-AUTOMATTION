"""
Configuration file for WhatsApp Task Manager Backend.

This file contains all configuration variables for the Flask application.
In production, sensitive values should be loaded from environment variables.
"""
# Kapso API Configuration
KAPSO_API_KEY = "7819cb622458c2ca2e3300008d391d85d39b962ee2b9996e8a562fa9408a5f81"  # From Kapso dashboard → Settings → API Keys
PHONE_NUMBER_ID = "597907523413541"  # From Kapso dashboard → Connected Numbers
KAPSO_API_BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"
import os

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# FLASK CONFIGURATION
# ============================================================================

# Flask environment: "development" or "production"
FLASK_ENV = "development"

# Port number for Flask server
PORT = 5001  # Changed from 5000 (macOS Control Center uses 5000)

# Enable/disable debug mode (auto-reload, detailed errors)
DEBUG = True


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
# KAPSO API CONFIGURATION (for Stage 6)
# ============================================================================

# Kapso API credentials (to be filled in Stage 5.5)
# Get these from: https://app.kapso.ai/settings/api-keys
KAPSO_API_KEY = "your_api_key_here"

# Phone Number ID from Kapso dashboard
# Get from: Connected Numbers section
PHONE_NUMBER_ID = "your_phone_number_id_here"

# Kapso API base URL (do not change)
KAPSO_API_BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"


# ============================================================================
# KAPSO WORKFLOW CONFIGURATION (for Stage 7)
# ============================================================================

# Workflow ID for EOD task status collection (to be filled in Stage 7)
# Get after creating workflow in Kapso dashboard
WORKFLOW_ID = "your_workflow_id_here"


# ============================================================================
# SCHEDULER CONFIGURATION (for Stage 7)
# ============================================================================

# Time to trigger EOD workflow (24-hour format)
EOD_TRIGGER_HOUR = 17  # 5 PM
EOD_TRIGGER_MINUTE = 0

# Timezone for scheduler
TIMEZONE = "Asia/Kolkata"  # Change to your timezone


# ============================================================================
# NOTES
# ============================================================================

"""
IMPORTANT: Never commit real API keys to Git!

For production:
1. Create a .env file (add to .gitignore)
2. Load values using python-dotenv:
   
   from dotenv import load_dotenv
   import os
   
   load_dotenv()
   KAPSO_API_KEY = os.getenv("KAPSO_API_KEY")

3. Use environment variables on hosting platform
"""
