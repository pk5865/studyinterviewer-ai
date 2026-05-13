import threading
import time

class ProgressTracker:
    """Thread-safe progress tracking for async operations"""
    
    def __init__(self):
        self.progress = {}
        self.lock = threading.Lock()
    
    def start_session(self, session_id):
        """Initialize progress tracking for a new session"""
        with self.lock:
            self.progress[session_id] = {
                "status": "starting",
                "message": "Initializing upload...",
                "current_chunk": 0,
                "total_chunks": 0,
                "questions_generated": 0,
                "timestamp": time.time(),
                "started_at": time.time()
            }
    
    def update(self, session_id, status, message, current_chunk=None, 
               total_chunks=None, questions_generated=None):
        """Update progress for a session"""
        with self.lock:
            if session_id in self.progress:
                self.progress[session_id]["status"] = status
                self.progress[session_id]["message"] = message
                self.progress[session_id]["timestamp"] = time.time()
                if current_chunk is not None:
                    self.progress[session_id]["current_chunk"] = current_chunk
                if total_chunks is not None:
                    self.progress[session_id]["total_chunks"] = total_chunks
                if questions_generated is not None:
                    self.progress[session_id]["questions_generated"] = questions_generated
    
    def get_progress(self, session_id):
        """Get current progress for a session"""
        with self.lock:
            return self.progress.get(session_id, {
                "status": "idle",
                "message": "",
                "current_chunk": 0,
                "total_chunks": 0,
                "questions_generated": 0,
                "percentage": 0
            })
    
    def clear_session(self, session_id):
        """Remove progress tracking for a session"""
        with self.lock:
            if session_id in self.progress:
                del self.progress[session_id]
    
    def is_complete(self, session_id):
        """Check if a session's processing is complete"""
        progress = self.get_progress(session_id)
        if not progress:
            return True
        return progress["status"] in ["complete", "error", "idle"]

# Global singleton instance
tracker = ProgressTracker()