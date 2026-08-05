"""RAG document upload endpoint.

Accepts PDF, TXT, MD, or HTML files and ingests them into the project's
ChromaDB collection so generator and judge agents can retrieve relevant context.
"""

import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status

from ideaforge.api.dependencies import RAG, ProjectRepo
from ideaforge.rag.document_processor import DocumentProcessor
from ideaforge.rag.schemas import IngestResult

router = APIRouter(prefix="/projects", tags=["documents"])

_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post(
    "/{project_id}/documents",
    response_model=IngestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for RAG context",
)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile,
    project_repo: ProjectRepo,
    rag: RAG,
) -> IngestResult:
    """Ingest a file into this project's vector store.

    Supported formats: `.pdf`, `.txt`, `.md`, `.html`, `.htm`

    Text-based extraction is attempted first. For scanned/image PDFs,
    OpenAI Vision is used as a fallback (billed per page).
    """
    # Verify project exists
    project = await project_repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Validate file type
    filename = file.filename or "upload"
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    if ext not in DocumentProcessor.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(DocumentProcessor.SUPPORTED_EXTENSIONS))}",
        )

    # Read at most MAX+1 bytes so we never load a multi-GB file into RAM.
    content = await file.read(_MAX_FILE_SIZE + 1)
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds 20 MB limit.",
        )

    try:
        result = await rag.ingest(
            project_id=str(project_id),
            file_bytes=content,
            filename=filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {exc}",
        )

    return result
