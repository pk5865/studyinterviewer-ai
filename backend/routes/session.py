from flask import Blueprint, request, jsonify
from models.db import db, StudySession, Source, Question, AttemptLog
from services.vectorstore import delete_vectorstore
import os

session_bp = Blueprint("session", __name__)

@session_bp.route("/api/sessions", methods=["GET"])
def list_sessions():
    """List all study sessions"""
    try:
        sessions = StudySession.query.order_by(StudySession.created_at.desc()).all()
        result = []
        for s in sessions:
            source_count = Source.query.filter_by(session_id=s.id).count()
            question_count = Question.query.filter_by(session_id=s.id).count()
            result.append({
                "id": s.id,
                "title": s.title,
                "source_count": source_count,
                "question_count": question_count,
                "created_at": s.created_at.isoformat()
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@session_bp.route("/api/session/create", methods=["POST"])
def create_session():
    """Create a new study session"""
    try:
        data = request.get_json()
        title = data.get("title", "Untitled Session")
        
        session = StudySession(title=title)
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            "message": "Session created",
            "session_id": session.id,
            "title": session.title
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@session_bp.route("/api/session/<int:session_id>", methods=["GET"])
def get_session(session_id):
    """Get session details"""
    try:
        session = StudySession.query.get_or_404(session_id)
        sources = Source.query.filter_by(session_id=session_id).all()
        questions = Question.query.filter_by(session_id=session_id).all()
        
        return jsonify({
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "source_count": len(sources),
            "question_count": len(questions),
            "sources": [
                {
                    "id": s.id,
                    "type": s.source_type,
                    "name": s.name,
                    "summary": s.summary
                } for s in sources
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@session_bp.route("/api/session/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a session and all associated data"""
    try:
        session = StudySession.query.get_or_404(session_id)
        
        # Delete associated records
        AttemptLog.query.filter(
            AttemptLog.question_id.in_(
                db.session.query(Question.id).filter_by(session_id=session_id)
            )
        ).delete(synchronize_session=False)
        
        Question.query.filter_by(session_id=session_id).delete()
        Source.query.filter_by(session_id=session_id).delete()
        
        # Delete ChromaDB folder
        delete_vectorstore(session_id)
        
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({"message": "Session deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500