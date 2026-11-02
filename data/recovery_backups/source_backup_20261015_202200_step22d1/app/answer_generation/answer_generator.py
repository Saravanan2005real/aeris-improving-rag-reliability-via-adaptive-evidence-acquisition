import json
import time
import ollama
from typing import Dict, List, Any

from app.config import settings
from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.verification.graph_verifier import GraphVerificationResult
from app.verification.cross_claim_contradiction import CrossClaimContradictionReport
from app.answer_generation.schemas import GroundedAnswer, AnswerStatus, ProvenanceItem
from app.utils.json_parser import extract_json
from app.utils.model_client import get_ollama_client, timed_model_chat

class AnswerGenerator:
    def __init__(self, model: str = None, host: str = None, timeout: float = None):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.timeout = timeout or settings.ollama_timeout
        self.client = get_ollama_client(host=self.host, timeout=self.timeout)


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
- Respond ONLY with valid JSON. Do not include markdown blocks, preamble, or explanation outside the JSON.
- Start your response exactly with {{ and end exactly with }}.

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
        from app.utils.diagnostics import log_generation_attempt
        messages = [{"role": "user", "content": prompt}]
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            parse_success = False
            schema_success = False
            repair_invoked = False
            retry_invoked = (attempt > 1)
            
            try:
                chat_res = timed_model_chat(
                    client=self.client,
                    model=self.model,
                    messages=messages,
                    options={"temperature": 0, "num_predict": 1024},
                    stage="Answer Generation",
                )
                raw_content = chat_res["content"]
                elapsed = chat_res["elapsed_seconds"]
            except Exception as e:
                elapsed = 0.0
                ctx_size = len(messages[-1]["content"])
                print(f"Error during answer generation [Model: {self.model}, Stage: generator, Context: {ctx_size} chars]: {e}")
                raise e

            ctx_size = len(messages[-1]["content"])
            
            try:
                import json as std_json
                try:
                    std_json.loads(raw_content)
                except:
                    repair_invoked = True
                    
                json_text = extract_json(raw_content)
                parse_success = True
                data = std_json.loads(json_text)
                
                if "answer" not in data or data["answer"] is None:
                    raise ValueError("The 'answer' field is missing or null.")
                
                if "status" not in data:
                    raise ValueError("The 'status' field is missing.")
                    
                status = data["status"]
                try:
                    AnswerStatus(status)
                except ValueError:
                    raise ValueError(f"Invalid status '{status}'.")
                    
                supporting_chunks = data.get("supporting_chunk_ids", [])
                supporting_claims = data.get("supporting_claim_ids", [])
        
                def deduplicate(seq):
                    seen = set()
                    return [x for x in seq if not (x in seen or seen.add(x))]
                    
                valid_chunk_ids = deduplicate([cid for cid in supporting_chunks if cid in all_chunks])
                valid_claim_ids = deduplicate([cid for cid in supporting_claims if cid in graph.claims])
        
                data["supporting_chunk_ids"] = valid_chunk_ids
                data["supporting_claim_ids"] = valid_claim_ids
                
                is_answerable = data.get("is_answerable_from_evidence", True)
                
                if status in ["SUPPORTED", "PARTIALLY_SUPPORTED", "COMPLETED"] and (not valid_chunk_ids or not valid_claim_ids):
                    status = "INSUFFICIENT_EVIDENCE"
                    
                if status == "INSUFFICIENT_EVIDENCE" or (not valid_chunk_ids or not valid_claim_ids):
                    data["answer"] = "The document does not provide enough information to answer this question."
                    data["confidence"] = 0.0
                    data["insufficiency_reason"] = "Model provided unsupported or hallucinatory provenance."
                    data["supporting_claim_ids"] = []
                    is_answerable = False
        
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
        
                ans = GroundedAnswer(
                    question=question,
                    answer=data.get("answer", ""),
                    status=AnswerStatus(status),
                    is_answerable_from_evidence=is_answerable,
                    confidence=data.get("confidence", 0.0),
                    supporting_claim_ids=data.get("supporting_claim_ids", []),
                    supporting_chunk_ids=data.get("supporting_chunk_ids", []),
                    provenance=provenance,
                    conflict_information=data.get("conflict_information"),
                    insufficiency_reason=data.get("insufficiency_reason")
                )
                
                schema_success = True
                log_generation_attempt("Answer Generation", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                return ans
                
            except Exception as e:
                log_generation_attempt("Answer Generation", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                if attempt == max_attempts:
                    raise e
                    
                messages.append({"role": "assistant", "content": raw_content})
                error_msg = f"Your previous response failed validation with error: {str(e)}. Please correct the JSON structure. Ensure the 'answer' field is a valid string, not null."
                messages.append({"role": "user", "content": error_msg})
