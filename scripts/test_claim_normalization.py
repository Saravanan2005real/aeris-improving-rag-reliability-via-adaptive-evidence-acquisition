import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.claim_extraction.schemas import ExtractedClaim
from app.claim_extraction.normalizer import ClaimNormalizer

def main():
    print("=" * 80)
    print("STEP 12B — CLAIM NORMALIZATION TEST")
    print("=" * 80)

    # Use a high threshold to ensure 'dense' vs 'sparse' don't get merged
    normalizer = ClaimNormalizer(similarity_threshold=0.92)

    raw_claims = [
        # Semantically equivalent pair
        ExtractedClaim(
            claim_id="c1",
            text="AERIS utilizes a hybrid retrieval strategy.",
            source_chunk_id="chunk1",
            document_id="doc1"
        ),
        ExtractedClaim(
            claim_id="c2",
            text="AERIS uses a hybrid retrieval strategy.",
            source_chunk_id="chunk2",
            document_id="doc1"
        ),
        
        # Exact duplicate (modulo case/punctuation)
        ExtractedClaim(
            claim_id="c3",
            text="aeris utilizes a hybrid retrieval strategy",
            source_chunk_id="chunk3",
            document_id="doc1"
        ),

        # Distinct claim
        ExtractedClaim(
            claim_id="c4",
            text="The approach significantly improves recall over purely dense methods.",
            source_chunk_id="chunk1",
            document_id="doc1"
        ),
        
        # Semantically distinct but lexically similar words
        ExtractedClaim(
            claim_id="c5",
            text="The approach significantly improves recall over purely sparse methods.",
            source_chunk_id="chunk1",
            document_id="doc1"
        )
    ]

    print("RAW CLAIMS:")
    for claim in raw_claims:
        print(f" - [{claim.claim_id}] {claim.text} (from {claim.source_chunk_id})")

    print("\n" + "-" * 80)
    print("Normalizing and Deduplicating...")
    print("-" * 80)

    normalized_claims = normalizer.normalize_and_deduplicate(raw_claims)

    print(f"\nFINAL CLAIMS ({len(normalized_claims)} remaining):")
    for claim in normalized_claims:
        print(f" - [{claim.claim_id}] {claim.text} (from {claim.source_chunk_id})")

    print("\n" + "=" * 80)
    print("STEP 12B TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
