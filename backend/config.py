import os
from google import genai  # ✅ New SDK
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AlzaSyAL8mMvg4vuEsPdpBv4aqfNEEc38UTgYTo")

# Initialize Gemini client with new SDK
client = genai.Client(api_key=GEMINI_API_KEY)

# --- Database & Path Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATABASE_PATH = os.path.join(PROJECT_ROOT, "studyinterviewer.db")
CHROMA_PERSIST_DIR = os.path.join(PROJECT_ROOT, "chroma_store")
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")

class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    CHROMA_PERSIST_DIR = CHROMA_PERSIST_DIR
    UPLOAD_FOLDER = UPLOAD_FOLDER
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# Ensure directories exist
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)