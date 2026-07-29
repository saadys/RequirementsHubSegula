"""
Parse Input Node

Extracts text from uploaded PDF and Excel files.
MVP: structured PDFs (pdfplumber) and Excel/CSV (pandas) only.

Owner: Track B
"""

# TODO [Track B]: Implement parse_input node
#
# Input from state: uploaded_files (list of file paths)
# Output to state: parsed_files_text (list of extracted text strings)
#
# def parse_input(state: PipelineState) -> dict:
#     1. Loop through uploaded_files
#     2. For .pdf → pdfplumber.open() → extract_text() per page
#     3. For .xlsx/.csv → pandas.read_excel/read_csv → to_string()
#     4. For unsupported → "[Unsupported file type: {ext}]"
#     5. Return {"parsed_files_text": [...]}
