import fitz


def extract_text_from_pdf(content: bytes) -> str:
    """Extract plain text from a PDF byte stream."""
    with fitz.open(stream=content, filetype="pdf") as doc:
        text = "\n".join(page.get_text() for page in doc).strip()

    if not text:
        raise ValueError("PDF contains no extractable text (scanned image?)")

    return text
