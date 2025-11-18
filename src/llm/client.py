"""
LLM Client Configuration
"""
from src.config.settings import settings
from src.config.llm_config import get_llm

# Use the configuration-based LLM
llm = get_llm()