from enum import Enum

from pydantic import BaseModel, Field
from ollama import Client


class CrossLingualAgreementLabel(str, Enum):
    AGREEMENT = "AGREEMENT"
    CONTRADICTION = "CONTRADICTION"
    CONTEXTUAL_DIFFERENCE = "CONTEXTUAL_DIFFERENCE"
    UNCERTAIN = "UNCERTAIN"


class CrossLingualAgreementResult(BaseModel):
    evidence_a: str
    evidence_b: str

    language_a: str
    language_b: str

    label: CrossLingualAgreementLabel
    confidence: float = Field(ge=0.0, le=1.0)

    rationale: str


class CrossLingualEvidenceClassifier:
    """
    Classifies whether two pieces of evidence written in
    different languages express the same factual information.

    The classifier must reason about meaning, not surface-level
    lexical similarity.

    Translation-equivalent evidence is not automatically treated
    as factual agreement if the underlying claims differ.
    """

    CONFIDENCE_SCORES = {
        CrossLingualAgreementLabel.AGREEMENT: 0.90,
        CrossLingualAgreementLabel.CONTRADICTION: 0.90,
        CrossLingualAgreementLabel.CONTEXTUAL_DIFFERENCE: 0.80,
        CrossLingualAgreementLabel.UNCERTAIN: 0.35,
    }

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "llama3.2:latest",
    ):
        self.client = Client(host=host)
        self.model = model

    def classify(
        self,
        evidence_a: str,
        evidence_b: str,
        language_a: str,
        language_b: str,
    ) -> CrossLingualAgreementResult:

        if not evidence_a or not evidence_a.strip():
            raise ValueError("evidence_a cannot be empty")

        if not evidence_b or not evidence_b.strip():
            raise ValueError("evidence_b cannot be empty")

        if not language_a or not language_a.strip():
            raise ValueError("language_a cannot be empty")

        if not language_b or not language_b.strip():
            raise ValueError("language_b cannot be empty")

        prompt = f"""
You are a strict cross-lingual evidence consistency classifier.

Compare two evidence passages written in different languages.

Classify the relationship using exactly one label:

AGREEMENT
CONTRADICTION
CONTEXTUAL_DIFFERENCE
UNCERTAIN

Definitions:

AGREEMENT:
Both passages express the same factual proposition or compatible
factual information, even if the wording and languages differ.

CONTRADICTION:
Both passages concern substantially the same subject and context,
but assert incompatible factual information.

CONTEXTUAL_DIFFERENCE:
The passages differ because of scope, condition, population,
time, metric, or another contextual distinction. They should not
be treated as direct contradiction.

UNCERTAIN:
The relationship cannot be established reliably from the
provided passages alone.

Important rules:

1. Compare meaning, not words.
2. Do not use outside knowledge.
3. Do not assume that similar words imply factual agreement.
4. Do not assume that different wording implies contradiction.
5. Preserve numerical values, dates, quantities, names, and conditions.
6. A translation-equivalent statement should normally be AGREEMENT.
7. If one passage changes an important condition, use
   CONTEXTUAL_DIFFERENCE.
8. If evidence is insufficient, use UNCERTAIN.

Return JSON only!

Example 1 (AGREEMENT):
Evidence A (English): "AERIS uses hybrid retrieval combining dense retrieval and BM25."
Evidence B (Tamil): "AERIS அடர்த்தியான மீட்டெடுப்பு மற்றும் BM25 ஐ இணைத்து கலப்பு மீட்டெடுப்பைப் பயன்படுத்துகிறது."
Output:
{{
  "label": "AGREEMENT",
  "rationale": "Both describe AERIS using hybrid retrieval with dense retrieval and BM25."
}}

Example 2 (CONTRADICTION):
Evidence A (English): "The experiment achieved 91 percent recall using hybrid retrieval."
Evidence B (Tamil): "கலப்பு மீட்டெடுப்பைப் பயன்படுத்திய சோதனையில் மீட்டெடுப்பு விகிதம் 76 சதவீதமாக இருந்தது."
Output:
{{
  "label": "CONTRADICTION",
  "rationale": "One says 91% recall, the other says 76% recall for the same setup."
}}

Example 3 (CONTEXTUAL_DIFFERENCE):
Evidence A (English): "For short queries, the retrieval system achieved 92 percent recall."
Evidence B (Tamil): "நீண்ட வினவல்களுக்கு, மீட்டெடுப்பு அமைப்பு 85 சதவீத மீட்டெடுப்பை அடைந்தது."
Output:
{{
  "label": "CONTEXTUAL_DIFFERENCE",
  "rationale": "Different conditions: short queries vs long queries."
}}

Example 4 (UNCERTAIN):
Evidence A (English): "The system performed well."
Evidence B (Tamil): "அமைப்பு நன்றாக இருந்தது."
Output:
{{
  "label": "UNCERTAIN",
  "rationale": "Too vague to definitively establish agreement on specific facts."
}}

Now analyze the following:

Evidence A language:
{language_a}

Evidence A:
{evidence_a}

Evidence B language:
{language_b}

Evidence B:
{evidence_b}
"""

        response = self.client.chat(
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
            format="json",
        )

        data = response["message"]["content"]

        import json

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            import re
            match = re.search(r'{{.*}}', data, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                raise

        label = CrossLingualAgreementLabel(
            parsed["label"]
        )

        confidence = self.CONFIDENCE_SCORES[label]

        return CrossLingualAgreementResult(
            evidence_a=evidence_a,
            evidence_b=evidence_b,
            language_a=language_a,
            language_b=language_b,
            label=label,
            confidence=confidence,
            rationale=parsed["rationale"],
        )
