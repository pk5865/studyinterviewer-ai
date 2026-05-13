import pdfplumber

def extract_text_from_pdf(path):
    """Extract text from PDF with memory-safe settings"""
    text = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text.append(t.strip())
        return "\n\n".join(text)
    except Exception as e:
        print(f"PDF parse error: {e}")
        return ""