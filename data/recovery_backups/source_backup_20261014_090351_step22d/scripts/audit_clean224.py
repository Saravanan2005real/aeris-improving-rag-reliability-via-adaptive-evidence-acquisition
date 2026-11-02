import json
import os
import numpy as np

def run_audit():
    with open("data/results/clean_full_ablation.json", "r", encoding="utf-8") as f:
        results = json.load(f)
        
    variants = [
        "FULL_AERIS", "NO_ADAPTIVE_RETRIEVAL", "NO_QUERY_REFORMULATION", 
        "NO_RETRIEVAL_MEMORY", "NO_CLAIM_VERIFICATION", "NO_CONTRADICTION_ANALYSIS", 
        "NO_CROSSLINGUAL_AGREEMENT", "NO_SELECTIVE_VERIFICATION"
    ]
    
    questions = sorted(list(set(r["question_id"] for r in results)))
    
    # 1. Dataset Integrity
    experiment_id = results[0]["experiment_id"]
    print("Experiment ID:", experiment_id)
    unique_pairs = set((r["question_id"], r["variant"]) for r in results)
    print("Unique pairs:", len(unique_pairs))
    
    # Check cache sizes
    for v in variants:
        f = f"data/clean_full_ablation_cache_{v}.json"
        if os.path.exists(f):
            with open(f, "r") as cf:
                cache = json.load(cf)
                print(f"Cache {v} keys: {len(cache)}")
        else:
            print(f"Cache {v} not found")

    # 6. Matrix
    matrix = {}
    for r in results:
        v = r["variant"]
        q = r["question_id"]
        if q not in matrix:
            matrix[q] = {}
        matrix[q][v] = r

    with open("data/results/ablation_audit_clean224_matrix.json", "w") as f:
        json.dump(matrix, f, indent=2)

    # 5/8. Identical metric investigation & Variance
    full_aeris_data = {r["question_id"]: r for r in results if r["variant"] == "FULL_AERIS"}
    
    for v in variants:
        if v == "FULL_AERIS": continue
        changed_retrieval = 0
        changed_evidence = 0
        changed_verification = 0
        changed_contradiction = 0
        changed_crosslingual = 0
        changed_selective = 0
        
        for q in questions:
            base = full_aeris_data[q]
            ablation = matrix[q][v]
            
            # Evidence hit / recall used final supporting chunks!
            if set(base.get("supporting_chunk_ids", [])) != set(ablation.get("supporting_chunk_ids", [])):
                changed_evidence += 1
                
            if base.get("verified_claim_count", 0) != ablation.get("verified_claim_count", 0):
                changed_verification += 1
                
            if base.get("selected_verification_count", 0) != ablation.get("selected_verification_count", 0):
                changed_selective += 1
                
            if base.get("metadata", {}).get("contradiction_relations", 0) != ablation.get("metadata", {}).get("contradiction_relations", 0):
                changed_contradiction += 1
                
            if base.get("metadata", {}).get("cross_lingual_relations", 0) != ablation.get("metadata", {}).get("cross_lingual_relations", 0):
                changed_crosslingual += 1
                
        print(f"Variant: {v}")
        print(f"  Changed Evidence Chunks: {changed_evidence}")
        print(f"  Changed Verifications: {changed_verification}")
        print(f"  Changed Contradictions: {changed_contradiction}")
        print(f"  Changed Crosslingual: {changed_crosslingual}")
        print(f"  Changed Selective: {changed_selective}")
        
if __name__ == "__main__":
    run_audit()
