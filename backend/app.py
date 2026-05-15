from flask import Flask, jsonify
from flask_cors import CORS
from models.db import db, enforce_session_limit  # ✅ Import from db.py
from routes.session import session_bp
from routes.upload import upload_bp
from routes.chat import chat_bp
from routes.summary import summary_bp
import os

def create_app():
    app = Flask(__name__)  # ✅ Fixed: __name__ with double underscores
    CORS(app)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'studyinterviewer.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    app.register_blueprint(session_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(summary_bp)

    @app.route('/')
    def index():
        return jsonify({"message": "StudyInterviewer AI API is running!"}), 200

    with app.app_context():
        db.create_all()
        enforce_session_limit(max_sessions=3)  # ✅ Auto-cleanup on startup

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)