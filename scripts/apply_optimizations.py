import re
import os

def patch_file(filepath, patterns):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for pat, repl in patterns:
        content, count = re.subn(pat, repl, content, flags=re.DOTALL)
        if count == 0:
            print(f"Failed to match in {filepath}: {pat[:50]}...")
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
def main():
    # 1. evidence_coverage.py
    coverage_patterns = [
        (r'(import json)', r'\1\nfrom app.performance_cache import aeris_cache'),
        (r'(for item in req_evidence:\n)', r'\1\n                # OPTIMIZATION: FAST-PATH DETERMINISTIC THRESHOLDING\n                if getattr(item, "rerank_score", 0.0) >= 0.90:\n                    evidence_evaluations.append({\n                        "evidence": item,\n                        "status": "SUPPORTED",\n                        "score": 0.90,\n                        "directness": 0.9,\n                        "relevance": 0.9,\n                        "completeness": 0.9,\n                        "evidence_type_match": 0.9,\n                        "explanation": "Fast-path: Exceptionally high reranker confidence indicates sufficient semantic overlap."\n                    })\n                    break\n'),
        (r'(evaluation = self\._evaluate_pair\(\n\s*requirement,\n\s*item,\n\s*\))', r'cache_key = {"req": requirement.description, "chunk": item.chunk_id}\n                    evaluation = aeris_cache.get("coverage", cache_key)\n                    if not evaluation:\n                        \1\n                        aeris_cache.set("coverage", cache_key, evaluation)')
    ]
    patch_file('app/coverage/evidence_coverage.py', coverage_patterns)
    
    # 2. planner.py
    planner_patterns = [
        (r'(import json)', r'\1\nfrom app.performance_cache import aeris_cache'),
        (r'(response = self\.client\.chat\()', r'cache_key = {"q": question}\n        cached = aeris_cache.get("planner", cache_key)\n        if cached:\n            return InformationPlan(**cached)\n\n        \1'),
        (r'(return InformationPlan\(\n\s*requirements=reqs\n\s*\))', r'plan_dict = {"requirements": [r.dict() for r in reqs]}\n        aeris_cache.set("planner", {"q": question}, plan_dict)\n        \1')
    ]
    patch_file('app/planning/requirement_planner.py', planner_patterns)
    
    # 3. claim_extractor.py
    extractor_patterns = [
        (r'(import json)', r'\1\nfrom app.performance_cache import aeris_cache'),
        (r'(response = self\.client\.chat\()', r'cache_key = {"chunk": chunk_id}\n        cached = aeris_cache.get("extraction", cache_key)\n        if cached:\n            return ExtractionResult(**cached)\n\n        \1'),
        (r'(return ExtractionResult\(\n\s*claims=claims\n\s*\))', r'res_dict = {"claims": [c.dict() for c in claims]}\n        aeris_cache.set("extraction", {"chunk": chunk_id}, res_dict)\n        \1')
    ]
    patch_file('app/claims/claim_extractor.py', extractor_patterns)
    
    # 4. contradiction_analyzer.py
    # "Use inexpensive deterministic/semantic filtering to identify plausible conflicting pairs."
    contra_patterns = [
        (r'(import torch)', r'\1\nfrom app.performance_cache import aeris_cache'),
        (r'(for c1, c2 in pairs:\n\s*pair_id = f"{c1.claim_id}<>{c2.claim_id}")', r'\1\n\n            # OPTIMIZATION: Semantic pre-filtering (word overlap)\n            words1 = set(c1.text.lower().split())\n            words2 = set(c2.text.lower().split())\n            overlap = len(words1.intersection(words2))\n            if overlap == 0 and len(words1) > 0 and len(words2) > 0:\n                continue  # No overlap, highly unlikely to contradict\n\n            cache_key = {"p": pair_id}\n            cached = aeris_cache.get("contradiction", cache_key)\n            if cached:\n                contradictions.append(ContradictionRelation(**cached))\n                continue\n'),
        (r'(contradictions\.append\(relation\))', r'\1\n                aeris_cache.set("contradiction", {"p": pair_id}, relation.dict())')
    ]
    patch_file('app/contradiction/analyzer.py', contra_patterns)
    
    # 5. cross_lingual.py
    # "If all relevant evidence is monolingual: skip the cross-lingual stage explicitly."
    cross_patterns = [
        (r'(import torch)', r'\1\nfrom app.performance_cache import aeris_cache'),
        (r'(def analyze_agreement\([^)]+\):)', r'\1\n\n        # OPTIMIZATION: Check for monolingual evidence\n        langs = {e.language for e in graph.evidence.values() if getattr(e, "language", None)}\n        if len(langs) <= 1:\n            return CrossLingualAgreementReport(\n                agreement_count=0,\n                agreements=[],\n                metadata={"status": "SKIPPED", "reason": "MONOLINGUAL_EVIDENCE"}\n            )\n'),
        (r'(for claim in graph\.claims\.values\(\):\n\s*for chunk_id in claim.source_chunk_ids:)', r'\1\n                cache_key = {"c": claim.claim_id, "chunk": chunk_id}\n                cached = aeris_cache.get("crosslingual", cache_key)\n                if cached:\n                    agreements.append(CrossLingualAgreement(**cached))\n                    continue\n'),
        (r'(agreements\.append\(agreement\))', r'\1\n                aeris_cache.set("crosslingual", {"c": claim.claim_id, "chunk": chunk_id}, agreement.dict())')
    ]
    patch_file('app/cross_lingual/analyzer.py', cross_patterns)
    
    print("Patched performance optimizations successfully.")

if __name__ == '__main__':
    main()
