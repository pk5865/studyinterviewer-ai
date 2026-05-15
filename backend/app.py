import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from models.db import db, enforce_session_limit
from routes.session import session_bp
from routes.upload import upload_bp
from routes.chat import chat_bp
from routes.summary import summary_bp

# ✅ Hide repetitive GET logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

def create_app():
    app = Flask(__name__)
    CORS(app)

    # ✅ PostgreSQL for production, SQLite for local
    db_uri = os.environ.get("DATABASE_URL")
    if not db_uri:
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_uri = "sqlite:///" + os.path.join(basedir, "studyinterviewer.db")
        
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # ✅ Add 5MB file upload limit
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

    db.init_app(app)

    app.register_blueprint(session_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(summary_bp)

    @app.route('/')
    def index():
        return jsonify({"message": "StudyInterviewer AI API is running!"}), 200
    
    # ✅ Error handler for file too large
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({
            "error": "File too large. Maximum size is 5MB. Please compress your PDF."
        }), 413

    with app.app_context():
        db.create_all()
        enforce_session_limit(max_sessions=3)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)