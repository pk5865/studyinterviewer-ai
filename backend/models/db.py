from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import shutil

db = SQLAlchemy()

def init_db(app):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "studyinterviewer.db")
    CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CHROMA_PERSIST_DIR"] = CHROMA_DIR
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    os.makedirs(CHROMA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()

# Models
class StudySession(db.Model):
    __tablename__ = "study_sessions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sources = db.relationship("Source", backref="session", lazy=True, cascade="all, delete-orphan")
    questions = db.relationship("Question", backref="session", lazy=True, cascade="all, delete-orphan")

class Source(db.Model):
    __tablename__ = "sources"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("study_sessions.id"), nullable=False)
    source_type = db.Column(db.String(50))
    name = db.Column(db.String(500))
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("study_sessions.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20))
    source_ref = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AttemptLog(db.Model):
    __tablename__ = "attempt_logs"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    user_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    feedback = db.Column(db.Text)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

# ✅ Auto-cleanup function - MOVED HERE to avoid circular import
def enforce_session_limit(max_sessions=3):
    """Delete old sessions to keep only the latest 'max_sessions'."""
    try:
        all_sessions = StudySession.query.order_by(StudySession.id.desc()).all()
        if len(all_sessions) > max_sessions:
            sessions_to_delete = all_sessions[max_sessions:]
            for session in sessions_to_delete:
                print(f"🗑️ Deleting old session {session.id}: {session.title}")
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                chroma_path = os.path.join(BASE_DIR, "chroma_store", str(session.id))
                if os.path.exists(chroma_path):
                    shutil.rmtree(chroma_path)
                db.session.delete(session)
            db.session.commit()
            print(f"✅ Cleaned up {len(sessions_to_delete)} old session(s).")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
        db.session.rollback()