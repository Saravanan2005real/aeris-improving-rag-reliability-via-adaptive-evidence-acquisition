# AERIS-RAG — Independent Scientific and Engineering Audit of Step 22E Post-Run Remediation

**Audit Date:** 2026-10-21  
**Auditor:** Independent Scientific & Engineering Auditor (Automated Antigravity Pair-Programming Agent)  
**Target Document:** `data/results/step22e_postrun_remediation_report.md`  
**Current Operational Status:** SCIENTIFICALLY BLOCKED (Execution of full 224-record benchmark strictly prohibited without separate explicit authorization)

---

## 1. Executive Summary & Audit Mandate

This report provides an independent, strictly read-only scientific and engineering audit of the remediations performed following the Step 22E benchmark anomalies (`exp_final224_step22e_20261020_160000`).

The audit covers five mandatory dimensions:
1. Grounding and evidence-scope discrepancy of benchmark question `q_unans_02`.
2. Hardware grounding and validation repairs in `RequirementSupportValidator`.
3. Claim-extraction timeout configuration (180s), bounded retries, and telemetry logging in `ClaimExtractor`.
4. Test validity, mock inspection, and test suite execution integrity.
5. Byte-for-byte SHA-256 integrity verification of the benchmark dataset and all historical artifacts.

---

## 2. Audit Finding 1: `q_unans_02` Evidence-Scope Discrepancy

**Status:** `VERIFIED`

