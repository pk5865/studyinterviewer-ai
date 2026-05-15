import os
import time
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models.db import db, StudySession, Source, Question, enforce_session_limit
from services.pdf_parser import extract_text_from_pdf
from services.youtube_parser import extract_text_from_youtube
from services.web_parser import extract_text_from_web
from services.vectorstore import add_text_to_vectorstore
from services.question_generator import generate_questions_with_progress
from services.summarizer import summarize_content
from services.progress_tracker import tracker

upload_bp = Blueprint("upload", __name__)

ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_URL_LENGTH = 2048  # 2KB for URLs

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route("/api/upload/pdf", methods=["POST"])
def upload_pdf():
    session_id = request.form.get("session_id")
    
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # ✅ Check file size before processing
    file.seek(0, 2)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > MAX_FILE_SIZE:
        return jsonify({
            "error": f"File too large ({file_length / 1024 / 1024:.1f}MB). Maximum size is 5MB. Please compress your PDF or use a smaller file."
        }), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        try:
            text = extract_text_from_pdf(filepath)
            if not text or len(text) < 50:
                raise ValueError("Could not extract valid text from PDF. The file might be corrupted or contain only images.")
            
            add_text_to_vectorstore(session_id, text, filename)
            
            tracker.start_session(session_id)
            questions = generate_questions_with_progress(session_id, text, filename)
            summary = summarize_content(text[:2000], filename)
            
            source = Source(
                session_id=session_id,
                source_type="pdf",
                name=filename,
                summary=summary
            )
            db.session.add(source)
            db.session.commit()
            
            for q in questions:
                question = Question(
                    session_id=session_id,
                    question=q.get("question", ""),
                    answer=q.get("answer", ""),
                    level=q.get("level", "moderate").lower(),
                    source_ref=q.get("source_ref", filename)
                )
                db.session.add(question)
            db.session.commit()
            
            # ✅ Auto-cleanup old sessions
            enforce_session_limit(max_sessions=3)
            
            tracker.update(session_id, "complete", "Done!")
            
            return jsonify({
                "message": "PDF processed successfully",
                "questions_count": len(questions),
                "session_id": session_id
            }), 200
            
        except Exception as e:
            db.session.rollback()
            tracker.update(session_id, "error", str(e))
            print(f"Upload error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

@upload_bp.route("/api/upload/youtube", methods=["POST"])
def upload_youtube():
    session_id = request.form.get("session_id")
    url = request.form.get("url", "")
    
    # ✅ Validate URL length
    if len(url) > MAX_URL_LENGTH:
        return jsonify({"error": "URL too long. Maximum length is 2KB."}), 400
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        text = extract_text_from_youtube(url)
        add_text_to_vectorstore(session_id, text, f"YouTube: {url}")
        questions = generate_questions_with_progress(session_id, text, f"YouTube: {url}")
        summary = summarize_content(text[:2000], f"YouTube: {url}")
        
        source = Source(
            session_id=session_id,
            source_type="youtube",
            name=url,
            summary=summary
        )
        db.session.add(source)
        db.session.commit()
        
        for q in questions:
            question = Question(
                session_id=session_id,
                question=q.get("question", ""),
                answer=q.get("answer", ""),
                level=q.get("level", "moderate").lower(),
                source_ref=q.get("source_ref", url)
            )
            db.session.add(question)
        db.session.commit()
        
        return jsonify({
            "message": "YouTube video processed successfully",
            "questions_count": len(questions),
            "session_id": session_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"YouTube upload error: {e}")
        return jsonify({"error": f"Failed to process YouTube video: {str(e)}"}), 500

@upload_bp.route("/api/upload/web", methods=["POST"])
def upload_web():
    session_id = request.form.get("session_id")
    url = request.form.get("url", "")
    
    # ✅ Validate URL length
    if len(url) > MAX_URL_LENGTH:
        return jsonify({"error": "URL too long. Maximum length is 2KB."}), 400
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        text = extract_text_from_web(url)
        add_text_to_vectorstore(session_id, text, f"Web: {url}")
        questions = generate_questions_with_progress(session_id, text, f"Web: {url}")
        summary = summarize_content(text[:2000], f"Web: {url}")
        
        source = Source(
            session_id=session_id,
            source_type="web",
            name=url,
            summary=summary
        )
        db.session.add(source)
        db.session.commit()
        
        for q in questions:
            question = Question(
                session_id=session_id,
                question=q.get("question", ""),
                answer=q.get("answer", ""),
                level=q.get("level", "moderate").lower(),
                source_ref=q.get("source_ref", url)
            )
            db.session.add(question)
        db.session.commit()
        
        return jsonify({
            "message": "Web page processed successfully",
            "questions_count": len(questions),
            "session_id": session_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Web upload error: {e}")
        return jsonify({"error": f"Failed to process web page: {str(e)}"}), 500

@upload_bp.route("/api/progress/<int:session_id>", methods=["GET"])
def get_upload_progress(session_id):
    progress = tracker.get_progress(session_id)
    if not progress:
        return jsonify({
            "status": "idle",
            "message": "",
            "current_chunk": 0,
            "total_chunks": 0,
            "questions_generated": 0,
            "percentage": 0,
            "timestamp": time.time()
        }), 200
    
    percentage = 0
    if progress.get("total_chunks", 0) > 0:
        percentage = int((progress["current_chunk"] / progress["total_chunks"]) * 100)
    elif progress["status"] == "complete":
        percentage = 100
    
    return jsonify({
        "status": progress.get("status", "idle"),
        "message": progress.get("message", ""),
        "current_chunk": progress.get("current_chunk", 0),
        "total_chunks": progress.get("total_chunks", 0),
        "questions_generated": progress.get("questions_generated", 0),
        "percentage": percentage,
        "timestamp": time.time()
    }), 200