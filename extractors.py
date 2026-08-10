from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import docx
import pymupdf
import re
from docx.text.paragraph import Paragraph
from docx.table import Table


def _read_source_bytes(source: bytes | str | Path | BinaryIO) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    if isinstance(source, str):
        return Path(source).read_bytes()

    data = source.read()
    return data if isinstance(data, bytes) else data.encode()


def read_pdf(pdf_source: bytes | str | Path | BinaryIO) -> str:
    """Extracts raw text from a PDF file using PyMuPDF with clean spacing and error handling."""
    text_parts = []
    try:
        if isinstance(pdf_source, (str, Path)):
            with pymupdf.open(str(pdf_source)) as doc:
                for page in doc:
                    page_text = page.get_text("text")
                    if page_text:
                        text_parts.append(page_text)
        else:
            with pymupdf.open(stream=_read_source_bytes(pdf_source), filetype="pdf") as doc:
                for page in doc:
                    page_text = page.get_text("text")
                    if page_text:
                        text_parts.append(page_text)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    
    # Clean up redundant multiple newlines and spaces
    full_text = "\n".join(text_parts)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', full_text)
    return cleaned_text.strip()


def read_docx(docx_source: bytes | str | Path | BinaryIO) -> str:
    """Extracts raw text from paragraphs and tables in a DOCX file in document order with robust handling."""
    full_text = []
    try:
        if isinstance(docx_source, (str, Path)):
            doc = docx.Document(str(docx_source))
        else:
            doc = docx.Document(BytesIO(_read_source_bytes(docx_source)))
        for child in doc.element.body:
            if child.tag.endswith('p'):
                paragraph_text = Paragraph(child, doc).text
                if paragraph_text.strip():
                    full_text.append(paragraph_text.strip())
            elif child.tag.endswith('tbl'):
                table = Table(child, doc)
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        # Extract cell text and strip spacing
                        cell_val = cell.text.strip() if cell.text else ""
                        if cell_val:
                            row_text.append(cell_val)
                    if row_text:
                        full_text.append(" | ".join(row_text))
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""
                
    return "\n".join(full_text)


def read_resume(file_source: bytes | str | Path | BinaryIO, file_name: str | None = None) -> str:
    if file_name:
        extension = Path(file_name).suffix.lower()
    elif isinstance(file_source, (str, Path)):
        extension = Path(file_source).suffix.lower()
    else:
        extension = ""

    if extension == '.pdf':
        return read_pdf(file_source)
    elif extension == '.docx':
        return read_docx(file_source)
    else:
        return ""
