import json
import os
import re
from enum import Enum
from typing import List, Optional

import ollama
from pydantic import BaseModel, Field


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
    # JSON PARSER
    # =========================================================

    def _extract_json(self, text: str) -> dict:

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        cleaned = re.sub(
            r"```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE,
        ).replace("```", "").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(
            r"\{.*\}",
            text,
            flags=re.DOTALL,
        )

        if match:
            return json.loads(match.group(0))

        if "{" in text and "}" not in text:
            try:
                fixed_text = text.strip()
                if not fixed_text.endswith('"'):
                    fixed_text += '"'
                fixed_text += "\n}"
                return json.loads(fixed_text[fixed_text.find("{"):])
            except Exception:
                pass

        raise ValueError(
            f"Could not parse verifier JSON:\n{text}"
        )

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

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            options={
                "temperature": 0,
            },
        )

        result = self._extract_json(
            response["message"]["content"]
        )

        label = VerificationLabel(
            result["label"].strip().upper()
        )

        strength = VerificationStrength(
            result["strength"].strip().upper()
        )

        confidence = self.STRENGTH_SCORES[strength]

        return ClaimVerificationResult(
            claim=claim,
            evidence=evidence,
            label=label,
            confidence=confidence,
            strength=strength,
            rationale=str(
                result["rationale"]
            ).strip(),
        )

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

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            options={
                "temperature": 0,
            },
        )

        result = self._extract_json(
            response["message"]["content"]
        )

        label = VerificationLabel(
            result["label"].strip().upper()
        )

        strength = VerificationStrength(
            result["strength"].strip().upper()
        )

        confidence = self.STRENGTH_SCORES[strength]

        return MultiEvidenceVerificationResult(
            claim=claim,
            evidence_count=len(evidence),
            evidence=evidence,
            label=label,
            confidence=confidence,
            strength=strength,
            rationale=str(
                result["rationale"]
            ).strip(),
        )
