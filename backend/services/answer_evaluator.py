import re

def evaluate_answer(question, correct_answer, user_answer):
    """Evaluate answer WITHOUT AI - simple keyword matching + length scoring"""
    
    if not user_answer or not user_answer.strip():
        return {
            "is_correct": False,
            "score": 0,
            "verdict": "Wrong",
            "feedback": "No answer provided. Please type your response.",
            "correct_answer": correct_answer
        }
    
    # Clean text for comparison
    def clean(text):
        return re.sub(r'[^a-z0-9\s]', '', text.lower())
    
    user_clean = clean(user_answer)
    correct_clean = clean(correct_answer)
    
    # Score based on keyword overlap
    user_words = set(user_clean.split())
    correct_words = set(correct_clean.split())
    
    if user_words and correct_words:
        overlap = len(user_words & correct_words)
        score = min(100, overlap * 25)  # 4 matching words = 100%
    else:
        score = 0
    
    # Bonus for detailed answers
    if len(user_answer) > 50:
        score = min(100, score + 10)
    if len(user_answer) > 100:
        score = min(100, score + 10)
    
    # Determine verdict
    if score >= 70:
        verdict = "Correct"
        feedback = "Great answer! You covered the key concepts."
    elif score >= 40:
        verdict = "Partially Correct"
        feedback = "Good start! Try adding more specific details or examples."
    else:
        verdict = "Needs Improvement"
        feedback = f"Review the reference answer: {correct_answer[:100]}..."
    
    return {
        "is_correct": score >= 50,
        "score": score,
        "verdict": verdict,
        "feedback": feedback,
        "correct_answer": correct_answer
    }