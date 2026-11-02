from enum import Enum
from pydantic import BaseModel, Field
import ollama

from app.config import settings


class ContradictionLabel(str, Enum):
    NO_CONTRADICTION = "NO_CONTRADICTION"
    CONTEXTUAL_DIFFERENCE = "CONTEXTUAL_DIFFERENCE"
    CONTRADICTION = "CONTRADICTION"
    UNCERTAIN = "UNCERTAIN"


class ContradictionResult(BaseModel):
    evidence_a: str
    evidence_b: str
    label: ContradictionLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class ContextualContradictionClassifier:
    """
    Determines whether two evidence passages genuinely contradict
    each other after considering their context.

    The classifier distinguishes:
    - genuine contradiction
    - contextual difference
    - no contradiction
    - uncertain cases

    Confidence is a deterministic strength score, not a calibrated
    probability. Calibration is handled later in Step 17.
    """

    LABEL_SCORES = {
        ContradictionLabel.CONTRADICTION: 0.90,
        ContradictionLabel.NO_CONTRADICTION: 0.90,
        ContradictionLabel.CONTEXTUAL_DIFFERENCE: 0.80,
        ContradictionLabel.UNCERTAIN: 0.35,
    }

    def __init__(self, model: str | None = None):
        self.model = model or settings.ollama_model

    def classify(
        self,
        evidence_a: str,
        evidence_b: str,
    ) -> ContradictionResult:

        if not evidence_a.strip():
            raise ValueError("evidence_a cannot be empty")

        if not evidence_b.strip():
            raise ValueError("evidence_b cannot be empty")

        prompt = f"""
You are a strict evidence contradiction analyzer.

Determine the relationship between Evidence A and Evidence B.

IMPORTANT:
- Do not assume two different statements contradict each other automatically.
- Check subject, scope, conditions, time, population, metric, and other context.
- If they discuss different non-conflicting facts, they do not contradict.
- If the conditions or contexts are different (e.g. short queries vs long queries), use CONTEXTUAL_DIFFERENCE.
- A CONTRADICTION exists when the two statements make mutually exclusive claims about the exact same context.
- If two statements provide different numbers or metrics for the exact same thing (e.g., 94% vs 87% accuracy on the exact same dataset), this is a CONTRADICTION.
- If the evidence is insufficient to determine the relationship, use UNCERTAIN.
- Do not use outside knowledge.

Allowed labels:
NO_CONTRADICTION
CONTEXTUAL_DIFFERENCE
CONTRADICTION
UNCERTAIN

Examples:

Evidence A: "The system achieved 94% accuracy."
Evidence B: "The system achieved 87% accuracy."
{{
  "label": "CONTRADICTION",
  "rationale": "Different metrics for the exact same context."
}}

Evidence A: "BM25 performs better for short queries."
Evidence B: "Dense retrieval performs better for long queries."
{{
  "label": "CONTEXTUAL_DIFFERENCE",
  "rationale": "Different conditions (short vs long queries)."
}}

Evidence A: "The system uses BM25."
Evidence B: "The system uses dense embeddings."
{{
  "label": "NO_CONTRADICTION",
  "rationale": "Compatible non-conflicting facts."
}}

Evidence A: "The model performed better."
Evidence B: "The model performed worse."
{{
  "label": "UNCERTAIN",
  "rationale": "Insufficient context to know if they discuss the same metric or dataset."
}}

Return ONLY valid JSON with exactly these fields:

{{
  "label": "NO_CONTRADICTION | CONTEXTUAL_DIFFERENCE | CONTRADICTION | UNCERTAIN",
  "rationale": "brief explanation"
}}

Evidence A:
{evidence_a}

Evidence B:
{evidence_b}
"""

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

        content = response["message"]["content"].strip()

        # Simple json extraction fallback (we did this in earlier steps but the user prompt doesn't specify it)
        # Actually I will just use what the user provided, if it fails I'll add the brace fallback.
        import json

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            # Let's add a basic extraction just in case since local models hallucinate markdown
            try:
                import re
                json_match = re.search(r"\{.*?\}", content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    raise ValueError(f"Invalid contradiction-classifier JSON: {content}") from exc
            except Exception:
                raise ValueError(
                    f"Invalid contradiction-classifier JSON: {content}"
                ) from exc

        label = ContradictionLabel(data["label"])

        confidence = self.LABEL_SCORES[label]

        return ContradictionResult(
            evidence_a=evidence_a,
            evidence_b=evidence_b,
            label=label,
            confidence=confidence,
            rationale=data["rationale"],
        )
