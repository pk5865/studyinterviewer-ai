import os
import re
import shutil
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import pdfplumber
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from youtube_transcript_api import YouTubeTranscriptApi

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
VECTOR_ROOT = BASE_DIR / "chroma_store"
GENERATED_FOLDER = BASE_DIR / "generated"
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_URL_LENGTH = 2048
ALLOWED_EXTENSIONS = {"pdf"}
URL_RE = re.compile(r"(https?://[^\s<>\"']+)")

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
sqlite_path = (BASE_DIR / "studyinterviewer.db").as_posix()
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or f"sqlite:///{sqlite_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

db = SQLAlchemy()
db.init_app(app)


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
    source_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("study_sessions.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), default="moderate")
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AttemptLog(db.Model):
    __tablename__ = "attempt_logs"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    user_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    feedback = db.Column(db.Text)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProgressTracker:
    def __init__(self):
        self.progress = {}
        self.lock = threading.Lock()

    def start_session(self, session_id):
        key = str(session_id)
        with self.lock:
            self.progress[key] = {
                "status": "starting",
                "message": "Initializing upload...",
                "current_chunk": 0,
                "total_chunks": 0,
                "questions_generated": 0,
                "timestamp": time.time(),
                "started_at": time.time(),
            }

    def update(self, session_id, status, message, current_chunk=None, total_chunks=None, questions_generated=None):
        key = str(session_id)
        with self.lock:
            if key in self.progress:
                self.progress[key]["status"] = status
                self.progress[key]["message"] = message
                self.progress[key]["timestamp"] = time.time()
                if current_chunk is not None:
                    self.progress[key]["current_chunk"] = current_chunk
                if total_chunks is not None:
                    self.progress[key]["total_chunks"] = total_chunks
                if questions_generated is not None:
                    self.progress[key]["questions_generated"] = questions_generated

    def get_progress(self, session_id):
        key = str(session_id)
        with self.lock:
            return self.progress.get(
                key,
                {
                    "status": "idle",
                    "message": "",
                    "current_chunk": 0,
                    "total_chunks": 0,
                    "questions_generated": 0,
                    "percentage": 0,
                },
            )

    def clear_session(self, session_id):
        key = str(session_id)
        with self.lock:
            self.progress.pop(key, None)


tracker = ProgressTracker()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def payload_dict():
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    if request.form:
        return request.form.to_dict()
    return {}


def parse_session_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_text_from_pdf(path):
    text = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text.strip())
        return "\n\n".join(text)
    except Exception as exc:
        print(f"PDF parse error: {exc}")
        return ""


def extract_text_from_youtube(url):
    try:
        video_id = None
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        elif "/shorts/" in url:
            video_id = url.split("/shorts/")[1].split("?")[0]

        if not video_id:
            return "Could not extract YouTube video ID from URL."

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
        text = " ".join(entry["text"] for entry in transcript)
        text = re.sub(r"\s+", " ", text).strip()
        return text if text else "No transcript available for this video."
    except Exception as exc:
        print(f"YouTube transcript error: {exc}")
        return f"Error fetching transcript: {exc}"


