# AERIS-RAG — Independent Verification Report: Partial-Support Remediation

**Report ID:** `step22e_partial_support_verification_report`  
**Date:** 2026-10-21  
**Verification Auditor:** Independent Scientific Verification Agent  
**Target Reference Experiment:** `exp_final224_step22e_remediation_20261021_125813`  
**Remediation Documentation Reviewed:**
- `data/results/step22e_partial_support_remediation_report.md`
- `data/results/step22e_partial_support_remediation_independent_audit.md`  
**Verification Verdict:** **VERIFICATION PASSED** (Implementation, Metric Contracts, Regression Suite, and Historical Integrity Confirmed)

---

## 1. Executive Summary

This report provides a strictly read-only, independent verification of the remediation implemented to eliminate partial-support false positives on multi-aspect queries (specifically `q_meth_02`) following benchmark experiment `exp_final224_step22e_remediation_20261021_125813`.

All modified source files, test fixtures, metric aggregation scripts, regression results, and cryptographic hashes of the benchmark dataset and historical artifacts were independently inspected and validated.

---

## 2. Independent Inspection of Source Diffs

The auditor inspected the exact unified diffs between the modified workspace files and the pre-remediation backup (`data/recovery_backups/source_backup_20261021_203500_post_benchmark_remediation/`):

### 2.1 `app/verification/requirement_support.py`
1. **Modality Decoupling:**
   - Previous synonym group `{"retrieval", "retriever", "dense", "sparse", "dpr", "bm25", "search"}` was dismantled.
   - Distinct, non-overlapping semantic sets were created:
     - `{"retrieval", "retriever", "search", "lookup"}`
     - `{"dense", "dpr", "embedding", "vector", "bi-encoder", "biencoder"}`
     - `{"sparse", "bm25", "tfidf", "tf-idf", "lexical", "keyword"}`
     - `{"fuse", "fused", "fusion", "combines", "combination", "hybrid", "joint"}`
2. **Elimination of Self-Support:**
   - Previous: `source_evidence_text = " ".join(claims) + " " + evidence_str` (allowed ungrounded claims to introduce hallucinated words into the evidence bag).
   - Remediated: `source_tokens = evidence_tokens | (claim_grounded_tokens if claim_only_tokens else set())`.
   - Verified: Only tokens directly present in `evidence_tokens` or verified as grounded via `claim_grounded_tokens` can serve as evidence. Ungrounded claims cannot self-support.
3. **Distinctive Facet Checks:**
   - Explicit checks enforce that if a query or planned requirement demands `dense`, `sparse`, or `fusion`, the concept must be present in `source_tokens`. If missing, the validator returns `NOT_ESTABLISHED` with downgrade category `REQUIREMENT_UNSATISFIED`.
4. **General Non-Numeric Contradiction Detection:**
   - Negation pattern analysis was extended from numerical claims to candidate entities from `combined_target_tokens` and `claim_only_tokens`.
   - If an entity is qualified by explicit negation (`not used`, `not supported`, `never`, `unsupported`, `not implemented`) in `evidence_str`, it returns `CONTRADICTED` with `downgrade_category="CONTRADICTED_BY_EVIDENCE"`.

### 2.2 `app/controller/controller.py`
1. **Essential Requirement Isolation:**
   - Essential requirements are identified via `getattr(r, "priority", 1) == 1`. If no requirements have priority 1, all planned requirements are treated as essential.
   - `essential_unsupported` and `essential_contradicted` lists are explicitly tracked.
2. **Strict Downgrade Contract:**
   - When `supported_count < total_reqs`, any answer with status `SUPPORTED` or `COMPLETED` is downgraded to `PARTIALLY_SUPPORTED`.
   - Missing essential requirements strictly prevent classification as fully `SUPPORTED`.
3. **Telemetry Enrichment:**
   - Controller downgrade metadata records `essential_unsupported` and `essential_contradicted` alongside validator rationales.

