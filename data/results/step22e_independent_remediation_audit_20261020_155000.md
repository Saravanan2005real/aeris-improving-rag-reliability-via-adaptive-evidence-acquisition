# AERIS-RAG Step 22E — Independent Remediation Audit Report

**Date / Timestamp:** 2026-10-20T15:50:00+05:30  
**Audit Target:** Step 22E Answer-Support Validator Remediation  
**Primary Remediation Report Audited:** `data/results/step22e_answer_support_remediation_20261018_010000.md`  
**Prior Failure Report:** `data/results/exp_final224_remediation_20261017_142200_independent_scientific_audit.md`  
**Auditor:** Independent Scientific Audit Subagent  

---

## 1. Executive Summary & Verdict

### Audit Verdict: **PASS**

An independent, strictly read-only audit of the Step 22E answer-support validator remediation was conducted. The audit verified the source code, production call paths, regression tests, and historical experiment artifacts across all four reported defects:
- **B1 (Self-Support Prevention):** Verified. Generated answer text is completely excised from the evidence matching corpus (`source_evidence_text`), preventing answers from validating themselves through lexical parroting.
- **B2 (Evidence Entailment):** Verified. Strict semantic entailment enforced via generic NLP domain word filtering, normalized numerical equality verification, bibliography citation decoupling, refutation/negation detection, and sub-requirement concept scoping.
- **B3 (Judge Contract & Guardrails):** Verified. The LLM judge prompt was upgraded to an evidence-only evaluation contract with explicit prohibition against world knowledge (e.g., Tokyo/Japan) and a structured 4-state output (`SUPPORTED`, `CONTRADICTED`, `NOT_ESTABLISHED`, `INSUFFICIENT_OR_AMBIGUOUS`). A deterministic grounding guardrail strictly prevents LLM hallucination from overriding absence of document evidence.
- **B4 (Conjunctive Aggregation):** Verified. The unsafe disjunctive `any(is_supported)` in `AERISController` was replaced with strict conjunctive logic: contradictory evidence triggers `CONFLICTED`/`INSUFFICIENT_EVIDENCE`, total evidence failure triggers `INSUFFICIENT_EVIDENCE`, and partial support is safely downgraded to `PARTIALLY_SUPPORTED`.

### Critical Scientific Invariant
Unit and regression test passes confirm that specific audited defects are remediated. However, this audit explicitly affirms that **the ≤ 5.0% false-support benchmark gate (Gate 3) remains unverified until a separately authorized, full 224-record benchmark execution**.

---

## 2. Detailed Findings for Audited Defects (B1–B4)

### Defect B1: Self-Support Prevention
- **Root Cause in Pre-Step-22E:** In `app/verification/requirement_support.py:214` (prior implementation), the code assembled `combined_claim_text = " ".join(claims) + " " + answer + " " + evidence_str`. When an answer parroted the words of the user question/requirement (e.g., in `q_meth_02`: "The system fuses dense and sparse retrieval..."), the validator matched the target concepts against the generated answer itself rather than against the cited evidence.
- **Remediation Implementation (`app/verification/requirement_support.py:258-260`):**
  ```python
  # Match target requirement tokens STRICTLY against claims and evidence, NEVER against generated answer
  source_evidence_text = " ".join(claims) + " " + evidence_str
  source_tokens = get_semantic_tokens(source_evidence_text)
  ```
- **Call-Path Trace:** In `AERISController.run()` (`app/controller/controller.py:569-586`), `claims_texts` are retrieved exclusively from `graph_builder.claims[cid].text` for `supporting_claim_ids`, and `evidence_texts` are retrieved exclusively from `graph_builder.evidence[cid].text` for `supporting_chunk_ids`. The answer string `final_answer` is passed into `validator.validate(..., answer=final_answer, ...)` for LLM prompt context, but within `_evaluate_semantic_support` it is excluded from `source_tokens`.
- **Pre vs. Post Verification:** A read-only re-evaluation of Test 1 against the pre-Step-22E backup produced `is_supported = True` (FAIL). On the remediated code, it produces `is_supported = False, status = NOT_ESTABLISHED` (PASS).