def extract_text_from_web(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text[:4000] if text else "No readable content found."
    except Exception as exc:
        print(f"Web parse error: {exc}")
        return f"Error fetching webpage: {exc}"


def add_text_to_vectorstore(session_id, text, source_name):
    try:
        session_dir = VECTOR_ROOT / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        safe_name = secure_filename(source_name) or f"source-{session_id}"
        text_file = session_dir / f"{safe_name}.txt"
        text_file.write_text(text, encoding="utf-8")
        return True
    except Exception as exc:
        print(f"Error saving text: {exc}")
        return False


def delete_vectorstore(session_id):
    try:
        session_dir = VECTOR_ROOT / str(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
        return True
    except Exception as exc:
        print(f"Error deleting vectorstore: {exc}")
        return False


def summarize_content(content, source_name):
    try:
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 30]
        if len(sentences) >= 2:
            summary = "Summary: " + ". ".join(sentences[:2]) + "."
            return summary if len(summary) < 500 else summary[:497] + "..."
        return f"Study material from {source_name}. Review for key concepts."
    except Exception as exc:
        print(f"Summarizer error: {exc}")
        return f"Content from {source_name}"


def create_offline_question(chunk, source_ref):
    chunk = chunk.strip()
    if not chunk:
        return None

    match = re.search(r"([A-Z][a-z][^.]*?)\s+is\s+([^.]+)\.", chunk)
    if match:
        term = match.group(1).strip()
        definition = match.group(2).strip()
        return {
            "level": "important",
            "question": f"What is {term}?",
            "answer": f"{term} is {definition}.",
            "source_ref": source_ref,
        }

    lines = [line.strip() for line in chunk.split("\n") if line.strip() and len(line.strip()) > 20]
    if lines and lines[0].startswith(("•", "-", "*")):
        content = lines[0].lstrip("•-* ").strip()
        return {
            "level": "moderate",
            "question": f"Explain: {content[:60]}...",
            "answer": content,
            "source_ref": source_ref,
        }

    sentences = [s.strip() for s in re.split(r"[.!?]+", chunk) if len(s.strip()) > 30]
    topic = sentences[0][:70] if sentences else chunk[:50]
    return {
        "level": "okay",
        "question": f"What do you know about: {topic}...?",
        "answer": chunk[:200] + ("..." if len(chunk) > 200 else ""),
        "source_ref": source_ref,
    }


def generate_questions_with_progress(session_id, content, source_name):
    chunk_size = 800
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
    all_questions = []

    tracker.start_session(session_id)
    tracker.update(
        session_id,
        "processing",
        "Generating questions (offline mode)...",
        total_chunks=len(chunks),
        current_chunk=0,
        questions_generated=0,
    )

    for index, chunk in enumerate(chunks, 1):
        tracker.update(
            session_id,
            "generating",
            f"Processing chunk {index}/{len(chunks)}...",
            current_chunk=index,
            questions_generated=len(all_questions),
        )
        question = create_offline_question(chunk, f"{source_name} (part {index})")
        if question:
            all_questions.append(question)

    if not all_questions:
        all_questions.append(
            {
                "level": "okay",
                "question": f"What are the key ideas in {source_name}?",
                "answer": content[:300] or f"Content from {source_name}",
                "source_ref": source_name,
            }
        )

    tracker.update(
        session_id,
        "complete",
        "Generation complete!",
        current_chunk=len(chunks),
        questions_generated=len(all_questions),
    )
    return all_questions


def evaluate_answer(question, correct_answer, user_answer):
    if not user_answer or not user_answer.strip():
        return {
            "is_correct": False,
            "score": 0,
            "verdict": "Wrong",
            "feedback": "No answer provided. Please type your response.",
            "correct_answer": correct_answer,
        }

    def clean(text):
        return re.sub(r"[^a-z0-9\s]", "", text.lower())

    user_words = set(clean(user_answer).split())
    correct_words = set(clean(correct_answer).split())

    score = 0
    if user_words and correct_words:
        overlap = len(user_words & correct_words)
        score = min(100, overlap * 25)

    if len(user_answer) > 50:
        score = min(100, score + 10)
    if len(user_answer) > 100:
        score = min(100, score + 10)

    if score >= 70:
        verdict, feedback = "Correct", "Great answer! You covered the key concepts."
    elif score >= 40:
        verdict, feedback = "Partially Correct", "Good start! Try adding more specific details."
    else:
        verdict, feedback = "Needs Improvement", f"Review reference: {correct_answer[:100]}..."

    return {
        "is_correct": score >= 50,
        "score": score,
        "verdict": verdict,
        "feedback": feedback,
        "correct_answer": correct_answer,
    }


def enforce_session_limit(max_sessions=3):
    try:
        sessions = StudySession.query.order_by(StudySession.id.desc()).all()
        if len(sessions) <= max_sessions:
            return
        for session in sessions[max_sessions:]:
            delete_vectorstore(session.id)
            db.session.delete(session)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        print(f"Cleanup failed: {exc}")


def session_stats(session_id):
    question_total = Question.query.filter_by(session_id=session_id).count()
    attempted = (
        db.session.query(AttemptLog)
        .join(Question, AttemptLog.question_id == Question.id)
        .filter(Question.session_id == session_id)
        .count()
    )
    correct = (
        db.session.query(AttemptLog)
        .join(Question, AttemptLog.question_id == Question.id)
        .filter(Question.session_id == session_id, AttemptLog.is_correct.is_(True))
        .count()
    )
    score_pct = round((correct / question_total) * 100) if question_total else 0
    return question_total, attempted, correct, score_pct


@app.errorhandler(413)
def too_large(error):
    return jsonify({"error": "File too large. Maximum size is 5MB."}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "message": "StudyInterviewer AI API is running!",
            "database": "postgres" if DATABASE_URL else "sqlite",
        }
    ), 200


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    sessions = StudySession.query.order_by(StudySession.created_at.desc()).all()
    result = []
    for session in sessions:
        source_count = Source.query.filter_by(session_id=session.id).count()
        question_count = Question.query.filter_by(session_id=session.id).count()
        result.append(
            {
                "id": session.id,
                "title": session.title,
                "source_count": source_count,
                "question_count": question_count,
                "created_at": session.created_at.isoformat(),
            }
        )
    return jsonify(result), 200


