"""Policy retrieval-augmented generation helpers."""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage

from src.api.models.session_models import Session
from src.config.llm_config import get_llm
from src.config.prompts import SYSTEM_PROMPT_POLICY_RAG
from src.config.settings import settings
from src.rag import milvus_store
from src.rag.embedder import get_embedder


class PolicyRAGChatService:
	"""Chat service that augments answers with travel policy context."""

	def __init__(self) -> None:
		self.sessions: Dict[str, Session] = {}
		self.embedder = get_embedder()
		self.llm = get_llm()
		self.top_k = max(1, settings.RAG_TOP_K)
		self.max_context_chars = max(200, settings.RAG_CONTEXT_MAX_CHARS)

	# ─────────────────────────────
	# Session helpers
	# ─────────────────────────────
	def _cleanup_old_sessions(self) -> None:
		cutoff = datetime.now() - timedelta(hours=settings.SESSION_TIMEOUT_HOURS)
		stale_ids = [sid for sid, sess in self.sessions.items() if sess.last_activity < cutoff]
		for sid in stale_ids:
			del self.sessions[sid]

	def _get_or_create_session(self, session_id: Optional[str]) -> Tuple[str, Session]:
		if session_id and session_id in self.sessions:
			session = self.sessions[session_id]
			session.update_activity()
			return session_id, session

		new_id = str(uuid.uuid4())
		self.sessions[new_id] = Session(system_prompt=SYSTEM_PROMPT_POLICY_RAG)
		return new_id, self.sessions[new_id]

	# ─────────────────────────────
	# Retrieval helpers
	# ─────────────────────────────
	def _search(self, query: str) -> List[Dict]:
		embedding = self.embedder.embed_query(query)
		return milvus_store.search(embedding, top_k=self.top_k)

	def _format_sources(self, hits: List[Dict]) -> List[Dict[str, str]]:
		sources: List[Dict[str, str]] = []
		for idx, hit in enumerate(hits, 1):
			snippet = (hit.get("text") or "").strip()
			if len(snippet) > self.max_context_chars:
				snippet = f"{snippet[: self.max_context_chars]}…"
			sources.append({
				"id": str(hit.get("id", idx)),
				"text": snippet,
			})
		return sources

	def _build_context_block(self, sources: List[Dict[str, str]]) -> str:
		if not sources:
			return "No matching travel policy excerpts were retrieved."
		chunks = []
		for idx, source in enumerate(sources, 1):
			chunks.append(f"Source {idx} -> {source['text']}")
		context = "\n\n".join(chunks)
		if len(context) > self.max_context_chars:
			return f"{context[: self.max_context_chars]}…"
		return context

	def _compose_user_message(self, question: str, context_block: str) -> str:
		guidelines = (
			"You answer employee travel policy questions using ONLY the provided context. "
			"Quote rupee amounts, limits, and grade-based allowances where available. "
			"If the context lacks the answer, politely say you don't have that information and suggest checking with HR."
		)
		return (
			f"{guidelines}\n\n"
			f"Policy Context:\n{context_block}\n\n"
			f"Employee Question:\n{question.strip()}"
		)

	# ─────────────────────────────
	# Public API
	# ─────────────────────────────
	async def chat(self, message: str, session_id: Optional[str] = None) -> Dict:
		if not message or not message.strip():
			raise ValueError("Message cannot be empty")

		self._cleanup_old_sessions()
		session_id, session = self._get_or_create_session(session_id)

		hits = self._search(message)
		sources = self._format_sources(hits)
		context_block = self._build_context_block(sources)
		enhanced_message = self._compose_user_message(message, context_block)

		session.history.append(HumanMessage(content=enhanced_message))
		response = await self.llm.ainvoke(session.history)
		session.history.append(response)
		session.update_activity()

		return {
			"response": response.content or "",
			"session_id": session_id,
			"sources": sources,
		}


_policy_rag_service: Optional[PolicyRAGChatService] = None


def get_policy_rag_service() -> PolicyRAGChatService:
	"""Return singleton policy chat service."""
	global _policy_rag_service
	if _policy_rag_service is None:
		_policy_rag_service = PolicyRAGChatService()
	return _policy_rag_service
