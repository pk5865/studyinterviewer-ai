from flask import Blueprint, jsonify
from models.db import Source

summary_bp = Blueprint("summary", __name__)

@summary_bp.route("/api/summary/<int:source_id>", methods=["GET"])
def get_summary(source_id):
    """Get summary for a source"""
    try:
        source = Source.query.get_or_404(source_id)
        return jsonify({
            "id": source.id,
            "type": source.source_type,
            "name": source.name,
            "summary": source.summary or "No summary available"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500