### 2.3 `scripts/audit_final_224.py` & `scripts/audit_ablation_scientific_validity.py`
1. **Metric Definition Separation:**
   ```python
   is_fully_supported = status in ["SUPPORTED", "COMPLETED"]
   is_substantive_support = status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]
   ```
2. **Answerable Questions:** Only `is_fully_supported` increments `ans_correct_supported`. Partial support does not inflate full answer support.
3. **Unanswerable Questions:** Under the existing benchmark contract, any substantive claim of support (`is_substantive_support`) increments `unans_incorrect_supported` (false support).
4. **Consistency:** Both scripts use identical classification rules, denominators, and gate evaluation logic.

---

## 3. Verification of Concept Separation and Grounding Assurance

The auditor independently verified the execution behavior of the requirement support validator:

1. **Ungrounded Tokens Cannot Contribute to Evidence Matching:**
   Because `source_tokens` is composed solely of `evidence_tokens | claim_grounded_tokens`, if an extracted claim contains a concept (e.g. `sparse`) that does not appear in the cited chunk, `sparse` is excluded from `claim_grounded_tokens` and does not enter `source_tokens`. The claim cannot validate itself.
2. **Distinct Evaluation of Dense, Sparse, and Fusion:**
   Because `dense`, `sparse`, and `fuse` reside in separate synonym groups and are gated by distinctive facet checks, a passage describing DPR (dense) cannot satisfy a sparse requirement or a fusion requirement.

---

## 4. Verification of Metric Semantics and Accounting Integrity

| Metric Domain | Rule Applied | Verified Accounting |
| :--- | :--- | :--- |
| **Answerable Queries** | Full satisfaction of all essential requirements | Only answers with status `SUPPORTED` or `COMPLETED` count toward `ans_correct_supported`. `PARTIALLY_SUPPORTED` is recorded as insufficient/partial and excluded from full support. |
| **Unanswerable Queries** | Rejection of substantive claims under benchmark contract | Any answer claiming `SUPPORTED`, `COMPLETED`, or `PARTIALLY_SUPPORTED` on an unanswerable question counts as false support (`unans_incorrect_supported`). |
| **Denominators** | Intent-to-treat accounting | Unanswerable denominator = `unans_incorrect_supported + unans_correct_insufficient + unans_execution_failures` (64 total). Answerable denominator = `ans_correct_supported + ans_conservative_insufficient + ans_execution_failures` (160 total). |

The auditor confirms the metric definitions are mathematically sound, mutually consistent across scripts, and faithfully preserve the benchmark contract.

---

## 5. Production Code Path Verification of Regression Tests

The auditor inspected all six test cases in `tests/test_step22e_partial_support_remediation.py` to confirm that they exercise actual production components:

1. `test_dense_supported_sparse_unsupported_fusion_unsupported`: Directly exercises `RequirementSupportValidator.validate` across a 3-requirement query, verifying that dense DPR evidence establishes R1 (dense) while failing R2 (sparse) and R3 (fusion).
2. `test_all_essential_requirements_supported`: Exercises `RequirementSupportValidator.validate` confirming that grounded evidence satisfies all requirements.
3. `test_one_essential_requirement_contradicted`: Exercises the general contradiction detection logic in `RequirementSupportValidator.validate` against explicit text negation.
4. `test_genuinely_partial_answer_downgraded_and_metrics_separated`: Exercises `AERISController` requirement aggregation and status downgrade logic using real `RequirementPlan` and `InformationRequirement` models.
5. `test_unanswerable_question_partial_support_counts_as_false_support`: Exercises the benchmark evaluation contract, verifying that partial support on an unanswerable question is counted as false support.
6. `test_ablation_variants_retain_intended_behavior`: Calls `get_config_for_variant` from `app.ablation.config` and inspects `ControllerConfig` for all 8 ablation variants, verifying that every component flag is correctly configured.

All six tests invoke production classes and verify real system invariants.

---

## 6. Test Suite Re-Run Results

The full test suite was independently executed:
- **Command:** `python -m pytest tests/ -v`
- **Total Test Files:** 18
- **Total Tests Collected:** 101
- **Execution Result:** **101 passed, 0 failed, 0 errors, 0 skipped** (8.28s execution time)

