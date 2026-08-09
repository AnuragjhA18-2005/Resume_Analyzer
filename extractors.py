import re 
import pymupdf
import docx
import os
from pathlib import Path
import json
from docx.text.paragraph import Paragraph
from docx.table import Table

def read_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF file using PyMuPDF with clean spacing and error handling."""
    text_parts = []
    try:
        with pymupdf.open(pdf_path) as doc:
            for page in doc:
                page_text = page.get_text("text")
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""
    
    # Clean up redundant multiple newlines and spaces
    full_text = "\n".join(text_parts)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', full_text)
    return cleaned_text.strip()


def read_docx(docx_path: str) -> str:
    """Extracts raw text from paragraphs and tables in a DOCX file in document order with robust handling."""
    full_text = []
    try:
        doc = docx.Document(docx_path)
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
        print(f"Error reading DOCX {docx_path}: {e}")
        return ""
                
    return "\n".join(full_text)

def read_resume(file_path: Path) -> str:
    # Ensure file_path is a Path object
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    if extension == '.pdf':
        return read_pdf(file_path)
    elif extension == '.docx':
        return read_docx(file_path)
    else:
        return 'Incorrect File Format uploaded'