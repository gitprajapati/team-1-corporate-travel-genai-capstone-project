"""Embedding utilities for policy RAG."""
from langchain_openai import AzureOpenAIEmbeddings

from src.config.settings import settings


def _validate_settings() -> None:
	missing = []
	if not settings.AZURE_API_KEY:
		missing.append("AZURE_API_KEY")
	if not settings.AZURE_API_BASE:
		missing.append("AZURE_API_BASE")
	if not settings.AZURE_API_VERSION:
		missing.append("AZURE_API_VERSION")
	if missing:
		joined = ", ".join(missing)
		raise RuntimeError(f"Missing Azure OpenAI configuration: {joined}")


def create_embedder() -> AzureOpenAIEmbeddings:
	"""Instantiate a configured Azure embedding client."""
	_validate_settings()
	return AzureOpenAIEmbeddings(
		azure_endpoint=settings.AZURE_API_BASE,
		openai_api_key=settings.AZURE_API_KEY,
		openai_api_version=settings.AZURE_API_VERSION,
		azure_deployment=settings.AZURE_EMBEDDING_DEPLOYMENT,
		model=settings.AZURE_EMBEDDING_MODEL,
		chunk_size=settings.EMBEDDING_CHUNK_SIZE,
	)


def get_embedder() -> AzureOpenAIEmbeddings:
	"""Return a singleton embedding client."""
	if not hasattr(get_embedder, "_instance"):
		get_embedder._instance = create_embedder()
	return get_embedder._instance
