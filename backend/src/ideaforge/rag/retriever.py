import structlog

from ideaforge.rag.embedder import RAGEmbedder
from ideaforge.rag.schemas import RAGContext

logger = structlog.get_logger(__name__)


class RAGRetriever:
    def __init__(self, embedder: RAGEmbedder, top_k: int = 5) -> None:
        self._embedder = embedder
        self._top_k = top_k

    async def get_context(self, project_id: str, query: str) -> RAGContext:
        """Retrieve relevant chunks and return a RAGContext ready for prompt injection."""
        try:
            chunks = await self._embedder.similarity_search(project_id, query, self._top_k)
        except Exception as exc:
            logger.warning("rag.retrieval_error", project_id=project_id, error=str(exc))
            chunks = []

        context_text = "\n\n---\n\n".join(chunks) if chunks else ""
        return RAGContext(chunks=chunks, context_text=context_text)
