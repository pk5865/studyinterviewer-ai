def summarize_content(content, source_name):
    """Generate summary - works offline without Ollama"""
    try:
        # Fallback: Extract first 2-3 sentences
        sentences = content.split('.')
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        if len(meaningful) >= 2:
            summary = "Summary: " + ". ".join(meaningful[:2]) + "."
            return summary if len(summary) < 500 else summary[:497] + "..."
        
        # Final fallback
        return f"Study material from {source_name}. Review for key concepts."
        
    except Exception as e:
        print(f"Summarizer error: {str(e)}")
        return f"Study material from {source_name}."