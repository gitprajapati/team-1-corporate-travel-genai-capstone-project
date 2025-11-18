# src/api/services/session_service.py
"""
Session management service
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from src.api.models.session_models import Session
from src.config.settings import settings

class SessionService:
    """Manages chat sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    def get_or_create(self, session_id: Optional[str] = None) -> Tuple[str, Session]:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.update_activity()
            return session_id, session
        
        new_id = str(uuid.uuid4())
        self.sessions[new_id] = Session()
        return new_id, self.sessions[new_id]
    
    def cleanup_old_sessions(self):
        """Remove sessions older than configured timeout"""
        cutoff = datetime.now() - timedelta(hours=settings.SESSION_TIMEOUT_HOURS)
        to_remove = [
            sid for sid, sess in self.sessions.items()
            if sess.last_activity < cutoff
        ]
        for sid in to_remove:
            del self.sessions[sid]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)

# Singleton instance
_session_service: Optional[SessionService] = None

def get_session_service() -> SessionService:
    """Get session service singleton"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service