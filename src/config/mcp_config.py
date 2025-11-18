# src/config/mcp_config.py
"""
MCP Configuration and Server Setup (Environment-based)
"""
from src.config.settings import settings

def get_mcp_servers():
    """
    Build MCP servers configuration from environment variables
    Returns a dictionary compatible with MultiServerMCPClient
    """
    mcp_servers = {
        "airline-booking": {
            "transport": "stdio",
            "command": settings.MCP_AIRLINE_COMMAND,
            "args": settings.MCP_AIRLINE_ARGS
        },
        "hotel-booking": {
            "transport": "stdio",
            "command": settings.MCP_HOTEL_COMMAND,
            "args": settings.MCP_HOTEL_ARGS
        }
    }
    return mcp_servers

def load_mcp_servers_config():
    """Load MCP servers configuration from environment"""
    return get_mcp_servers()