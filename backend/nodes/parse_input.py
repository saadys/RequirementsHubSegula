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
        logger.error("PDF file not found at path: %s", file_path)
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if path.suffix.lower() != ".pdf":
        logger.error("Invalid file extension for PDF parser: %s", file_path)
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

    extracted_pages: list[str] = []
    
    try:
        with pdfplumber.open(path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    extracted_pages.append(f"--- Page {index} ---\n{page_text.strip()}")
                else:
                    logger.warning("Page %d in '%s' contained no extractable text (scanned or empty)", index, path.name)
    except Exception as exc:
        logger.error("Failed to parse PDF file '%s': %s", file_path, exc, exc_info=True)
        return f"[ERROR] Failed to parse PDF '{path.name}': {str(exc)}"

    if not extracted_pages:
        logger.warning("PDF file '%s' yielded zero extractable text", file_path)
        return f"[WARNING] File '{path.name}' contains no extractable text (image-based scanned PDF)."

    return "\n\n".join(extracted_pages)


# Alias to satisfy specified function naming while maintaining PEP 8 snake_case standards
ParsingPDF = parse_pdf


def parse_input(state: PipelineState) -> dict:
    """
    LangGraph Node function to process all uploaded files in PipelineState.
    Idempotent: Reuses existing parsed_files_text if no new uploaded_files are provided.
    
    Args:
        state (PipelineState): The current graph state.
        
    Returns:
        dict: State update containing 'parsed_files_text'.
    """
    uploaded_files = state.get("uploaded_files", [])
    existing_parsed = state.get("parsed_files_text", [])

    # If no new uploaded files are provided and we already have extracted text (e.g. clarification round)
    if not uploaded_files and existing_parsed:
        return {"parsed_files_text": existing_parsed}

    parsed_results: list[str] = []

    for file_path in uploaded_files:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            try:
                parsed_text = parse_pdf(file_path)
                parsed_results.append(parsed_text)
            except Exception as exc:
                logger.error("Error reading PDF %s: %s", file_path, exc)
                parsed_results.append(f"[ERROR] Unable to parse file '{path.name}': {exc}")
        else:
            logger.info("Skipping non-PDF file in parse_input: %s", file_path)

    final_results = (existing_parsed + parsed_results) if (existing_parsed and uploaded_files) else parsed_results
    return {"parsed_files_text": final_results}