### 2.1 Primary Evidence Verification
- **Benchmark Entry ([aeris_benchmark.json](file:///e:/aeris-rag/data/benchmark/aeris_benchmark.json)):**
  - `question_id`: `"q_unans_02"`
  - `question`: *"What hardware was used to train the RAG models?"*
  - `category`: `"UNANSWERABLE"`
  - `answerability`: `false`
  - `expected_status`: `"INSUFFICIENT_EVIDENCE"`
  - `supporting_chunk_ids`: `[]` (Empty list)
  - `supporting_pages`: `[]` (Empty list)
- **Document Text ([data/indexes/test_document/metadata.json](file:///e:/aeris-rag/data/indexes/test_document/metadata.json)):**
  - Chunk ID: `test_document_p017_c037` (Page 17, Section C: *"Training setup Details"*)
  - Explicit Text:
    > *"We train all RAG models and BART baselines using Fairseq [45]. We train with mixed precision floating point arithmetic [40], distributing training across 8, 32GB NVIDIA V100 GPUs, though training and inference can be run on one GPU."*
- **Corpus & Retrieval Scope:**
  - The corpus index contains 42 chunks across pages 1 through 19. All 19 pages are indexed in the vector store.
  - Appendix pages 18 and 19 are actively cited as ground-truth evidence for multiple benchmark questions, including `q_df_03` (pages 2, 18, 19), `q_df_05` (page 18), `q_mh_01` (pages 6, 18), `q_mh_03` (pages 18, 19), and `q_contra_02` (pages 8, 18).
  - No index filter or retrieval boundary currently excludes Appendix C (page 17).

### 2.2 Implications for False-Support Scoring and Scientific Validity
1. **The Core Defect in Step 22E:** In experiment `exp_final224_step22e_20261020_160000`, the retrieval engine did **not** retrieve Appendix C (p. 17). It retrieved chunk `test_document_p004_c010` (p. 4), which discusses `"train/dev/test splits"` and abstractive QA on MSMARCO. The validator scored this chunk as `SUPPORTED` due to the generic presence of the token `"train"`, producing 7 false-supported records across all 7 ablation variants.
2. **Benchmark Validity Implication:** The issue is a dual discrepancy:
   - A **benchmark-labeling flaw**: The benchmark curator marked `q_unans_02` as `UNANSWERABLE` on the assumption that the paper did not disclose hardware, whereas Appendix C explicitly does.
   - An **overly permissive semantic validation flaw**: The validator accepted an unrelated text chunk (p. 4) that contains zero hardware information.
3. **Audit Assessment:** The benchmark cannot be declared valid merely because the question is answerable in Appendix C, because in the actual run the system cited p. 4, which is factually unsupported. Furthermore, altering the benchmark dataset without authorization would corrupt the historical baseline. Preserving the benchmark dataset hash (`ce9a86b6...`) while fixing the validator to strictly require hardware concepts in cited evidence is scientifically sound and appropriate.

---

## 3. Audit Finding 2: Hardware Grounding Remediation

**Status:** `VERIFIED`

### 3.1 Trace of `RequirementSupportValidator` with Unrelated Page 4 Evidence
- **File:** [app/verification/requirement_support.py](file:///e:/aeris-rag/app/verification/requirement_support.py)
- **Trace Details:**
  1. **Stopword Filtering (lines 179–186):** When evaluating requirement `"Identify training hardware"`, directive verbs (`identify`, `explain`, `describe`, etc.) are removed, yielding target tokens `{"training", "hardware"}`.
  2. **Facet Decoupling (lines 205, 209):** `train/trained/training` is isolated in its own synonym group and decoupled from location/facility.
  3. **Hardware Concept Ontology (lines 211, 399–404):** `hardware_concept_tokens` explicitly defines hardware synonyms (`hardware`, `gpu`, `gpus`, `tpu`, `tpus`, `cpu`, `cpus`, `processor`, `processors`, `v100`, `a100`, `nvidia`, `accelerator`, `compute`, `cluster`, `node`, etc.).
  4. **Distinctive Facet Check (lines 405–420):** 
     ```python
     if any(w in combined_target_tokens for w in {"hardware", "gpu", ...}):
         source_has_hardware = any(w in source_tokens for w in hardware_concept_tokens)
         if not source_has_hardware:
             return RequirementSupportResult(
                 is_supported=False,
                 evidence_support_status="NOT_ESTABLISHED",
                 rationale="Target requirement specifies hardware...",
                 downgrade_category="REQUIREMENT_UNSATISFIED",
             )
     ```
  5. **Page 4 Evaluation:** Evidence chunk `test_document_p004_c010` contains `"train/dev/test splits"` but zero hardware tokens. `source_has_hardware` evaluates to `False`. The validator returns `is_supported=False`, `evidence_support_status="NOT_ESTABLISHED"`, and `downgrade_category="REQUIREMENT_UNSATISFIED"`.
  6. **Judge LLM Override (lines 148–153):** If an LLM judge is active and attempts to hallucinate support from outside knowledge, the deterministic guardrail firmly forces `is_sup = False` and status to `NOT_ESTABLISHED`.

### 3.2 Generic Matches and Bibliography Isolation
- **Generic "train" Routines:** Statements like *"We train all models using the Adam optimizer"* lack hardware concepts and are rejected at line 407.
- **Bibliographic Citations (lines 424–435):** If evidence is a reference string (e.g., `"[40] Paulius Micikevicius et al. Mixed precision training on GPU architectures. In ICLR, 2018"`), `is_bib_entry` matches and detects that no descriptive body statements (`"we train"`, `"our model"`, `"distributed training"`) exist. It returns `NOT_ESTABLISHED` with `REQUIREMENT_UNSATISFIED`.

### 3.3 Explicit Hardware Evidence & Paraphrases
- **Appendix C (p. 17):** Text contains `"8, 32GB NVIDIA V100 GPUs"`. `source_has_hardware` is `True`. Concept `"training"` matches via training synonym group; concept `"hardware"` matches via `{"nvidia", "v100", "gpus"}`. Match ratio is 1.0 $\ge 0.50$, returning `is_supported=True`, `evidence_support_status="SUPPORTED"`.
- **Paraphrases (TPUs, compute nodes, processors):** Validated in `test_valid_hardware_paraphrases_accepted`. Paraphrases like *"Trained on a cluster of TPU v3 accelerators"* match both training and hardware concepts without requiring rigid literal keywords.

### 3.4 Preservation of Prior Safeguards
- **Self-Support Prevention (lines 260–281):** Tokens are matched strictly against `source_evidence_text = " ".join(claims) + " " + evidence_str`, never against `answer`.
- **Quantitative Entailment & Contradictions (lines 317–376):** Number extraction, normalization, and contradiction detection (`CONTRADICTED_BY_EVIDENCE`) remain fully active.
- **Short-Requirement Threshold (line 437):** Set to $\ge 0.50$ for requirements with $\le 3$ concept tokens, preventing single-token false positives.

---

## 4. Audit Finding 3: Claim-Extraction Timeout and Retry Remediation

**Status:** `VERIFIED`

### 4.1 Timeout Configuration Trace
- **Configuration Parameter ([app/config.py](file:///e:/aeris-rag/app/config.py#L10)):**
  `ollama_claim_extraction_timeout: float = 180.0`
- **ClaimExtractor Default ([app/claim_extraction/extractor.py](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L15-L37)):**
  `DEFAULT_EXTRACTION_TIMEOUT = 180.0`
  ```python
  self.timeout = timeout if timeout is not None else getattr(settings, "ollama_claim_extraction_timeout", DEFAULT_EXTRACTION_TIMEOUT)
  ```
- **Client Construction ([app/utils/model_client.py](file:///e:/aeris-rag/app/utils/model_client.py#L56-L77)):**
  ```python
  effective_timeout = timeout if timeout is not None else settings.ollama_timeout
  httpx_timeout = httpx.Timeout(
      timeout=effective_timeout,
      connect=effective_connect_timeout,
      read=effective_timeout,
      write=effective_timeout,
      pool=effective_connect_timeout,
  )
  return ollama.Client(host=effective_host, timeout=httpx_timeout)
  ```
  **Runtime HTTP Read Timeout Confirmation:** When `ClaimExtractor` initializes, `effective_timeout` is 180.0s. The underlying `httpx.Timeout.read` is configured to `180.0s`. Fast generation/planning components continue to use `settings.ollama_timeout` (60.0s).

### 4.2 Retry Limits, Telemetry, and Failure Visibility
- **Retry Bounds (lines 98, 102, 203–204):**
  - Default `max_retries = 1`, resulting in `max_attempts = 2`.
  - If attempt 1 encounters a read timeout or transient JSON error, attempt 2 executes.
  - If attempt 2 fails, line 204 executes: `raise last_exception`.
  - The timeout or extraction exception is propagated visibly to the controller/runner. Failures are never converted into empty or successful evaluations.
- **Telemetry Logging (lines 157–169, 186–198):**
  `log_generation_attempt` is invoked on both successful and failed attempts, recording `stage="Claim Extraction"`, attempt number, context character length, latency, parse success, schema success, and retry status.
- **No Risk of Duplicate or Partial Claims:**
  - Cache lookup occurs at line 94.
  - Cache write occurs strictly at line 181 after successful completion of all parsing and claim validation.
  - On failure, no cache write occurs, preventing partial or corrupt cached claims.

### 4.3 Separation from Sleep/Suspension Anomaly Threshold
- `app/config.py` line 11 sets `max_anomaly_latency_seconds: float = 300.0`.
- In `app/utils/model_client.py` line 87, `max_anomaly_seconds` detects system sleep/suspension via monotonic vs wall-clock skew.
- The 180.0s claim extraction timeout operates entirely at the HTTP client level and does not alter the 300.0s system anomaly threshold.

---

## 5. Audit Finding 4: Test Validity

**Status:** `VERIFIED`

### 5.1 Inspection of New Tests
- **[tests/test_step22e_answer_support_remediation.py](file:///e:/aeris-rag/tests/test_step22e_answer_support_remediation.py):**
  - `test_defect_q_unans_02_dataset_splits_rejected`: Instantiates production `RequirementSupportValidator`, supplies the exact text from p. 4 (`test_document_p004_c010`), and asserts rejection (`NOT_ESTABLISHED`, `REQUIREMENT_UNSATISFIED`).
  - `test_q_unans_02_explicit_hardware_evidence_accepted`: Supplies Appendix C text (`test_document_p017_c037`) and asserts `SUPPORTED`.
  - `test_generic_train_and_bibliography_cannot_establish_hardware`: Validates rejection of both generic Adam optimizer statements and bibliography citation lines.
  - `test_valid_hardware_paraphrases_accepted`: Validates multi-case paraphrases (TPUs, AMD compute nodes).
  - *Evaluation:* These tests use live production code and real document text without mocks bypassing the validation algorithms.
- **[tests/test_step22e_claim_extraction_timeout.py](file:///e:/aeris-rag/tests/test_step22e_claim_extraction_timeout.py):**
  - `test_claim_extractor_default_timeout`: Instantiates real `ClaimExtractor()` and directly inspects `extractor.client._client.timeout.read == 180.0`.
  - `test_claim_extractor_custom_timeout_override`: Tests explicit custom timeout override.
  - `test_claim_extractor_timeout_error_raised_when_exhausted`: Verifies that `ModelTimeoutError` is raised visibly after 2 attempts.
  - `test_claim_extractor_retry_success_after_transient_failure`: Verifies recovery on attempt 2 without duplicates.
  - `test_claim_extractor_telemetry_recorded`: Verifies telemetry arguments.
  - `test_claim_extractor_retry_limit_enforced`: Verifies `max_retries = 0` limits attempts to 1.
  - *Evaluation:* Timeout tests correctly mock the remote model response while exercising the real retry loop, client configuration, and exception propagation logic.

### 5.2 Test Suite Execution Output
```
Command: python -m pytest tests/
Status: 95 passed in 1.59s (0 failed, 0 errors)
Test modules: 17
```
All existing tests across retrieval memory, cache isolation, answer guardrails, semantic robustness, latency accounting, and scientific validity passed cleanly.

---

## 6. Audit Finding 5: Integrity Verification

**Status:** `VERIFIED`

Independent SHA-256 verification confirms that no benchmark data or historical experiment artifacts were modified:

| Artifact Path | Expected Baseline SHA-256 | Current Computed SHA-256 | Match |
| :--- | :--- | :--- | :--- |
| `data/benchmark/aeris_benchmark.json` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | **YES** |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000.json` | `4d9d1655378b8123b415110d35f68740a9be9e08f96b65961872ed058e14e83c` | `4d9d1655378b8123b415110d35f68740a9be9e08f96b65961872ed058e14e83c` | **YES** |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000_manifest.json` | `5bbb6cce9686282562c1d4e9ef58f1692018a348c947b5629572a44cf7c99632` | `5bbb6cce9686282562c1d4e9ef58f1692018a348c947b5629572a44cf7c99632` | **YES** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_metrics.json` | `863434c4a39d55b24ff88bab917de3367b2e29cb49a558b009647fd322514a95` | `863434c4a39d55b24ff88bab917de3367b2e29cb49a558b009647fd322514a95` | **YES** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_scientific_audit.json` | `d3dde38a897436b9af0dc405f1354dda73b018262d617bda35dd8f96396eb387` | `d3dde38a897436b9af0dc405f1354dda73b018262d617bda35dd8f96396eb387` | **YES** |
| `data/results/exp_final224_step22e_20261020_160000_root_cause_investigation.md` | `10027ef7c541fd65cb9710291fccc4721ed2919e80611c9f9907ee9c374538d2` | `10027ef7c541fd65cb9710291fccc4721ed2919e80611c9f9907ee9c374538d2` | **YES** |
| `data/results/step22e_postrun_remediation_report.md` | `061ae55b121ed7f3ecb5aaafc098a3bdb78ccd541d8dac5f2e629c2f0c18976d` | `061ae55b121ed7f3ecb5aaafc098a3bdb78ccd541d8dac5f2e629c2f0c18976d` | **YES** |

---

## 7. Audit Checklist & Summary Matrix

| Audit Item | Target | Finding | Evidence |
| :--- | :--- | :--- | :--- |
| **1. Evidence Scope** | `q_unans_02` semantic verification | `VERIFIED` | Appendix C (p. 17) has hardware; p. 4 lacks hardware; benchmark hash unchanged. |
| **2. Hardware Grounding** | `RequirementSupportValidator` | `VERIFIED` | Distinctive facet check blocks p. 4; bibliography filter blocks citations; paraphrases supported. |
| **3. Timeout & Retry** | `ClaimExtractor` 180s timeout | `VERIFIED` | `httpx` read timeout = 180s; bounded retry = 2 attempts; errors remain visible; 300s anomaly separate. |
| **4. Test Validity** | Unit & regression tests | `VERIFIED` | 10 new tests exercise real production behavior; full suite: 95 passed in 1.59s. |
| **5. Data Integrity** | Benchmark & historical artifacts | `VERIFIED` | All SHA-256 hashes byte-for-byte identical; zero unauthorized edits. |

---

## 8. Final Verdict

### **READY FOR A NEW BENCHMARK — SUBJECT TO EXPLICIT AUTHORIZATION**

> [!IMPORTANT]
> **Operational Safeguard Notice:**  
> This passing audit confirms that the engineering and scientific remediation is sound, complete, and verified. However, pursuant to experimental governance protocols:
> 1. This audit **does NOT authorize or launch** a benchmark run.
> 2. The 224-record benchmark remains **unexecuted**.
> 3. Step 23 remains **unstarted**.
> 4. A separate explicit user authorization is required before initiating any new benchmark execution.
