# src/api/models/chat_models.py
"""
Chat and booking request/response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    """Chat message request"""
    message: str
    session_id: Optional[str] = None
    indent_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat message response"""
    response: str
    session_id: str
    tools_used: List[str] = []
    booking_complete: bool = False

class StatusUpdateRequest(BaseModel):
    """Status update request"""
    status: str


class PolicySource(BaseModel):
    """Chunk of policy context returned to the UI."""
    id: str
    text: str


class PolicyChatRequest(BaseModel):
    """Employee policy assistant request."""
    message: str
    session_id: Optional[str] = None


class PolicyChatResponse(BaseModel):
    """Employee policy assistant response."""
    response: str
    session_id: str
    sources: List[PolicySource] = Field(default_factory=list)