@app.route("/api/session/create", methods=["POST"])
def create_session():
    data = payload_dict()
    title = (data.get("title") or "Untitled Session").strip()
    session = StudySession(title=title)
    try:
        db.session.add(session)
        db.session.commit()
        return jsonify({"message": "Session created", "session_id": session.id, "title": session.title}), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@app.route("/api/session/<int:session_id>", methods=["GET"])
def get_session(session_id):
    session = StudySession.query.get_or_404(session_id)
    sources = Source.query.filter_by(session_id=session_id).all()
    questions = Question.query.filter_by(session_id=session_id).all()
    return jsonify(
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "source_count": len(sources),
            "question_count": len(questions),
            "sources": [
                {
                    "id": source.id,
                    "type": source.source_type,
                    "name": source.name,
                    "summary": source.summary,
                }
                for source in sources
            ],
        }
    ), 200


@app.route("/api/session/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    session = StudySession.query.get_or_404(session_id)
    try:
        AttemptLog.query.filter(
            AttemptLog.question_id.in_(db.session.query(Question.id).filter_by(session_id=session_id))
        ).delete(synchronize_session=False)
        Question.query.filter_by(session_id=session_id).delete()
        Source.query.filter_by(session_id=session_id).delete()
        delete_vectorstore(session_id)
        tracker.clear_session(session_id)
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": "Session deleted"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@app.route("/api/upload/pdf", methods=["POST"])
def upload_pdf():
    session_id = parse_session_id(request.form.get("session_id"))
    if session_id is None:
        return jsonify({"error": "Missing session_id"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    if file_length > MAX_FILE_SIZE:
        return jsonify({"error": "File too large. Maximum size is 5MB."}), 400

    safe_name = secure_filename(file.filename) or f"upload-{session_id}.pdf"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        text = extract_text_from_pdf(tmp_path)
        if not text or len(text.strip()) < 50:
            raise ValueError("Could not extract valid text from PDF.")

        add_text_to_vectorstore(session_id, text, safe_name)
        questions = generate_questions_with_progress(session_id, text, safe_name)
        summary = summarize_content(text[:2000], safe_name)

        source = Source(session_id=session_id, source_type="pdf", name=safe_name, summary=summary)
        db.session.add(source)
        db.session.commit()

        for item in questions:
            db.session.add(
                Question(
                    session_id=session_id,
                    question=item.get("question", ""),
                    answer=item.get("answer", ""),
                    level=(item.get("level") or "moderate").lower(),
                    source_ref=item.get("source_ref", safe_name),
                )
            )
        db.session.commit()
        enforce_session_limit(max_sessions=3)
        return jsonify({"message": "PDF processed successfully", "questions_count": len(questions), "session_id": session_id}), 200
    except Exception as exc:
        db.session.rollback()
        tracker.update(session_id, "error", str(exc))
        return jsonify({"error": str(exc)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/api/upload/youtube", methods=["POST"])
def upload_youtube():
    data = payload_dict()
    session_id = parse_session_id(data.get("session_id"))
    url = (data.get("url") or "").strip()
    if session_id is None:
        return jsonify({"error": "Missing session_id"}), 400
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if len(url) > MAX_URL_LENGTH:
        return jsonify({"error": "URL too long. Maximum length is 2KB."}), 400

    try:
        text = extract_text_from_youtube(url)
        add_text_to_vectorstore(session_id, text, f"YouTube-{session_id}")
        questions = generate_questions_with_progress(session_id, text, f"YouTube: {url}")
        summary = summarize_content(text[:2000], f"YouTube: {url}")

        source = Source(session_id=session_id, source_type="youtube", name=url, summary=summary)
        db.session.add(source)
        db.session.commit()

        for item in questions:
            db.session.add(
                Question(
                    session_id=session_id,
                    question=item.get("question", ""),
                    answer=item.get("answer", ""),
                    level=(item.get("level") or "moderate").lower(),
                    source_ref=item.get("source_ref", url),
                )
            )
        db.session.commit()
        enforce_session_limit(max_sessions=3)
        return jsonify({"message": "YouTube video processed successfully", "questions_count": len(questions), "session_id": session_id}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to process YouTube video: {exc}"}), 500


@app.route("/api/upload/webpage", methods=["POST"])
@app.route("/api/upload/web", methods=["POST"])
def upload_webpage():
    data = payload_dict()
    session_id = parse_session_id(data.get("session_id"))
    url = (data.get("url") or "").strip()
    if session_id is None:
        return jsonify({"error": "Missing session_id"}), 400
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if len(url) > MAX_URL_LENGTH:
        return jsonify({"error": "URL too long. Maximum length is 2KB."}), 400

    try:
        text = extract_text_from_web(url)
        add_text_to_vectorstore(session_id, text, f"Web-{session_id}")
        questions = generate_questions_with_progress(session_id, text, f"Web: {url}")
        summary = summarize_content(text[:2000], f"Web: {url}")

        source = Source(session_id=session_id, source_type="web", name=url, summary=summary)
        db.session.add(source)
        db.session.commit()

        for item in questions:
            db.session.add(
                Question(
                    session_id=session_id,
                    question=item.get("question", ""),
                    answer=item.get("answer", ""),
                    level=(item.get("level") or "moderate").lower(),
                    source_ref=item.get("source_ref", url),
                )
            )
        db.session.commit()
        enforce_session_limit(max_sessions=3)
        return jsonify({"message": "Web page processed successfully", "questions_count": len(questions), "session_id": session_id}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to process web page: {exc}"}), 500


@app.route("/api/progress/<int:session_id>", methods=["GET"])
def get_progress(session_id):
    upload_progress = tracker.get_progress(session_id)
    question_total, attempted, correct, score_pct = session_stats(session_id)
    return (
        jsonify(
            {
                "status": upload_progress.get("status", "idle"),
                "message": upload_progress.get("message", ""),
                "current_chunk": upload_progress.get("current_chunk", 0),
                "total_chunks": upload_progress.get("total_chunks", 0),
                "questions_generated": upload_progress.get("questions_generated", 0),
                "percentage": upload_progress.get("percentage", 0),
                "correct": correct,
                "attempted": attempted,
                "total": question_total,
                "score_pct": score_pct,
                "timestamp": time.time(),
            }
        ),
        200,
    )


@app.route("/api/questions/<int:session_id>", methods=["GET"])
def get_questions(session_id):
    questions = Question.query.filter_by(session_id=session_id).all()
    important = [q.to_dict() for q in questions if q.level == "important"]
    moderate = [q.to_dict() for q in questions if q.level == "moderate"]
    okay = [q.to_dict() for q in questions if q.level == "okay"]
    return jsonify({"questions": {"important": important, "moderate": moderate, "okay": okay}}), 200


@app.route("/api/questions/all/<int:session_id>", methods=["GET"])
def get_all_questions(session_id):
    questions = Question.query.filter_by(session_id=session_id).all()
    return jsonify({"questions": [q.to_dict() for q in questions]}), 200


@app.route("/api/answer", methods=["POST"])
def submit_answer():
    data = payload_dict()
    question_id = data.get("question_id")
    user_answer = data.get("user_answer", "")
    question = Question.query.get_or_404(question_id)

    result = evaluate_answer(question.question, question.answer, user_answer)
    attempt = AttemptLog(
        question_id=question_id,
        user_answer=user_answer,
        is_correct=result.get("is_correct", False),
        feedback=result.get("feedback", ""),
    )
    try:
        db.session.add(attempt)
        db.session.commit()
        return jsonify(result), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@app.route("/api/summary/<int:source_id>", methods=["GET"])
def get_summary(source_id):
    source = Source.query.get_or_404(source_id)
    return jsonify(
        {
            "id": source.id,
            "type": source.source_type,
            "name": source.name,
            "summary": source.summary or "No summary available",
        }
    ), 200


with app.app_context():
    try:
        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        VECTOR_ROOT.mkdir(parents=True, exist_ok=True)
        GENERATED_FOLDER.mkdir(parents=True, exist_ok=True)
        db.create_all()
        enforce_session_limit(max_sessions=3)
    except Exception as exc:
        print(f"Database initialization warning: {exc}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
