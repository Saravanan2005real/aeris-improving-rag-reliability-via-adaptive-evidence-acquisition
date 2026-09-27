import json
import os
import re
from typing import List

import ollama
from app.config import settings
from app.claim_extraction.schemas import ExtractedClaim, TypedClaim, ClaimType

class ClaimTyper:
    """Classifies extracted claims into specific semantic/factual roles."""

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

    def type_claims(self, claims: List[ExtractedClaim]) -> List[TypedClaim]:
        """
        Takes a list of ExtractedClaims and returns them as TypedClaims 
        without altering their content or provenance.
        """
        if not claims:
            return []
            
        claims_dict = {
            claim.claim_id: claim.text for claim in claims
        }
        
        prompt = (
            "You are an expert taxonomy classifier for a research-grade RAG system.\n"
            "Your task is to classify each provided claim into EXACTLY ONE of the "
            "following categories:\n\n"
            "- FACT: A general statement of fact.\n"
            "- METHOD: A procedure, process, strategy, or system behavior.\n"
            "- COMPONENT: A specific model, dataset, module, or piece of architecture.\n"
            "- RELATIONSHIP: How two entities or concepts interact.\n"
            "- QUANTITATIVE: A claim containing specific numerical values or metrics.\n"
            "- COMPARATIVE: A claim comparing two or more entities/methods (e.g. 'improves over X').\n"
            "- CAUSAL: A claim stating cause and effect.\n"
            "- DEFINITION: The meaning of a term or concept.\n"
            "- OTHER: Use this ONLY as a fallback if no other category fits.\n\n"
            
            "RULES:\n"
            "1. DO NOT change the text, claim_id, or meaning of the claims.\n"
            "2. Output strictly a JSON object where keys are the claim IDs and values are the category names (in uppercase).\n"
            "3. Ensure every claim_id provided in the input is present in the output.\n\n"
            
            f"CLAIMS TO CLASSIFY:\n{json.dumps(claims_dict, indent=2)}"
        )
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0.0}
            )
            
            result_str = response["message"]["content"]
            json_text = self._extract_json(result_str)
            typing_results = json.loads(json_text)
            
            typed_claims = []
            for claim in claims:
                claim_type_str = typing_results.get(claim.claim_id, "OTHER").upper()
                try:
                    claim_type = ClaimType(claim_type_str)
                except ValueError:
                    claim_type = ClaimType.OTHER
                    
                typed_claims.append(
                    TypedClaim(
                        claim_id=claim.claim_id,
                        text=claim.text,
                        source_chunk_id=claim.source_chunk_id,
                        document_id=claim.document_id,
                        claim_type=claim_type
                    )
                )
                
            return typed_claims
        except Exception as e:
            print(f"Error during claim typing: {e}")
            # Fallback: return everything as OTHER
            return [
                TypedClaim(
                    claim_id=c.claim_id,
                    text=c.text,
                    source_chunk_id=c.source_chunk_id,
                    document_id=c.document_id,
                    claim_type=ClaimType.OTHER
                )
                for c in claims
            ]
