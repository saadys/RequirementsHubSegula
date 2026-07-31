"""
Node: parse_input
Responsibility: Extract text content from uploaded files (PDFs, Excel) 
and populate state['parsed_files_text'].
"""

import logging
from pathlib import Path
import pdfplumber

from backend.contracts.state import PipelineState

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """
    Extract text content from a text-based PDF file page by page using pdfplumber.
    
    Args:
        file_path (str): Absolute or relative path to the PDF file on disk.
        
    Returns:
        str: Consolidated plain text extracted from all readable pages.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file path does not point to a PDF.
    """
    path = Path(file_path)
    if not path.is_file():
        logger.error(f"PDF file not found at path: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if path.suffix.lower() != ".pdf":
        logger.error(f"Invalid file extension for PDF parser: {file_path}")
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

    extracted_pages: list[str] = []
    
    try:
        with pdfplumber.open(path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    extracted_pages.append(f"--- Page {index} ---\n{page_text.strip()}")
                else:
                    logger.warning(f"Page {index} in '{path.name}' contained no extractable text (possibly scanned or empty).")
    except Exception as exc:
        logger.error(f"Failed to parse PDF file '{file_path}': {str(exc)}", exc_info=True)
        return f"[ERROR] Failed to parse PDF '{path.name}': {str(exc)}"

    if not extracted_pages:
        logger.warning(f"PDF file '{file_path}' yielded zero extractable text.")
        return f"[WARNING] File '{path.name}' contains no extractable text (image-based scanned PDF)."

    return "\n\n".join(extracted_pages)


# Alias to satisfy specified function naming while maintaining PEP 8 snake_case standards
ParsingPDF = parse_pdf


def parse_input(state: PipelineState) -> dict:
    """
    LangGraph Node function to process all uploaded files in PipelineState.
    
    Args:
        state (PipelineState): The current graph state.
        
    Returns:
        dict: State update containing 'parsed_files_text'.
    """
    uploaded_files = state.get("uploaded_files", [])
    parsed_results: list[str] = []

    for file_path in uploaded_files:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            parsed_text = parse_pdf(file_path)
            parsed_results.append(parsed_text)
        else:
            logger.info(f"Skipping non-PDF file in parse_input: {file_path}")

    return {"parsed_files_text": parsed_results}
