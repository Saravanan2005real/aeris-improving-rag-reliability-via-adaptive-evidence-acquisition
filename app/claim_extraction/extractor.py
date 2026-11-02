import os
import json
import re
import time
from typing import Optional
from app.performance_cache import aeris_cache

import ollama
from app.config import settings
from app.claim_extraction.schemas import ExtractedClaim, ClaimExtractionResult
from app.utils.json_parser import extract_json
from app.utils.model_client import get_ollama_client, timed_model_chat
from app.utils.diagnostics import log_generation_attempt

DEFAULT_EXTRACTION_TIMEOUT: float = 180.0


class ClaimExtractor:
    """
    Extracts atomic, verifiable claims from a given chunk of evidence text
    using an LLM.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 1,
    ):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.timeout = (
            timeout
            if timeout is not None
            else getattr(settings, "ollama_claim_extraction_timeout", DEFAULT_EXTRACTION_TIMEOUT)
        )
        self.max_retries = max_retries
        self.client = get_ollama_client(host=self.host, timeout=self.timeout)

    def extract(self, chunk_id: str, document_id: str, text: str) -> ClaimExtractionResult:
        """
        Extract claims from a single chunk of text with telemetry and deliberate retry logic.
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
            "10. Do not explain, summarize, interpret, or evaluate the claims.\n"
            "11. Do not repeat claims or output duplicate entries. Extract each factual assertion at most once.\n"
            "12. When document headers, titles, author names, or affiliations are present in the text, extract them as factual claims (e.g., 'X is the first author', 'X is affiliated with Y').\n\n"

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
            "Do not include markdown, explanations, numbering, or any other fields.\n"
            "Respond ONLY with valid JSON. Do not include markdown blocks, preamble, or explanation outside the JSON.\n"
            "Start your response exactly with { and end exactly with }.\n\n"

            f"TEXT TO ANALYZE:\n{text}"
        )

        cache_key = {"chunk": chunk_id}
        cached = aeris_cache.get("extraction", cache_key)
        if cached:
            return ClaimExtractionResult(**cached)

        max_attempts = max(1, self.max_retries + 1)
        last_exception = None
        ctx_size = len(prompt)

        for attempt in range(1, max_attempts + 1):
            parse_success = False
            schema_success = False
            repair_invoked = False
            retry_invoked = (attempt > 1)
            elapsed = 0.0

            try:
                chat_res = timed_model_chat(
                    client=self.client,
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    format="json",
                    options={
                        "temperature": 0.0,
                        "num_predict": 2048,
                    },
                    stage="Claim Extraction",
                )
                elapsed = chat_res["elapsed_seconds"]
                result_str = chat_res["content"]

                try:
                    data = json.loads(result_str)
                except Exception:
                    repair_invoked = True
                    json_text = extract_json(result_str)
                    data = json.loads(json_text)

                parse_success = True

                if not isinstance(data, dict) or "claims" not in data:
                    raise ValueError("Claim extraction output must be a JSON object with a 'claims' array.")

                raw_claims = data.get("claims", [])
                if not isinstance(raw_claims, list):
                    raise ValueError("The 'claims' field must be a list of strings.")

                schema_success = True

                extracted_claims = []
                seen_claim_texts = set()
                for claim_text in raw_claims:
                    if isinstance(claim_text, str) and claim_text.strip():
                        cleaned = claim_text.strip()
                        if cleaned not in seen_claim_texts:
                            seen_claim_texts.add(cleaned)
                            claim_id = f"{chunk_id}_claim_{len(extracted_claims) + 1}"
                            extracted_claims.append(
                                ExtractedClaim(
                                    claim_id=claim_id,
                                    text=cleaned,
                                    source_chunk_id=chunk_id,
                                    document_id=document_id
                                )
                            )

                log_generation_attempt(
                    stage="Claim Extraction",
                    question_id="UNKNOWN",
                    variant="UNKNOWN",
                    attempt=attempt,
                    model=self.model,
                    context_size=ctx_size,
                    latency=elapsed,
                    parse_success=parse_success,
                    schema_success=schema_success,
                    repair_invoked=repair_invoked,
                    retry_invoked=retry_invoked,
                )

                res = ClaimExtractionResult(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    claims=extracted_claims
                )
                res_dict = {
                    "chunk_id": res.chunk_id,
                    "document_id": res.document_id,
                    "claims": [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in res.claims],
                }
                aeris_cache.set("extraction", cache_key, res_dict)
                return res

            except Exception as e:
                last_exception = e
                log_generation_attempt(
                    stage="Claim Extraction",
                    question_id="UNKNOWN",
                    variant="UNKNOWN",
                    attempt=attempt,
                    model=self.model,
                    context_size=ctx_size,
                    latency=elapsed,
                    parse_success=parse_success,
                    schema_success=schema_success,
                    repair_invoked=repair_invoked,
                    retry_invoked=retry_invoked,
                )
                print(
                    f"Error during claim extraction [Model: {self.model}, Attempt: {attempt}/{max_attempts}, "
                    f"Context: {ctx_size} chars, Time: {elapsed:.2f}s]: {e}"
                )
                if attempt == max_attempts:
                    raise last_exception
