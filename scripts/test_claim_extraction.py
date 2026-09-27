import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.claim_extraction.extractor import ClaimExtractor

def main():
    print("=" * 80)
    print("STEP 12A — CLAIM EXTRACTION TEST")
    print("=" * 80)

    extractor = ClaimExtractor()

    document_id = "test_document"
    chunk_id = "test_document_p001_c001"
    
    text = (
        "AERIS utilizes a hybrid retrieval strategy. It combines dense retrieval "
        "using the all-MiniLM-L6-v2 model with sparse retrieval using BM25. "
        "The results are then fused together using Reciprocal Rank Fusion (RRF). "
        "This approach significantly improves recall over purely dense or purely sparse methods."
    )

    print(f"\nSource Chunk: {chunk_id}")
    print(f"Text:\n{text}\n")
    print("-" * 80)
    print("Extracting claims...")

    result = extractor.extract(
        chunk_id=chunk_id,
        document_id=document_id,
        text=text
    )

    print("\n" + "-" * 80)
    print(f"Extracted {len(result.claims)} claims:")
    print("-" * 80)

    for claim in result.claims:
        print(f"\n[ID: {claim.claim_id}]")
        print(f"Claim: {claim.text}")
        print(f"Source: {claim.source_chunk_id}")

    print("\n" + "=" * 80)
    print("STEP 12A TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