---

## 7. Cryptographic Verification of Benchmark and Historical Assets

Cryptographic SHA-256 hashes were computed for the benchmark dataset, historical results, diagnostics, manifests, and prior audit reports:

| File Path | Verified SHA-256 Hash | Integrity Status |
| :--- | :--- | :---: |
| `data/benchmark/aeris_benchmark.json` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_results_exp_final224_step22e_remediation_20261021_125813.json` | `0884edf7fa4e81a4a4abb9f2733ddfb0e1d1b4d8931237df8fa788cd60b9fe40` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_results_exp_final224_step22e_remediation_20261021_125813.md` | `0ff2c5326947c49a448ed56e24e8c46defcada0d83dea22c42536b3e6192d315` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_results_exp_final224_step22e_remediation_20261021_125813_diagnostics.jsonl` | `4ac6189da01232ad903237ede740dcbd7ff0278393563f288bbdcb4ccbdbe98b` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_results_exp_final224_step22e_remediation_20261021_125813_manifest.json` | `19e46ff29352ddfc5bba1de415648a067baf0c9d68fe046fee44397b95d38e35` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_exp_final224_step22e_remediation_20261021_125813_metrics.json` | `e661f5ee66dd2f45f55d1d4b5770735f83449b0bd34d5771d247910ed26bc50d` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_exp_final224_step22e_remediation_20261021_125813_scientific_audit.json` | `e69884bf0620f879ac93672e139c5d003c2c7f6ed0e28ce7e6a7de4c5de808ce` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_exp_final224_step22e_remediation_20261021_125813_structural_audit.json` | `75dbfe2ce97ec68632665da3ae895236e43685003a0f632331743403eee39b59` | **MATCH (UNMODIFIED)** |
| `data/results/ablation_exp_final224_step22e_remediation_20261021_125813_activation_audit.json` | `6b7fdf4b7fcb13be843ff246f5bbf2c6fc0125fa6d47b7e4230d1dc1422000cb` | **MATCH (UNMODIFIED)** |
| `data/results/exp_final224_step22e_remediation_20261021_125813_postrun_review.md` | `0b53e703ae9471ff1f6ffac8bfe8d1648e834297c14ae20fe87e82b1d250def4` | **MATCH (UNMODIFIED)** |
| `data/results/step22e_final_preflight.md` | `88746d1ab6cdcd4ebf0203192759e222442d865c32b8977a7dca85c55648737c` | **MATCH (UNMODIFIED)** |
| `data/results/step22e_postrun_remediation_independent_audit.md` | `723e91d05a56a3ba8864c3560cf7e5277f95b785769651a5e5b2691ee6f5a856` | **MATCH (UNMODIFIED)** |
| `data/results/step22e_postrun_remediation_report.md` | `061ae55b121ed7f3ecb5aaafc098a3bdb78ccd541d8dac5f2e629c2f0c18976d` | **MATCH (UNMODIFIED)** |

All historical files and audit reports remain byte-for-byte identical.

---

## 8. Compliance with Restrictions & Scientific Gate Status

1. **Zero Benchmark Executions:** No benchmark runs, reruns, or test evaluations were launched.
2. **Data & Audit Immutability:** Benchmark data, questions, labels, historical results, and previous audit reports remain intact.
3. **Step 23 Constraint:** Step 23 was not started.
4. **Gate 3 Status:** Gate 3 remains scientifically pending evaluation. While unit and regression testing confirm the defect is remediated in code, Gate 3 can only be cleared by a future authorized, completed, independently audited 224-record benchmark evaluation.

---

## 9. Conclusion

The partial-support remediation is **INDEPENDENTLY VERIFIED AND APPROVED**. The code changes strictly enforce evidence grounding, decouple multi-aspect retrieval modalities, maintain consistent metric semantics across the codebase, pass all 101 unit/regression tests, and preserve historical experiment integrity with complete fidelity.
