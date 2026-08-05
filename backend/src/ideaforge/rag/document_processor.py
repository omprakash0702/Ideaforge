"""Document text extraction pipeline.

Tier 1 — library-based text extraction (pypdf / bs4 / raw decode).
Tier 2 — OpenAI Vision: used ONLY when Tier 1 yields fewer than
          _MIN_TEXT_CHARS characters (e.g. scanned / image-heavy PDFs).
"""

import asyncio
import base64
import io
import re
from pathlib import Path

import fitz  # PyMuPDF
import structlog
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pypdf import PdfReader

from ideaforge.rag.schemas import ProcessedDocument, SourceType

logger = structlog.get_logger(__name__)

_MIN_TEXT_CHARS = 100   # below this, PDF text extraction is considered failed
_MAX_VISION_PAGES = 15  # cap to control Vision API cost

_VISION_PROMPT = (
    "Extract all text content from this document page. "
    "Return only the raw extracted text, preserving paragraph structure. "
    "Do not add commentary, headers, or extra formatting."
)


class DocumentProcessor:
    SUPPORTED_EXTENSIONS = frozenset({".pdf", ".txt", ".md", ".html", ".htm"})

    def __init__(self, api_key: str, vision_model: str = "gpt-4o") -> None:
        self._api_key = api_key
        self._vision_model = vision_model

    async def process(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            accepted = ", ".join(sorted(self.SUPPORTED_EXTENSIONS))
            raise ValueError(f"Unsupported file type {ext!r}. Accepted: {accepted}")

        if ext == ".pdf":
            return await self._process_pdf(file_bytes, filename)
        if ext in {".html", ".htm"}:
            return self._process_html(file_bytes, filename)
        if ext == ".md":
            return self._process_markdown(file_bytes, filename)
        return self._process_text(file_bytes, filename)

    # ── PDF ───────────────────────────────────────────────────────────────────

    async def _process_pdf(self, data: bytes, filename: str) -> ProcessedDocument:
        text, page_count = await asyncio.to_thread(self._extract_pdf_text, data)

        if len(text.strip()) >= _MIN_TEXT_CHARS:
            logger.info("rag.pdf_text_ok", filename=filename, chars=len(text))
            return ProcessedDocument(
                text=text.strip(),
                source_type=SourceType.PDF_TEXT,
                filename=filename,
                char_count=len(text),
                page_count=page_count,
            )

        logger.warning(
            "rag.pdf_text_sparse",
            filename=filename,
            chars=len(text),
            fallback="vision",
        )
        vision_text = await self._extract_pdf_vision(data, filename)
        return ProcessedDocument(
            text=vision_text.strip(),
            source_type=SourceType.PDF_VISION,
            filename=filename,
            char_count=len(vision_text),
            page_count=page_count,
        )

    @staticmethod
    def _extract_pdf_text(data: bytes) -> tuple[str, int]:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages), len(pages)

    async def _extract_pdf_vision(self, data: bytes, filename: str) -> str:
        images_b64 = await asyncio.to_thread(self._render_pdf_pages, data)
        llm = ChatOpenAI(api_key=self._api_key, model=self._vision_model)
        page_texts: list[str] = []

        for i, img_b64 in enumerate(images_b64[:_MAX_VISION_PAGES]):
            logger.debug("rag.vision_page", filename=filename, page=i + 1)
            msg = HumanMessage(content=[
                {"type": "text", "text": _VISION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                },
            ])
            response = await llm.ainvoke([msg])
            page_texts.append(str(response.content))

        return "\n\n".join(page_texts)

    @staticmethod
    def _render_pdf_pages(data: bytes) -> list[str]:
        doc = fitz.open(stream=data, filetype="pdf")
        result: list[str] = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            result.append(base64.b64encode(pix.tobytes("png")).decode())
        doc.close()
        return result

    # ── HTML ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _process_html(data: bytes, filename: str) -> ProcessedDocument:
        soup = BeautifulSoup(data, "lxml")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        logger.info("rag.html_ok", filename=filename, chars=len(text))
        return ProcessedDocument(
            text=text,
            source_type=SourceType.HTML,
            filename=filename,
            char_count=len(text),
        )

    # ── Markdown ──────────────────────────────────────────────────────────────

    @staticmethod
    def _process_markdown(data: bytes, filename: str) -> ProcessedDocument:
        text = data.decode("utf-8", errors="replace")
        text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        text = text.strip()

        logger.info("rag.markdown_ok", filename=filename, chars=len(text))
        return ProcessedDocument(
            text=text,
            source_type=SourceType.MARKDOWN,
            filename=filename,
            char_count=len(text),
        )

    # ── Plain text ────────────────────────────────────────────────────────────

    @staticmethod
    def _process_text(data: bytes, filename: str) -> ProcessedDocument:
        text = data.decode("utf-8", errors="replace").strip()
        logger.info("rag.text_ok", filename=filename, chars=len(text))
        return ProcessedDocument(
            text=text,
            source_type=SourceType.TEXT,
            filename=filename,
            char_count=len(text),
        )
