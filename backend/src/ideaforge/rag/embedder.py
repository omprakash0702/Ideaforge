"""pgvector embedding layer.

Chunks are stored in the `document_chunks` PostgreSQL table using the pgvector
extension. One row per chunk; namespaced by project_id so retrieval never
crosses project boundaries. Persistent across restarts — no local disk needed.
"""

import asyncio
import hashlib
import json

import structlog
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text

from ideaforge.infrastructure.database.postgres import AsyncSessionLocal
from ideaforge.rag.schemas import ProcessedDocument

logger = structlog.get_logger(__name__)

EMBEDDING_DIM = 1536  # text-embedding-3-small


class RAGEmbedder:
    def __init__(
        self,
        api_key: str,
        embedding_model: str,
        chunk_size: int = 800,
        chunk_overlap: int = 80,
    ) -> None:
        self._embeddings = OpenAIEmbeddings(api_key=api_key, model=embedding_model)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    async def embed_document(self, project_id: str, document: ProcessedDocument) -> int:
        chunks = self._splitter.split_text(document.text)
        if not chunks:
            logger.warning("rag.embed_empty", filename=document.filename)
            return 0

        doc_hash = hashlib.md5(document.text.encode()).hexdigest()[:8]

        # Embed all chunks in one batched API call
        embeddings: list[list[float]] = await asyncio.to_thread(
            self._embeddings.embed_documents, chunks
        )

        async with AsyncSessionLocal() as session:
            # Remove previous chunks for this exact file (idempotent re-upload)
            await session.execute(
                text(
                    "DELETE FROM document_chunks "
                    "WHERE project_id = :pid AND doc_hash = :doc_hash"
                ),
                {"pid": project_id, "doc_hash": doc_hash},
            )

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                await session.execute(
                    text("""
                        INSERT INTO document_chunks
                            (project_id, filename, source_type, doc_hash,
                             chunk_index, content, embedding)
                        VALUES
                            (:pid, :filename, :source_type, :doc_hash,
                             :chunk_index, :content, :embedding::vector)
                    """),
                    {
                        "pid": project_id,
                        "filename": document.filename,
                        "source_type": document.source_type.value,
                        "doc_hash": doc_hash,
                        "chunk_index": i,
                        "content": chunk,
                        "embedding": json.dumps(embedding),
                    },
                )

            await session.commit()

        logger.info(
            "rag.embedded",
            project_id=project_id,
            filename=document.filename,
            chunks=len(chunks),
        )
        return len(chunks)

    async def similarity_search(
        self, project_id: str, query: str, top_k: int = 5
    ) -> list[str]:
        query_embedding: list[float] = await asyncio.to_thread(
            self._embeddings.embed_query, query
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT content
                    FROM document_chunks
                    WHERE project_id = :pid
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :top_k
                """),
                {
                    "pid": project_id,
                    "embedding": json.dumps(query_embedding),
                    "top_k": top_k,
                },
            )
            return [row[0] for row in result.fetchall()]
