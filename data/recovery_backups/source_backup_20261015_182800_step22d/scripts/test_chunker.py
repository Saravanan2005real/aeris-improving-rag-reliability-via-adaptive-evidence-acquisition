import sys
import os
import argparse
import io

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.pdf_loader import load_pdf
from app.chunking.semantic_chunker import chunk_document

def main():
    parser = argparse.ArgumentParser(description="Test PDF Chunking")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found at {args.pdf_path}")
        sys.exit(1)

    print("=" * 50)
    print("AERIS-RAG CHUNKING TEST")
    print("=" * 50)
    print()

    document = load_pdf(args.pdf_path)
    chunks = chunk_document(document)

    print(f"Total Pages : {document.page_count}")
    print(f"Total Chunks: {len(chunks)}")
    print()
    
    if not chunks:
        print("No chunks generated.")
        return

    sizes = [c.character_count for c in chunks]

    multi_page = sum(1 for c in chunks if len(c.pages) > 1)
    valid_doc = all(c.document_id == document.document_id for c in chunks)
    valid_prov = all(c.start_page <= c.end_page for c in chunks)

    print("PROVENANCE VALIDATION SUMMARY")
    print(f"- Number of chunks                 : {len(chunks)}")
    print(f"- Minimum chunk size               : {min(sizes)}")
    print(f"- Maximum chunk size               : {max(sizes)}")
    print(f"- Average chunk size               : {sum(sizes) / len(sizes):.1f}")
    print(f"- Chunks spanning multiple pages   : {multi_page}")
    print(f"- Every chunk has valid document_id: {valid_doc}")
    print(f"- Every chunk has valid provenance : {valid_prov}")
    print()

    print("FIRST 10 CHUNKS:")
    print("=" * 50)
    for chunk in chunks[:10]:
        print(f"Chunk ID    : {chunk.chunk_id}")
        print(f"Document ID : {chunk.document_id}")
        print(f"Pages       : {chunk.pages}")
        print(f"Start Page  : {chunk.start_page}")
        print(f"End Page    : {chunk.end_page}")
        print(f"Language    : {chunk.language}")
        print(f"Characters  : {chunk.character_count}")
        print()
        
        snippet = chunk.text[:300].replace('\n', ' ')
        print("First 300 chars:")
        try:
            print(snippet)
        except UnicodeEncodeError:
            print(snippet.encode('ascii', 'replace').decode('ascii'))
        print("-" * 50)

if __name__ == "__main__":
    main()
