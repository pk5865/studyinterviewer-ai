import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from models.db import db, enforce_session_limit
from routes.session import session_bp
from routes.upload import upload_bp
from routes.chat import chat_bp
from routes.summary import summary_bp

# ✅ Hide repetitive GET/POST logs (clean terminal)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

def create_app():
    app = Flask(__name__)
    CORS(app)

    # ✅ Use PostgreSQL in production (Neon), SQLite locally
    db_uri = os.environ.get("DATABASE_URL")
    if not db_uri:
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_uri = "sqlite:///" + os.path.join(basedir, "studyinterviewer.db")
        
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # ✅ 5MB file upload limit
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(session_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(summary_bp)

    @app.route('/')
    def index():
        return jsonify({"message": "StudyInterviewer AI API is running!"}), 200
    
    # ✅ Error handler for file too large (413)
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({
            "error": "File too large. Maximum size is 5MB. Please compress your PDF."
        }), 413
    
    # ✅ Generic error handler
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    with app.app_context():
        db.create_all()
        # ✅ Auto-cleanup old sessions on startup
        enforce_session_limit(max_sessions=3)

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)