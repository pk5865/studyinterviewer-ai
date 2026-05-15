import os
import shutil
from pathlib import Path

def add_text_to_vectorstore(session_id, text, source_name):
    """
    Simple text storage (no langchain needed).
    In a real app, you'd use ChromaDB/Pinecone here.
    """
    try:
        # Create session directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chroma_dir = os.path.join(BASE_DIR, "chroma_store", str(session_id))
        os.makedirs(chroma_dir, exist_ok=True)
        
        # Save text to file (simple alternative to vectorstore)
        text_file = os.path.join(chroma_dir, f"{source_name.replace('/', '_')}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"✅ Saved text to {text_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving to vectorstore: {e}")
        return False

def delete_vectorstore(session_id):
    """Delete vectorstore for a session"""
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chroma_dir = os.path.join(BASE_DIR, "chroma_store", str(session_id))
        
        if os.path.exists(chroma_dir):
            shutil.rmtree(chroma_dir)
            print(f"🗑️ Deleted vectorstore for session {session_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting vectorstore: {e}")
        return False

def search_vectorstore(session_id, query, top_k=5):
    """
    Simple keyword search (no embeddings).
    For production, use ChromaDB or Pinecone with embeddings.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chroma_dir = os.path.join(BASE_DIR, "chroma_store", str(session_id))
        
        if not os.path.exists(chroma_dir):
            return []
        
        # Simple keyword matching
        results = []
        query_lower = query.lower()
        
        for filename in os.listdir(chroma_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(chroma_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if query_lower in content.lower():
                        results.append({
                            'source': filename,
                            'content': content[:500]  # First 500 chars
                        })
        
        return results[:top_k]
    except Exception as e:
        print(f"❌ Error searching vectorstore: {e}")
        return []