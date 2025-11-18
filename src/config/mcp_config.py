# src/config/mcp_config.py
"""
MCP Configuration and Server Setup (Environment-based)
"""
from src.config.settings import settings


def _http_entry(url: str | None):
    """Return Streamable HTTP transport entry when a URL is supplied."""
    if not url:
        return None
    return {"transport": "streamable_http", "url": url.rstrip("/")}


def get_mcp_servers():
    """Build MCP servers configuration for MultiServerMCPClient."""
    servers = {}

    airline_entry = _http_entry(settings.MCP_AIRLINE_URL)
    if airline_entry:
        servers["airline-booking"] = airline_entry

    hotel_entry = _http_entry(settings.MCP_HOTEL_URL)
    if hotel_entry:
        servers["hotel-booking"] = hotel_entry

    return servers


def load_mcp_servers_config():
    """Load MCP servers configuration from environment."""
    return get_mcp_servers()