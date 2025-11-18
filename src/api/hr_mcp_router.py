# src/api/hr_mcp_router.py
"""
MCP-Based HR Booking Router
AI-powered travel booking with chat interface using MCP tools
"""
import json
from fastapi import APIRouter, HTTPException, Depends
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.auth.jwt_service import get_current_user
from src.api.models import ChatRequest, ChatResponse, StatusUpdateRequest
from src.api.services import (
    get_session_service,
    build_context_message,
    get_travel_indent_service
)
from src.api.handlers import get_mcp_handler

# Router
router = APIRouter()

# ─────────────────────────────
# Startup/Shutdown Events
# ─────────────────────────────
@router.on_event("startup")
async def startup_mcp():
    """Initialize MCP client and LLM on startup"""
    mcp_handler = get_mcp_handler()
    await mcp_handler.initialize()

@router.on_event("shutdown")
async def shutdown_mcp():
    """Cleanup on shutdown"""
    mcp_handler = get_mcp_handler()
    await mcp_handler.cleanup()

# ─────────────────────────────
# API Endpoints
# ─────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with MCP tool support"""
    session_service = get_session_service()
    travel_indent_service = get_travel_indent_service()
    mcp_handler = get_mcp_handler()
    
    # Cleanup old sessions
    session_service.cleanup_old_sessions()
    
    # Get or create session
    session_id, session = session_service.get_or_create(request.session_id)
    
    # Load travel indent if provided
    if request.indent_id and not session.travel_indent:
        session.travel_indent = travel_indent_service.get_by_id(request.indent_id)
    
    # Build context message
    enhanced_message = build_context_message(request.message, session.travel_indent)
    
    # Add user message to history
    session.history.append(HumanMessage(content=enhanced_message))
    
    tools_used = []
    booking_complete = False
    
    try:
        llm_with_tools = mcp_handler.get_llm_with_tools()
        
        # First pass: let model decide whether to call tools
        first_response = await llm_with_tools.ainvoke(session.history)
        tool_calls = getattr(first_response, "tool_calls", None)
        
        if not tool_calls:
            # No tools needed
            session.history.append(first_response)
            return ChatResponse(
                response=first_response.content or "",
                session_id=session_id,
                tools_used=tools_used,
                booking_complete=booking_complete
            )
        
        # Execute tools
        session.history.append(first_response)
        
        tool_msgs = []
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("args") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except:
                    pass
            
            tool = mcp_handler.get_tool(name)
            if not tool:
                tool_msgs.append(ToolMessage(
                    tool_call_id=tc["id"],
                    content=json.dumps({"error": f"Tool {name} not found"})
                ))
                continue
            
            result = await tool.ainvoke(args)
            tool_msgs.append(ToolMessage(tool_call_id=tc["id"], content=json.dumps(result)))
            tools_used.append(name)
        
        session.history.extend(tool_msgs)
        
        # Final response
        from src.config.llm_config import create_llm
        final_llm = create_llm()
        final_response = await final_llm.ainvoke(session.history)
        session.history.append(final_response)
        
        # Check if booking complete
        if "book_flight" in tools_used and "book_hotel" in tools_used:
            booking_complete = True
            if session.travel_indent:
                try:
                    travel_indent_service.update_status(
                        session.travel_indent['indent_id'],
                        "completed_hr"
                    )
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
        
        return ChatResponse(
            response=final_response.content or "",
            session_id=session_id,
            tools_used=tools_used,
            booking_complete=booking_complete
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/travel-indents")
async def get_travel_indents():
    """Get all travel indents for HR dashboard"""
    travel_indent_service = get_travel_indent_service()
    return travel_indent_service.get_all()

@router.patch("/tickets/{indent_id}/status")
async def update_ticket_status(
    indent_id: str,
    request: StatusUpdateRequest,
):
    """Update ticket status"""
    travel_indent_service = get_travel_indent_service()
    try:
        success = travel_indent_service.update_status(indent_id, request.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    if success:
        return {"message": f"Ticket status updated to {request.status}"}
    raise HTTPException(status_code=404, detail="Ticket not found")

@router.get("/health")
async def health_check():
    """Health check for MCP system"""
    mcp_handler = get_mcp_handler()
    session_service = get_session_service()
    
    return {
        "status": "healthy",
        "mcp_available": mcp_handler.is_available(),
        "tools_available": mcp_handler.get_tool_count(),
        "active_sessions": session_service.get_active_session_count()
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user=Depends(get_current_user)):
    """Delete a session"""
    session_service = get_session_service()
    
    if session_service.delete_session(session_id):
        return {"message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, current_user=Depends(get_current_user)):
    """Get chat history for session"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = []
    for msg in session.history:
        if isinstance(msg, HumanMessage):
            history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            history.append({"role": "assistant", "content": msg.content})
    
    return {"session_id": session_id, "history": history}

# Helper function for main health check
async def get_mcp_health():
    """Get MCP health status"""
    mcp_handler = get_mcp_handler()
    session_service = get_session_service()
    
    return {
        "mcp_available": mcp_handler.is_available(),
        "tools_count": mcp_handler.get_tool_count(),
        "active_sessions": session_service.get_active_session_count()
    }