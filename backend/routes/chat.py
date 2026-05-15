from flask import Blueprint, request, jsonify
from models.db import db, Question, AttemptLog
from services.answer_evaluator import evaluate_answer

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/api/questions/<int:session_id>", methods=["GET"])
def get_questions(session_id):
    """Get questions for practice (grouped by difficulty)"""
    try:
        questions = Question.query.filter_by(session_id=session_id).all()
        
        important = [q.to_dict() for q in questions if q.level == "important"]
        moderate = [q.to_dict() for q in questions if q.level == "moderate"]
        okay = [q.to_dict() for q in questions if q.level == "okay"]
        
        return jsonify({
            "questions": {
                "important": important,
                "moderate": moderate,
                "okay": okay
            }
        }), 200
    except Exception as e:
        print(f"Error getting questions: {e}")
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/api/questions/all/<int:session_id>", methods=["GET"])
def get_all_questions(session_id):
    """Get all questions for viewing"""
    try:
        questions = Question.query.filter_by(session_id=session_id).all()
        return jsonify({
            "questions": [q.to_dict() for q in questions]
        }), 200
    except Exception as e:
        print(f"Error getting all questions: {e}")
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/api/answer", methods=["POST"])
def submit_answer():
    """Submit answer for evaluation (100% OFFLINE)"""
    try:
        data = request.get_json()
        question_id = data.get("question_id")
        user_answer = data.get("user_answer", "")
        
        question = Question.query.get_or_404(question_id)
        
        result = evaluate_answer(
            question.question,    # ✅ Correct field
            question.answer,      # ✅ Correct field
            user_answer
        )
        
        attempt = AttemptLog(
            question_id=question_id,
            user_answer=user_answer,
            is_correct=result.get("is_correct", False),
            feedback=result.get("feedback", "")
        )
        db.session.add(attempt)
        db.session.commit()
        
        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error evaluating answer: {e}")
        return jsonify({"error": str(e)}), 500