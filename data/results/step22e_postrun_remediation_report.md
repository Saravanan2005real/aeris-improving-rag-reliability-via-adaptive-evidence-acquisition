# AERIS-RAG — Step 22E Remediation Planning and Targeted Validation Report

**Date:** 2026-10-21  
**Status:** SCIENTIFICALLY BLOCKED (Benchmark execution strictly prohibited)  
**Target Benchmark Dataset:** `data/benchmark/aeris_benchmark.json` (SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`)  
**Historical Artifact Evaluated:** `exp_final224_step22e_20261020_160000`  
**Test Suite Status:** 95 Passed, 0 Failed (1.54s execution)

---

## 1. Executive Summary

Following the read-only root cause investigation of experiment `exp_final224_step22e_20261020_160000`, the AERIS-RAG benchmark remains **SCIENTIFICALLY BLOCKED**. 

This remediation task executed the necessary source-code repairs and targeted test validations under strict protocol controls:
1. **Phase A (Evidence Semantics Resolution):** Analyzed the ground-truth benchmark entry for `q_unans_02`, the paper's Appendix C (`test_document_p017_c037`), chunk indexing boundaries, and retrieval eligibility. Determined that the issue is primarily a **benchmark-labeling defect** compounded by global retrieval scoping. Strictly adhered to the safeguard: **zero modifications** were made to the benchmark question, answerability label, expected status, or dataset hash.
2. **Phase B (Smallest Source Remediation):**
   - Corrected `RequirementSupportValidator` (`app/verification/requirement_support.py`) to prevent generic matches like `"train"` in `"train/dev/test splits"` from establishing hardware support, while supporting valid hardware paraphrases (GPUs, TPUs, compute clusters, processors) and rejecting bibliographic citations.
   - Replaced the hardcoded 60s HTTP read timeout in `ClaimExtractor` (`app/claim_extraction/extractor.py` and `app/config.py`) with a dedicated `180.0s` timeout (`ollama_claim_extraction_timeout`), while leaving the 300s sleep/suspension threshold unchanged.
   - Implemented bounded retry logic (`max_retries = 1`) with extraction telemetry (`log_generation_attempt`) and full exception visibility upon exhaustion.
3. **Phase C (Safety and Test Validation):**
   - Backed up all affected files to `data/recovery_backups/source_backup_20261021_120500_step22e_remediation/`.
   - Executed targeted unit and regression tests (10 new tests).
   - Executed the complete repository test suite: **95 passed, 0 failed in 1.54s**.
   - Verified that the benchmark dataset and all historical experiment artifacts remain byte-for-byte identical.

---

## 2. Phase A: Evidence-Scope Decision Report for `q_unans_02`

### 2.1 Benchmark & Document Inspection

| Attribute | Specification |
| :--- | :--- |
| **Question ID** | `q_unans_02` |
| **Question Text** | *"What hardware was used to train the RAG models?"* |
| **Ground Truth Answerability** | `UNANSWERABLE` |
| **Expected Evaluation Status** | `INSUFFICIENT_EVIDENCE` |
| **Supporting Chunk IDs** | `[]` (Empty list) |
| **Source Document** | *"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"* (Lewis et al., 2020) |
| **Corpus Index Scope** | 42 chunks (`test_document_p001_c000` to `test_document_p019_c041`) spanning pages 1–19 |
| **Appendix C Location** | Page 17, chunk `test_document_p017_c037` |
| **Appendix C Text** | *"Training setup Details: We train all RAG models and BART baselines using Fairseq. We train with mixed precision floating point arithmetic, distributing training across 8, 32GB NVIDIA V100 GPUs, though training and inference can be run on one GPU."* |

### 2.2 Semantic and Retrieval Scope Findings

1. **Retrieval Index Inclusions:** The vector index includes all 42 chunks covering the full 19 pages of the source document. Multiple benchmark questions deliberately cite pages 18 and 19 (e.g., `q_df_03`, `q_df_05`, `q_mh_01`, `q_mh_03`, `q_contra_02`). Thus, appendices are active, eligible index constituents.
2. **Defect in Step 22E Execution:** In experiment `exp_final224_step22e_20261020_160000`, the retrieval pipeline did **not** retrieve Appendix C (p. 17). Instead, it retrieved page 4 (`test_document_p004_c010`), which discussed `"train/dev/test splits"` and abstractive QA on MSMARCO. The validator marked this chunk as `SUPPORTED` because the single token `"train"` matched the requirement `"Identify training hardware"`.
3. **Classification of the Problem:**
   - **Benchmark-Labeling Problem:** The benchmark creator labeled `q_unans_02` as `UNANSWERABLE` under the assumption that the paper did not disclose training hardware. However, Lewis et al. explicitly disclose the hardware in Appendix C.
   - **Retrieval-Scope Problem:** If the benchmark intention was that unanswerability questions test questions unanswerable *from the main body text (pages 1–8)*, no retrieval-scope restriction or metadata filter was ever encoded in the system or benchmark metadata.
   - **Validation-Logic Vulnerability:** The validator allowed a false match because `"train"` (a generic verb/split noun) was treated as establishing the domain concept of "hardware".

### 2.3 Explicit Evidence-Scope Decision

> **DECISION:**  
> The issue is **both a benchmark-labeling discrepancy and a semantic validation flaw**.  
> Under strict task constraints (*"Do not change the benchmark question, answerability label, expected status, or dataset hash without explicit approval"*), `aeris_benchmark.json` **must remain untouched**.  
> Therefore, remediation is focused on the **validator logic**:
> 1. Unrelated chunks (e.g. p. 4 dataset splits) citing generic training terminology must be **firmly rejected** when the requirement demands hardware.
> 2. The validator must strictly require evidence to establish actual hardware facets (e.g., GPUs, TPUs, CPUs, accelerators, compute nodes) when validating hardware-related requirements.
> 3. If Appendix C (p. 17) is ever retrieved in an eligible context, explicit hardware grounding logic will correctly identify the 8 NVIDIA V100 GPUs.
> 4. The benchmark dataset hash remains `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`.

---

## 3. Phase B: Smallest Source Remediation Implementation

### 3.1 `RequirementSupportValidator` (`app/verification/requirement_support.py`)

1. **Directive Term Stopwords:** Added prompt directive verbs (`identify`, `explain`, `describe`, `determine`, `find`, `compare`) to the semantic stopwords list. When a requirement states `"Identify training hardware"`, the validator evaluates `{hardware, training}`, preventing generic match skew.
2. **Facet Decoupling:** Decoupled `train/trained/training` from `location/facility` synonyms.
3. **Domain Ontology for Hardware:** Added an extensive, non-rigid synonym group for hardware concepts:
   `{"hardware", "gpu", "gpus", "tpu", "tpus", "cpu", "cpus", "processor", "processors", "v100", "a100", "h100", "rtx", "nvidia", "amd", "accelerator", "accelerators", "compute", "cluster", "node", "nodes"}`.
4. **Distinctive Facet Enforcement:** When a requirement contains hardware terms, the validator ensures that at least one distinct hardware concept is present in the evidence. Generic dataset splits or generic training routines (`"we train our model with Adam"`) are classified as `REQUIREMENT_UNSATISFIED`.
5. **Bibliography Citation Defense:** Added filtering against bibliographic citations (e.g., `[40] Author et al. Mixed precision training on GPU architectures. In ICLR, 2018`) so that paper references in citations cannot satisfy factual implementation claims.
6. **Short-Requirement Match Threshold:** Set a calibrated match threshold of $\ge 0.50$ for short requirements ($\le 3$ concept tokens) to prevent single-token false positives.

### 3.2 `ClaimExtractor` Timeout & Telemetry (`app/claim_extraction/extractor.py` & `app/config.py`)

1. **Explicit 180s HTTP Timeout:**
   - Added `ollama_claim_extraction_timeout: float = 180.0` in `app/config.py`.
   - Set `DEFAULT_EXTRACTION_TIMEOUT = 180.0` in `app/claim_extraction/extractor.py`.
   - Replaced `self.timeout = config.ollama_timeout` (60s) with `self.timeout = config.ollama_claim_extraction_timeout` (180s).
   - Preserved `ollama_timeout = 60.0` for all other fast generation/planning modules, and kept the 300s system sleep/suspension anomaly threshold intact.
2. **Telemetry & Retries:**
   - Added stage telemetry using `log_generation_attempt("Claim Extraction", ...)`.
   - Implemented bounded retry behavior (`max_retries = 1`, `max_attempts = 2`) for transient read timeouts.
   - Ensured that on final failure/timeout, the exception is logged and re-raised visibly rather than swallowed or silently returned as an empty extraction record.
3. **Pydantic Compatibility:** Updated deprecated `.dict()` calls to `.model_dump()` to ensure clean deprecation-free operation under modern Pydantic.

---

## 4. Phase C: Safety and Test Validation

### 4.1 Backup Verification

Prior to modifying any code, backup archives were recorded in:
`data/recovery_backups/source_backup_20261021_120500_step22e_remediation/`
- `app/config.py`
- `app/claim_extraction/extractor.py`
- `app/verification/requirement_support.py`
- `tests/test_step22e_answer_support_remediation.py`

### 4.2 Targeted Regression & New Unit Tests

Ten new targeted tests were developed and validated:

#### In `tests/test_step22e_answer_support_remediation.py`:
- `test_defect_q_unans_02_dataset_splits_rejected`: Validates that `q_unans_02` with p. 4 dataset splits (`test_document_p004_c010`) is rejected (`NOT_ESTABLISHED`).
- `test_q_unans_02_explicit_hardware_evidence_accepted`: Validates that Appendix C (`test_document_p017_c037`) with 8 NVIDIA V100 GPUs is accepted (`SUPPORTED`).
- `test_generic_train_and_bibliography_cannot_establish_hardware`: Validates that generic training statements and bibliography entries mentioning hardware cannot establish hardware support.
- `test_valid_hardware_paraphrases_accepted`: Validates that valid hardware paraphrases (TPUs, compute nodes, processors) are correctly accepted without rigid keyword locking.

#### In `tests/test_step22e_claim_extraction_timeout.py`:
- `test_claim_extractor_default_timeout_is_180s`: Verifies default timeout is 180s.
- `test_claim_extractor_custom_timeout_override`: Verifies custom timeout override.
- `test_claim_extractor_timeout_exception_remains_visible`: Verifies timeout exceptions are not swallowed into successful evaluations.
- `test_claim_extractor_bounded_retry_success`: Verifies bounded transient retry recovery.
- `test_claim_extractor_telemetry_logging`: Verifies telemetry logging of attempts, durations, and errors.
- `test_claim_extractor_retry_limits`: Verifies retry attempts are bounded (`max_attempts = 2`).

### 4.3 Test Suite Execution Summary

```powershell
python -m pytest tests/
```
**Results:**
- Collected: 95 items
- Passed: 95
- Failed: 0
- Execution Time: 1.54s

```
tests\test_answer_guardrail.py ...                                       [  3%]
tests\test_cache_isolation.py .......                                    [ 10%]
tests\test_integration_measurement_repair.py .....                       [ 15%]
tests\test_json_parsing.py .....                                         [ 21%]
tests\test_profiler_accounting.py ..                                     [ 23%]
tests\test_requirement_support.py .                                      [ 24%]
tests\test_retrieval_vs_citation_metrics.py ....                         [ 28%]
tests\test_scientific_validity.py ....                                   [ 32%]
tests\test_semantic_robustness.py ..........                             [ 43%]
tests\test_step22d1_retrieval_memory_repair.py .........                 [ 52%]
tests\test_step22d_adaptive_retrieval_isolation.py ...                   [ 55%]
tests\test_step22d_answer_support_validation.py .......                  [ 63%]
tests\test_step22d_cross_lingual_agreement.py ....                       [ 67%]
tests\test_step22d_retrieval_memory_scoping.py .....                     [ 72%]
tests\test_step22d_timeouts_and_latency.py ......                        [ 78%]
tests\test_step22e_answer_support_remediation.py ..............          [ 93%]
tests\test_step22e_claim_extraction_timeout.py ......                    [100%]
============================= 95 passed in 1.54s ==============================
```

---

## 5. Byte-for-Byte Integrity Verification

All critical benchmark and historical result artifacts were hashed to confirm zero byte tampering or inadvertent modification:

| Artifact Path | Expected SHA-256 | Actual SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| `data/benchmark/aeris_benchmark.json` | `ce9a86b6...e974` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | **IDENTICAL** |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000.json` | `4d9d1655...e83c` | `4d9d1655378b8123b415110d35f68740a9be9e08f96b65961872ed058e14e83c` | **IDENTICAL** |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000_manifest.json` | `5bbb6cce...9632` | `5bbb6cce9686282562c1d4e9ef58f1692018a348c947b5629572a44cf7c99632` | **IDENTICAL** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_metrics.json` | `863434c4...4a95` | `863434c4a39d55b24ff88bab917de3367b2e29cb49a558b009647fd322514a95` | **IDENTICAL** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_scientific_audit.json` | `d3dde38a...b387` | `d3dde38a897436b9af0dc405f1354dda73b018262d617bda35dd8f96396eb387` | **IDENTICAL** |
| `data/results/exp_final224_step22e_20261020_160000_root_cause_investigation.md` | `10027ef7...38d2` | `10027ef7c541fd65cb9710291fccc4721ed2919e80611c9f9907ee9c374538d2` | **IDENTICAL** |

---

## 6. Changed Files Summary

The minimal set of modifications implemented in this remediation:

1. **`app/config.py`**:
   - Added configuration parameter `ollama_claim_extraction_timeout: float = 180.0`.
2. **`app/claim_extraction/extractor.py`**:
   - Added `DEFAULT_EXTRACTION_TIMEOUT = 180.0`.
   - Wired `self.timeout = config.ollama_claim_extraction_timeout`.
   - Added bounded retry loop (`max_retries = 1`) and telemetry logging (`log_generation_attempt`).
   - Replaced `.dict()` with `.model_dump()`.
3. **`app/verification/requirement_support.py`**:
   - Added directive stopwords (`identify`, `explain`, `describe`, etc.).
   - Decoupled `train` from `location/facility`.
   - Added rich `hardware` ontology and facet validation.
   - Added bibliography false match defense.
   - Adjusted short-requirement match threshold to $\ge 0.50$.
4. **`tests/test_step22e_answer_support_remediation.py`**:
   - Added Tests 11, 12, 13, and 14 for hardware grounding, Appendix C acceptance, bibliography isolation, and paraphrasing.
5. **`tests/test_step22e_claim_extraction_timeout.py`**:
   - Added 6 unit tests covering timeout configuration, timeout exception visibility, bounded retry behavior, and telemetry.

---

## 7. Recommendation for Independent Scientific Audit

1. **Maintain SCIENTIFICALLY BLOCKED Status:** The full 224-record benchmark must not be rerun or resumed until an independent scientific audit explicitly verifies:
   - The mathematical validity of the $\ge 0.50$ concept overlap threshold for short requirements.
   - The benchmark curation policy regarding Appendix C for `q_unans_02`.
   - The robustness of the 180s claim extraction timeout under live Ollama inference load.
2. **Pre-Benchmark Audit Gate:** An independent audit artifact should be compiled and approved before lifting the block.
3. **Prohibition on Step 23:** Step 23 must not be started.
