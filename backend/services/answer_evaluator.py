import re

def evaluate_answer(question, correct_answer, user_answer):
    if not user_answer or not user_answer.strip():
        return {"is_correct": False, "score": 0, "verdict": "Wrong", 
                "feedback": "No answer provided. Please type your response.", "correct_answer": correct_answer}
    
    def clean(text):
        return re.sub(r'[^a-z0-9\s]', '', text.lower())
    
    user_words = set(clean(user_answer).split())
    correct_words = set(clean(correct_answer).split())
    
    score = 0
    if user_words and correct_words:
        overlap = len(user_words & correct_words)
        score = min(100, overlap * 25)  # 4 matching words = 100%
    
    if len(user_answer) > 50: score = min(100, score + 10)
    if len(user_answer) > 100: score = min(100, score + 10)
    
    if score >= 70:
        verdict, feedback = "Correct", "Great answer! You covered the key concepts."
    elif score >= 40:
        verdict, feedback = "Partially Correct", "Good start! Try adding more specific details."
    else:
        verdict, feedback = "Needs Improvement", f"Review reference: {correct_answer[:100]}..."
    
    return {"is_correct": score >= 50, "score": score, "verdict": verdict, 
            "feedback": feedback, "correct_answer": correct_answer}