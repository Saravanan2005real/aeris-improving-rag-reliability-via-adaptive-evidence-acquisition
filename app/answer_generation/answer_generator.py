import json
import ollama
from typing import Dict, List, Any

from app.config import settings
from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.verification.graph_verifier import GraphVerificationResult
from app.verification.cross_claim_contradiction import CrossClaimContradictionReport
from app.answer_generation.schemas import GroundedAnswer, AnswerStatus, ProvenanceItem

class AnswerGenerator:
    def __init__(self, model: str = None, host: str = None):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.client = ollama.Client(host=self.host)

    def _extract_json(self, text: str) -> str:
        print(f"RAW MODEL OUTPUT:\n{text}\n")
        text = text.strip()
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
            
        return text

    def generate(
        self,
        question: str,
        graph: ClaimEvidenceGraphBuilder,
        verification_results: List[GraphVerificationResult],
        contradiction_report: CrossClaimContradictionReport = None
    ) -> GroundedAnswer:
        
        # Prepare evidence context
        evidence_context = []
        all_chunks = {}
        for claim_id, claim in graph.claims.items():
            edges = graph.get_claim_evidence(claim_id)
            if not edges:
                continue
            
            # Check verification
            verified_info = ""
            for v in verification_results:
                if v.claim_id == claim_id:
                    verified_info = f"[Status: {v.label.value}, Confidence: {v.verification_confidence:.2f}]"
                    break
            
            claim_chunks = []
            for edge in edges:
                chunk = graph.evidence.get(edge.chunk_id)
                if chunk:
                    all_chunks[chunk.chunk_id] = chunk
                    claim_chunks.append(chunk.chunk_id)
            
            evidence_context.append(f"Claim ({claim_id}): {claim.text} {verified_info}\nSupporting Chunks: {', '.join(claim_chunks)}")
            
        for chunk_id, chunk in all_chunks.items():
            pages = getattr(chunk, 'pages', 'Unknown')
            evidence_context.append(f"\nChunk ({chunk_id}) [Pages: {pages}]:\n{chunk.text}")
            
        context_str = "\n".join(evidence_context)
        
        contradictions_str = "None"
        if contradiction_report and contradiction_report.conflicts:
            contradictions = []
            for c in contradiction_report.conflicts:
                contradictions.append(f"Conflict between Claim {c.claim_a_id} and Claim {c.claim_b_id}: {c.rationale}")
            contradictions_str = "\n".join(contradictions)

        prompt = f"""
You are a strict grounded answer generator for AERIS-RAG.

QUESTION:
{question}

DOCUMENT EVIDENCE:
{context_str}

CONTRADICTIONS FOUND:
{contradictions_str}

RULES:
- Answer ONLY from the provided DOCUMENT EVIDENCE.
- Do NOT use outside knowledge or world knowledge.
- Do NOT invent or infer unsupported facts.
- If the evidence does not contain the answer to the question, you MUST set status to "INSUFFICIENT_EVIDENCE" and state that the document does not provide enough information. Do not guess or use outside knowledge.
- If evidence conflicts, explicitly mention the conflict rather than silently choosing one claim, and set status to "CONFLICTED".
- Prefer verified claims with high confidence. Preserve uncertainty when evidence is weak.
- Provide a concise answer. Do not expose internal reasoning or chain of thought in the final answer.
- Always output your response in JSON format exactly matching the structure below.

OUTPUT FORMAT:
{{
  "is_answerable_from_evidence": true/false,
  "answer": "Your grounded natural-language answer here, or a statement that the document lacks sufficient information.",
  "status": "SUPPORTED|PARTIALLY_SUPPORTED|INSUFFICIENT_EVIDENCE|CONFLICTED",
  "confidence": 0.0,
  "supporting_claim_ids": ["claim_id_1", "claim_id_2"],
  "supporting_chunk_ids": ["chunk_id_1", "chunk_id_2"],
  "conflict_information": "Brief description of conflict if applicable, else null",
  "insufficiency_reason": "Brief reason if insufficient, else null"
}}
"""
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        raw_content = response["message"]["content"]
        json_text = self._extract_json(raw_content)
        data = json.loads(json_text)
        
        # Post-generation guardrail against hallucinations
        status = data.get("status", "INSUFFICIENT_EVIDENCE")
        supporting_chunks = data.get("supporting_chunk_ids", [])
        
        if status in ["SUPPORTED", "PARTIALLY_SUPPORTED"] and not supporting_chunks:
            status = "INSUFFICIENT_EVIDENCE"
            data["answer"] = "The document does not provide enough information to answer this question."
            data["confidence"] = 0.0

        # Build provenance
        provenance = []
        for chunk_id in supporting_chunks:
            chunk = all_chunks.get(chunk_id)
            if chunk:
                rel_claims = [c_id for c_id in data.get("supporting_claim_ids", []) 
                              if any(e.chunk_id == chunk_id for e in graph.get_claim_evidence(c_id))]
                provenance.append(ProvenanceItem(
                    document_id=chunk.document_id,
                    chunk_id=chunk_id,
                    pages=getattr(chunk, 'pages', []),
                    relevant_claim_ids=rel_claims
                ))

        return GroundedAnswer(
            question=question,
            answer=data.get("answer", ""),
            status=AnswerStatus(status),
            confidence=data.get("confidence", 0.0),
            supporting_claim_ids=data.get("supporting_claim_ids", []),
            supporting_chunk_ids=data.get("supporting_chunk_ids", []),
            provenance=provenance,
            conflict_information=data.get("conflict_information"),
            insufficiency_reason=data.get("insufficiency_reason")
        )
