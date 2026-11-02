import json
import os
import re
from enum import Enum
from typing import List, Optional

import ollama
from pydantic import BaseModel, Field
from app.utils.json_parser import extract_json


class VerificationLabel(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    RELATED = "RELATED"


class VerificationStrength(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClaimVerificationResult(BaseModel):
    claim: str
    evidence: str
    label: VerificationLabel
    confidence: float = Field(ge=0.0, le=1.0)
    strength: VerificationStrength
    rationale: str


class MultiEvidenceVerificationResult(BaseModel):
    claim: str
    evidence_count: int = Field(ge=1)
    evidence: List[str]
    label: VerificationLabel
    confidence: float = Field(ge=0.0, le=1.0)
    strength: VerificationStrength
    rationale: str


class ClaimVerifier:
    """
    Verifies claims against one or multiple evidence passages.

    Semantic similarity is not treated as factual verification.
    """

    STRENGTH_SCORES = {
        VerificationStrength.HIGH: 0.90,
        VerificationStrength.MEDIUM: 0.65,
        VerificationStrength.LOW: 0.35,
    }

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv(
            "OLLAMA_MODEL",
            "llama3.2:latest",
        )

    # =========================================================
    # SINGLE-EVIDENCE VERIFICATION
    # =========================================================

    def _build_prompt(
        self,
        claim: str,
        evidence: str,
    ) -> str:

        return f"""
You are a strict evidence verification system.

Determine the relationship between ONE CLAIM and ONE EVIDENCE
passage.

CLAIM:
{claim}

EVIDENCE:
{evidence}

Choose exactly one relationship:

SUPPORTS:
The evidence directly establishes or materially supports
the claim.

CONTRADICTS:
The evidence explicitly conflicts with the claim.

RELATED:
The evidence discusses the same or a closely related topic,
but neither establishes nor contradicts the claim.

Also choose exactly one verification strength:

HIGH:
The relationship is explicit and directly stated.

MEDIUM:
The relationship is reasonably clear but has limited detail.

LOW:
The relationship is weak, indirect, or only partially evident.

Rules:
1. Use ONLY the supplied evidence.
2. Do not use outside knowledge.
3. Do not treat topical similarity as factual support.
4. Do not infer missing facts.
5. If the evidence simply omits a specific detail mentioned in the claim (like a specific method name), it is RELATED, not CONTRADICTS and not SUPPORTS.
6. Be conservative.
7. Return JSON only.
8. Do not return a numeric confidence.

Return exactly:

{{
  "label": "SUPPORTS | CONTRADICTS | RELATED",
  "strength": "HIGH | MEDIUM | LOW",
  "rationale": "brief explanation based only on the evidence"
}}
"""

    # =========================================================
    # MULTI-EVIDENCE VERIFICATION
    # =========================================================

    def _build_multi_evidence_prompt(
        self,
        claim: str,
        evidence: List[str],
    ) -> str:

        evidence_text = "\n\n".join(
            f"EVIDENCE {index + 1}:\n{text}"
            for index, text in enumerate(evidence)
        )

        return f"""
You are a strict evidence verification system.

Determine the relationship between ONE CLAIM and a SET of
EVIDENCE passages. The evidence passages must be considered TOGETHER.

CLAIM:
{claim}

{evidence_text}

Choose exactly one relationship:

SUPPORTS:
The combined evidence directly establishes or materially
supports the claim.

CONTRADICTS:
The combined evidence explicitly conflicts with the claim.

RELATED:
The combined evidence discusses the same or a closely related topic,
but neither establishes nor contradicts the claim.

Also choose exactly one verification strength:

HIGH:
The relationship is explicit and directly stated.

MEDIUM:
The relationship is reasonably clear but has limited detail.

LOW:
The relationship is weak, indirect, or only partially evident.

Rules:
1. Use ONLY the supplied evidence.
2. Do not use outside knowledge.
3. Do not treat topical similarity as factual support.
4. Do not infer missing facts.
5. If the combined evidence simply omits a specific detail mentioned in the claim (like a specific method name), it is RELATED, not CONTRADICTS and not SUPPORTS.
6. Be conservative.
7. Return JSON only.
8. confidence is NOT requested. The system calculates it from verification strength.

Return ONLY a valid JSON object. Do not include any conversational text.
Return exactly:

{{
  "label": "SUPPORTS | CONTRADICTS | RELATED",
  "strength": "HIGH | MEDIUM | LOW",
  "rationale": "brief explanation based ONLY on the supplied evidence"
}}
"""


    # =========================================================
    # SINGLE EVIDENCE API
    # =========================================================

    def verify(
        self,
        claim: str,
        evidence: str,
    ) -> ClaimVerificationResult:

        prompt = self._build_prompt(
            claim=claim,
            evidence=evidence,
        )

        from app.utils.diagnostics import log_generation_attempt
        messages = [{"role": "user", "content": prompt}]
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            parse_success = False
            schema_success = False
            repair_invoked = False
            retry_invoked = (attempt > 1)
            
            try:
                import time
                start_time = time.time()
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": 0,
                        "num_predict": 1024,
                    },
                )
                elapsed = time.time() - start_time
            except Exception as e:
                elapsed = time.time() - start_time if 'start_time' in locals() else 0.0
                ctx_size = len(messages[-1]["content"])
                print(f"Error during claim verification [Model: {self.model}, Stage: verification, Context: {ctx_size} chars, Time: {elapsed:.2f}s]: {e}")
                raise e

            raw_content = response["message"]["content"]
            ctx_size = len(messages[-1]["content"])

            try:
                import json as std_json
                try:
                    std_json.loads(raw_content)
                except:
                    repair_invoked = True
                    
                json_text = extract_json(raw_content)
                parse_success = True
                
                result = std_json.loads(json_text)
                
                label = VerificationLabel(result["label"].strip().upper())
                strength = VerificationStrength(result["strength"].strip().upper())
                rationale = str(result["rationale"]).strip()
                schema_success = True
                
                confidence = self.STRENGTH_SCORES[strength]
                
                res = ClaimVerificationResult(
                    claim=claim,
                    evidence=evidence,
                    label=label,
                    confidence=confidence,
                    strength=strength,
                    rationale=rationale,
                )
                
                log_generation_attempt("Verification", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                return res
                
            except Exception as e:
                log_generation_attempt("Verification", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                if attempt == max_attempts:
                    raise e
                    
                messages.append({"role": "assistant", "content": raw_content})
                error_msg = f"Your previous response failed validation with error: {str(e)}. Please correct the JSON structure to strictly contain 'label', 'strength', and 'rationale' as specified."
                messages.append({"role": "user", "content": error_msg})

    # =========================================================
    # MULTI-EVIDENCE API
    # =========================================================

    def verify_multiple(
        self,
        claim: str,
        evidence: List[str],
    ) -> MultiEvidenceVerificationResult:

        if not evidence:
            raise ValueError(
                "At least one evidence passage is required."
            )

        prompt = self._build_multi_evidence_prompt(
            claim=claim,
            evidence=evidence,
        )

        from app.utils.diagnostics import log_generation_attempt
        messages = [{"role": "user", "content": prompt}]
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            parse_success = False
            schema_success = False
            repair_invoked = False
            retry_invoked = (attempt > 1)
            
            try:
                import time
                start_time = time.time()
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": 0,
                        "num_predict": 1024,
                    },
                )
                elapsed = time.time() - start_time
            except Exception as e:
                elapsed = time.time() - start_time if 'start_time' in locals() else 0.0
                ctx_size = len(messages[-1]["content"])
                print(f"Error during claim verification [Model: {self.model}, Stage: verification, Context: {ctx_size} chars, Time: {elapsed:.2f}s]: {e}")
                raise e

            raw_content = response["message"]["content"]
            ctx_size = len(messages[-1]["content"])

            try:
                import json as std_json
                try:
                    std_json.loads(raw_content)
                except:
                    repair_invoked = True
                    
                json_text = extract_json(raw_content)
                parse_success = True
                
                result = std_json.loads(json_text)
                
                label = VerificationLabel(result["label"].strip().upper())
                strength = VerificationStrength(result["strength"].strip().upper())
                rationale = str(result["rationale"]).strip()
                schema_success = True
                
                confidence = self.STRENGTH_SCORES[strength]
                
                res = MultiEvidenceVerificationResult(
                    claim=claim,
                    evidence_count=len(evidence),
                    evidence=evidence,
                    label=label,
                    confidence=confidence,
                    strength=strength,
                    rationale=rationale,
                )
                
                log_generation_attempt("Verification", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                return res
                
            except Exception as e:
                log_generation_attempt("Verification", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                if attempt == max_attempts:
                    raise e
                    
                messages.append({"role": "assistant", "content": raw_content})
                error_msg = f"Your previous response failed validation with error: {str(e)}. Please correct the JSON structure to strictly contain 'label', 'strength', and 'rationale' as specified."
                messages.append({"role": "user", "content": error_msg})
