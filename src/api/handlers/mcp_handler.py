# src/api/handlers/mcp_handler.py
"""
MCP Client initialization and lifecycle management
"""
from typing import Optional, Dict, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.config.settings import settings
from src.config.mcp_config import get_mcp_servers
from src.config.llm_config import get_llm

class MCPHandler:
    """Handles MCP client initialization and management"""
    
    def __init__(self):
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List = []
        self.tool_by_name: Dict = {}
        self.llm_with_tools = None
    
    async def initialize(self):
        """Initialize MCP client and LLM on startup"""
        try:
            llm = get_llm()
            servers = get_mcp_servers()
            
            if servers:
                self.client = MultiServerMCPClient(servers)
                self.tools = await self.client.get_tools()
                self.tool_by_name = {t.name: t for t in self.tools}
                
                # Bind tools to LLM
                self.llm_with_tools = llm.bind_tools(self.tools)
                
                print(f"✓ MCP initialized with {len(self.tools)} tools")
            else:
                print("⚠ No MCP servers configured")
                self.llm_with_tools = llm
        except Exception as e:
            print(f"✗ MCP initialization failed: {e}")
            self.llm_with_tools = get_llm()
    
    async def cleanup(self):
        """Cleanup on shutdown"""
        if self.client:
            await self.client.cleanup()
    
    def get_llm_with_tools(self):
        """Get LLM with tools bound"""
        return self.llm_with_tools
    
    def get_tools(self) -> List:
        """Get list of available tools"""
        return self.tools
    
    def get_tool(self, name: str):
        """Get tool by name"""
        return self.tool_by_name.get(name)
    
    def get_tool_count(self) -> int:
        """Get number of available tools"""
        return len(self.tools)
    
    def is_available(self) -> bool:
        """Check if MCP is available"""
        return self.client is not None

# Singleton instance
_mcp_handler: Optional[MCPHandler] = None

def get_mcp_handler() -> MCPHandler:
    """Get MCP handler singleton"""
    global _mcp_handler
    if _mcp_handler is None:
        _mcp_handler = MCPHandler()
    return _mcp_handler