---

### Defect B2: Enforce Evidence Entailment
- **Root Cause in Pre-Step-22E:** 
  1. Broad terminology overlap: Generic words like `model`, `methods`, `evaluation`, and `tasks` allowed unanswerable questions (e.g., `q_multi_01`) to exceed the 20% match threshold.
  2. Spurious numerical matching: Reference metadata in bibliographies (e.g., in `q_quant_03`, chunk `test_document_p015_c034`: `...In Proceedings of NAACL: HLT, Volume 1, pages 809-819...`) falsely satisfied quantitative claims like "1,000 instances".
  3. Lack of negation awareness: When evidence explicitly stated "Batch size 2048 was not used", the number `2048` appeared in `evidence_nums`, falsely clearing the check.
- **Remediation Implementation (`app/verification/requirement_support.py:187-217, 288-372`):**
  1. *Generic Domain Words Filter (`lines 187-192, 288-310`):* `generic_domain_words` (including `paper`, `model`, `system`, `method`, `task`, `evaluation`, `nlp`, `rag`) are excluded from `specific_target_tokens`. If specific content tokens exist, at least one must be grounded in cited evidence, preventing superficial NLP terminology matches.
  2. *Normalized Quantitative Equality (`lines 338-358`):* Claimed numbers are normalized (removing commas, percentage signs) and strictly verified against normalized numbers in the evidence (`norm_claim_nums.intersection(norm_evidence_nums)`).
  3. *Bibliography Isolation (`lines 362-371`):* If the target asks for instances or sample counts, the evidence must contain explicit sample/instance indicators (`instances`, `samples`, `examples`, `pairs`, `size`). Volume numbers in bibliography citations are rejected.
  4. *Negation / Refutation Detection (`lines 317-330`):* Regex pattern `\b{escaped_num}\b[^.,;\n]*?\b(?:not used|not supported|never|neither|no|false)\b` detects direct evidence refutation and returns `CONTRADICTED`.
  5. *Distinctive Facet Checks (`lines 374-392`):* Queries demanding specific features (e.g., `sparse`, `multilingual`) fail if those specific facets are absent from evidence.
- **Pre vs. Post Verification:**
  - Test 3 (Bibliography `q_quant_03`): Old code = `True` (FAIL); New code = `False` (`MISSING_QUANTITATIVE_EVIDENCE`, PASS).
  - Test 4 (Dense-Sparse `q_meth_02`): Old code = `True` (FAIL); New code = `False` (`NOT_ESTABLISHED`, PASS).
  - Test 5 (Multilingual `q_multi_01`): Old code = `True` (FAIL); New code = `False` (`NOT_ESTABLISHED`, PASS).
  - Test 7 (Contradiction): Old code = `True` (FAIL); New code = `False` (`CONTRADICTED`, PASS).

---

### Defect B3: LLM Judge Behavior & Grounding Guardrail
- **Root Cause in Pre-Step-22E:** The judge evaluated real-world factual correctness without strict document grounding, accepting true facts absent from the text (e.g., `q_unans_01`: "What is the capital of Japan? Tokyo" with Wizard of Wikipedia citation). Furthermore, the contract was a loose binary boolean with no structured status.
- **Remediation Implementation (`app/verification/requirement_support.py:83-160`):**
  1. *Evidence-Only Evaluation Contract (`lines 88-123`):* Explicit prompt constraints state that world knowledge is not evidence, specifically citing real-world truths like Tokyo/Japan. Requires structured 4-state response: `SUPPORTED`, `CONTRADICTED`, `NOT_ESTABLISHED`, `INSUFFICIENT_OR_AMBIGUOUS`.
  2. *Robust Response Parsing (`lines 135-142`):* Extracts JSON, normalizes status strings, requires `(status_val == "SUPPORTED") and bool(data.get("is_supported", False))`. Malformed outputs gracefully fall back to deterministic evaluation.
  3. *Deterministic Grounding Guardrail (`lines 144-152`):*
     ```python
     if is_sup and not sem_result.is_supported and sem_result.evidence_support_status in ["NOT_ESTABLISHED", "CONTRADICTED"]:
         is_sup = False
         status_val = sem_result.evidence_support_status
         rationale = f"{rationale} [Judge override: cited evidence does not contain required facts: {sem_result.rationale}]"
         category = sem_result.downgrade_category or "REQUIREMENT_UNSATISFIED"
     ```
  4. *Overriding Verification:* Independent testing with simulated LLM hallucination confirmed that even when an LLM explicitly outputs `{"evidence_support_status": "SUPPORTED", "is_supported": true}`, the deterministic grounding guardrail intercepts the decision and overrides it to `False` (`NOT_ESTABLISHED`) because required facts are absent from the document evidence.

