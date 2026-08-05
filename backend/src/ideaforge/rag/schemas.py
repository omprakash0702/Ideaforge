import enum

from pydantic import BaseModel


class SourceType(str, enum.Enum):
    PDF_TEXT = "pdf_text"      # pypdf text extraction succeeded
    PDF_VISION = "pdf_vision"  # text extraction failed, OpenAI Vision used
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"


class ProcessedDocument(BaseModel):
    text: str
    source_type: SourceType
    filename: str
    char_count: int
    page_count: int | None = None


class IngestResult(BaseModel):
    project_id: str
    filename: str
    source_type: str
    chunk_count: int
    char_count: int


class RAGContext(BaseModel):
    chunks: list[str]
    context_text: str  # chunks joined with separators, ready for prompt injection
