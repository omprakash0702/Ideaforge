"""add pgvector extension and document_chunks table

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id          BIGSERIAL PRIMARY KEY,
            project_id  UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            filename    TEXT        NOT NULL,
            source_type TEXT        NOT NULL,
            doc_hash    TEXT        NOT NULL,
            chunk_index INTEGER     NOT NULL,
            content     TEXT        NOT NULL,
            embedding   vector(1536) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # cosine similarity index (IVFFlat — fast approximate NN)
    op.execute("""
        CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
        ON document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # fast per-project filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS document_chunks_project_id_idx
        ON document_chunks (project_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_chunks")
    # intentionally leave the vector extension in place —
    # removing it would break other tables using it
