import os
import json
import re

import ollama
from app.config import settings
from app.claim_extraction.schemas import ExtractedClaim, ClaimExtractionResult

class ClaimExtractor:
    """
    Extracts atomic, verifiable claims from a given chunk of evidence text
    using an LLM.
    """

    def __init__(self, model: str = None, host: str = None):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.client = ollama.Client(host=self.host)

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No valid JSON object found in model response.")
        return text[start : end + 1]

    def extract(self, chunk_id: str, document_id: str, text: str) -> ClaimExtractionResult:
        """
        Extract claims from a single chunk of text.
        """
        prompt = (
            "You are an expert fact extractor for a research-grade retrieval system.\n\n"
            "Your task is to extract ALL atomic, independently verifiable claims from "
            "the provided evidence text.\n\n"

            "DEFINITION:\n"
            "An atomic claim is one self-contained proposition that can be independently "
            "verified from the source text. Each distinct factual assertion must become "
            "a separate claim.\n\n"

            "IMPORTANT RULES:\n"
            "1. Extract EVERY factual proposition. Do not omit factual details.\n"
            "2. If one sentence contains multiple independent factual assertions, split "
            "them into separate claims.\n"
            "3. Preserve important entities, model names, algorithms, methods, metrics, "
            "relationships, and quantitative or comparative statements.\n"
            "4. Do not merge separate methods or relationships into one claim.\n"
            "5. Do not invent information that is not explicitly supported by the text.\n"
            "6. Preserve the meaning of the source text.\n"
            "7. Resolve pronouns only when their reference is explicitly clear from "
            "the provided text.\n"
            "8. Comparative or causal statements must remain claims when they are "
            "explicitly stated in the source.\n"
            "9. Each claim should normally express one subject-predicate relationship "
            "or one independently testable proposition.\n"
            "10. Do not explain, summarize, interpret, or evaluate the claims.\n\n"

            "EXAMPLE:\n"
            "Input:\n"
            "\"The system combines dense retrieval using Model X with sparse retrieval "
            "using BM25. The results are fused using RRF.\"\n\n"

            "Correct output:\n"
            "{\"claims\": ["
            "\"The system uses dense retrieval using Model X.\", "
            "\"The system uses sparse retrieval using BM25.\", "
            "\"The dense and sparse retrieval results are fused using Reciprocal Rank Fusion (RRF).\""
            "]}\n\n"

            "Return STRICTLY a JSON object with a single key 'claims'.\n"
            "The value of 'claims' must be a list of strings.\n"
            "Do not include markdown, explanations, numbering, or any other fields.\n\n"

            f"TEXT TO ANALYZE:\n{text}"
        )

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                format="json",
                options={
                    "temperature": 0.0,
                },
            )

            result_str = response["message"]["content"]
            json_text = self._extract_json(result_str)
            data = json.loads(json_text)
            raw_claims = data.get("claims", [])

            extracted_claims = []
            for i, claim_text in enumerate(raw_claims):
                claim_id = f"{chunk_id}_claim_{i+1}"
                extracted_claims.append(
                    ExtractedClaim(
                        claim_id=claim_id,
                        text=claim_text.strip(),
                        source_chunk_id=chunk_id,
                        document_id=document_id
                    )
                )

            return ClaimExtractionResult(
                chunk_id=chunk_id,
                document_id=document_id,
                claims=extracted_claims
            )

        except Exception as e:
            print(f"Error during claim extraction: {e}")
            return ClaimExtractionResult(
                chunk_id=chunk_id,
                document_id=document_id,
                claims=[]
            )
