import os, shutil
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ✅ Disable telemetry to save RAM
os.environ["ANONYMIZED_TELEMETRY"] = "False"

def get_chroma_dir():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "chroma_store")

def add_text_to_vectorstore(sid, text, source):
    """Split text into small chunks for low-RAM systems"""
    # ✅ Ultra-small chunks for 8GB RAM
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,  # Small = less memory
        chunk_overlap=50
    )
    chunks = splitter.split_text(text)
    
    # ✅ SKIP ChromaDB entirely for testing (saves ~500MB RAM)
    # Questions will still generate from raw text
    return len(chunks)

def delete_vectorstore(sid):
    """Clean up ChromaDB folder for a session"""
    d = os.path.join(get_chroma_dir(), str(sid))
    if os.path.exists(d):
        shutil.rmtree(d)