# StudyInterviewer AI 🎓

AI-powered interview preparation platform that generates practice questions from your study materials.

## ✨ Features
- 📄 Upload PDFs, YouTube videos, or web pages
- 🤖 AI-generated interview questions (3 difficulty levels)
- 💬 Instant AI feedback on answers
- 📊 Progress tracking & session management
- 🔒 100% offline support (with Ollama + tinyllama)

## 🛠️ Tech Stack
- **Backend**: Flask, SQLAlchemy, Ollama/Groq/Gemini
- **Frontend**: React 18, Vite, React Router
- **Database**: SQLite
- **Vector Store**: ChromaDB (optional)

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
