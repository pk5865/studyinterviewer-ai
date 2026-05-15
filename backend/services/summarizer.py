def summarize_content(content, source_name):
    """Generate summary WITHOUT AI - rule-based fallback"""
    try:
        sentences = content.split('.')
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        if len(meaningful) >= 2:
            summary = "Summary: " + ". ".join(meaningful[:2]) + "."
            return summary if len(summary) < 500 else summary[:497] + "..."
        
        return f"Study material from {source_name}. Review for key concepts."
        
    except Exception as e:
        print(f"Summarizer error: {str(e)}")
        return f"Content from {source_name}"