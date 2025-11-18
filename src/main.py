# src/main.py
"""
Unified FastAPI Application
Combines traditional workflow routes and MCP-based AI booking routes
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Traditional routers
from src.api.auth_router import router as auth_router
from src.api.employee_router import router as employee_router
from src.api.manager_router import router as manager_router

# MCP-based HR router
from src.api.hr_mcp_router import router as hr_mcp_router

# Create FastAPI app
app = FastAPI(
    title="Travel Management System",
    description="Unified API for employee travel management with AI-powered booking",
    version="2.0.0"
)

# ---------------------------
# CORS Configuration
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Traditional Routers
# ---------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(employee_router, prefix="/employee", tags=["Employee"])
app.include_router(manager_router, tags=["Manager"])  # Has its own prefix

# ---------------------------
# MCP-Based AI Booking Router
# ---------------------------
app.include_router(hr_mcp_router, prefix="/hr-mcp", tags=["HR - AI Booking"])

# ---------------------------
# Root Endpoint
# ---------------------------
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Travel Management System API",
        "version": "2.0.0",
        "features": [
            "Traditional workflow (Employee → Manager → HR)",
            "MCP-based AI booking with chat interface"
        ],
        "endpoints": {
            "auth": "/auth",
            "employee": "/employee",
            "manager": "/manager",
            "hr_ai_booking": "/hr-mcp"
        }
    }

# ---------------------------
# Health Check
# ---------------------------
@app.get("/health", tags=["Root"])
async def health_check():
    """Combined health check for entire system"""
    from src.api.hr_mcp_router import get_mcp_health
    
    mcp_health = await get_mcp_health()
    
    return {
        "status": "healthy",
        "traditional_routes": "active",
        "mcp_routes": "active" if mcp_health["mcp_available"] else "unavailable",
        "mcp_details": mcp_health
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)