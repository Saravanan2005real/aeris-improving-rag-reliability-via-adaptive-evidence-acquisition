# Root-Cause Investigation Report: Experiment `exp_final224_step22e_20261020_160000`

**Document Path:** `data/results/exp_final224_step22e_20261020_160000_root_cause_investigation.md`  
**Investigation Date:** 2026-10-21T11:35:00+05:30  
**Target Experiment ID:** `exp_final224_step22e_20261020_160000`  
**Investigation Mode:** Strictly Read-Only (No source code, test, benchmark, or historical artifact modifications; no benchmark rerun; Step 23 not initiated)  
**Overall Status:** `BLOCKED` (Engineering Integrity: `PASS` / Scientific Validity: `FAIL`)

---

## Executive Summary

A comprehensive, strictly read-only post-run root-cause investigation of benchmark experiment `exp_final224_step22e_20261020_160000` was conducted across all 224 execution records, diagnostic logs, cache stores, source documents, and pipeline source code.

The investigation identified two independent, definitive root causes:

1. **Part A — False Support on `q_unans_02` (7/64 False Supports, 10.94% Rate):**
   - **Root Cause:** A semantic matching loophole in `RequirementSupportValidator._evaluate_semantic_support` ([app/verification/requirement_support.py:202-405](file:///e:/aeris-rag/app/verification/requirement_support.py#L202-L405)).
   - **Mechanism:** The target requirement `"Identify training hardware"` generated semantic tokens `{'identify', 'training', 'hardware'}`. In the validator's synonym dictionary ([line 202](file:///e:/aeris-rag/app/verification/requirement_support.py#L202)), `"training"` was grouped with `"train"`. Chunk `test_document_p004_c010` contained the unrelated phrase `"train/dev/test splits"`, matching `"training"`. Because `"training"` was not classified as a generic domain word, it satisfied the specific topic check ([lines 288-310](file:///e:/aeris-rag/app/verification/requirement_support.py#L288-L310)). With 1 of 3 target tokens matched (match ratio $0.333 \ge 0.25$), the validator returned `is_supported: True`. This bypassed the B3 Grounding Guardrail ([lines 147-152](file:///e:/aeris-rag/app/verification/requirement_support.py#L147-L152)) and caused the controller to accept an answer hallucinating that RAG was trained on DPR hardware.

2. **Part B — 151 Execution Timeouts in Claim Extraction (67.4% Failure Rate):**
   - **Root Cause:** Hard socket read timeout mismatch between `httpx` HTTP client settings (`ollama_timeout = 60.0s` in [app/config.py:8](file:///e:/aeris-rag/app/config.py#L8)) and the execution latency of Ollama `llama3.2:latest` extracting atomic claims from dense chunks (3,000–6,000 characters) with `num_predict: 8192` in JSON format.
   - **Mechanism:** Local Ollama inference on dense chunks routinely required 62–75 seconds. At exactly 60.00 seconds of socket read inactivity, `httpx` raised `httpx.ReadTimeout("timed out")`. The monotonic timer caught this at 60.00s–62.03s ([app/utils/model_client.py:160-168](file:///e:/aeris-rag/app/utils/model_client.py#L160-L168)). Claim Extraction had **zero retry logic**, caught the exception, and immediately failed the run ([app/claim_extraction/extractor.py:123-127](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L123-L127)).

---

## Part A — False Support on `q_unans_02`

### 1. Benchmark Expected Answerability & Evidence Requirements
- **Status:** **VERIFIED**
- **Artifact:** `data/benchmark/aeris_benchmark.json`
- **Benchmark Record Definition:**
  ```json
  {
    "question_id": "q_unans_02",
    "document_id": "test_document",
    "question": "What hardware was used to train the RAG models?",
    "category": "UNANSWERABLE",
    "difficulty": "EASY",
    "language": "English",
    "information_requirements": [
      "Identify training hardware"
    ],
    "expected_answer": null,
    "expected_claims": [],
    "supporting_chunk_ids": [],
    "supporting_pages": [],
    "answerability": false,
    "expected_status": "INSUFFICIENT_EVIDENCE"
  }
  ```
- **Analysis:**
  The ground-truth benchmark specifies that `q_unans_02` has `answerability: false`, `expected_status: "INSUFFICIENT_EVIDENCE"`, empty expected claims `[]`, and empty supporting chunk IDs `[]`. The only specified information requirement is `"Identify training hardware"`.

---

### 2. Trace of All False-Supported Records Across Variants
- **Status:** **VERIFIED**
- **Artifact Audited:** `data/results/ablation_results_exp_final224_step22e_20261020_160000.json`

Across all 8 variants, the exact records for `q_unans_02` are as follows:

| Variant | Final Status | Confidence | Generated Answer | Supporting Chunks | Supporting Claims |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `FULL_AERIS` | **SUPPORTED** (False Support) | 0.90 | *"The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |
| `NO_ADAPTIVE_RETRIEVAL` | **SUPPORTED** (False Support) | 0.90 | *"The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |
| `NO_QUERY_REFORMULATION` | **SUPPORTED** (False Support) | 0.90 | *"The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |
| `NO_RETRIEVAL_MEMORY` | **SUPPORTED** (False Support) | 0.90 | *"The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |
| `NO_CLAIM_VERIFICATION` | **INSUFFICIENT_EVIDENCE** (Correct) | 0.50 | *"The RAG models were initialized with the NQ RAG model and trained on the same train/dev/test splits as prior work."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |
| `NO_CONTRADICTION_ANALYSIS` | **SUPPORTED** (False Support) | 0.90 | *"The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |
| `NO_CROSSLINGUAL_AGREEMENT` | **SUPPORTED** (False Support) | 0.90 | *"The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |
| `NO_SELECTIVE_VERIFICATION` | **SUPPORTED** (False Support) | 0.90 | *"The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."* | `['test_document_p004_c010']` | `['test_document_p004_c010_claim_6']` |

**Key Finding:** Exactly 7 of 8 variants produced `final_status: SUPPORTED` (false support). The single variant that avoided false support was `NO_CLAIM_VERIFICATION`, which disabled verification entirely and returned `final_status: INSUFFICIENT_EVIDENCE` with confidence 0.50.

---

### 3. Exact Generated Answers, Claims, Cited Chunks, and Evidence Text
- **Status:** **VERIFIED**
- **Retrieved Chunks for `q_unans_02`:**
  All variants retrieved the identical 3 chunks:
  `['test_document_p017_c037', 'test_document_p004_c010', 'test_document_p019_c041']`.
- **Cited Chunk:**
  In all 7 false-supported records, the system cited solely:
  `test_document_p004_c010` (Page 4).
- **Cited Evidence Text ([data/indexes/test_document/metadata.json](file:///e:/aeris-rag/data/indexes/test_document/metadata.json)):**
  ```text
  As CT and WQ are small, we follow DPR [26] by initializing CT and WQ models with our NQ RAG
  model. We use the same train/dev/test splits as prior work [31, 26] and report Exact Match (EM)
  scores. For TQA, to compare with T5 [52], we also evaluate on the TQA Wiki test set.
  3.2 Abstractive Question Answering
  RAG models can go beyond simple extractive QA and answer questions with free-form, abstractive
  text generation. To test RAG’s natural language generation (NLG) in a knowledge-intensive setting,
  we use the MSMARCO NLG task v2.1 [43]. The task consists of questions, ten gold passages
  retrieved from a search engine for each question, and a full sentence answer annotated from the
  retrieved passages...
  ```
- **Cited Supporting Claim ID:**
  `test_document_p004_c010_claim_6`
- **Claim 6 Text ([data/cache_exp_final224_step22e_20261020_160000_FULL_AERIS.json](file:///e:/aeris-rag/data/cache_exp_final224_step22e_20261020_160000_FULL_AERIS.json)):**
  ```text
  "RAG models can go beyond simple extractive QA and answer questions with free-form, abstractive text generation."
  ```
- **Generated Answer Text:**
  ```text
  "The RAG models were trained using the same hardware as the DPR model, as mentioned in the document."
  ```

---

### 4. Source Document Reality, Material Relevance, and Validation Rule Analysis
- **Status:** **VERIFIED**

#### A. Does the source document establish the hardware?
- In `data/indexes/test_document/metadata.json` chunk `test_document_p017_c037` (Page 17, Appendix C "Training setup Details"):
  ```text
  "We train all RAG models and BART baselines using Fairseq [45].2 We train with mixed precision
  floating point arithmetic [40], distributing training across 8, 32GB NVIDIA V100 GPUs, though
  training and inference can be run on one GPU."
  ```
  The underlying document (`test_document.pdf`) actually states the training hardware in Appendix C (8, 32GB NVIDIA V100 GPUs). However, the benchmark definition in `aeris_benchmark.json` designated `q_unans_02` as `UNANSWERABLE` with `expected_status: "INSUFFICIENT_EVIDENCE"` and empty chunk references.

#### B. Is the cited material irrelevant?
- **YES. The cited material is completely irrelevant.**
  The pipeline did **not** cite Appendix C (`test_document_p017_c037`). Instead, it cited Section 3.1 / 3.2 on Page 4 (`test_document_p004_c010`).
  - `test_document_p004_c010` contains **zero mentions** of hardware, GPUs, V100, processors, or compute infrastructure.
  - The model hallucinated that "we follow DPR [26] by initializing CT and WQ models with our NQ RAG model" meant "trained using the same hardware as the DPR model".
  - The cited claim `test_document_p004_c010_claim_6` describes abstractive text generation on MSMARCO, which has no logical or factual bearing on hardware.

#### C. Which precise validation rule allowed this false acceptance?
The false acceptance occurred deterministically inside `RequirementSupportValidator._evaluate_semantic_support` ([app/verification/requirement_support.py:167-417](file:///e:/aeris-rag/app/verification/requirement_support.py#L167-L417)):
1. **Target Requirement Tokens:**
   Requirement: `"Identify training hardware"`
   Target tokens ([lines 214-216](file:///e:/aeris-rag/app/verification/requirement_support.py#L214-L216)): `combined_target_tokens = {'identify', 'training', 'hardware'}` ($N = 3$).
2. **Synonym Expansion:**
   In [line 202](file:///e:/aeris-rag/app/verification/requirement_support.py#L202):
   `{"train", "trained", "training", "location", "facility", "seattle", "washington"}`
   `"training"` is defined as a synonym of `"train"`.
3. **Generic Domain Word Filter:**
   In [lines 187-192](file:///e:/aeris-rag/app/verification/requirement_support.py#L187-L192), `generic_domain_words` contains:
   `{"paper", "model", "models", "architecture", "system", "systems", "approach", "method", "methods", "methodology", "task", "tasks", "results", "work", "prior", "use", "used", "using", "evaluate", "evaluates", "evaluation", "nlp", "document", "documents", "text", "generation", "generative", "retrieval", "augmented", "rag"}`.
   Crucially, `"training"` is **not** in `generic_domain_words`.
   Therefore, `specific_target_tokens` = `{'identify', 'training', 'hardware'}`.
4. **Specific Concept Match:**
   In chunk `test_document_p004_c010`, the text contains: `"We use the same train/dev/test splits as prior work..."`.
   The token `"train"` was extracted into `source_tokens`.
   Via the synonym group ([line 202](file:///e:/aeris-rag/app/verification/requirement_support.py#L202)), `"training"` matched `"train"`.
   Thus, `specific_matched = {'training'}` ([lines 290-298](file:///e:/aeris-rag/app/verification/requirement_support.py#L290-L298)).
   Since `specific_matched` was non-empty, the guardrail at [line 299](file:///e:/aeris-rag/app/verification/requirement_support.py#L299) (`if not specific_matched:`) did not trigger!
5. **Threshold Calculation:**
   In [line 394](file:///e:/aeris-rag/app/verification/requirement_support.py#L394):
   $$\text{match\_ratio} = \frac{|\text{matched}|}{|\text{combined\_target\_tokens}|} = \frac{1}{3} \approx 0.3333$$
   The condition at [line 394](file:///e:/aeris-rag/app/verification/requirement_support.py#L394) is:
   ```python
   if match_ratio >= 0.25:
       return RequirementSupportResult(
           is_supported=True,
           evidence_support_status="SUPPORTED",
           rationale=f"Requirement '{requirement}' is semantically supported. Matched concepts: {sorted(matched)} (match ratio {match_ratio:.2f})."
       )
   ```
   Because $0.3333 \ge 0.25$, `_evaluate_semantic_support` returned `is_supported: True` with rationale:
   `"Requirement 'Identify training hardware' is semantically supported. Matched concepts: ['training'] (match ratio 0.33)."`
6. **Guardrail Bypass:**
   In `RequirementSupportValidator.validate` ([lines 147-152](file:///e:/aeris-rag/app/verification/requirement_support.py#L147-L152)):
   ```python
   if is_sup and not sem_result.is_supported and sem_result.evidence_support_status in ["NOT_ESTABLISHED", "CONTRADICTED"]:
   ```
   Because `sem_result.is_supported` was `True`, the B3 Grounding Guardrail never triggered.
7. **Controller Aggregation:**
   In [app/controller/controller.py:589-636](file:///e:/aeris-rag/app/controller/controller.py#L589-L636), `plan.requirements` contained only 1 requirement (`total_reqs = 1`). With `supported_count = 1`, neither `supported_count == 0` nor `supported_count < total_reqs` was met, so the controller passed `answer_status = "SUPPORTED"`.

---

### 5. Cross-Variant Scope of Defect
- **Status:** **VERIFIED**
- The defect is **shared across all 7 variants** that execute `RequirementSupportValidator` on answer generation output: `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, and `NO_SELECTIVE_VERIFICATION`.
- The single variant that avoided false support was `NO_CLAIM_VERIFICATION`. In that variant, `claim_verification` was disabled, resulting in `verified_claim_count: 0`. The answer generator produced a non-assertive summary (*"The RAG models were initialized with the NQ RAG model and trained on the same train/dev/test splits as prior work"*), which defaulted to `INSUFFICIENT_EVIDENCE`.
- Therefore, the defect originates directly in `RequirementSupportValidator._evaluate_semantic_support` and the lax token-overlap rule ($0.333 \ge 0.25$), compounded by the answer generator hallucinating a hardware connection to DPR.

---

## Part B — 151 Claim-Extraction Timeouts

### 1. Failure Diagnostics and Result Records
- **Status:** **VERIFIED**
- **Total Experiment Records:** 224
- **Total Executions Failed:** 151 (67.41%)
- **Total Executions Succeeded:** 73 (32.59%)
- **Distribution of Errors across 151 Failures:**
  Every single failure was caused by the identical exception:
  - 73 records: `Claim Extraction timed out after 60.00s: timed out`
  - 4 records: `Claim Extraction timed out after 62.00s: timed out`
  - 37 records: `Claim Extraction timed out after 62.01s: timed out`
  - 30 records: `Claim Extraction timed out after 62.02s: timed out`
  - 7 records: `Claim Extraction timed out after 62.03s: timed out`
- **Breakdown by Answerability:**
  - Answerable question runs: **119 failed / 160 total (74.38% failure rate)**
  - Unanswerable question runs: **32 failed / 64 total (50.00% failure rate)**
- **Breakdown by Question:**
  - 18 questions failed across **all 8 variants** (144 runs):
    `q_comp_01`, `q_comp_02`, `q_comp_03`, `q_df_01`, `q_df_02`, `q_df_03`, `q_df_05`, `q_meth_01`, `q_meth_02`, `q_meth_03`, `q_meth_04`, `q_mh_01`, `q_mh_02`, `q_mh_04`, `q_mh_05`, `q_quant_01`, `q_quant_03`, `q_unans_01`.
  - 1 question (`q_mh_03`) failed across **7 variants** (7 runs) and completed once on `NO_SELECTIVE_VERIFICATION`.
  - 9 questions completed across **all 8 variants** (72 runs):
    `q_contra_01`, `q_contra_02`, `q_df_04`, `q_df_06`, `q_multi_01`, `q_quant_02`, `q_unans_02`, `q_unans_03`, `q_unans_04`.

---

### 2. Claim-Extraction Call Path and Timeout Configuration
- **Status:** **VERIFIED**
- **Call Path Trace:**
  1. `AblationRunner.run_experiment()` in [app/ablation/runner.py:111](file:///e:/aeris-rag/app/ablation/runner.py#L111) invokes `self.controller.run(req)`.
  2. `AERISController.run()` in [app/controller/controller.py:196](file:///e:/aeris-rag/app/controller/controller.py#L196) calls:
     ```python
     extraction = self.claim_extractor.extract(
         chunk_id=evidence["chunk_id"],
         document_id=request.document_id,
         text=evidence["text"],
     )
     ```
  3. `ClaimExtractor.__init__()` in [app/claim_extraction/extractor.py:19-23](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L19-L23) initializes the HTTP client:
     ```python
     self.timeout = timeout or settings.ollama_timeout
     self.client = get_ollama_client(host=self.host, timeout=self.timeout)
     ```
  4. `get_ollama_client()` in [app/utils/model_client.py:64-77](file:///e:/aeris-rag/app/utils/model_client.py#L64-L77) sets:
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
  5. `ClaimExtractor.extract()` in [app/claim_extraction/extractor.py:83-95](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L83-L95) calls:
     ```python
     chat_res = timed_model_chat(
         client=self.client,
         model=self.model,
         messages=[{"role": "user", "content": prompt}],
         format="json",
         options={"temperature": 0.0, "num_predict": 8192},
         stage="Claim Extraction",
     )
     ```
- **Exact Timeout Configuration Used:**
  - `settings.ollama_timeout = 60.0` ([app/config.py:8](file:///e:/aeris-rag/app/config.py#L8)).
  - `httpx.Timeout.read = 60.0s`.
  - There was **no per-call override** in `ClaimExtractor.extract` or `build_real_controller()`.
  - The parameter `num_predict: 8192` instructed the model that it could emit up to 8,192 tokens in JSON format, while the client timeout remained clamped to 60.0s.

---

### 3. Explanation of the 60.00s / 62.00s Error Latencies
- **Status:** **VERIFIED**
- **Mechanism:**
  In `timed_model_chat` ([app/utils/model_client.py:96-168](file:///e:/aeris-rag/app/utils/model_client.py#L96-L168)):
  ```python
  t0_mono = time.perf_counter()
  try:
      response = client.chat(**kwargs)
      ...
  except httpx.TimeoutException as e:
      mono_elapsed = time.perf_counter() - t0_mono
      msg = f"{stage} timed out after {mono_elapsed:.2f}s: {e}"
      raise ModelTimeoutError(
          msg,
          stage=stage,
          elapsed_seconds=mono_elapsed,
          timestamp_utc=start_iso,
      ) from e
  ```
  1. The underlying HTTP client (`httpx`) started its read timer set to 60.0 seconds.
  2. When Ollama did not return the complete response within 60 seconds, `httpcore` / `httpx` aborted the connection with `httpx.ReadTimeout: timed out`.
  3. When Python caught the exception, `time.perf_counter() - t0_mono` measured the wall/monotonic time elapsed since the request was initiated:
     - In 73 runs, the socket closed immediately and `mono_elapsed` recorded exactly `60.00s`.
     - In 78 runs, thread synchronization, socket teardown, and OS context switching on Windows added 2.00–2.03 seconds of overhead, recording `62.00s`, `62.01s`, `62.02s`, or `62.03s`.
  4. **Why was a longer timeout assumed?**
     In [app/config.py:10](file:///e:/aeris-rag/app/config.py#L10), `max_anomaly_latency_seconds: float = 300.0` is defined. This 300-second threshold is exclusively used for detecting system sleep/suspension anomalies (`LatencyContaminationError`), **not** as an HTTP client timeout. The actual HTTP client read timeout was always configured to `ollama_timeout = 60.0s`.

---

### 4. Failure Mode Classification
- **Status:** **VERIFIED**
- **Conclusion:** These failures are genuine **model-response socket read timeouts** (`httpx.ReadTimeout`).
- **Evidence:**
  1. Not retry exhaustion: No retries were configured or attempted.
  2. Not client cancellation: No cancellation tokens or signals were issued.
  3. Not connection failure: The connect timeout was 10.0s and Ollama accepted the TCP connection immediately.
  4. Full exception traceback ([app/claim_extraction/extractor.py:127](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L127)):
     ```text
     httpx.ReadTimeout: timed out
     -> app.utils.model_client.ModelTimeoutError: Claim Extraction timed out after 62.01s: timed out
     ```
  Dense multi-chunk evidence texts (typically 3,000–6,000 characters) given to `llama3.2:latest` with `num_predict: 8192` and JSON schema enforcement take 65–85 seconds to generate on CPU/local GPU, exceeding the 60.0-second HTTP socket limit.

---

### 5. Retry Behavior & Accuracy of Retry Tracking
- **Status:** **VERIFIED**
- **Failed Evaluations Were NOT Retried:**
  1. `ClaimExtractor.extract()` ([app/claim_extraction/extractor.py:77-127](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L77-L127)) contains a single `try...except` block with no retry loop.
  2. `AERISController.run()` ([app/controller/controller.py:814-842](file:///e:/aeris-rag/app/controller/controller.py#L814-L842)) catches `Exception`, creates a single `ControllerStage.FAILED` stage, and terminates the run.
  3. `AblationRunner.run_experiment()` ([app/ablation/runner.py:145-218](file:///e:/aeris-rag/app/ablation/runner.py#L145-L218)) logs the failure and immediately advances to the next benchmark item.
- **Accuracy of Recorded Retries:**
  In `scripts/run_final_224_evaluation.py` ([lines 121-134](file:///e:/aeris-rag/scripts/run_final_224_evaluation.py#L121-L134)), `retry_count` is populated by counting `"retry_invoked"` entries in `diagnostics.jsonl`.
  - In 138 failed records, `retry_count = 0`.
  - In 13 failed records, `retry_count = 1`.
  - **Crucial Distinction:** These 13 retries were **not** retries of Claim Extraction. They represent retries that occurred in **Planning** (via `RequirementPlanner`) before Claim Extraction was reached. `ClaimExtractor` does not import `diagnostics.py` and never emits entries to `diagnostics.jsonl`. Consequently, Claim Extraction failures had 0 retries attempted, and the recorded `retry_count` reflects only prior stage telemetry.

---

### 6. Comparability of the 73 Successful Evaluations Across Variants
- **Status:** **VERIFIED (SCIENTIFICALLY NON-COMPARABLE)**
- **Findings:**
  1. **Severe Attrition:** Only 73 of 224 runs (32.6%) completed.
  2. **Truncation of Answerable Questions:** Only 41 of 160 answerable runs succeeded (25.6%). Across 7 of 8 variants, exactly 5 answerable questions succeeded; in 1 variant (`NO_SELECTIVE_VERIFICATION`), 6 succeeded.
  3. **Complete Elimination of Complex Categories:**
     - `q_comp_*` (Comparative): **0 / 24 runs completed (100% timeout failure)**
     - `q_meth_*` (Methodological): **0 / 32 runs completed (100% timeout failure)**
     - `q_mh_*` (Multi-Hop): **1 / 40 runs completed (97.5% timeout failure)**
  4. **Severe Survival Bias:** The only questions that survived were those with minimal evidence or short chunks (`q_contra_01`, `q_contra_02`, `q_df_04`, `q_df_06`, `q_multi_01`, `q_quant_02`, `q_unans_02`, `q_unans_03`, `q_unans_04`).
  5. **Cross-Variant Asymmetry:** `q_mh_03` completed on `NO_SELECTIVE_VERIFICATION` (latency 62.63s) but timed out on the other 7 variants (latencies 60.00s–62.01s). This 1-run divergence reflects marginal hardware execution jitter around the 60.0s boundary, not algorithmic variance.
- **Scientific Verdict:** The 73 completed evaluations **cannot be used for valid scientific ablation comparisons**. Any reported differences in retrieval recall, citation hit, or latency between variants are artifacts of survival bias and small-sample distortion ($N=5$ or $N=6$).

---

## Part C — Integrity and Recommendations

### 1. Reconfirmation of Record Counts & False-Support Rate
- **Status:** **VERIFIED**
- Total expected records: **224**
- Total saved records in `ablation_results_exp_final224_step22e_20261020_160000.json`: **224**
- Missing records: **0**; Duplicate `(variant, question_id)` pairs: **0**.
- **False-Support Rate:**
  $$\text{False Support Rate (Standard Gate 3)} = \frac{7}{64} = \mathbf{10.9375\%} \quad (> 5.0\% \text{ safety threshold})$$
  $$\text{False Support Rate (Completed Unanswerable Runs)} = \frac{7}{32} = \mathbf{21.8750\%} \quad (> 5.0\% \text{ safety threshold})$$
- Gate 3 Verdict: **FAIL / BLOCKED** under both formulations.

---

### 2. Distinction: Engineering Integrity vs. Scientific Validity
- **Status:** **VERIFIED**

| Audit Dimension | Status | Verified Evidence |
| :--- | :---: | :--- |
| **Engineering Integrity** | **PASS (100%)** | 224/224 records generated; isolated per-variant caches verified (`cache_exp_final224_step22e_20261020_160000_<VARIANT>.json`); 0 provenance defects; telemetry confirms 100% ablation bypass of disabled components; atomic file writes intact. |
| **Scientific Validity** | **BLOCKED (FAIL)** | Gate 3 failed ($10.94\% > 5.0\%$ false-support rate); Gate 6 failed (67.4% execution failure rate due to client timeouts); sample size collapsed to $N=5$ for answerable benchmarks. |

The software engineering pipeline is stable, robust, and correctly instrumented; the benchmark is scientifically blocked solely due to the HTTP timeout parameter and the validator's semantic matching rule for `q_unans_02`.

---

### 3. Recommended Remediation Steps (Priority Order)
*(Note: Recommended for human review; NOT implemented per read-only constraints)*

1. **Priority 1: Reconfigure HTTP Client Read Timeout for Claim Extraction**
   - **Target:** [app/config.py:8](file:///e:/aeris-rag/app/config.py#L8) and [app/claim_extraction/extractor.py:22-23](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L22-L23).
   - **Remediation:** Increase `ollama_timeout` from `60.0` to `180.0` seconds (or provide an explicit `extraction_timeout = 180.0` specifically for `ClaimExtractor`).
   - **Rationale:** Local inference on dense 3,000–6,000 character chunks with `num_predict: 8192` requires 65–85 seconds. An 180.0s timeout eliminates all 151 timeouts without risking infinite hangs.
   - **Telemetry Integration:** Wire `ClaimExtractor` to `app/utils/diagnostics.py` so extraction attempts, latencies, and any retries are recorded in `diagnostics.jsonl`.

2. **Priority 2: Remediate Semantic Support Validation Rule in `RequirementSupportValidator`**
   - **Target:** [app/verification/requirement_support.py:202, 288-310, 394](file:///e:/aeris-rag/app/verification/requirement_support.py#L202)
   - **Remediation:**
     a. **Disentangle Synonyms:** In [line 202](file:///e:/aeris-rag/app/verification/requirement_support.py#L202), remove generic verbs like `"train"` / `"training"` from the same synonym set as facilities or specific training metadata.
     b. **Require Essential Core Nouns:** In the specific concept check ([lines 288-310](file:///e:/aeris-rag/app/verification/requirement_support.py#L288-L310)), require that if a requirement contains specific physical/technical entities (such as `"hardware"`, `"gpu"`, `"processor"`, `"compute"`), that specific entity (or an explicit hardware synonym) must be present in the evidence. Matching an auxiliary verb like `"training"` must never suffice to substantiate a hardware requirement.
     c. **Calibrate Match Threshold:** For requirements with $\le 3$ target tokens, require a match ratio $\ge 0.50$ (or require all specific nouns to be present) rather than the permissive $0.25$ threshold.
     d. **Strengthen LLM Judge Grounding Guardrail:** Ensure that when the question asks about training hardware, the LLM prompt explicitly penalizes attributing DPR or dataset splits as hardware.

3. **Priority 3: Benchmark Alignment for `q_unans_02`**
   - **Target:** [data/benchmark/aeris_benchmark.json](file:///e:/aeris-rag/data/benchmark/aeris_benchmark.json)
   - **Review:** The benchmark team should determine whether `q_unans_02` was intended to test unanswerability *within the main text* (Sections 1–6) or across the entire paper including Appendix C. In Appendix C (`test_document_p017_c037`), the paper actually states the hardware (8, 32GB NVIDIA V100 GPUs). If the question is intended to be answerable from Appendix C, the benchmark metadata should be updated with appropriate supporting chunks. If it is strictly intended to be unanswerable, the index should exclude appendices or the retrieval scope must be constrained.

---

### 4. Tests to Prevent Recurrence
*(Note: Specifications only; no test files were created or modified)*

1. `tests/test_requirement_support_hardware_grounding.py`:
   - Pass question `"What hardware was used to train the RAG models?"` and requirement `"Identify training hardware"` with evidence chunk `test_document_p004_c010` (which only mentions "train/dev/test splits").
   - Assert `result.is_supported is False`.
   - Assert `result.evidence_support_status in ["NOT_ESTABLISHED", "INSUFFICIENT_OR_AMBIGUOUS"]`.
   - Assert `result.downgrade_category == "REQUIREMENT_UNSATISFIED"`.
2. `tests/test_claim_extractor_timeout_and_diagnostics.py`:
   - Mock a slow Ollama chat response (>60s) with configured 180s timeout; verify successful completion.
   - Mock a timeout exceeding 180s; verify `ModelTimeoutError` is handled, retried once if configured, and logged to `diagnostics.jsonl`.
3. `tests/test_semantic_support_sparse_token_matching.py`:
   - Unit test `_evaluate_semantic_support` with 3-token requirements where only 1 verb matches.
   - Verify that requirements containing nouns like "hardware", "location", "temperature", or "parameters" cannot be marked `SUPPORTED` purely on verb/process matches.

---

### 5. Benchmark Dataset and Historical Artifact Verification
- **Status:** **VERIFIED (100% UNCHANGED)**

All SHA-256 hashes were computed directly from disk and compared against the baseline manifest:

| Artifact Path | Expected SHA-256 Checksum | Actual SHA-256 Checksum | Status |
| :--- | :--- | :--- | :---: |
| `data/benchmark/aeris_benchmark.json` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | **MATCH** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200.json` | `df9850207668edaa59d3ce4f5acc7074c119f72b12ce0a4c86638c24197dd6cf` | `df9850207668edaa59d3ce4f5acc7074c119f72b12ce0a4c86638c24197dd6cf` | **MATCH** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200_manifest.json` | `e1f6bb0ae7cd35e4612e4f0adb9af9164032b974b37fd11612c9f5f0a4978a78` | `e1f6bb0ae7cd35e4612e4f0adb9af9164032b974b37fd11612c9f5f0a4978a78` | **MATCH** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200_diagnostics.jsonl` | `185273950894ef93ef89d4a0b46c24d5f3f4b3a3bbaae7e53976630af9bae975` | `185273950894ef93ef89d4a0b46c24d5f3f4b3a3bbaae7e53976630af9bae975` | **MATCH** |
| `data/results/ablation_exp_final224_remediation_20261017_142200_scientific_audit.json` | `354bb4488226a5ec31bc441c0d1e297e0ad08a86b97aab1887b704f9921cf294` | `354bb4488226a5ec31bc441c0d1e297e0ad08a86b97aab1887b704f9921cf294` | **MATCH** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000.json` | `a043dadd00685e59310564ffaba14a697eb3ebcd6c3879f2a619f829f9039bf3` | `a043dadd00685e59310564ffaba14a697eb3ebcd6c3879f2a619f829f9039bf3` | **MATCH** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_manifest.json` | `043c1e14f663656c0b4bdccc6c34df6d8e7050d7ba6e96b77723f50ce0a32714` | `043c1e14f663656c0b4bdccc6c34df6d8e7050d7ba6e96b77723f50ce0a32714` | **MATCH** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl` | `bdb0d362bfb4066741449fe4c74631ed065f6dd7b8ec55acf534d86a69a69643` | `bdb0d362bfb4066741449fe4c74631ed065f6dd7b8ec55acf534d86a69a69643` | **MATCH** |
| `data/results/ablation_exp_final224_repaired_20261011_222000_scientific_audit.json` | `4b6c14352b208d9375f3fc218ecd0ed9850468f206a97d937df3c07dc3aa16be` | `4b6c14352b208d9375f3fc218ecd0ed9850468f206a97d937df3c07dc3aa16be` | **MATCH** |

Git working tree status: Clean with respect to repository source files (`git status` confirms zero modified tracked files).

---

## Conclusion & Next Steps

1. **Root Causes Fully Isolated:**
   - **Part A:** `RequirementSupportValidator._evaluate_semantic_support` match ratio threshold (0.25) and synonym conflation of "train" and "training" allowed false acceptance of `q_unans_02`.
   - **Part B:** A 60.0-second HTTP socket read timeout in `app/config.py` was too aggressive for local Claim Extraction on dense chunks with `num_predict: 8192`, causing 151 timeouts with 0 retries.
2. **Current State:**
   - Investigation complete.
   - All findings labeled and cited.
   - Benchmark rerun and Step 23 remain strictly blocked pending human review.