---

### Defect B4: Multi-Requirement Aggregation Semantics
- **Root Cause in Pre-Step-22E:** `app/controller/controller.py:589` previously evaluated:
  `any_supported = any(res.is_supported for _, res in req_val_results)`
  If any single requirement was supported, the entire answer was marked `SUPPORTED`, even if essential sibling requirements were ungrounded or contradicted.
- **Remediation Implementation (`app/controller/controller.py:589-651`):**
  1. *Contradiction Priority (`lines 608-620`):* If `contradicted_count > 0`, `answer_status = "CONFLICTED"` (or `"INSUFFICIENT_EVIDENCE"`), appending `REQUIREMENT_CONTRADICTED`.
  2. *Zero Evidence Support (`lines 622-634`):* If `supported_count == 0`, `answer_status = "INSUFFICIENT_EVIDENCE"`, appending `REQUIREMENT_UNSUPPORTED`.
  3. *Partial Support Downgrade (`lines 636-651`):* If `0 < supported_count < total_reqs`, `answer_status` is downgraded from `SUPPORTED`/`COMPLETED` to `PARTIALLY_SUPPORTED`, recording `REQUIREMENT_PARTIALLY_UNSUPPORTED`, the exact list of unsupported sub-requirements, and validator rationales.
- **Pre vs. Post Verification:**
  - Test 6 evaluated against pre-Step-22E code: Result remained `"SUPPORTED"` (FAIL).
  - Test 6 evaluated against remediated code: Result downgraded to `"PARTIALLY_SUPPORTED"` (PASS).

---

## 3. Test-Quality Assessment & Coverage Analysis

The regression test file `tests/test_step22e_answer_support_remediation.py` contains 10 dedicated test cases. All 10 tests were executed and passed in 0.66s.

### Test Coverage Matrix:
| Behavioral Requirement | Test Name | Tested Implementation Path | Pre-22E Outcome | Post-22E Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Question repetition with irrelevant evidence** | `test_defect_self_support_repetition_rejected` | Production `RequirementSupportValidator` | `True` (FAIL) | `False` (PASS) |
| **World knowledge absent from document** | `test_defect_world_knowledge_absent_from_document_rejected` | Production `RequirementSupportValidator` | Guardrail bypassed | Rejected (PASS) |
| **Bibliography numbers mistaken for counts** | `test_defect_bibliography_numerical_match_rejected` | Production `RequirementSupportValidator` | `True` (FAIL) | `False` (PASS) |
| **Unsupported dense-sparse fusion** | `test_defect_dense_sparse_fusion_unsupported_rejected` | Production `RequirementSupportValidator` | `True` (FAIL) | `False` (PASS) |
| **Unsupported multilingual evaluation** | `test_defect_multilingual_evaluation_claim_rejected` | Production `RequirementSupportValidator` | `True` (FAIL) | `False` (PASS) |
| **Partial support multi-requirement downgrade** | `test_controller_partially_supported_multi_requirement_downgrade` | Full `AERISController.run()` pipeline | `"SUPPORTED"` (FAIL) | `"PARTIALLY_SUPPORTED"` (PASS) |
| **Contradictory / negated evidence** | `test_contradictory_evidence_handling` | Production `RequirementSupportValidator` | `True` (FAIL) | `False` (PASS) |
| **Fully supported direct facts (True Positives)** | `test_genuinely_supported_claim_accepted` | Production `RequirementSupportValidator` | `True` | `True` (PASS) |
| **Multi-hop answer with all sub-reqs entailed** | `test_multi_hop_answer_all_requirements_supported` | Production `RequirementSupportValidator` | `True` | `True` (PASS) |
| **Missing or malformed evidence/provenance** | `test_malformed_missing_evidence_and_provenance` | Production `RequirementSupportValidator` | Rejected | Rejected (PASS) |

