import os
from typing import List, Set

import torch
from sentence_transformers import SentenceTransformer, util

from app.claim_extraction.schemas import ExtractedClaim

class ClaimNormalizer:
    """
    Normalizes and deduplicates a list of raw extracted claims.
    Uses dense embeddings to detect and merge semantically equivalent claims.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.92
    ):
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        # Load the sentence transformer model
        self.model = SentenceTransformer(self.model_name)

    def normalize_and_deduplicate(self, claims: List[ExtractedClaim]) -> List[ExtractedClaim]:
        """
        Deduplicates a list of claims by comparing their semantic embeddings.
        Preserves the first encountered claim and its provenance.
        """
        if not claims:
            return []

        # 1. Exact string deduplication (case-insensitive, stripped)
        seen_texts = set()
        unique_raw_claims = []
        for claim in claims:
            normalized_text = claim.text.strip().lower()
            # Remove trailing periods for exact matching
            if normalized_text.endswith("."):
                normalized_text = normalized_text[:-1]
                
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_raw_claims.append(claim)
                
        if not unique_raw_claims:
            return []

        # 2. Semantic deduplication
        texts = [claim.text for claim in unique_raw_claims]
        embeddings = self.model.encode(texts, convert_to_tensor=True)
        cosine_scores = util.cos_sim(embeddings, embeddings).cpu().numpy()

        final_claims = []
        merged_indices = set()

        for i in range(len(unique_raw_claims)):
            if i in merged_indices:
                continue
                
            final_claims.append(unique_raw_claims[i])
            
            for j in range(i + 1, len(unique_raw_claims)):
                if j not in merged_indices:
                    if cosine_scores[i][j] >= self.similarity_threshold:
                        merged_indices.add(j)

        return final_claims
