# AERIS-RAG Step 22E — Answer-Support Validator Remediation Report

**Date / Timestamp:** 2026-10-18T01:00:00+05:30  
**Phase:** Step 22E Remediation  
**Status:** **REMEDIATION COMPLETE — INDEPENDENT REVIEW REQUIRED**  
**Audit Reference:** `data/results/exp_final224_remediation_20261017_142200_independent_scientific_audit.md`  

---

## 1. Executive Summary

During the independent scientific audit of experiment `exp_final224_remediation_20261017_142200`, the automated scientific validity audit blocked promotion due to **13.84% (31/224) false support on unanswerable questions**, exceeding the mandatory ≤ 5.0% Gate 3 threshold. Detailed inspection revealed four root causes in the answer-support validation pipeline:
1. **Self-support via answer text inclusion:** Generated answers that parroted question vocabulary artificially satisfied token-overlap matching against themselves.
2. **Superficial concept and citation overlap:** Generic NLP domain terms (`model`, `evaluation`, `methodology`) and bibliography citations (`[56] Vol. 1`) satisfied quantitative and methodological requirements even when cited documents lacked the required facts (e.g., `q_meth_02`, `q_quant_03`, `q_multi_01`).
3. **LLM judge world-knowledge reliance and binary output:** The judge evaluated real-world factual plausibility (e.g., confirming Tokyo as Japan's capital on unanswerable question `q_unans_01`) rather than strict document entailment, and lacked a structured 4-state evidentiary classification.
4. **Unsafe disjunctive requirement aggregation:** The controller applied `any(res.is_supported)` across requirements, marking multi-part answers as fully `SUPPORTED` even when essential sub-requirements were unsupported or contradicted.

In Step 22E, minimal, targeted source-code remediations were implemented to resolve all four defects. A comprehensive suite of 10 regression and adversarial tests was established in `tests/test_step22e_answer_support_remediation.py`, asserting strict evidence-grounded rejection and acceptance. All 10 new tests and all 75 existing tests (85 total) pass with zero regressions.

**Crucial Scientific Disclaimer:**  
Passing unit tests does **NOT** prove or claim that the ≤ 5.0% false-support benchmark gate has passed. That gate remains unverified until a separately authorized, full independent benchmark execution.

---

## 2. Source-Code Recovery Backup & Audit Integrity

Before applying any edits, an immutable source-code recovery backup was created at:  
`data/recovery_backups/source_backup_20261018_001500_step22e/`

### Backed-up Files and SHA-256 Manifest:
| File Path | Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :--- |
| `app/verification/requirement_support.py` | 13,140 | `5797ce410bfc42b386d413a7a4208c01c6f606dbf02ecf37fb29b87e936999c6` |
| `app/controller/controller.py` | 40,879 | `76b198af137de574d7448f128818ee88facefb8ed423fca1650c0149d77f487b` |
| `app/verification/__init__.py` | 2,967 | `12d0cb61c92d8a58a9ac417c0766b980f30a0e0295180060ee4fccd583ec829b` |
| `app/answer_generation/schemas.py` | 1,114 | `b2936fec0c23a05237e9d280294e18e607bc9738c163e9c36d9d189eedabab79` |
| `app/answer_generation/answer_generator.py` | 10,139 | `4f9b732945574e4eea63dcea6b1d581953c121aef71d87e95f8bbaf63d5083eb` |
| `tests/test_step22d_answer_support_validation.py` | 9,934 | `0bbcaa5f7d5ee4a2c3eddf028c02fbd7008d38de6f9614105e180ab38ea0872d` |
| `tests/test_requirement_support.py` | 4,782 | `b148f468a8b77694c2431194544f37c7597c435861489b0a2a1da05ebd7d9677` |

### Confirmation of Historical Experiment Immutability:
Both prior benchmark experiments and the benchmark dataset remain strictly unmodified:
- `data/results/ablation_results_exp_final224_remediation_20261017_142200.json` (SHA-256: `df9850207668edaa...` — UNCHANGED)
- `data/results/ablation_results_exp_final224_remediation_20261017_142200_manifest.json` (SHA-256: `e1f6bb0ae7cd35e4...` — UNCHANGED)
- `data/results/ablation_results_exp_final224_remediation_20261017_142200_diagnostics.jsonl` (SHA-256: `185273950894ef93...` — UNCHANGED)
- `data/results/ablation_results_exp_final224_repaired_20261011_222000.json` (SHA-256: `a043dadd00685e59...` — UNCHANGED)
- `data/results/ablation_results_exp_final224_repaired_20261011_222000_manifest.json` (SHA-256: `043c1e14f663656c...` — UNCHANGED)
- `data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl` (SHA-256: `bdb0d362bfb40667...` — UNCHANGED)
- `data/benchmark/aeris_benchmark.json` (SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` — UNCHANGED)

No benchmark records were rerun; Step 23 was not started.

---

## 3. Source Files Changed & Behavioral Modifications

Only two source files were modified, implementing the minimum necessary changes:

### 1. `app/verification/requirement_support.py`
- **Structured 4-State Schema (`RequirementSupportResult`):**
  Added `evidence_support_status: str`, populated with one of:
  - `SUPPORTED`: Strictly entailed by the supplied evidence.
  - `CONTRADICTED`: Refuted or directly negated by the supplied evidence.
  - `NOT_ESTABLISHED`: Evidence does not contain the required facts or is silent on the specific topic.
  - `INSUFFICIENT_OR_AMBIGUOUS`: Evidence is incomplete, ambiguous, or lacks required quantitative details.
  Added provenance tracking fields: `supporting_claim_ids: List[str]` and `supporting_chunk_ids: List[str]`.

- **Prevention of Self-Support (B1 Fix):**
  Excluded the generated `answer` string from the evidence token pool (`source_evidence_text = " ".join(claims) + " " + evidence_str`). Requirements are matched strictly against evidence and extracted claims. An answer repeating question keywords cannot validate itself.

- **Strict Evidence Entailment & Quantitative Verification (B2 Fix):**
  - Introduced `generic_domain_words` filter (filtering out words like `model`, `methods`, `evaluation`, `nlp`, `rag`) so that domain stop-words cannot satisfy specific content requirements.
  - Added specific content term validation: if requirement contains specific non-generic topic tokens, at least one must be grounded in cited evidence.
  - Quantitative entailment: numbers claimed in the answer/claims are normalized (`45,000` $\rightarrow$ `45000`) and checked for exact appearance in cited evidence.
  - Bibliography protection: reference metadata (`Vol. 1`, `Proceedings of...`) cannot satisfy requests for dataset sizes or experimental counts without evidence mentioning instances, examples, or dataset sizes.
  - Contradiction / Negation detection: regular expressions detect when numerical or entity claims are directly qualified by negation patterns (e.g. `2048 was not used`), returning `CONTRADICTED`.
  - Scoped requirement targeting: sub-requirements in multi-part queries are judged against their specific target tokens (`req_tokens`), preventing token inflation from sibling requirements.

- **Evidence-Only LLM Judge Contract & Deterministic Guardrail (B3 Fix):**
  - Updated LLM judge prompt with explicit constraints: world knowledge, commonsense facts, and question restatement cannot justify `SUPPORTED`. Specifically instructs the judge that real-world truth (e.g., "Tokyo is the capital of Japan") must be classified as `NOT_ESTABLISHED` if missing from supplied evidence.
  - Required the judge to output JSON with structured `evidence_support_status`.
  - Added deterministic fallback guardrail: if deterministic token/entity analysis determines required concepts or numbers are completely absent or contradicted, an LLM judge hallucination based on external world knowledge is overridden to `NOT_ESTABLISHED` or `CONTRADICTED`.

### 2. `app/controller/controller.py`
- **Multi-Part Requirement Aggregation Semantics (B4 Fix):**
  Replaced unsafe disjunctive logic (`any_supported = any(...)`) with strict conjunctive semantics:
  1. **Contradicted Evidence:** If any requirement receives `CONTRADICTED`, `answer_status` is downgraded to `CONFLICTED` (or `INSUFFICIENT_EVIDENCE`), recording `REQUIREMENT_CONTRADICTED`.
  2. **Total Evidence Failure:** If `supported_count == 0`, `answer_status` is downgraded to `INSUFFICIENT_EVIDENCE`, recording `REQUIREMENT_UNSUPPORTED`.
  3. **Partial Evidence Support:** If `0 < supported_count < total_reqs`, the response is downgraded from `SUPPORTED` to `PARTIALLY_SUPPORTED`, recording `REQUIREMENT_PARTIALLY_UNSUPPORTED` along with the list of unsupported sub-requirements and validator rationales.

---

## 4. Defect-to-Test Mapping

All four audited defects and their edge cases are covered by dedicated, high-fidelity test cases in `tests/test_step22e_answer_support_remediation.py`:

| Defect ID | Audited Vulnerability / Scenario | Dedicated Test Name | Decision Asserted | Status |
| :--- | :--- | :--- | :--- | :--- |
| **B1** | Generated answer parrots question while evidence discusses an unrelated topic | `test_defect_self_support_repetition_rejected` | `is_supported=False`, `NOT_ESTABLISHED` | **PASS** |
| **B2** | Quantitative claim falsely matched to bibliography volume number (`q_quant_03`) | `test_defect_bibliography_numerical_match_rejected` | `is_supported=False`, `MISSING_QUANTITATIVE_EVIDENCE` | **PASS** |
| **B2** | False dense–sparse fusion claim when evidence describes dense retrieval only (`q_meth_02`) | `test_defect_dense_sparse_fusion_unsupported_rejected` | `is_supported=False`, `NOT_ESTABLISHED` | **PASS** |
| **B2** | False multilingual claim when evidence covers only English datasets (`q_multi_01`) | `test_defect_multilingual_evaluation_claim_rejected` | `is_supported=False`, `NOT_ESTABLISHED` | **PASS** |
| **B3** | True world fact absent from document ("Tokyo is capital of Japan" on `q_unans_01`) | `test_defect_world_knowledge_absent_from_document_rejected` | `is_supported=False`, `NOT_ESTABLISHED` | **PASS** |
| **B3** | Evidence directly refutes claimed hyperparameter ("Batch size 2048 was not used") | `test_contradictory_evidence_handling` | `is_supported=False`, `CONTRADICTED` | **PASS** |
| **B4** | Multi-part query where 1 of 2 essential requirements is ungrounded | `test_controller_partially_supported_multi_requirement_downgrade` | `answer_status="PARTIALLY_SUPPORTED"`, `REQUIREMENT_PARTIALLY_UNSUPPORTED` | **PASS** |
| **Baseline** | Legitimate direct fact supported by evidence (true positive retention) | `test_genuinely_supported_claim_accepted` | `is_supported=True`, `SUPPORTED` | **PASS** |
| **Baseline** | Multi-hop reasoning where each requirement is verified by distinct chunks | `test_multi_hop_answer_all_requirements_supported` | All sub-reqs `is_supported=True`, `SUPPORTED` | **PASS** |
| **Robustness** | Empty, None, or ungrounded evidence and malformed provenance | `test_malformed_missing_evidence_and_provenance` | `is_supported=False`, `NOT_ESTABLISHED`, `EVIDENCE_UNSUPPORTED` | **PASS** |

---

## 5. Test Suite Verification & Regressions

### 1. Step 22E Targeted Test Execution:
```bash
python -m pytest tests/test_step22e_answer_support_remediation.py -v
```
**Outcome:** **10 passed in 0.66s (100%)**

### 2. Full Repository Test Suite Execution:
```bash
python -m pytest tests/
```
**Outcome:** **85 passed in 1.31s (100%)**
- `tests/test_answer_guardrail.py`: 3 passed
- `tests/test_cache_isolation.py`: 7 passed
- `tests/test_integration_measurement_repair.py`: 5 passed
- `tests/test_json_parsing.py`: 5 passed
- `tests/test_profiler_accounting.py`: 2 passed
- `tests/test_requirement_support.py`: 1 passed
- `tests/test_retrieval_vs_citation_metrics.py`: 4 passed
- `tests/test_scientific_validity.py`: 4 passed
- `tests/test_semantic_robustness.py`: 10 passed
- `tests/test_step22d1_retrieval_memory_repair.py`: 9 passed
- `tests/test_step22d_adaptive_retrieval_isolation.py`: 3 passed
- `tests/test_step22d_answer_support_validation.py`: 7 passed
- `tests/test_step22d_cross_lingual_agreement.py`: 4 passed
- `tests/test_step22d_retrieval_memory_scoping.py`: 5 passed
- `tests/test_step22d_timeouts_and_latency.py`: 6 passed
- `tests/test_step22e_answer_support_remediation.py`: 10 passed

**Regressions:** **0 regressions across all existing components.**

---

## 6. Remaining Limitations & Next Steps

1. **Gate 3 Benchmark Verification Pending:** While unit test cases confirm rejection of the specific unanswerable failure modes (`q_meth_02`, `q_quant_03`, `q_multi_01`, `q_unans_01`), the aggregate benchmark false-support rate across all 224 variant runs cannot and must not be declared passed based on unit tests alone.
2. **LLM Runtime Dependence:** In offline environments or test suites without an active Ollama instance, the validator falls back to deterministic semantic analysis. The deterministic rules have been strengthened with strict grounding checks, but optimal nuanced reasoning requires an active judge LLM.
3. **Subsequent Authorization Required:** A separate future authorization is required before executing any new 224-record benchmark run.

---

## 7. Stop Condition & Final Status

Remediation and regression tests are complete. Historical artifacts remain preserved. No benchmark was rerun. Step 23 was not initiated.

**Final Status:**  
**REMEDIATION COMPLETE — INDEPENDENT REVIEW REQUIRED**
