import re

def main():
    with open('app/controller/controller.py', 'r') as f:
        code = f.read()

    # 1. Add time import
    if 'import time' not in code:
        code = 'import time\n' + code

    # 2. Modify _stage signature
    code = code.replace(
        'metadata: Optional[Dict[str, Any]] = None,',
        'metadata: Optional[Dict[str, Any]] = None,\n        latency_seconds: float = 0.0,'
    )
    code = code.replace(
        'metadata=metadata or {},',
        'metadata=metadata or {},\n            latency_seconds=latency_seconds,'
    )

    # 3. Add timers to run()
    replacements = [
        # PLANNING
        (r'(plan = self.planner.plan\(request.question\))', r't_start = time.time()\n            \1\n            t_plan = time.time() - t_start'),
        (r'(ControllerStage.PLANNING,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?len\(plan.requirements\),\n                )\)', r'\1    latency_seconds=t_plan,\n                )'),

        # RETRIEVAL
        (r'(retrieval_results = \[\])', r't_start = time.time()\n            \1'),
        (r'(evidence_items = self._collect_evidence\(\n                retrieval_results\n            \))', r'\1\n            t_retrieval = time.time() - t_start'),
        (r'(ControllerStage.RETRIEVAL,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?len\(evidence_items\),\n                )\)', r'\1    latency_seconds=t_retrieval,\n                )'),

        # COVERAGE
        (r'(coverage_metadata = self._collect_coverage_metadata\(\n                retrieval_results\n            \))', r't_start = time.time()\n            \1\n            t_cov = time.time() - t_start'),
        (r'(ControllerStage.COVERAGE,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?len\(evidence_items\),\n.*?coverage_metadata,\n                )\)', r'\1    latency_seconds=t_cov,\n                )'),

        # CLAIM EXTRACTION
        (r'(raw_claims = \[\])', r't_start = time.time()\n            \1'),
        (r'(raw_claims.extend\(claims\))', r'\1\n            t_extract = time.time() - t_start'),
        (r'(ControllerStage.CLAIM_GRAPH,\n.*?StageStatus.COMPLETED,\n.*?"Claims extracted.*?,\n.*?len\(raw_claims\),\n                )\)', r'\1    latency_seconds=t_extract,\n                )'),

        # GRAPH BUILD (Combining normalization, typing, graph build)
        (r'(normalized_claims = \(\n                self.claim_normalizer)', r't_start = time.time()\n            \1'),
        (r'(claim_type=claim.claim_type,\n                ))', r'\1\n            t_graph = time.time() - t_start'),
        (r'(ControllerStage.CLAIM_GRAPH,\n.*?StageStatus.COMPLETED,\n.*?"Claim-evidence graph constructed.*?,\n.*?len\(typed_claims\),\n                )\)', r'\1    latency_seconds=t_graph,\n                )'),
        
        # VERIFICATION
        (r'(verification_results = \[\])', r't_start = time.time()\n            \1'),
        (r'(verified_count \+= 1)', r'\1\n            t_verify = time.time() - t_start'),
        (r'(ControllerStage.VERIFICATION,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?verified_count,\n                )\)', r'\1    latency_seconds=t_verify,\n                )'),

        # CONTRADICTION
        (r'(contradiction_report = None)', r't_start = time.time()\n            \1'),
        (r'(contradiction_count = self._count_contradictions\(contradiction_report\))', r'\1\n                    t_contra = time.time() - t_start'),
        (r'(ControllerStage.CONTRADICTION,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?contradiction_count,\n                        )\)', r'\1    latency_seconds=t_contra,\n                        )'),

        # CROSS LINGUAL
        (r'(cross_lingual_report = None)', r't_start = time.time()\n            \1'),
        (r'(cross_lingual_count = len\(cross_lingual_report.agreements\))', r'\1\n                    t_cross = time.time() - t_start'),
        (r'(ControllerStage.CROSS_LINGUAL,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?cross_lingual_count,\n                        )\)', r'\1    latency_seconds=t_cross,\n                        )'),

        # CALIBRATION
        (r'(calibration_records = self._build_calibration_records\()', r't_start = time.time()\n            \1'),
        (r'(calibrated_count = len\(\n                        calibration_records\n                    \))', r'\1\n                    t_calib = time.time() - t_start'),
        (r'(ControllerStage.CALIBRATION,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?calibrated_count,\n                        )\)', r'\1    latency_seconds=t_calib,\n                        )'),

        # SELECTIVE VERIFICATION
        (r'(selected_count = 0)', r't_start = time.time()\n            \1'),
        (r'(selected_count = getattr\(\n                    selective_report,\n                    "selected_count",\n                    0,\n                \))', r'\1\n                t_sel = time.time() - t_start'),
        (r'(ControllerStage.SELECTIVE_VERIFICATION,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?selected_count,\n                    )\)', r'\1    latency_seconds=t_sel,\n                    )'),

        # ANSWER GENERATION
        (r'(final_answer = None)', r't_start = time.time()\n            \1'),
        (r'(insufficiency_info = answer_result.insufficiency_reason)', r'\1\n                t_ans = time.time() - t_start'),
        (r'(ControllerStage.ANSWER_GENERATION,\n.*?StageStatus.COMPLETED,\n.*?".*?",\n.*?1,\n                    )\)', r'\1    latency_seconds=t_ans,\n                    )'),
    ]

    for pat, repl in replacements:
        code, count = re.subn(pat, repl, code, flags=re.DOTALL)
        if count == 0:
            print(f"Failed to match: {pat[:50]}...")
            
    with open('app/controller/controller.py', 'w') as f:
        f.write(code)
    
    print("Patched controller.py")

if __name__ == "__main__":
    main()
