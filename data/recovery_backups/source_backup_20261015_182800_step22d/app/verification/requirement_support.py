import json
import os
from pydantic import BaseModel
import ollama
from app.config import settings
from app.utils.json_parser import extract_json

class RequirementSupportResult(BaseModel):
    is_supported: bool
    rationale: str

class RequirementSupportValidator:
    """
    Validates whether the generated answer and its supporting claims actually satisfy
    the user's original information requirement.
    """
    def __init__(self, model: str = None, host: str = None):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.client = ollama.Client(host=self.host)

    def validate(self, question: str, requirement: str, answer: str, claims: list[str]) -> RequirementSupportResult:
        if not claims:
            return RequirementSupportResult(is_supported=False, rationale="No supporting claims provided.")
            
        claims_text = "\n".join([f"- {c}" for c in claims])
        
        prompt = f"""
You are a strict semantic evaluator.

Determine if the provided CLAIMS actually contain the factual information requested by the REQUIREMENT.

REQUIREMENT:
{requirement}

CLAIMS EXTRACTED FROM EVIDENCE:
{claims_text}

RULES:
1. The CLAIMS must directly provide the information asked for by the REQUIREMENT.
2. If the CLAIMS only discuss the general topic, but do not contain the specific facts to fulfill the requirement, it is NOT SUPPORTED.
3. Ignore minor differences in phrasing. Focus on factual fulfillment.

Evaluate strictly.

Respond ONLY with valid JSON in this format:
{{
  "is_supported": true/false,
  "rationale": "Brief explanation of why the claims do or do not fulfill the requirement."
}}
"""
        messages = [{"role": "user", "content": prompt.strip()}]
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.0, "num_predict": 256}
            )
            raw = response["message"]["content"]
            data = json.loads(extract_json(raw))
            return RequirementSupportResult(
                is_supported=data.get("is_supported", False),
                rationale=data.get("rationale", "No rationale provided.")
            )
        except Exception as e:
            # On failure, be conservative
            return RequirementSupportResult(
                is_supported=False, 
                rationale=f"Validation failed: {str(e)}"
            )
