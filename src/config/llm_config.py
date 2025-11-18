# src/config/llm_config.py
"""
LLM Configuration and Initialization
"""
from langchain_litellm import ChatLiteLLM
from src.config.settings import settings

def create_llm():
    """Create and return configured LLM instance"""
    return ChatLiteLLM(
        model=settings.AZURE_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        verbose=settings.LLM_VERBOSE
    )

def get_llm():
    """Get singleton LLM instance"""
    if not hasattr(get_llm, '_instance'):
        get_llm._instance = create_llm()
    return get_llm._instance