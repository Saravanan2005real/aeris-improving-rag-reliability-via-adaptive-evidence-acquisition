import json
import os
import re
import time
from typing import List

import ollama
from app.config import settings
from app.claim_extraction.schemas import ExtractedClaim, TypedClaim, ClaimType
from app.utils.json_parser import extract_json
from app.utils.model_client import get_ollama_client, timed_model_chat

class ClaimTyper:
    """Classifies extracted claims into specific semantic/factual roles."""

    def __init__(self, model: str = None, host: str = None, timeout: float = None):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.timeout = timeout or settings.ollama_timeout
        self.client = get_ollama_client(host=self.host, timeout=self.timeout)

    def type_claims(self, claims: List[ExtractedClaim]) -> List[TypedClaim]:
        """
        Takes a list of ExtractedClaims and returns them as TypedClaims 
        without altering their content or provenance.
        Uses deterministic batching and Python-owned numerical indices to prevent
        the LLM from hallucinating claim identities.
        """
        if not claims:
            return []
            
        typed_claims_result = []
        batch_size = 10
        
        from app.utils.diagnostics import log_generation_attempt
        import json as std_json
        
        for i in range(0, len(claims), batch_size):
            batch = claims[i : i + batch_size]
            
            # Create a deterministic mapping from local index to the original claim
            index_to_claim = {idx: claim for idx, claim in enumerate(batch)}
            
            # Prepare the LLM input
            input_payload = [
                {"index": idx, "claim_text": claim.text}
                for idx, claim in index_to_claim.items()
            ]
            
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
                "1. Output strictly a JSON array of objects, each containing 'index' and 'claim_type'.\n"
                "2. Ensure every index provided in the input is present in the output exactly once.\n"
                "3. Respond ONLY with valid JSON. Do not include markdown blocks, preamble, or explanation.\n"
                "4. Start your response exactly with [ and end exactly with ].\n"
                "5. Do NOT include any original text or chunk IDs in your response.\n\n"
                
                f"CLAIMS TO CLASSIFY:\n{std_json.dumps(input_payload, indent=2)}"
            )
            
            messages = [{"role": "user", "content": prompt}]
            max_attempts = 3
            
            
            for attempt in range(1, max_attempts + 1):
                batch_typed_claims = []
                parse_success = False
                schema_success = False
                repair_invoked = False
                retry_invoked = (attempt > 1)
                
                try:
                    chat_res = timed_model_chat(
                        client=self.client,
                        model=self.model,
                        messages=messages,
                        options={
                            "temperature": 0.0,
                            "num_predict": 8192,
                        },
                        stage="Claim Typing",
                    )
                    elapsed = chat_res["elapsed_seconds"]
                    result_str = chat_res["content"]
                except Exception as e:
                    elapsed = 0.0
                    ctx_size = len(messages[-1]["content"])
                    print(f"Error during claim typing [Model: {self.model}, Stage: typing, Context: {ctx_size} chars]: {e}")
                    raise e
    
                ctx_size = len(messages[-1]["content"])
    
                try:
                    try:
                        std_json.loads(result_str)
                    except:
                        repair_invoked = True
                        
                    json_text = extract_json(result_str)
                    parse_success = True
                    typing_results = std_json.loads(json_text)
                    
                    # Unwrap dictionary wrappers e.g. {"claims": [...]}
                    if isinstance(typing_results, dict):
                        for k in ("claims", "results", "typed_claims", "data", "classifications"):
                            if k in typing_results and isinstance(typing_results[k], list):
                                typing_results = typing_results[k]
                                break

                    # Flatten any single-level nested list e.g. [[{...}]]
                    if isinstance(typing_results, list) and len(typing_results) > 0 and isinstance(typing_results[0], list):
                        flat = []
                        for sublist in typing_results:
                            if isinstance(sublist, list):
                                flat.extend(sublist)
                            else:
                                flat.append(sublist)
                        typing_results = flat

                    if not isinstance(typing_results, list):
                        raise ValueError("Output must be a JSON array of objects.")
                        
                    returned_indexes = []
                    parsed_results = {}
                    
                    for i, item in enumerate(typing_results):
                        if not isinstance(item, dict):
                            if isinstance(item, str):
                                import re
                                match = re.search(r"(\d+)\s*[:\-]\s*([A-Za-z_]+)", item)
                                if match:
                                    item = {"index": int(match.group(1)), "claim_type": match.group(2)}
                                else:
                                    item = {"index": i, "claim_type": item.strip()}
                            else:
                                raise ValueError("Each item in the JSON array must be an object.")
                        if "index" not in item or "claim_type" not in item:
                            raise ValueError("Each object must contain 'index' and 'claim_type'.")
                        
                        idx = int(item["index"])
                        returned_indexes.append(idx)
                        parsed_results[idx] = item["claim_type"]
                        
                    expected_indexes = set(index_to_claim.keys())
                    returned_set = set(returned_indexes)
                    
                    if len(returned_indexes) != len(returned_set):
                        raise ValueError("Duplicate indexes found in the response.")
                        
                    missing_indexes = expected_indexes - returned_set
                    unknown_indexes = returned_set - expected_indexes
                    
                    if missing_indexes or unknown_indexes:
                        error_details = []
                        if missing_indexes:
                            error_details.append(f"Missing required indexes: {list(missing_indexes)}")
                        if unknown_indexes:
                            error_details.append(f"Unknown indexes returned (not in input): {list(unknown_indexes)}")
                        raise ValueError(" | ".join(error_details))
    
                    if len(parsed_results) != len(expected_indexes):
                        raise ValueError(f"Number of returned classifications ({len(parsed_results)}) must exactly match input ({len(expected_indexes)}).")
    
                    schema_success = True
                    
                    # Demo-era engineering fix: narrowly scoped normalization alias mapping
                    # Maps LLM-emitted 'COMPARE' to canonical ClaimType.COMPARATIVE while preserving strict validation
                    CLAIM_TYPE_ALIASES = {
                        "COMPARE": ClaimType.COMPARATIVE.value,
                    }

                    for idx, claim in index_to_claim.items():
                        claim_type_raw = str(parsed_results[idx]).upper().strip()
                        claim_type_str = CLAIM_TYPE_ALIASES.get(claim_type_raw, claim_type_raw)
                        try:
                            claim_type = ClaimType(claim_type_str)
                        except ValueError:
                            raise ValueError(f"Invalid claim type '{claim_type_raw}' for index {idx}.")
                            
                        batch_typed_claims.append(
                            TypedClaim(
                                claim_id=claim.claim_id,
                                text=claim.text,
                                source_chunk_id=claim.source_chunk_id,
                                document_id=claim.document_id,
                                claim_type=claim_type
                            )
                        )
                        
                    log_generation_attempt("Claim Typing", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                    break # Batch successful
                    
                except Exception as e:
                    log_generation_attempt("Claim Typing", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                    CLAIM_TYPE_ALIASES = {
                        "COMPARE": ClaimType.COMPARATIVE.value,
                    }
                    if attempt == max_attempts:
                        # Resilient fallback: instead of crashing the entire pipeline with an unhandled exception,
                        # populate any missing or unparsed claims with ClaimType.FACT
                        import logging
                        logging.getLogger("app.claim_extraction.typer").warning(
                            f"Claim typing attempt {attempt} failed with {e}; applying fallback FACT classification."
                        )
                        batch_typed_claims.clear()
                        for idx, claim in index_to_claim.items():
                            ctype_val = parsed_results.get(idx, ClaimType.FACT.value)
                            ctype_raw = str(ctype_val).upper().strip()
                            ctype_str = CLAIM_TYPE_ALIASES.get(ctype_raw, ctype_raw)
                            try:
                                claim_type = ClaimType(ctype_str)
                            except ValueError:
                                claim_type = ClaimType.FACT
                            batch_typed_claims.append(
                                TypedClaim(
                                    claim_id=claim.claim_id,
                                    text=claim.text,
                                    source_chunk_id=claim.source_chunk_id,
                                    document_id=claim.document_id,
                                    claim_type=claim_type
                                )
                            )
                        break
                        
                    messages.append({"role": "assistant", "content": result_str})
                    if "Missing required indexes" in str(e) or "Unknown indexes" in str(e):
                        error_msg = f"Your previous response failed validation: {str(e)}.\n\nReturn exactly one classification for every required index. Valid indexes are {list(expected_indexes)}. Do not omit or invent indexes."
                    else:
                        error_msg = f"Your previous response failed validation with error: {str(e)}. Please correct the JSON structure to strictly be a JSON array of objects with 'index' and 'claim_type'."
                    messages.append({"role": "user", "content": error_msg})
                    
            typed_claims_result.extend(batch_typed_claims)
            
        return typed_claims_result
