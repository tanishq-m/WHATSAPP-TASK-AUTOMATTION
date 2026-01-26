"""
WhatsApp Task Manager - Flask Backend
Main application file for the task management API.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import config
from config import FLASK_ENV, PORT, DEBUG, ALLOWED_ORIGINS
from db import init_database
from api import register_blueprints


def create_app(test_config=None):
    """
    Application factory for creating Flask app instances.
    
    Args:
        test_config: Optional dict of config overrides for testing
        
    Returns:
        Flask application instance
    """
    # Initialize Flask app
    app = Flask(__name__)

    # Configure CORS to allow requests from React frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Configure Flask app
    app.config['ENV'] = FLASK_ENV
    app.config['DEBUG'] = DEBUG
    
    # Apply test config if provided
    if test_config:
        app.config.update(test_config)

    # Initialize database
    init_database()

    # Register API blueprints
    register_blueprints(app)
    
    # Register routes and handlers
    _register_health_check(app)
    _register_root_webhook(app)
    _register_error_handlers(app)
    _register_request_logging(app)

    return app


def _register_health_check(app):
    """Register health check endpoint."""
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint to verify the API is running.
        
        Returns:
            JSON response with status and database connectivity
        
        Example:
            GET /api/health
            Response: {"status": "healthy", "database": "connected", "timestamp": "..."}
        """
        try:
            print("✅ Health check endpoint called")
            
            # Check database connectivity
            db_status = "connected"
            try:
                import sqlite3
                conn = sqlite3.connect(config.DATABASE_PATH)
                conn.execute("SELECT 1")
                conn.close()
            except Exception as db_error:
                db_status = f"error: {str(db_error)}"
            
            return jsonify({
                "status": "healthy",
                "database": db_status,
                "timestamp": datetime.now().isoformat(),
                "environment": FLASK_ENV
            }), 200
        except Exception as e:
            print(f"❌ Error in health check: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500


def _register_root_webhook(app):
    """Register root webhook endpoint for Kapso."""
    
    @app.route('/', methods=['POST'])
    def root_webhook():
        """
        Root webhook endpoint for Kapso.
        Kapso sends webhooks to the root path '/', so we delegate to the webhook handler.
        """
        from api.webhooks import whatsapp_webhook
        return whatsapp_webhook()


def _register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        print(f"❌ 404 Error: {request.url}")
        return jsonify({
            "success": False,
            "error": "Endpoint not found",
            "path": request.path
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        print(f"❌ 500 Error: {error}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        print(f"❌ 400 Error: {error}")
        return jsonify({
            "success": False,
            "error": "Bad request"
        }), 400


def _register_request_logging(app):
    """Register request logging for debugging."""
    
    @app.before_request
    def log_request():
        """Log all incoming requests for debugging."""
        print(f"📥 {request.method} {request.path}")
        if request.method in ['POST', 'PUT'] and request.is_json:
            print(f"   Body: {request.get_json()}")

    @app.after_request
    def log_response(response):
        """Log all outgoing responses for debugging."""
        print(f"📤 {request.method} {request.path} → Status: {response.status_code}")
        return response


# Create the default app instance for backward compatibility
# This allows existing code to import 'app' directly
app = create_app()


# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 WhatsApp Task Manager - Flask Backend Starting...")
    print("=" * 60)
    print(f"Environment: {FLASK_ENV}")
    print(f"Debug Mode: {DEBUG}")
    print(f"Port: {PORT}")
    print(f"Allowed Origins: {ALLOWED_ORIGINS}")
    print("=" * 60)
    
    print("\n✅ Flask server is ready!")
    print(f"🌐 API running at: http://localhost:{PORT}/api")
    print(f"🏥 Health check: http://localhost:{PORT}/api/health")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    # Run the Flask development server
    app.run(
        host='0.0.0.0',  # Allow connections from any IP (for testing)
        port=PORT,
        debug=DEBUG,
        use_reloader=True  # Auto-reload on code changes
    )
