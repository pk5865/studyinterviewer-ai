from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import shutil

db = SQLAlchemy()

def init_db(app):
    # ✅ Fix: Use __file__ (with double underscores)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "studyinterviewer.db")
    CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CHROMA_PERSIST_DIR"] = CHROMA_DIR
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max

    os.makedirs(CHROMA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()

# ✅ Auto-Cleanup Function: Keeps only the newest 3 sessions
def enforce_session_limit(max_sessions=3):
    try:
        # Get all sessions ordered by ID (newest first)
        all_sessions = StudySession.query.order_by(StudySession.id.desc()).all()
        
        # If we have more than max_sessions, delete the old ones
        if len(all_sessions) > max_sessions:
            sessions_to_delete = all_sessions[max_sessions:]
            
            for session in sessions_to_delete:
                print(f"🗑️ Cleaning up old session {session.id}: {session.title}")
                
                # 1. Delete ChromaDB folder for this session
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                chroma_path = os.path.join(BASE_DIR, "chroma_store", str(session.id))
                if os.path.exists(chroma_path):
                    shutil.rmtree(chroma_path)
                
                # 2. Delete from Database (Cascade deletes Sources, Questions, Logs)
                db.session.delete(session)
            
            db.session.commit()
            print(f"✅ Cleaned up {len(sessions_to_delete)} old session(s).")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        db.session.rollback()

# Models
class StudySession(db.Model):
    __tablename__ = "study_sessions"  # ✅ Fixed: Added underscores
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sources = db.relationship("Source", backref="session", lazy=True, cascade="all, delete-orphan")
    questions = db.relationship("Question", backref="session", lazy=True, cascade="all, delete-orphan")

class Source(db.Model):
    __tablename__ = "sources"  # ✅ Fixed: Added underscores
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("study_sessions.id"), nullable=False)
    source_type = db.Column(db.String(50))
    name = db.Column(db.String(500))
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = "questions"  # ✅ Fixed: Added underscores
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("study_sessions.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20))
    source_ref = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "level": self.level,
            "source_ref": self.source_ref,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class AttemptLog(db.Model):
    __tablename__ = "attempt_logs"  # ✅ Fixed: Added underscores
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    user_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    feedback = db.Column(db.Text)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)