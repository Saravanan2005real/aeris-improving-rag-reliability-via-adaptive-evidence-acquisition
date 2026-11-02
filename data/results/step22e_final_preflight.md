# AERIS-RAG — Final Preflight Before New Benchmark Authorization

**Date:** 2026-10-21  
**Preflight Type:** Strictly Read-Only Preflight Inspection  
**Benchmark Target:** 224-record scientific ablation benchmark (28 questions $\times$ 8 ablation variants)  
**Target Output Artifact:** `data/results/step22e_final_preflight.md`  
**Governing Audit:** [step22e_postrun_remediation_independent_audit.md](file:///e:/aeris-rag/data/results/step22e_postrun_remediation_independent_audit.md) (`READY FOR A NEW BENCHMARK — SUBJECT TO EXPLICIT AUTHORIZATION`)  
**Current Scientific Status:** SCIENTIFICALLY BLOCKED (Execution strictly prohibited without separate explicit authorization)

---

## 1. Preflight Verification Checklist Summary

| Check ID | Verification Dimension | Status | Key Evidence / Metric |
| :---: | :--- | :---: | :--- |
| **Check 1** | **Remediation State** | `PASS` | Hardware grounding facet check in place; ClaimExtractor 180s timeout configured; bounded retries & telemetry wired; independent audit records PASS. |
| **Check 2** | **Test Suite State** | `PASS` | Most recent verified test run: 95 passed, 0 failed in 1.59s across 17 test modules. Zero code modifications since. |
| **Check 3** | **Benchmark Integrity** | `PASS` | SHA-256 is `ce9a86b6...e974` (exact match). 28 questions $\times$ 8 variants = 224 records. `q_unans_02` intact and untouched. |
| **Check 4** | **Historical Preservation** | `PASS` | All historical experiment artifacts (Step 22D, Step 22E) verified byte-for-byte identical via SHA-256. Blocked Step 22E experiment preserved. |
| **Check 5** | **Runtime Readiness** | `PASS` | Ollama online with `llama3.2:latest`; E: drive has 443.97 GB free; unique experiment ID strategy defined. |
| **Check 6** | **Scientific Reporting** | `PASS` | `q_unans_02` semantic discrepancy documented; separate attrition and false-support reporting mandated; previous benchmark remains BLOCKED. |

**Overall Preflight Status:** **READY FOR A NEW BENCHMARK — SUBJECT TO EXPLICIT AUTHORIZATION**

---

## 2. Check 1: Remediation State Verification

**Status:** `PASS`

1. **Hardware-Grounding Remediation ([app/verification/requirement_support.py](file:///e:/aeris-rag/app/verification/requirement_support.py)):**
   - **Directive Stopwords (lines 184–186):** Stopwords include prompt instructions (`identify`, `identifying`, `explain`, `explaining`, `describe`, `describing`, `determine`, `determining`, `find`, `finding`, `compare`, `comparing`). Requirement `"Identify training hardware"` cleanly isolates `{"training", "hardware"}`.
   - **Synonym Decoupling (lines 205, 209):** `train/trained/training` is decoupled from `location/facility`.
   - **Hardware Ontology (lines 211, 399–404):** `hardware_concept_tokens` covers `{"hardware", "gpu", "gpus", "tpu", "tpus", "cpu", "cpus", "processor", "processors", "v100", "a100", "h100", "nvidia", "accelerator", "accelerators", "compute", "cluster", "supercomputer", "machine", "machines"}`.
   - **Distinctive Facet Check (lines 405–420):** If a requirement specifies hardware, the cited evidence must contain at least one hardware concept token; otherwise it returns `is_supported=False`, `evidence_support_status="NOT_ESTABLISHED"`, and `downgrade_category="REQUIREMENT_UNSATISFIED"`.
   - **Bibliography Defense (lines 424–435):** Paper citations (e.g., `[40] Author et al. ... In ICLR, 2018`) lacking descriptive body statements cannot establish hardware or implementation claims.
   - **Threshold Calibration (line 437):** Short requirements ($\le 3$ concept tokens) enforce a minimum concept overlap ratio of $\ge 0.50$.
   - **Existing Safeguards Preserved:** Lines 260–281 enforce evidence-only matching (no answer self-support); lines 317–376 enforce quantitative grounding and contradiction refutation.

2. **ClaimExtractor 180-Second Timeout ([app/config.py](file:///e:/aeris-rag/app/config.py) & [app/claim_extraction/extractor.py](file:///e:/aeris-rag/app/claim_extraction/extractor.py)):**
   - `app/config.py` line 10 defines `ollama_claim_extraction_timeout: float = 180.0`.
   - `ClaimExtractor.__init__` sets `self.timeout = ... or getattr(settings, "ollama_claim_extraction_timeout", DEFAULT_EXTRACTION_TIMEOUT)` (line 36).
   - In `app/utils/model_client.py` lines 70–76, `httpx.Timeout(..., read=effective_timeout)` configures `read=180.0`.
   - Standard Ollama timeout (`ollama_timeout = 60.0`) remains active for fast planning and generation modules.
   - The system sleep/suspension anomaly threshold (`max_anomaly_latency_seconds = 300.0`) remains separate and unaltered.

3. **Bounded Retries, Exception Propagation, and Telemetry:**
   - Default `max_retries = 1`, bounding execution to at most 2 attempts per chunk (lines 98, 102).
   - On final attempt exhaustion, line 204 executes `raise last_exception`. Timeout and parse failures remain fully visible and are never converted into empty or successful extractions.
   - Telemetry via `log_generation_attempt` is invoked on both success (lines 157–169) and failure (lines 186–198).
   - Cache write occurs strictly at line 181 after complete extraction and schema validation, eliminating the risk of partial or duplicate records.

4. **Independent Audit Confirmation:**
   - The independent audit report [step22e_postrun_remediation_independent_audit.md](file:///e:/aeris-rag/data/results/step22e_postrun_remediation_independent_audit.md) was reviewed. It officially records:
     > **Final Audit Verdict: READY FOR A NEW BENCHMARK — SUBJECT TO EXPLICIT AUTHORIZATION**

---

## 3. Check 2: Test Suite State

**Status:** `PASS`

1. **Latest Test Results Inspection:**
   - The test suite was executed under Python 3.10.0 and pytest 9.1.1:
     ```powershell
     python -m pytest tests/ -v
     ```
   - **Total Tests:** 95 collected
   - **Passed:** 95
   - **Failed:** 0
   - **Execution Time:** 1.59s
   - **Modules Tested:** 17 test modules, including:
     - `test_step22e_answer_support_remediation.py`: 14 tests (Tests 11–14 covering p. 4 rejection, Appendix C acceptance, bibliography blocking, hardware paraphrases).
     - `test_step22e_claim_extraction_timeout.py`: 6 tests (180s default timeout, custom timeout override, exception visibility, bounded retry recovery, telemetry logging, retry limits).
     - All regression suites: cache isolation, retrieval memory repair, adaptive retrieval scoping, answer guardrails, latency contamination, profiler accounting, and scientific validity.
2. **Current State:**
   - Git working tree inspection confirms that zero source code or test files have been altered since the verified 95-test run.
   - In accordance with preflight instructions (*"do not run tests unless separately authorized"*), no unprompted test suite was run during this preflight turn.

---

## 4. Check 3: Benchmark Integrity Verification

**Status:** `PASS`

1. **SHA-256 Hash Verification:**
   - Benchmark File: `data/benchmark/aeris_benchmark.json`
   - Baseline SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`
   - Current SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`
   - Result: **100% BYTE-FOR-BYTE IDENTICAL**.
2. **Benchmark Dimensionality:**
   - Number of Questions: 28 questions.
   - Number of Ablation Variants: 8 variants (`FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`).
   - Expected Benchmark Records: $28 \times 8 = 224$ records.
3. **Question `q_unans_02` Status:**
   - Question: *"What hardware was used to train the RAG models?"*
   - Category: `UNANSWERABLE`
   - Expected Answer: `null`
   - Expected Claims: `[]`
   - Supporting Chunk IDs: `[]`
   - Supporting Pages: `[]`
   - Expected Status: `INSUFFICIENT_EVIDENCE`
   - Answerability: `false`
   - Result: **Preserved without modification**.

---

## 5. Check 4: Historical Preservation

**Status:** `PASS`

All previous experiment artifacts and audit reports are preserved and verified unchanged:

| Artifact Path | Expected Baseline SHA-256 | Current SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000.json` | `4d9d1655...e83c` | `4d9d1655378b8123b415110d35f68740a9be9e08f96b65961872ed058e14e83c` | **MATCH** |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000_manifest.json` | `5bbb6cce...9632` | `5bbb6cce9686282562c1d4e9ef58f1692018a348c947b5629572a44cf7c99632` | **MATCH** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_metrics.json` | `863434c4...4a95` | `863434c4a39d55b24ff88bab917de3367b2e29cb49a558b009647fd322514a95` | **MATCH** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_scientific_audit.json` | `d3dde38a...b387` | `d3dde38a897436b9af0dc405f1354dda73b018262d617bda35dd8f96396eb387` | **MATCH** |
| `data/results/exp_final224_step22e_20261020_160000_root_cause_investigation.md` | `10027ef7...38d2` | `10027ef7c541fd65cb9710291fccc4721ed2919e80611c9f9907ee9c374538d2` | **MATCH** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200.json` | `df985020...d6cf` | `df9850207668edaa59d3ce4f5acc7074c119f72b12ce0a4c86638c24197dd6cf` | **MATCH** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000.json` | `a043dadd...9bf3` | `a043dadd00685e59310564ffaba14a697eb3ebcd6c3879f2a619f829f9039bf3` | **MATCH** |
| `data/results/step22e_postrun_remediation_report.md` | `061ae55b...8976` | `061ae55b121ed7f3ecb5aaafc098a3bdb78ccd541d8dac5f2e629c2f0c18976d` | **MATCH** |
| `data/results/step22e_postrun_remediation_independent_audit.md` | `723e91d0...a856` | `723e91d05a56a3ba8864c3560cf7e5277f95b785769651a5e5b2691ee6f5a856` | **MATCH** |

- **No Overwrite Policy:** The blocked Step 22E experiment ID `exp_final224_step22e_20261020_160000` is strictly sealed. Any future run will use a new, unique experiment ID.

---

## 6. Check 5: Runtime Readiness

**Status:** `PASS`

1. **Ollama Service & Model Availability:**
   - Endpoint: `http://localhost:11434/api/tags`
   - Service Status: **ONLINE**
   - Configured Generation Model: `llama3.2:latest` (Present)
   - Configured Embedding Model: `nomic-embed-text:latest` (Present)
   - Other Local Models: `llama3.2:3b`, `mistral:latest`, `qwen2.5:3b`, `llava:latest`, `tneb-agent:latest`.
2. **Storage Resources:**
   - Workspace Drive (`E:\`): **443.97 GB Free** / 476.93 GB Total.
   - System/Model Drive (`C:\`): **30.01 GB Free** / 474.72 GB Total.
   - Capacity is more than sufficient for storing raw outputs, manifest files, and jsonl diagnostics (< 100 MB per run).
3. **Execution Script & Output Paths:**
   - Runner Script: `scripts/run_final_224_evaluation.py`
   - Proposed Unique Experiment ID Strategy:
     `exp_final224_step22e_remediation_YYYYMMDD_HHMMSS` (e.g. `exp_final224_step22e_remediation_20261021_130000`).
   - Planned Output Paths:
     - Results: `data/results/ablation_results_exp_final224_step22e_remediation_<timestamp>.json`
     - Diagnostics: `data/results/ablation_results_exp_final224_step22e_remediation_<timestamp>_diagnostics.jsonl`
     - Manifest: `data/results/ablation_results_exp_final224_step22e_remediation_<timestamp>_manifest.json`
4. **Runtime Risks & Operational Mitigations:**
   - **Timeout Headroom:** The 180s claim extraction timeout provides a $3\times$ safety margin over the previous 60s timeout that caused the transient timeout at 73.5s on `q_mh_03` in Step 22E.
   - **Concurrency:** Single-process sequential execution is maintained by `AblationRunner` to prevent GPU memory thrashing on local hardware.
   - **Execution Time:** A full 224-record run is projected to take approximately 35–45 minutes of active Ollama inference.

---

## 7. Check 6: Scientific Reporting Governance

**Status:** `PASS`

1. **Documentation of `q_unans_02` Discrepancy:**
   - **Benchmark Ground Truth:** `q_unans_02` is marked `UNANSWERABLE` with `expected_status: "INSUFFICIENT_EVIDENCE"` and `supporting_chunk_ids: []`.
   - **Document Factuality:** Appendix C (page 17, `test_document_p017_c037`) contains hardware details (*"8, 32GB NVIDIA V100 GPUs"*). The vector index contains all 42 chunks across pages 1–19, and pages 18–19 are cited by other benchmark questions.
   - **Strict Protocol:** The benchmark dataset label and hash remain strictly preserved (`ce9a86b6...`). In Step 22E, the system cited page 4 (`test_document_p004_c010`), which contains zero hardware concepts; the validator falsely approved it due to generic `"train"` matching. Under the remediated validator, page 4 is strictly rejected.
2. **Next Experiment Audit Mandate:**
   - The post-run scientific audit for the next experiment must report:
     - **Execution Attrition Rate:** Count of timeouts, connection drops, or malformed generation records.
     - **False-Support Rate:** Grounding accuracy specifically on unanswerable and out-of-scope questions.
     - These two metrics must be tracked and analyzed as independent scientific dimensions.
3. **Historical Baseline Integrity:**
   - Experiment `exp_final224_step22e_20261020_160000` remains documented as **BLOCKED and REJECTED** due to the 7 false-supported records on `q_unans_02`. It is not claimed to have passed.

---

## 8. Final Recommendation

### **TECHNICAL STATUS: READY FOR A NEW BENCHMARK**
### **OPERATIONAL STATUS: STRICTLY BLOCKED AWAITING EXPLICIT AUTHORIZATION**

All six preflight verification gates evaluated to **`PASS`**. There are zero technical blockers preventing the execution of a clean 224-record benchmark. 

However, in accordance with the experimental safeguard protocols:
1. **No benchmark run was started or resumed.**
2. **Step 23 was not started.**
3. **A separate, explicit authorization from the user is required before launching the next benchmark.**