### Test Quality Observations & Coverage Notes:
1. **Direct Production Testing:** The tests do not mock validator internal logic; they invoke `RequirementSupportValidator.validate()` directly with realistic prompts, questions, claims, and evidence text excerpts taken directly from the failure records.
2. **Controller Integration:** Test 6 constructs an `AERISController` instance and exercises the entire planning, retrieval, validation, and metadata downgrade aggregation pipeline.
3. **Identified Unit Test Gap (Addressed in Audit):** In `test_step22e_answer_support_remediation.py`, all tests execute with `val.client = None` (deterministic mode) to allow fast, reproducible offline CI runs. To verify the live LLM prompt parsing and the deterministic guardrail override under simulated LLM responses, this audit executed an independent harness (`audit_llm_edge_cases.py`), verifying that malformed JSON, invalid status strings, and LLM hallucination overrides function as designed.

---

## 4. Production Call-Path & Downstream Compatibility

The audit inspected downstream consumers of `answer_status` across the codebase:

1. **Controller Result Schema (`app/controller/schemas.py:120`):**
   `ControllerResult` defines `answer_status: Optional[str] = None`. Adding statuses like `"PARTIALLY_SUPPORTED"` and `"CONFLICTED"` adheres to the string schema without breaking pydantic validation.
2. **Execution Runners (`runner.py:159`, `clean_full_ablation.py:95`):**
   `final_status = str(result.answer_status) if result.answer_status else str(result.status.value)`.
   Downstream logging and persistence capture the exact refined status.
3. **Metric Calculation (`scripts/evaluate_ablation.py:115-121`):**
   ```python
   if res.get("answer_status") == "SUPPORTED":
       stats[v]["supported_answers"] += 1
   elif res.get("answer_status") == "INSUFFICIENT_EVIDENCE":
       stats[v]["insuff_answers"] += 1
   elif res.get("answer_status") == "CONTRADICTED":
       stats[v]["contra_answers"] += 1
   ```
   `"PARTIALLY_SUPPORTED"` is **not** counted as `"SUPPORTED"`, ensuring that partial support cannot inflate accuracy.
4. **Scientific Validity Audit (`scripts/audit_ablation_scientific_validity.py:57-60`):**
   ```python
   else: # unanswerable questions
       if final_status in ['SUPPORTED', 'COMPLETED', 'PARTIALLY_SUPPORTED']:
           supported_unans += 1
       else:
           insuff_unans += 1
   ```
   Crucially, the scientific audit script includes `'PARTIALLY_SUPPORTED'` in `supported_unans` for unanswerable questions. Because the remediated controller sets `answer_status = "INSUFFICIENT_EVIDENCE"` when all requirements are unsupported (`supported_count == 0`), unanswerable questions correctly fall into `insuff_unans`, while preventing any partial false support from evading detection.
5. **Retrieval Memory & Provenance Guardrails:**
   The cache-hit delivery audited in Step 22D.1 and the provenance chunk-id verification in `controller.py:652-666` operate independently and remain fully intact.

---

## 5. Historical Artifact Integrity Verification

Read-only SHA-256 verification was performed on all historical experiments and benchmark data. Every single artifact matches its recorded checksum exactly:

| Artifact Path | Size (Bytes) | Verified SHA-256 Checksum | Integrity Status |
| :--- | :--- | :--- | :--- |
| `data/benchmark/aeris_benchmark.json` | 19,894 | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | **UNCHANGED** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200.json` | 842,787 | `df9850207668edaa59d3ce4f5acc7074c119f72b12ce0a4c86638c24197dd6cf` | **UNCHANGED** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200_manifest.json` | 1,038 | `e1f6bb0ae7cd35e4612e4f0adb9af9164032b974b37fd11612c9f5f0a4978a78` | **UNCHANGED** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200_diagnostics.jsonl` | 1,312,357 | `185273950894ef93ef89d4a0b46c24d5f3f4b3a3bbaae7e53976630af9bae975` | **UNCHANGED** |
| `data/results/ablation_exp_final224_remediation_20261017_142200_metrics.json` | 11,128 | `85ff338a216dd85026c44067dfe1ebaffddd13fdf4eb8c5c9022b00fa09b0506` | **UNCHANGED** |
| `data/results/ablation_exp_final224_remediation_20261017_142200_scientific_audit.json` | 3,583 | `354bb4488226a5ec31bc441c0d1e297e0ad08a86b97aab1887b704f9921cf294` | **UNCHANGED** |
| `data/results/ablation_exp_final224_remediation_20261017_142200_structural_audit.json` | 1,574 | `32f4456fe61a0c4b1c6c861e220c38bc39e665a45ff27994bfc534acff6ac381` | **UNCHANGED** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000.json` | 754,943 | `a043dadd00685e59310564ffaba14a697eb3ebcd6c3879f2a619f829f9039bf3` | **UNCHANGED** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_manifest.json` | 1,029 | `043c1e14f663656c0b4bdccc6c34df6d8e7050d7ba6e96b77723f50ce0a32714` | **UNCHANGED** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl` | 1,303,274 | `bdb0d362bfb4066741449fe4c74631ed065f6dd7b8ec55acf534d86a69a69643` | **UNCHANGED** |
| `data/results/ablation_exp_final224_repaired_20261011_222000_metrics.json` | 11,201 | `285461958aa2709991788cd5b1ce5e0bab8cdc48271f9e7ecf2b3aa9397dc8d6` | **UNCHANGED** |
| `data/results/ablation_exp_final224_repaired_20261011_222000_scientific_audit.json` | 3,569 | `4b6c14352b208d9375f3fc218ecd0ed9850468f206a97d937df3c07dc3aa16be` | **UNCHANGED** |
| `data/results/ablation_exp_final224_repaired_20261011_222000_structural_audit.json` | 1,568 | `00efbee9424b3f377eec223f55c7541ca872acb0bb97b65a1815907184c4a177` | **UNCHANGED** |

No benchmark records were rerun, and Step 23 was not started.

---

## 6. Unresolved Concerns & Recommendations

1. **Gate 3 Remains Formally Unverified:** The historical 13.84% (31/224) false-support rate recorded in experiment `exp_final224_remediation_20261017_142200` remains the scientific baseline of record. While the targeted unit tests confirm that all four defect mechanisms are effectively blocked, only an independent end-to-end benchmark execution can empirically verify whether the system achieves ≤ 5.0% false support across all 224 runs.
2. **Deterministic Fallback Reliance:** The validator utilizes deterministic fallback when the LLM service is unavailable or times out. The deterministic rules have been significantly fortified with grounding checks, but complex multi-clause syntactic reasoning still benefits from LLM verification.
3. **Recommendation:** A new benchmark run is scientifically justified to evaluate the aggregate impact of the Step 22E remediation.

---

## 7. Audit Conclusion & Final Status

The source code changes are minimal, precisely targeted to the four audited root causes, accompanied by high-quality regression tests, and fully backward-compatible with the broader system architecture.

### Final Audit Status:
**READY FOR A NEW BENCHMARK — SUBJECT TO EXPLICIT AUTHORIZATION**
