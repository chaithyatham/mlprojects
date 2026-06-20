import re

def parse_pdf(filepath: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(pages)
    except ImportError:
        pass

    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages)
    except Exception:
        pass

    raise RuntimeError("Could not parse PDF — install pdfplumber: pip install pdfplumber")


def parse_resume(filepath: str) -> str:
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        text = parse_pdf(filepath)
    elif ext in ("doc", "docx"):
        try:
            import docx
            doc = docx.Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise RuntimeError("python-docx not installed. Upload a PDF instead.")
    else:
        with open(filepath, "r", errors="ignore") as f:
            text = f.read()

    # Normalise whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
