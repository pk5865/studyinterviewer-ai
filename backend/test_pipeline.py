#!/usr/bin/env python3
"""
Test script to verify question generation WITHOUT frontend.
Run with: python test_pipeline.py
"""
import os
import sys
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your services
from services.pdf_parser import extract_text_from_pdf
from services.question_generator import generate_questions_with_progress
from services.progress_tracker import tracker

# Config
TEST_PDF = "pages_1_to_2.pdf"  # Update if needed
TEST_SESSION_ID = "3"

def main():
    print(f"🚀 Starting test at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📄 Testing file: {TEST_PDF}")
    
    # Check if file exists
    if not os.path.exists(TEST_PDF):
        print(f"❌ File not found: {TEST_PDF}")
        print(f"💡 Tip: Upload your PDF to backend/uploads/ first")
        return
    
    # Get file size
    file_size = os.path.getsize(TEST_PDF) / 1024  # KB
    print(f"📊 File size: {file_size:.1f} KB")
    
    start_time = time.time()
    
    # Step 1: Extract text
    print("\n📄 Step 1: Extracting text from PDF...")
    text = extract_text_from_pdf(TEST_PDF)
    
    if not text:
        print("❌ Failed to extract text")
        return
    
    char_count = len(text)
    word_count = len(text.split())
    print(f"✅ Extracted: {char_count:,} chars, {word_count:,} words")
    
    # Step 2: Generate questions
    print(f"\n🤖 Step 2: Generating questions (session: {TEST_SESSION_ID})...")
    print("⏱️  This may take 2-5 minutes for large files...")
    
    questions = generate_questions_with_progress(
        session_id=TEST_SESSION_ID,
        content=text,
        source_name="JS_Notes_compressed.pdf"
    )
    
    elapsed = time.time() - start_time
    
    # Step 3: Show results
    print(f"\n{'='*60}")
    print(f"🎉 TEST COMPLETE")
    print(f"{'='*60}")
    print(f"⏱️  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"❓ Questions generated: {len(questions)}")
    print(f"📋 Sample questions:")
    
    for i, q in enumerate(questions[:3], 1):  # Show first 3
        print(f"\n  {i}. [{q.get('level', 'N/A')}] {q.get('question', 'N/A')[:100]}...")
        print(f"     Answer: {q.get('answer', 'N/A')[:100]}...")
    
    if len(questions) > 3:
        print(f"\n  ... and {len(questions) - 3} more questions")
    
    # Save questions to JSON for inspection
    import json
    output_file = f"test_output_{TEST_SESSION_ID}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Questions saved to: {output_file}")
    
    # Cleanup progress tracker
    tracker.clear_session(TEST_SESSION_ID)
    
    print(f"\n✅ Test finished successfully!")

if __name__ == "__main__":
    main()