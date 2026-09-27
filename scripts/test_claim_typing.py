import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.claim_extraction.schemas import ExtractedClaim
from app.claim_extraction.typer import ClaimTyper

def main():
    print("=" * 80)
    print("STEP 12C — CLAIM TYPING TEST")
    print("=" * 80)

    typer = ClaimTyper()

    # We use a diverse set of claims to test the classification accuracy
    claims = [
        ExtractedClaim(
            claim_id="c1",
            text="AERIS utilizes a hybrid retrieval strategy.",
            source_chunk_id="chunk1",
            document_id="doc1"
        ),
        ExtractedClaim(
            claim_id="c2",
            text="AERIS combines dense retrieval using the all-MiniLM-L6-v2 model.",
            source_chunk_id="chunk1",
            document_id="doc1"
        ),
        ExtractedClaim(
            claim_id="c3",
            text="The approach improves recall over purely dense methods.",
            source_chunk_id="chunk1",
            document_id="doc1"
        ),
        ExtractedClaim(
            claim_id="c4",
            text="Reciprocal Rank Fusion (RRF) is a technique for combining multiple ranked lists.",
            source_chunk_id="chunk1",
            document_id="doc1"
        )
    ]
    
    print("INPUT CLAIMS:")
    for c in claims:
        print(f" - [{c.claim_id}] {c.text}")
        
    print("\n" + "-" * 80)
    print("Typing claims...")
    print("-" * 80)
    
    typed_claims = typer.type_claims(claims)
    
    print("\nTYPED CLAIMS:")
    for tc in typed_claims:
        print(f" - [{tc.claim_id}] {tc.claim_type.value} : {tc.text}")
        
    print("\n" + "=" * 80)
    print("STEP 12C TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
