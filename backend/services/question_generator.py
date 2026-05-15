import re
from services.progress_tracker import tracker

def generate_questions_with_progress(sid, content, source_name):
    chunk_size = 800
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    all_questions = []
    
    if sid:
        tracker.start_session(sid)
        tracker.update(sid, "processing", "Generating questions (offline mode)...", 
                      total_chunks=len(chunks), current_chunk=0, questions_generated=0)

    for i, chunk in enumerate(chunks, 1):
        if sid:
            tracker.update(sid, "generating", f"Processing chunk {i}/{len(chunks)}...", 
                          current_chunk=i, questions_generated=len(all_questions))
        
        question = create_offline_question(chunk, f"{source_name} (part {i})")
        if question:
            all_questions.append(question)

    if sid:
        tracker.update(sid, "complete", "Generation complete!", 
                      current_chunk=len(chunks), questions_generated=len(all_questions))

    print(f"🎉 Offline generation complete: {len(all_questions)} questions")
    return all_questions

def create_offline_question(chunk, source_ref):
    chunk = chunk.strip()
    if not chunk:
        return None
    
    # Strategy 1: "X is Y" definitions
    match = re.search(r'([A-Z][a-z][^.]*?)\s+is\s+([^.]+)\.', chunk)
    if match:
        term = match.group(1).strip()
        definition = match.group(2).strip()
        return {"level": "important", "question": f"What is {term}?", 
                "answer": f"{term} is {definition}.", "source_ref": source_ref}
    
    # Strategy 2: Bullet points
    lines = [l.strip() for l in chunk.split('\n') if l.strip() and len(l.strip()) > 20]
    if lines and lines[0].startswith(('•', '-', '*')):
        content = lines[0].lstrip('•-* ').strip()
        return {"level": "moderate", "question": f"Explain: {content[:60]}...", 
                "answer": content, "source_ref": source_ref}
    
    # Strategy 3: Fallback
    sentences = [s.strip() for s in re.split(r'[.!?]+', chunk) if len(s.strip()) > 30]
    topic = sentences[0][:70] if sentences else chunk[:50]
    return {"level": "okay", "question": f"What do you know about: {topic}...?", 
            "answer": chunk[:200] + ("..." if len(chunk) > 200 else ""), "source_ref": source_ref}