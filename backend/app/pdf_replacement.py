"""Experimental complete replacement for the PyMuPDF extract_pages boundary.

Runs only on experiment/full-pymupdf-replacement. No fitz import or fallback.
Docling is a standalone structured-document replacement.
Camelot is a table extractor, so the *Camelot+pdfminer* path is explicitly a
composite alternative, not falsely represented as Camelot-alone text parsing.
Never silently fall back to the original parser on failure.
"""
from __future__ import annotations

from collections import defaultdict
from io import BytesIO
import os
import re
import tempfile
from typing import Any

MAX_BYTES = 30 * 1024 * 1024
MAX_PAGES = 300
MAX_SCAN = 50
MAX_PAGE_CHARS = 4500


def _count_pages(data: bytes) -> int:
    from pdfminer.pdfpage import PDFPage
    try:
        count = sum(1 for _ in PDFPage.get_pages(BytesIO(data), check_extractable=True))
    except Exception as exc:
        raise ValueError("PDF metadata/page traversal failed or encrypted") from exc
    if not 1 <= count <= MAX_PAGES:
        raise ValueError("Unsupported page count")
    return count


def _normal_pages(per_page: dict[int, list[str]], count: int) -> tuple[int, list[dict[str, Any]]]:
    out: list[dict[str, Any]] = []
    for page in range(1, min(count, MAX_SCAN) + 1):
        text = re.sub(r"\s+", " ", " ".join(per_page.get(page, []))).strip()
        text = "".join(ch for ch in text if ch in "\t\n\r" or ord(ch) >= 32)
        if text:
            out.append({"page": page, "text": text[:MAX_PAGE_CHARS]})
    if not out:
        raise ValueError("No extractable text in replacement path")
    return count, out


def docling_pages(data: bytes, count: int) -> tuple[int, list[dict[str, Any]]]:
    from docling.datamodel.base_models import DocumentStream, InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    # Avoid OCR and GPU downloads to make a CPU comparison reproducible.
    opts = PdfPipelineOptions(do_ocr=False, do_table_structure=True)
    opts.generate_page_images = False
    opts.generate_picture_images = False
    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)},
    )
    stream = DocumentStream(name="paper.pdf", stream=BytesIO(data))
    result = converter.convert(stream, raises_on_error=True, page_range=(1, min(count, MAX_SCAN)))
    doc = result.document
    by_page: dict[int, list[str]] = defaultdict(list)
    unlocated = 0
    for item, _level in doc.iterate_items():
        if not hasattr(item, "prov") or not item.prov:
            unlocated += 1
            continue
        page = int(item.prov[0].page_no)
        if page < 1 or page > min(count, MAX_SCAN):
            continue
        value = getattr(item, "text", None)
        if isinstance(value, str) and value.strip():
            by_page[page].append(value)
            continue
        if hasattr(item, "export_to_dataframe"):
            try:
                frame = item.export_to_dataframe(doc=doc)
                rows = frame.values.tolist()
                flat = [" | ".join(str(cell).strip() for cell in row) for row in rows]
                by_page[page].extend(flat)
            except Exception:
                # Document conversion is successful, but table loss is a QA
                # failure, not an excuse to copy PyMuPDF's output.
                raise ValueError("Docling table export failed")
    if not by_page:
        raise ValueError("Docling returned no page-located text or tables")
    return _normal_pages(by_page, count)


def camelot_composite_pages(data: bytes, count: int) -> tuple[int, list[dict[str, Any]]]:
    import camelot
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer
    by_page: dict[int, list[str]] = defaultdict(list)
    for page_no, layout in enumerate(extract_pages(BytesIO(data), maxpages=min(count, MAX_SCAN)), start=1):
        # pdfminer is required here: Camelot alone is NOT a general PDF reader.
        blocks = [element for element in layout if isinstance(element, LTTextContainer)]
        for block in sorted(blocks, key=lambda x: (-x.y1, x.x0)):
            val = block.get_text()
            if val.strip():
                by_page[page_no].append(val)
    # Full replacement attempt: use Camelot for tables, not the old fitz path.
    # Keep the exact general-text contract (4500 chars) and capture the additional
    # table cells as part of the page text for the existing evidence engine.
    with tempfile.TemporaryDirectory(prefix="papersignal-camelot-replace-") as directory:
        filename = os.path.join(directory, "paper.pdf")
        with open(filename, "wb") as out:
            out.write(data)
        tables = camelot.read_pdf(filename, pages=f"1-{min(count, MAX_SCAN)}", flavor="stream")
        for table in tables:
            page = int(getattr(table, "page", 0) or 0)
            if page not in range(1, min(count, MAX_SCAN) + 1):
                raise ValueError("Camelot table has incorrect source page")
            rows = table.df.values.tolist()
            matrix_text = " ".join(" | ".join(str(cell).strip() for cell in row) for row in rows)
            if matrix_text.strip():
                # Tables precede prose because regressions are the primary target.
                by_page[page].insert(0, matrix_text)
    return _normal_pages(by_page, count)



def docling_parse_pages(data: bytes, count: int) -> tuple[int, list[dict[str, Any]]]:
    """Direct docling-parse v7: replacement PDF text, no fitz or ML models."""
    from docling_parse.pdf_parser import ContentConfig, ContentLevel, DecodeConfig, DoclingPdfParser
    with tempfile.TemporaryDirectory(prefix="papersignal-docling-native-") as d:
        p = os.path.join(d, "source.pdf")
        with open(p, "wb") as handle:
            handle.write(data)
        parser = DoclingPdfParser(loglevel="fatal")
        doc = parser.load(
            path_or_stream=p,
            decode_config=DecodeConfig(do_sanitization=True, keep_glyphs=False),
            content_config=ContentConfig(
                word_cells_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
                line_cells_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
                shapes_content_level=ContentLevel.SKIP,
                bitmaps_content_level=ContentLevel.SKIP,
            ),
        )
        if doc is None or doc.number_of_pages() != count:
            raise ValueError("docling-parse page-count mismatch")
        pages: dict[int, list[str]] = defaultdict(list)
        for n, page in doc.iterate_pages():
            if 1 <= int(n) <= min(count, MAX_SCAN):
                pages[int(n)].extend(c.text for c in page.textline_cells
                                     if isinstance(c.text, str) and c.text.strip())
    return _normal_pages(pages, count)

def extract_pages(data: bytes, backend: str | None = None) -> tuple[int, list[dict[str, Any]]]:
    if not isinstance(data, bytes) or not data.startswith(b"%PDF-") or not 0 < len(data) <= MAX_BYTES:
        raise ValueError("Expected a valid PDF of at most 30 MiB")
    mode = backend if backend is not None else os.environ.get("PAPERSIGNAL_PDF_BACKEND", "docling_parse")
    if mode not in ("docling", "camelot_composite", "docling_parse"):
        raise ValueError("Invalid experimental PDF backend")
    count = _count_pages(data)
    if mode == "docling":
        return docling_pages(data, count)
    if mode == "docling_parse":
        return docling_parse_pages(data, count)
    return camelot_composite_pages(data, count)
