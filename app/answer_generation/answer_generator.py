import json
import time
import ollama
from typing import Dict, List, Any

from app.config import settings
from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.verification.graph_verifier import GraphVerificationResult
from app.verification.cross_claim_contradiction import CrossClaimContradictionReport
from app.verification.contradiction_classifier import ContradictionLabel
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
        all_chunks = {}

        # First, ensure all evidence chunks in the graph are indexed
        if hasattr(graph, "evidence") and isinstance(graph.evidence, dict):
            for chunk_id, chunk in graph.evidence.items():
                all_chunks[chunk_id] = chunk

        # Format chunks first
        chunks_section = ["--- RETRIEVED DOCUMENT CHUNKS ---"]
        for chunk_id, chunk in all_chunks.items():
            pages = getattr(chunk, 'pages', 'Unknown')
            chunks_section.append(f"Chunk ({chunk_id}) [Pages: {pages}]:\n{chunk.text}\n")

        # Rank and select relevant claims
        import re
        q_words = set(re.findall(r"\b\w{3,}\b", question.lower()))
        
        scored_claims = []
        for claim_id, claim in graph.claims.items():
            edges = graph.get_claim_evidence(claim_id)
            claim_chunks = []
            for edge in edges:
                chunk = graph.evidence.get(edge.chunk_id)
                if chunk:
                    all_chunks[chunk.chunk_id] = chunk
                    claim_chunks.append(chunk.chunk_id)

            src_cid = getattr(claim, "source_chunk_id", None)
            if src_cid and src_cid in graph.evidence and src_cid not in claim_chunks:
                claim_chunks.append(src_cid)
                all_chunks[src_cid] = graph.evidence[src_cid]

            if not claim_chunks:
                continue

            # Check verification
            verified_info = ""
            for v in verification_results:
                if v.claim_id == claim_id:
                    verified_info = f"[Status: {v.label.value}, Confidence: {v.verification_confidence:.2f}]"
                    break

            # Calculate relevance score for the claim against question
            claim_words = set(re.findall(r"\b\w{3,}\b", claim.text.lower()))
            overlap = len(q_words.intersection(claim_words))
            
            # Boost front matter and author claims if question asks about authors
            is_author_q = any(w in q_words for w in ("author", "authors", "who", "affiliation", "affiliated", "name", "title"))
            author_boost = 5 if (is_author_q and any(w in claim_words for w in ("author", "authors", "affiliated", "affiliation", "wrote", "written", "title", "paper", "institute", "department", "dept"))) else 0

            score = overlap * 2 + author_boost
            entry_str = f"Claim ({claim_id}): {claim.text} {verified_info}\nSupporting Chunks: {', '.join(claim_chunks)}"
            scored_claims.append((score, claim_id, entry_str))

        # Sort claims by score descending, cap at top 30
        scored_claims.sort(key=lambda x: x[0], reverse=True)
        top_claims = scored_claims[:30]

        claims_section = ["--- EXTRACTED FACTUAL CLAIMS ---"]
        for _, _, c_str in top_claims:
            claims_section.append(c_str)

        context_str = "\n".join(chunks_section) + "\n\n" + "\n".join(claims_section)

        contradictions_str = "None"
        if contradiction_report and contradiction_report.conflicts:
            actual_conflicts = [
                c for c in contradiction_report.conflicts
                if getattr(c, "label", None) in (ContradictionLabel.CONTRADICTION, "CONTRADICTION")
                or getattr(getattr(c, "label", None), "value", None) == "CONTRADICTION"
            ]
            if actual_conflicts:
                contradictions = []
                for c in actual_conflicts[:5]:
                    rat = (c.rationale[:250] + "...") if len(c.rationale) > 250 else c.rationale
                    contradictions.append(f"Conflict between Claim {c.claim_a_id} and Claim {c.claim_b_id}: {rat}")
                contradictions_str = "\n".join(contradictions)

        prompt = f"""You are a strict grounded answer generator for AERIS-RAG.

DOCUMENT EVIDENCE:
{context_str}

CONTRADICTIONS FOUND:
{contradictions_str}

TARGET QUESTION TO ANSWER:
{question}

RULES:
- You MUST answer the exact TARGET QUESTION provided: "{question}". Do NOT answer or invent any other question.
- Answer ONLY from the provided DOCUMENT EVIDENCE.
- Do NOT use outside knowledge or world knowledge.
- Do NOT invent or infer unsupported facts.
- In academic document metadata and author lists, authors and affiliations are listed in numerical order (1st, 2nd, 3rd, 4th, 5th, etc.). The "first author" or "1st author" is the person designated with "1st" or "first author" (e.g., "1st Saravanan Sathishkumar"). Pay close attention to the word "first" (1st) versus "fifth" (5th). Do not confuse "first" with "fifth" or other authors.
- Answer factual and metadata questions (such as authors, affiliations, titles, institutions, scores, and definitions) directly from the evidence text and extracted claims. If the question asks for the first author, extract the name associated with "1st" / "first author", state it clearly, cite the supporting chunk and claim, and set status to "SUPPORTED".
- If the evidence contains the answer to "{question}", answer it directly, cite the supporting chunks and claims, and set status to "SUPPORTED".
- If the evidence does not contain the answer to "{question}", you MUST set status to "INSUFFICIENT_EVIDENCE" and state that the document does not provide enough information. Do not guess or use outside knowledge.
- If evidence conflicts, explicitly mention the conflict rather than silently choosing one claim, and set status to "CONFLICTED".
- Prefer verified claims with high confidence. Preserve uncertainty when evidence is weak.
- Provide a concise answer. Do not expose internal reasoning or chain of thought in the final answer.
- In "supporting_chunk_ids" and "supporting_claim_ids", cite the chunk ID (e.g. "{list(all_chunks.keys())[0] if all_chunks else 'chunk_id'}") and claim IDs.
- Respond ONLY with valid JSON. Do not include markdown blocks, preamble, or explanation outside the JSON.
- Start your response exactly with {{ and end exactly with }}.

OUTPUT FORMAT:
{{
  "is_answerable_from_evidence": true/false,
  "answer": "Your grounded natural-language answer to '{question}', or a statement that the document lacks sufficient information.",
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
                print(f"DEBUG ANSWER GENERATOR RAW_CONTENT:\n{raw_content}")
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
                print(f"DEBUG ANSWER GENERATOR PARSED DATA:\n{data}")
                print(f"DEBUG ALL_CHUNKS_KEYS: {list(all_chunks.keys())}")
                print(f"DEBUG GRAPH CLAIMS COUNT: {len(graph.claims)}")
                
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
                    
                # Support exact matching as well as substring/partial chunk_id matching
                resolved_chunks = []
                chunk_keys = list(all_chunks.keys())
                for cid in supporting_chunks:
                    cid_str = str(cid).strip()
                    clean_c = cid_str.replace("Chunk", "").replace("chunk", "").strip("() :_-\t\n\"'")
                    if cid_str in all_chunks:
                        resolved_chunks.append(cid_str)
                    elif clean_c in all_chunks:
                        resolved_chunks.append(clean_c)
                    elif clean_c.isdigit() and 1 <= int(clean_c) <= len(chunk_keys):
                        resolved_chunks.append(chunk_keys[int(clean_c) - 1])
                    else:
                        for real_cid in chunk_keys:
                            if clean_c and (clean_c == real_cid or f"c{clean_c.zfill(3)}" in real_cid or real_cid.endswith(clean_c) or clean_c in real_cid):
                                resolved_chunks.append(real_cid)
                                break
                valid_chunk_ids = deduplicate(resolved_chunks)
                
                resolved_claims = []
                for cid in supporting_claims:
                    cid_str = str(cid).strip()
                    clean_c = cid_str.replace("Claim", "").replace("claim", "").strip("() :_-\t\n\"'")
                    if cid_str in graph.claims:
                        resolved_claims.append(cid_str)
                    elif clean_c in graph.claims:
                        resolved_claims.append(clean_c)
                    else:
                        for real_cid in graph.claims:
                            if clean_c in real_cid or real_cid in clean_c or real_cid.endswith(clean_c):
                                resolved_claims.append(real_cid)
                                break
                valid_claim_ids = deduplicate(resolved_claims)

                # If generator cited claims but omitted chunks, resolve chunks from claims
                if not valid_chunk_ids and valid_claim_ids:
                    valid_chunk_ids = deduplicate([
                        getattr(graph.claims[c_id], "source_chunk_id", None)
                        or next((e.chunk_id for e in graph.get_claim_evidence(c_id)), None)
                        for c_id in valid_claim_ids
                        if c_id in graph.claims
                    ])
                    valid_chunk_ids = [cid for cid in valid_chunk_ids if cid and cid in all_chunks]

                # If the generator cited valid evidence chunks but omitted explicit claim IDs,
                # attribute the relevant claims associated with those chunks
                if not valid_claim_ids and valid_chunk_ids:
                    valid_claim_ids = [
                        c_id for c_id, c in graph.claims.items()
                        if getattr(c, "source_chunk_id", None) in valid_chunk_ids
                        or any(e.chunk_id in valid_chunk_ids for e in graph.get_claim_evidence(c_id))
                    ]

                data["supporting_chunk_ids"] = valid_chunk_ids
                data["supporting_claim_ids"] = valid_claim_ids

                is_answerable = data.get("is_answerable_from_evidence", True)

                if status in ["SUPPORTED", "PARTIALLY_SUPPORTED", "COMPLETED"] and not valid_chunk_ids:
                    status = "INSUFFICIENT_EVIDENCE"
                    data["answer"] = "The document does not provide enough information to answer this question."
                    data["confidence"] = 0.0
                    data["insufficiency_reason"] = "Model provided unsupported or hallucinatory provenance."
                    data["supporting_claim_ids"] = []
                    is_answerable = False
                elif status == "INSUFFICIENT_EVIDENCE":
                    data["answer"] = "The document does not provide enough information to answer this question."
                    data["confidence"] = 0.0
                    if not data.get("insufficiency_reason"):
                        data["insufficiency_reason"] = "The retrieved document evidence does not provide sufficient support to answer this question."
                    data["supporting_claim_ids"] = []
                    is_answerable = False
        
                # Build provenance
                provenance = []
                for chunk_id in valid_chunk_ids:
                    chunk = all_chunks.get(chunk_id)
                    if chunk:
                        rel_claims = [
                            c_id for c_id in data.get("supporting_claim_ids", []) 
                            if getattr(graph.claims.get(c_id), "source_chunk_id", None) == chunk_id
                            or any(e.chunk_id == chunk_id for e in graph.get_claim_evidence(c_id))
                        ]
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
