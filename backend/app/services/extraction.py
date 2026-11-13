"""Docling PDF/Word extraction, tokenizer-aware chunking, and Excel cell spans."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from transformers import AutoTokenizer
from app.config import EMBEDDING_MODEL


@dataclass(frozen=True)
class ExtractedChunk:
    text: str
    source_meta: dict


@lru_cache(maxsize=1)
def get_converter() -> DocumentConverter:
    # The standard PDF pipeline runs OCR when required (RapidOCR default).
    return DocumentConverter(allowed_formats=[InputFormat.PDF, InputFormat.DOCX])


@lru_cache(maxsize=1)
def get_chunker() -> HybridChunker:
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(EMBEDDING_MODEL),
        max_tokens=384,
    )
    return HybridChunker(tokenizer=tokenizer)


def extract_office_or_pdf(path: Path) -> list[ExtractedChunk]:
    dl_doc = get_converter().convert(str(path)).document
    chunker = get_chunker()
    extracted: list[ExtractedChunk] = []
    kind = path.suffix.lower().lstrip('.')
    for chunk in chunker.chunk(dl_doc=dl_doc):
        content = chunker.contextualize(chunk).strip()
        if not content:
            continue
        meta = chunk.meta
        pages = sorted({
            prov.page_no
            for item in (getattr(meta, 'doc_items', None) or [])
            for prov in (getattr(item, 'prov', None) or [])
            if getattr(prov, 'page_no', None) is not None
        })
        headings = list(getattr(meta, 'headings', None) or [])
        locator_type = 'page' if pages else ('section' if headings else 'document')
        extracted.append(ExtractedChunk(
            text=content,
            source_meta={
                'format': kind,
                'locator_type': locator_type,
                'pages': pages,                  # PDF pages only when Docling supplies them
                'headings': headings,            # Word sections; no invented Word pages
            },
        ))
    return extracted


def extract_excel(path: Path, rows_per_chunk: int = 12) -> list[ExtractedChunk]:
    """Spreadsheet-aware extraction with actual sheet/row/cell references.

    We deliberately use openpyxl for XLSX provenance. Docling can parse XLSX,
    but a Markdown export does not reliably preserve exact source cells.
    """
    output: list[ExtractedChunk] = []
    wb = load_workbook(path, read_only=True, data_only=False)
    try:
        total_rows = 0
        for ws in wb.worksheets:
            pending: list[str] = []
            first_row: int | None = None
            last_row: int | None = None
            max_col = 1
            def flush() -> None:
                nonlocal pending, first_row, last_row, max_col
                if not pending or first_row is None or last_row is None:
                    return
                escaped_sheet = ws.title.replace("'", "''")
                cell_range = f"'{escaped_sheet}'!A{first_row}:{get_column_letter(max_col)}{last_row}"
                output.append(ExtractedChunk(
                    text=f"Worksheet: {ws.title}\n" + '\n'.join(pending),
                    source_meta={
                        'format': 'xlsx',
                        'locator_type': 'cell_range',
                        'sheet': ws.title,
                        'cell_range': cell_range,
                        'row_start': first_row,
                        'row_end': last_row,
                    },
                ))
                pending = []
                first_row = last_row = None
                max_col = 1
            for row_num, row in enumerate(ws.iter_rows(values_only=True), 1):
                total_rows += 1
                if total_rows > 3000:
                    raise ValueError('Spreadsheet exceeds the local 3000-row processing limit')
                populated = [(i, str(value)) for i, value in enumerate(row, 1) if value is not None and str(value).strip()]
                if not populated:
                    continue
                if len(populated) > 60 or any(len(value) > 300 for _, value in populated):
                    raise ValueError('Spreadsheet cell/row exceeds this release processing limits')
                row_text = '; '.join(f'{get_column_letter(i)}{row_num}={value}' for i, value in populated)
                if len(row_text) > 1200:
                    raise ValueError('Spreadsheet row exceeds the local indexing text budget')
                if pending and (sum(map(len, pending)) + len(row_text) > 1200):
                    flush()
                if first_row is None:
                    first_row = row_num
                last_row = row_num
                max_col = max(max_col, populated[-1][0])
                pending.append(row_text)
                if len(pending) == rows_per_chunk:
                    flush()
            flush()
    finally:
        wb.close()
    return output


def extract_document(path: Path) -> list[ExtractedChunk]:
    chunks = extract_excel(path) if path.suffix.lower() == '.xlsx' else extract_office_or_pdf(path)
    if not chunks:
        raise ValueError('No searchable text was extracted')
    return chunks
