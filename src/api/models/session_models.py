# src/api/models/session_models.py
"""
Session and state management models
"""
from datetime import datetime
from typing import List, Optional
from langchain_core.messages import SystemMessage
from src.config.prompts import SYSTEM_PROMPT_HR_BOOKING

class Session:
    """Chat session with message history"""
    
    def __init__(self, system_prompt: str = SYSTEM_PROMPT_HR_BOOKING):
        self.history: List = [SystemMessage(content=system_prompt)]
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.travel_indent = None
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()