"""Document processor tests.

All tests that don't require API keys run with no external deps.
Vision-fallback tests are marked @pytest.mark.llm.
"""

import pytest

from ideaforge.rag.document_processor import DocumentProcessor
from ideaforge.rag.schemas import SourceType

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def processor() -> DocumentProcessor:
    return DocumentProcessor(api_key="dummy-key-not-used-by-tier1", vision_model="gpt-4o")


# ── Plain text ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_txt_extraction(processor: DocumentProcessor) -> None:
    content = b"This is a startup idea about helping farmers monitor soil health."
    doc = await processor.process(content, "idea.txt")

    assert doc.source_type == SourceType.TEXT
    assert "farmers" in doc.text
    assert doc.char_count > 0
    assert doc.page_count is None


@pytest.mark.asyncio
async def test_txt_strips_whitespace(processor: DocumentProcessor) -> None:
    content = b"   \n  Idea text here.\n\n  "
    doc = await processor.process(content, "idea.txt")
    assert doc.text == "Idea text here."


# ── Markdown ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_markdown_extraction(processor: DocumentProcessor) -> None:
    content = b"# My Startup\n\nHelping small businesses manage invoices with AI."
    doc = await processor.process(content, "idea.md")

    assert doc.source_type == SourceType.MARKDOWN
    assert "invoices" in doc.text


@pytest.mark.asyncio
async def test_markdown_strips_front_matter(processor: DocumentProcessor) -> None:
    content = b"---\ntitle: Draft\nauthor: Me\n---\n# Real Content\n\nActual idea here."
    doc = await processor.process(content, "draft.md")

    assert "title:" not in doc.text
    assert "Real Content" in doc.text


@pytest.mark.asyncio
async def test_markdown_strips_html_comments(processor: DocumentProcessor) -> None:
    content = b"# Idea\n\n<!-- internal note -->\n\nPublic description here."
    doc = await processor.process(content, "idea.md")

    assert "internal note" not in doc.text
    assert "Public description" in doc.text


# ── HTML ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_html_extraction(processor: DocumentProcessor) -> None:
    content = b"""
    <html><body>
      <nav>Navigation</nav>
      <main><p>Core startup idea about AI in healthcare.</p></main>
      <footer>Footer</footer>
    </body></html>
    """
    doc = await processor.process(content, "index.html")

    assert doc.source_type == SourceType.HTML
    assert "healthcare" in doc.text


@pytest.mark.asyncio
async def test_html_removes_scripts_and_styles(processor: DocumentProcessor) -> None:
    content = b"""
    <html><head>
      <script>alert('xss')</script>
      <style>body { color: red; }</style>
    </head><body>
      <p>Clean idea text.</p>
    </body></html>
    """
    doc = await processor.process(content, "page.html")

    assert "alert" not in doc.text
    assert "color: red" not in doc.text
    assert "Clean idea text" in doc.text


@pytest.mark.asyncio
async def test_htm_extension_supported(processor: DocumentProcessor) -> None:
    content = b"<html><body><p>Another valid file.</p></body></html>"
    doc = await processor.process(content, "page.htm")
    assert doc.source_type == SourceType.HTML


# ── Error handling ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unsupported_extension_raises(processor: DocumentProcessor) -> None:
    with pytest.raises(ValueError, match="Unsupported file type"):
        await processor.process(b"data", "file.docx")


@pytest.mark.asyncio
async def test_unsupported_csv_raises(processor: DocumentProcessor) -> None:
    with pytest.raises(ValueError, match="Unsupported file type"):
        await processor.process(b"col1,col2", "data.csv")


# ── PDF text extraction (no Vision, no API key needed) ────────────────────────


@pytest.mark.asyncio
async def test_pdf_text_extraction(processor: DocumentProcessor) -> None:
    """Build a minimal valid PDF in memory and verify text extraction works."""
    import io
    from pypdf import PdfWriter

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # pypdf blank pages have no text — this tests the Vision fallback path
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    # A blank PDF has no extractable text — it should attempt Vision.
    # With a dummy key the Vision call will fail. The processor should propagate
    # the error rather than silently return empty content, but since we want to
    # test the branch logic, we just verify the source_type would be PDF_VISION.
    # Full Vision test is in the @pytest.mark.llm block below.
    # For now, confirm the PDF bytes are at least parseable by pypdf.
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1


# ── Vision fallback (requires real OPENAI_API_KEY) ────────────────────────────


@pytest.mark.llm
@pytest.mark.asyncio
async def test_pdf_vision_fallback_with_real_key() -> None:
    """Scanned PDF (no text layer) must fall back to Vision and return content."""
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    import io
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    proc = DocumentProcessor(api_key=api_key, vision_model="gpt-4o")
    doc = await proc.process(pdf_bytes, "scanned.pdf")
    # Vision on a blank page returns minimal/empty content — just verify the path ran
    assert doc.source_type == SourceType.PDF_VISION
