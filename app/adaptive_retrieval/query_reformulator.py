import json
import re
from typing import List, Optional

import ollama

from app.config import settings
from app.planning.schemas import InformationRequirement

class QueryReformulator:
    """
    Generates alternative search queries when initial retrieval fails.
    """
    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None,
    ):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.client = ollama.Client(host=self.host)

    def _build_prompt(
        self,
        question: str,
        requirement: InformationRequirement,
        original_query: str,
        max_variants: int,
    ) -> str:
        return f"""
You are a retrieval query reformulator for AERIS-RAG.

The initial retrieval query failed to find sufficient evidence for this information requirement.
Generate {max_variants} alternative search queries to improve retrieval.

==================================================
CONTEXT
==================================================

Original User Question:
{question}

Requirement Description:
{requirement.description}

Requirement Type:
{requirement.requirement_type}

Expected Evidence Type:
{requirement.expected_evidence_type}

Failed Initial Query:
{original_query}

==================================================
RULES
==================================================
1. Preserve the original information need. Do NOT broaden the topic.
2. Generate genuinely different formulations (e.g., using synonyms, different grammatical structures, or more specific terminology likely to appear in the document).
3. Do NOT invent new entities not present in the requirement or question.
4. Do NOT attempt to answer the question.
5. Provide EXACTLY {max_variants} alternative queries.

==================================================
OUTPUT
==================================================
Return ONLY valid JSON. Do not include markdown formatting or explanations.

Use exactly this structure:
{{
  "queries": [
    "alternative query 1",
    "alternative query 2"
  ]
}}
""".strip()

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No valid JSON object found in model response.")
        return text[start:end + 1]

    def reformulate(
        self,
        question: str,
        requirement: InformationRequirement,
        original_query: str,
        max_variants: int = 2,
    ) -> List[str]:
        prompt = self._build_prompt(question, requirement, original_query, max_variants)
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0},
            )
            raw_content = response["message"]["content"]
            json_text = self._extract_json(raw_content)
            data = json.loads(json_text)
            queries = data.get("queries", [])
            if not isinstance(queries, list):
                return []
            return [str(q).strip() for q in queries if str(q).strip()]
        except Exception:
            return []
