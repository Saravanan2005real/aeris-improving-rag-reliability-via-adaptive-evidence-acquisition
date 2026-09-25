import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.pdf_loader import load_pdf

def main():
    parser = argparse.ArgumentParser(description="Test PDF Ingestion")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found at {args.pdf_path}")
        sys.exit(1)

    print("=" * 50)
    print("AERIS-RAG PDF INGESTION TEST")
    print("=" * 50)
    print()

    document = load_pdf(args.pdf_path)

    print(f"Document ID : {document.document_id}")
    print(f"Filename    : {document.filename}")
    print(f"Pages       : {document.page_count}")
    print(f"Language    : {document.language}")
    print()

    for page in document.pages:
        print("-" * 50)
        print(f"PAGE {page.page_number}")
        print(f"Language       : {page.language}")
        print(f"Characters     : {page.character_count}")
        print()
        
        # First 200 chars
        snippet = page.text[:200].replace('\n', ' ')
        print("First 200 chars:")
        try:
            print(snippet)
        except UnicodeEncodeError:
            print(snippet.encode('ascii', 'replace').decode('ascii'))
        print()

if __name__ == "__main__":
    main()
