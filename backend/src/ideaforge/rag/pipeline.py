import structlog

from ideaforge.rag.document_processor import DocumentProcessor
from ideaforge.rag.embedder import RAGEmbedder
from ideaforge.rag.retriever import RAGRetriever
from ideaforge.rag.schemas import IngestResult, RAGContext

logger = structlog.get_logger(__name__)


class RAGPipeline:
    """Orchestrates document ingestion and context retrieval for agent prompts."""

    def __init__(
        self,
        processor: DocumentProcessor,
        embedder: RAGEmbedder,
        retriever: RAGRetriever,
    ) -> None:
        self._processor = processor
        self._embedder = embedder
        self._retriever = retriever

    async def ingest(
        self, project_id: str, file_bytes: bytes, filename: str
    ) -> IngestResult:
        """Process and embed a document into the project's vector store."""
        logger.info("rag.ingest_start", project_id=project_id, filename=filename)

        document = await self._processor.process(file_bytes, filename)
        chunk_count = await self._embedder.embed_document(project_id, document)

        logger.info(
            "rag.ingest_done",
            project_id=project_id,
            filename=filename,
            source_type=document.source_type.value,
            chunks=chunk_count,
        )
        return IngestResult(
            project_id=project_id,
            filename=filename,
            source_type=document.source_type.value,
            chunk_count=chunk_count,
            char_count=document.char_count,
        )

    async def get_context(self, project_id: str, query: str) -> RAGContext:
        """Retrieve relevant context chunks for a query string."""
        return await self._retriever.get_context(project_id, query)
