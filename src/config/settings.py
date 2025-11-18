# src/config/settings.py
"""
Centralized configuration management using .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from .env"""
    
    # ═══════════════════════════════════════════════════════
    # AZURE OPENAI
    # ═══════════════════════════════════════════════════════
    AZURE_API_KEY = os.getenv("AZURE_API_KEY")
    AZURE_API_BASE = os.getenv("AZURE_API_BASE")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
    AZURE_MODEL = os.getenv("AZURE_MODEL", "azure/gpt-4o")
    AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    AZURE_EMBEDDING_MODEL = os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-3-small")
    
    # ═══════════════════════════════════════════════════════
    # LLM PARAMETERS
    # ═══════════════════════════════════════════════════════
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.8))
    LLM_VERBOSE = os.getenv("LLM_VERBOSE", "false").lower() == "true"
    EMBEDDING_CHUNK_SIZE = int(os.getenv("EMBEDDING_CHUNK_SIZE", 2048))
    
    # ═══════════════════════════════════════════════════════
    # DATABASE
    # ═══════════════════════════════════════════════════════
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "neondb")
    DB_USER = os.getenv("DB_USER", "user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_SSLMODE = os.getenv("DB_SSLMODE", "require")
    DB_MINCONN = int(os.getenv("DB_MINCONN", 1))
    DB_MAXCONN = int(os.getenv("DB_MAXCONN", 10))
    
    # ═══════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════
    SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", 1))
    
    # ═══════════════════════════════════════════════════════
    # AUTHENTICATION
    # ═══════════════════════════════════════════════════════
    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    
    # ═══════════════════════════════════════════════════════
    # MILVUS
    # ═══════════════════════════════════════════════════════
    MILVUS_URI = os.getenv("MILVUS_URI")
    MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")
    MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "travel_policy_embeddings")
    MILVUS_DIM = int(os.getenv("MILVUS_DIM", 1536))
    MILVUS_VECTOR_FIELD = os.getenv("MILVUS_VECTOR_FIELD", "vector")
    MILVUS_TEXT_FIELD = os.getenv("MILVUS_TEXT_FIELD", "text")

    # ═══════════════════════════════════════════════════════
    # RAG CONFIGURATION
    # ═══════════════════════════════════════════════════════
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", 3))
    RAG_CONTEXT_MAX_CHARS = int(os.getenv("RAG_CONTEXT_MAX_CHARS", 1800))
    
    # ═══════════════════════════════════════════════════════
    # MCP CONFIGURATION
    # ═══════════════════════════════════════════════════════
    MCP_AIRLINE_URL = os.getenv("MCP_AIRLINE_URL", "http://127.0.0.1:8001")
    MCP_HOTEL_URL = os.getenv("MCP_HOTEL_URL", "http://127.0.0.1:8002")
    MCP_AIRLINE_COMMAND = os.getenv("MCP_AIRLINE_COMMAND", "npx")
    MCP_AIRLINE_ARGS = os.getenv("MCP_AIRLINE_ARGS", "-y,mcp-remote,http://127.0.0.1:8001/mcp").split(",")
    MCP_HOTEL_COMMAND = os.getenv("MCP_HOTEL_COMMAND", "npx")
    MCP_HOTEL_ARGS = os.getenv("MCP_HOTEL_ARGS", "-y,mcp-remote,http://127.0.0.1:8002/mcp").split(",")

# Global settings instance
settings = Settings()