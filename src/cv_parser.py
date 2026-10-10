from pypdf import PdfReader
from docx import Document
from pathlib import Path


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


def extract_text_from_docx(file_path):
    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_text(file_path):
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(file_path)

    elif file_path.suffix.lower() == ".docx":
        return extract_text_from_docx(file_path)

    else:
        return ""


if __name__ == "__main__":

    files = list(Path("attachments").glob("*.pdf"))
    files += list(Path("attachments").glob("*.docx"))

    if not files:
        print("No CV files found.")

    else:
        for file in files:

            print(f"\nProcessing: {file.name}")
            print("--------------------")

            text = extract_text(file)

            if text.strip():
                print(text)
            else:
                print("Could not extract text from this file.")