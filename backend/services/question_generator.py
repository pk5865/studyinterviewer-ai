import json
import re
from services.progress_tracker import tracker

def generate_questions_with_progress(sid, content, source_name):
    """Generate questions using fast, large chunks for long files."""
    # ✅ FAST: 1200 chars per chunk = fewer API calls = faster
    chunk_size = 1200 
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    
    all_questions = []
    total_chunks = len(chunks)

    # Initialize progress
    if sid:
        tracker.start_session(sid)
        tracker.update(sid, "generating", "Starting generation...", total_chunks=total_chunks, current_chunk=0)

    for i, chunk in enumerate(chunks):
        sname = f"{source_name} (part {i+1})" if total_chunks > 1 else source_name
        
        # Update progress
        if sid:
            tracker.update(sid, "generating", f"Processing chunk {i+1}/{total_chunks}...", 
                          current_chunk=i+1, questions_generated=len(all_questions))

        try:
            # Simple rule-based extraction (Fallback/Safe mode for speed)
            # If you want AI, replace this section with ollama.chat()
            questions = create_smart_questions(chunk, sname)
            all_questions.extend(questions)
        except Exception as e:
            print(f"Error in chunk {i+1}: {e}")

    if sid:
        tracker.update(sid, "complete", "Generation complete!", current_chunk=total_chunks, questions_generated=len(all_questions))
    
    print(f"🎉 Generated {len(all_questions)} questions total.")
    return all_questions

def create_smart_questions(chunk, source_ref):
    """Rule-based question generation (100% offline & fast)."""
    questions = []
    lines = [line.strip() for line in chunk.split('\n') if line.strip()]
    
    # Strategy 1: Extract "X is Y" definitions
    for line in lines:
        if ' is ' in line and len(line) > 20 and len(line) < 150:
            questions.append({
                "level": "important",
                "question": f"What is {line.split(' is ')[0].strip()}?",
                "answer": line,
                "source_ref": source_ref
            })
            if len(questions) >= 1: break
    
    # Strategy 2: Bullet points
    if not questions:
        for line in lines:
            if line.startswith('•') or line.startswith('-'):
                questions.append({
                    "level": "moderate",
                    "question": f"Explain: {line[1:].strip()[:50]}...",
                    "answer": line,
                    "source_ref": source_ref
                })
                break

    # Fallback if nothing found
    if not questions:
        questions.append({
            "level": "okay",
            "question": f"Summarize this section: {chunk[:40]}...",
            "answer": chunk[:150],
            "source_ref": source_ref
        })
        
    return questions