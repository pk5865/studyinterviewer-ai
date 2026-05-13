import os
import time  # ✅ CRITICAL: Must be imported
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models.db import db, StudySession, Source, Question, enforce_session_limit  # ✅ Import from db.py
from services.pdf_parser import extract_text_from_pdf
from services.youtube_parser import extract_text_from_youtube
from services.web_parser import extract_text_from_web
from services.vectorstore import add_text_to_vectorstore
from services.question_generator import generate_questions_with_progress
from services.summarizer import summarize_content
from services.progress_tracker import tracker

upload_bp = Blueprint("upload", __name__)

ALLOWED_EXTENSIONS = {"pdf"}

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

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        try:
            # 1. Extract text
            tracker.start_session(session_id)
            tracker.update(session_id, "extracting", "Extracting text from PDF...")
            text = extract_text_from_pdf(filepath)
            
            if not text:
                raise ValueError("Failed to extract text from PDF.")

            # 2. Generate Questions
            tracker.update(session_id, "generating", "Generating questions...")
            questions = generate_questions_with_progress(session_id, text, filename)
            
            # 3. Generate Summary
            tracker.update(session_id, "summarizing", "Creating summary...")
            summary = summarize_content(text[:2000], filename)
            
            # 4. Save to Database
            tracker.update(session_id, "saving", "Saving to database...")
            
            # Save Source
            source = Source(
                session_id=session_id,
                source_type="pdf",
                name=filename,
                summary=summary
            )
            db.session.add(source)
            db.session.commit()
            
            # ✅ Save Questions - FIXED: Use correct field names
            for q in questions:
                question = Question(
                    session_id=session_id,  # ✅ Links to StudySession
                    # ❌ DO NOT use source_id - Question model doesn't have this field
                    question=q.get("question", ""),
                    answer=q.get("answer", ""),
                    level=q.get("level", "moderate"),
                    source_ref=q.get("source_ref", filename)  # ✅ Use source_ref for text reference
                )
                db.session.add(question)
            db.session.commit()
            
            tracker.update(session_id, "complete", "Done!")
            
            # ✅ Auto-cleanup - import now works because it's from db.py
            enforce_session_limit(max_sessions=3)
            
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

    return jsonify({"error": "Invalid file type"}), 400

@upload_bp.route("/api/upload/youtube", methods=["POST"])
def upload_youtube():
    session_id = request.form.get("session_id")
    url = request.form.get("url")
    
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
                level=q.get("level", "moderate"),
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
        return jsonify({"error": str(e)}), 500

@upload_bp.route("/api/upload/web", methods=["POST"])
def upload_web():
    session_id = request.form.get("session_id")
    url = request.form.get("url")
    
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
                level=q.get("level", "moderate"),
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
        return jsonify({"error": str(e)}), 500

@upload_bp.route("/api/progress/<int:session_id>", methods=["GET"])
def get_upload_progress(session_id):
    """Get real-time progress - works offline"""
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
    
    # Calculate percentage
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