import json
import os

def analyze_false_support(result_file, benchmark_file, output_file):
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        benchmark = json.load(f)
    
    bench_map = {b['question_id']: b for b in benchmark}
    
    with open(result_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
        
    false_support_cases = []
    
    for r in results:
        qid = r['question_id']
        b = bench_map[qid]
        
        is_answerable = b.get('answerability', True)
        final_status = r.get('final_status', '')
        
        if not is_answerable and final_status in ['SUPPORTED', 'COMPLETED', 'PARTIALLY_SUPPORTED']:
            case = {
                "question_id": qid,
                "variant": r.get('variant'),
                "question_text": b.get('question'),
                "final_status": final_status,
                "final_confidence": r.get('final_confidence'),
                "answer": r.get('answer'),
                "supporting_chunk_ids": r.get('supporting_chunk_ids'),
                "supporting_claim_ids": r.get('supporting_claim_ids'),
                "evidence_count": r.get('evidence_count'),
                "evidence_hit": r.get('evidence_hit'),
                "evidence_recall": r.get('evidence_recall'),
                "coverage_result": r.get('metadata', {}).get('coverage', {}),
                "verified_claims": r.get('verified_claim_count'),
                "selected_claims": r.get('selected_verification_count'),
                "contradiction_relations": r.get('metadata', {}).get('contradiction_relations'),
                "cross_lingual_relations": r.get('metadata', {}).get('cross_lingual_relations'),
                "telemetry": r.get('metadata'),
                "error": r.get('error')
            }
            false_support_cases.append(case)
            
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(false_support_cases, f, indent=2)
        
    print(f"Found {len(false_support_cases)} false support cases. Saved to {output_file}")

if __name__ == '__main__':
    analyze_false_support(
        'data/results/targeted_regression_step23.json',
        'data/benchmark/aeris_benchmark.json',
        'data/results/false_support_targeted_audit.json'
    )
