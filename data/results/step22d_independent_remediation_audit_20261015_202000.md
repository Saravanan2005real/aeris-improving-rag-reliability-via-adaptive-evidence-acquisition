# AERIS-RAG Step 22D — Independent Remediation Audit Report

**Audit Target:** Step 22D Remediation and Preflight Validation  
**Primary Evaluated Documents:**
- [`data/results/step22d_remediation_preflight_20261015_141833.md`](file:///e:/aeris-rag/data/results/step22d_remediation_preflight_20261015_141833.md)
- [`data/results/step22d_preflight_results_20261015_141833.json`](file:///e:/aeris-rag/data/results/step22d_preflight_results_20261015_141833.json)
- [`scripts/step22d_preflight_gate.py`](file:///e:/aeris-rag/scripts/step22d_preflight_gate.py)
- Historical baseline: [`data/results/ablation_exp_final224_repaired_20261011_222000_independent_scientific_audit.md`](file:///e:/aeris-rag/data/results/ablation_exp_final224_repaired_20261011_222000_independent_scientific_audit.md)  
**Audit Date / Timestamp:** `2026-10-15T20:20:00+05:30`  
**Auditor:** Independent Scientific Audit Subsystem (Antigravity AI)  
**Audit Protocol:** Read-Only Source Inspection, Code Tracing, Static Semantic Verification, and Assertion Rigor Audit  

---

## 1. Executive Verdict & Summary

### Verdict: **REJECTED (CONDITIONAL ON WORKSTREAM 3 REPAIR)**

The Step 22D remediation has made commendable progress on several of the critical defects that invalidated Step 22C (`exp_final224_repaired_20261011_222000`). Specifically, adaptive-retrieval schedule isolation, answer-support validation (the root cause of the 82 false downgrades), model client timeouts, and PC sleep/suspension contamination detection are well-designed and rigorously implemented.

**However, the preflight gate claim that all seven areas are production-ready is invalidated by a critical defect in Workstream 3 (Retrieval-Memory):**
> [!CAUTION]
> **Critical Architectural Defect Identified in Retrieval Memory:**  
> In [`app/adaptive_retrieval/controller.py:172-178`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L172-L178), when `memory.has_query_attempt(...)` reports a cache hit, the inner retrieval loop executes `continue` to avoid re-retrieval. **However, it never populates `all_evidence` or `all_chunk_ids` with the cached evidence.**  
> Consequently, on any cache hit, `AdaptiveRetrievalController` returns **zero evidence** for that requirement (`evidence=[]`, `final_coverage_status="UNSUPPORTED"`). Downstream claim extraction and answer generation receive an empty evidence set, triggering an immediate false downgrade to `INSUFFICIENT_EVIDENCE`. The cache hit is counted in telemetry, but catastrophically starves the pipeline of evidence.

Furthermore, **Gate Check 4** in [`scripts/step22d_preflight_gate.py:254-279`](file:///e:/aeris-rag/scripts/step22d_preflight_gate.py#L254-L279) passed only because it tested `has_query_attempt()` in isolation on the memory object without testing end-to-end evidence retrieval via `retrieve_for_requirement()`.

A rerun of the 224-record benchmark is **NOT JUSTIFIED** in the current state. Running a benchmark now would corrupt the `FULL_AERIS` and `NO_RETRIEVAL_MEMORY` ablation comparisons whenever queries encounter a cache hit.

---

## 2. Audit Findings Matrix

| Check # | Required Audit Check | Verdict | Core Finding / Mechanism |
|:---:|:---|:---:|:---|
| **1** | **Adaptive-Retrieval Isolation** | **PASS** | Candidate depth schedule pinned to base $k$ ($10$) under `NO_ADAPTIVE_RETRIEVAL`; depth expansions cleanly decoupled from query reformulation in telemetry. |
| **2** | **Answer-Support Validator** | **PASS** | Resolves the 82 false downgrades. Grounding checks lexical and quantitative numbers against cited evidence texts. Model failure falls back safely to deterministic rules. |
| **3** | **Retrieval-Memory Correctness** | **FAIL** | **Critical Defect:** Cache hit executes `continue` without loading cached chunks into `all_evidence`, starving downstream stages. Unbounded registry lacks TTL/concurrency locks. |
| **4** | **Cross-Lingual Agreement** | **PASS (Mechanics) / UNRESOLVED (Benchmark Validity)** | Code path correctly distinguishes agreement/contradiction; monolingual runs mark `SKIPPED (MONOLINGUAL)`. However, benchmark index is 100% English, so multilingual benchmark performance remains unexercised. |
| **5** | **Timeout and Latency Integrity** | **PASS** | All 10 model-calling components initialized via shared `get_ollama_client()`; monotonic timing enforced; sleep/suspension drift ($>10\text{s}$ divergence) halts contaminated runs. |
| **6** | **Preflight Gate Validity** | **FAIL** | 6 of 7 checks execute real assertions, but Gate Check 4 tests memory in isolation, failing to detect that production `retrieve_for_requirement()` produces zero evidence on cache hits. |
| **7** | **Historical Experiment Integrity** | **PASS** | Original Step 22C files (`ablation_results_exp_final224_repaired_20261011_222000*`) remain strictly unaltered and bit-identical. |

---

## 3. Detailed Audit by Required Check

### Check 1 — Adaptive-Retrieval Isolation
- **Status:** **PASS**
- **Inspected Files:**
  - [`app/ablation/config.py:12-13`](file:///e:/aeris-rag/app/ablation/config.py#L12-L13)
  - [`app/adaptive_retrieval/controller.py:163-166`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L163-L166)
  - [`app/controller/controller.py:670-699`](file:///e:/aeris-rag/app/controller/controller.py#L670-L699)
  - [`tests/test_step22d_adaptive_retrieval_isolation.py:1-125`](file:///e:/aeris-rag/tests/test_step22d_adaptive_retrieval_isolation.py#L1-L125)

#### Analysis
In the previous Step 22C audit, `NO_ADAPTIVE_RETRIEVAL` suffered from severe confounding: query reformulation attempts were incorrectly recorded as adaptive retrieval executions, and candidate depth expanded despite adaptive retrieval being disabled.

In Step 22D:
1. **Schedule Pinning:** In [`app/adaptive_retrieval/controller.py:163-166`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L163-L166):
   ```python
   if not enable_adaptive_retrieval:
       schedule = [self.candidate_k_schedule[0]] if self.candidate_k_schedule else [10]
   else:
       schedule = self.candidate_k_schedule
   ```
   When `enable_adaptive_retrieval=False`, the search depth schedule is pinned strictly to `schedule[0]` (typically 10). Even if query reformulation triggers multiple retrieval iterations, every query is evaluated at base $k$ ($10$). Candidate depth expansion is physically prevented.
2. **Orthogonal Execution:** In [`app/adaptive_retrieval/controller.py:168-243`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L168-L243), if `enable_query_reformulation=True`, the controller generates query variants via `self.query_reformulator.reformulate(...)` when initial coverage is inadequate, but candidate depth remains pinned to 10.
3. **Telemetry Decoupling:** In [`app/controller/controller.py:670-699`](file:///e:/aeris-rag/app/controller/controller.py#L670-L699):
   - `cand_expansions` counts attempts where `candidate_k > base_k`.
   - `adaptive_retrieval_triggered` is explicitly `(cand_expansions > 0) if request.config.enable_adaptive_retrieval else False`.
   - `reformulation_triggered` is independently tracked via `ref_calls > 0`.
   - Both counters are emitted separately in metadata.

**Conclusion:** Adaptive depth expansion and query reformulation are cleanly orthogonalized in configuration, controller execution loops, and telemetry.

---

### Check 2 — Answer-Support Validator
- **Status:** **PASS**
- **Inspected Files:**
  - [`app/verification/requirement_support.py:39-300`](file:///e:/aeris-rag/app/verification/requirement_support.py#L39-L300)
  - [`tests/test_requirement_support.py:1-210`](file:///e:/aeris-rag/tests/test_requirement_support.py#L1-L210)
  - [`tests/test_step22d_answer_support_validation.py:1-140`](file:///e:/aeris-rag/tests/test_step22d_answer_support_validation.py#L1-L140)

#### Analysis
In Step 22C, a defective validator caused an 89.4% false-negative rate (82 false downgrades to `INSUFFICIENT_EVIDENCE`), rejecting verified answers because of simplistic string comparisons that ignored cited evidence.

In Step 22D:
1. **Full Context Grounding:** [`RequirementSupportValidator.validate()`](file:///e:/aeris-rag/app/verification/requirement_support.py#L64-L142) takes `(question, requirement, answer, claims, evidence_texts)`.
2. **Semantic & Grounding Checks:**
   - In lines 181-196, quantitative extraction identifies numbers in claims using `re.findall(r'\b\d+(?:[\.,]\d+)?%?\b', ...)` and verifies their presence in cited evidence texts. Missing numbers immediately trigger `is_supported = False` with structured downgrade category `"EVIDENCE_UNSUPPORTED"`.
   - In lines 198-213, lexical content token overlap between claims and evidence texts enforces a grounding floor (`grounding_ratio >= 0.15`). Ungrounded claims trigger `"EVIDENCE_UNSUPPORTED"`.
   - In lines 215-283, requirement-to-evidence relevance requires keyword coverage across the requirement and evidence (`overlap_ratio >= 0.35`).
3. **Robust Fallback Handling:**
   - In lines 120-137, if the model client times out, raises `ModelCallError`, or returns non-JSON/malformed content, the validator logs a warning and falls back to deterministic rule-based semantic and grounding evaluation (`sem_result`). It neither silently accepts hallucinations nor systematically rejects valid answers due to model latency or formatting errors.
4. **Test Verification:**
   - `tests/test_step22d_answer_support_validation.py` includes meaningful positive tests (direct fact, method, quantitative, multi-hop, paraphrase) and negative controls (hallucinated batch size, wrong numerical metrics).

**Conclusion:** The answer-support validator reliably differentiates grounded answers from hallucinations and resolves the defect responsible for the 82 historical false downgrades.

---

### Check 3 — Retrieval-Memory Correctness
- **Status:** **FAIL**
- **Inspected Files:**
  - [`app/adaptive_retrieval/controller.py:172-178`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L172-L178)
  - [`app/retrieval_memory/memory.py:27-160`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L27-L160)
  - [`app/controller/controller.py:98-125`](file:///e:/aeris-rag/app/controller/controller.py#L98-L125)

#### Analysis
While `RetrievalMemoryRegistry` properly handles document and session scoping keys (`f"{document_id}::{session_id}"`), tracing the actual execution path reveals a **critical flaw in evidence acquisition**:

1. **The Empty Evidence Defect (`continue` without loading evidence):**
   In [`app/adaptive_retrieval/controller.py:172-178`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L172-L178):
   ```python
   for query in queries_to_try:
       for candidate_k in schedule:
           # Memory check: skip already-tried (query, candidate_k, document_id)
           if enable_retrieval_memory and memory is not None and memory.has_query_attempt(
               query=query, candidate_k=candidate_k, document_id=document_id
           ):
               continue  # <-- FATAL BUG
   ```
   When `has_query_attempt()` returns `True`, the controller treats this as "we already ran this query, skip it."
   **However, it completely fails to load the previously retrieved chunks or evidence items from `memory` into `all_evidence` or `all_chunk_ids`!**
   - At lines 245-257, `AdaptiveRetrievalResult` constructs its result using `evidence=all_evidence`.
   - If a query hits the cache, `all_evidence` remains empty.
   - When all queries for a requirement hit the cache, `AdaptiveRetrievalResult` returns `evidence=[]`, `all_chunk_ids=[]`, `success=False`, and `final_coverage_status="UNSUPPORTED"`.
   - In [`app/controller/controller.py:130-138`](file:///e:/aeris-rag/app/controller/controller.py#L130-L138), `_collect_evidence()` collects 0 chunks.
   - Downstream, `ClaimExtractor` receives no chunks, `AnswerGenerator` has no evidence, and the pipeline immediately downgrades to `INSUFFICIENT_EVIDENCE`.

2. **Semantic Invalidation & Scope:**
   - In [`app/retrieval_memory/memory.py:46-52`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L46-L52), `has_query_attempt()` simply checks if `(document_id, normalized_query, candidate_k)` exists in `self._history`. It records a hit counter (`self.hit_count += 1`), but does not return the chunks or check if the underlying document store changed.
   - While `record_query()` accepts `retrieved_chunk_ids`, `RetrievalMemory` does not even store the actual `EvidenceItem` objects needed by downstream controllers!
3. **Concurrency and Leakage Risks:**
   - `RetrievalMemoryRegistry._instances` is an unbounded class dictionary without a `threading.Lock()`.
   - There is no eviction policy (e.g. LRU) or TTL. In multi-threaded or long-running environments, memory will leak continuously.

**Conclusion:** Retrieval memory is broken in production. A cache hit starves the pipeline of evidence and forces an automatic downgrade.

---

### Check 4 — Cross-Lingual Agreement
- **Status:** **PASS (Code Mechanics) / UNRESOLVED (Benchmark Validity)**
- **Inspected Files:**
  - [`app/verification/cross_lingual_claim.py:32-155`](file:///e:/aeris-rag/app/verification/cross_lingual_claim.py#L32-L155)
  - [`app/verification/cross_lingual_agreement.py:58-219`](file:///e:/aeris-rag/app/verification/cross_lingual_agreement.py#L58-L219)
  - [`app/controller/controller.py:388-397`](file:///e:/aeris-rag/app/controller/controller.py#L388-L397)

#### Analysis
1. **Monolingual Bypass Logic:**
   In [`app/verification/cross_lingual_claim.py:58-132`](file:///e:/aeris-rag/app/verification/cross_lingual_claim.py#L58-L132), pairs are only sent to the classifier if `lang_a != lang_b`. If all pairs share the same language (e.g. `en == en`), the analyzer immediately returns `pair_count=0` and `rationale="SKIPPED (MONOLINGUAL)"`.
2. **Controller Stage Status:**
   In [`app/controller/controller.py:388-397`](file:///e:/aeris-rag/app/controller/controller.py#L388-L397):
   ```python
   if total_pairs == 0 and all_skipped_monolingual:
       stages.append(
           self._stage(
               ControllerStage.CROSS_LINGUAL,
               StageStatus.SKIPPED,
               "Stage skipped: all evidence pairs are monolingual (no cross-lingual pairs to evaluate).",
               0,
               latency_seconds=t_cross,
           )
       )
   ```
   This resolves the Step 22C issue where monolingual runs were falsely logged as completed cross-lingual evaluations.
3. **Benchmark Corpus Reality:**
   - The entire benchmark index in `data/index/test_document` is composed of 100% English documents (`"language": "en"`).
   - In any benchmark run over `test_document`, `cross_lingual_pairs_evaluated` is mathematically zero, and the stage is always `SKIPPED`.
   - While unit tests in `tests/test_step22d_cross_lingual_agreement.py` demonstrate that the Ollama prompt works for synthetic English-Tamil and English-Spanish pairs, **synthetic unit tests do not establish multilingual benchmark performance or validity on real benchmark corpora.**

**Conclusion:** The bypass and classification code paths are mechanically sound, but cross-lingual claims cannot be scientifically validated on a monolingual benchmark dataset.

---

### Check 5 — Timeout and Latency Integrity
- **Status:** **PASS**
- **Inspected Files:**
  - [`app/utils/model_client.py:56-183`](file:///e:/aeris-rag/app/utils/model_client.py#L56-L183)
  - [`app/config.py:4-16`](file:///e:/aeris-rag/app/config.py#L4-L16)
  - [`tests/test_step22d_timeouts_and_latency.py:1-154`](file:///e:/aeris-rag/tests/test_step22d_timeouts_and_latency.py#L1-L154)

#### Tracing of All 10 Model-Calling Components:
All 10 model-calling components in AERIS-RAG were inspected and verified to initialize their Ollama client via the centralized `get_ollama_client()` factory:
1. `RequirementPlanner` ([`app/planning/requirement_planner.py:33`](file:///e:/aeris-rag/app/planning/requirement_planner.py#L33))
2. `AnswerGenerator` ([`app/answer_generation/answer_generator.py:19`](file:///e:/aeris-rag/app/answer_generation/answer_generator.py#L19))
3. `ClaimExtractor` ([`app/claim_extraction/extractor.py:23`](file:///e:/aeris-rag/app/claim_extraction/extractor.py#L23))
4. `ClaimTyper` ([`app/claim_extraction/typer.py:20`](file:///e:/aeris-rag/app/claim_extraction/typer.py#L20))
5. `ClaimVerifier` ([`app/verification/claim_verifier.py:65`](file:///e:/aeris-rag/app/verification/claim_verifier.py#L65))
6. `ContextualContradictionClassifier` ([`app/verification/contradiction_classifier.py:50`](file:///e:/aeris-rag/app/verification/contradiction_classifier.py#L50))
7. `CrossLingualEvidenceClassifier` ([`app/verification/cross_lingual_agreement.py:56`](file:///e:/aeris-rag/app/verification/cross_lingual_agreement.py#L56))
8. `QueryReformulator` ([`app/adaptive_retrieval/query_reformulator.py:26`](file:///e:/aeris-rag/app/adaptive_retrieval/query_reformulator.py#L26))
9. `EvidenceCoverageEstimator` ([`app/coverage/evidence_coverage.py:110`](file:///e:/aeris-rag/app/coverage/evidence_coverage.py#L110))
10. `RequirementSupportValidator` ([`app/verification/requirement_support.py:28`](file:///e:/aeris-rag/app/verification/requirement_support.py#L28))
*(In addition, [`EmbeddingService`](file:///e:/aeris-rag/app/indexing/embedding_service.py#L8) was also verified to use `get_ollama_client()` with explicit timeouts).*

#### Timing and Sleep/Suspension Verification:
1. **Explicit HTTP Client Timeouts:** `get_ollama_client()` configures `httpx.Timeout(timeout=60.0, connect=10.0, read=60.0, write=60.0, pool=10.0)` based on `settings.ollama_timeout` and `settings.ollama_connect_timeout`.
2. **Monotonic Duration:** `timed_model_chat` measures elapsed time via `time.perf_counter()`, while separately logging UTC ISO forensic timestamps via `datetime.now(timezone.utc).isoformat()`.
3. **Suspension & Outlier Detection:**
   - If wall clock exceeds monotonic clock by $>10.0\text{s}$ (`(wall_elapsed - mono_elapsed) > 10.0`), `LatencyContaminationError("OS_SLEEP_OR_SUSPENSION_DETECTED")` is raised.
   - If monotonic time exceeds `max_anomaly_latency_seconds` ($300.0\text{s}$), `LatencyContaminationError("EXCEEDS_MAX_ANOMALY_THRESHOLD")` is raised.
   - Normal delays (e.g. a complex prompt taking 45s of active GPU time) advance wall and monotonic clocks equally ($\Delta \approx 0.0\text{s} \le 10.0\text{s}$), preventing false-positive suspension classifications.
4. **Contamination Containment:**
   When `LatencyContaminationError` is raised, it is re-raised by components and caught by `AERISController.run()` ([`app/controller/controller.py:766-795`](file:///e:/aeris-rag/app/controller/controller.py#L766-L795)), which terminates the run as `StageStatus.FAILED` with `metadata={"error_type": "LatencyContaminationError"}`. Contaminated runs cannot masquerade as valid results or enter clean latency aggregates unnoticed.

**Conclusion:** Model timeouts, monotonic timing, and laptop suspension detection are thoroughly implemented and sound.

---

### Check 6 — Preflight Gate Validity
- **Status:** **FAIL**
- **Inspected Files:**
  - [`scripts/step22d_preflight_gate.py:1-467`](file:///e:/aeris-rag/scripts/step22d_preflight_gate.py#L1-L467)
  - [`data/results/step22d_remediation_preflight_20261015_141833.md`](file:///e:/aeris-rag/data/results/step22d_remediation_preflight_20261015_141833.md)
  - [`data/results/step22d_preflight_results_20261015_141833.json`](file:///e:/aeris-rag/data/results/step22d_preflight_results_20261015_141833.json)

#### Analysis
An audit of `scripts/step22d_preflight_gate.py` was conducted to determine whether the gate checks execute genuine assertions or suffer from tautologies and mock bypasses:

1. **Checks 1, 2, 3, 5, 6, 7:**
   These checks execute real behavioral assertions against production modules:
   - Gate 1 asserts depth schedule pinning and telemetry isolation in `AdaptiveRetrievalController` and `AERISController`.
   - Gate 2 and 3 execute real semantic validation on 5 positive categories and 1 negative hallucination control.
   - Gate 5 asserts real language pair splitting and `SKIPPED (MONOLINGUAL)` rationale.
   - Gate 6 asserts real `ModelTimeoutError` and `LatencyContaminationError` raising.
   - Gate 7 asserts controller structured downgrade metadata generation.

2. **The Tautological Flaw in Gate Check 4:**
   Lines 256-274 of `scripts/step22d_preflight_gate.py`:
   ```python
   RetrievalMemoryRegistry.clear()
   mem1 = RetrievalMemoryRegistry.get_scoped_memory("docA", "sess1")
   mem1.record_query("query A", candidate_k=10, retrieved_chunk_ids=["chk_1"])

   # 1. Valid hit
   assert mem1.has_query_attempt("query A", candidate_k=10, document_id="docA") is True
   assert mem1.hit_count == 1
   ```
   **Why this check is invalid:**
   - Gate Check 4 only tested unit methods on the `RetrievalMemory` helper class.
   - It did **not** invoke `AdaptiveRetrievalController.retrieve_for_requirement()` with `memory` enabled on a cache hit.
   - Because of this isolated unit testing, the preflight gate failed to observe that `retrieve_for_requirement()` executes `continue` without populating `all_evidence`, returning empty evidence and failing the requirement!
   - A gate test that asserts `mem.hit_count == 1` while ignoring that the production pipeline drops all retrieved evidence is a **false-security gate**.

**Conclusion:** Gate Check 4 is insufficient and allowed a critical functional failure to be marked as "PASS".

---

### Check 7 — Historical Experiment Integrity
- **Status:** **PASS**
- **Inspected Files:**
  - `data/results/ablation_results_exp_final224_repaired_20261011_222000.json`
  - `data/results/ablation_results_exp_final224_repaired_20261011_222000.md`
  - `data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl`
  - `data/results/ablation_exp_final224_repaired_20261011_222000_independent_scientific_audit.md`
  - Backup: `data/recovery_backups/source_backup_20261015_182800_step22d/`

#### Analysis
1. **Timestamp Verification:**
   All `ablation_*exp_final224_repaired_20261011_222000*` artifacts have file modification timestamps of `13-10-2026 19:41:43` and `14-10-2026 09:01:49`, confirming they have not been touched during Step 22D.
2. **SHA256 Hash Verification:**
   - Target file: `data/results/ablation_results_exp_final224_repaired_20261011_222000.json`
   - Hash: `A043DADD00685E59310564FFABA14A697EB3EBCD6C3879F2A619F829F9039BF3`
   - The file was not modified, recalculated, or repaired in-place.
3. **Backup Completeness:**
   Prior to implementing Step 22D source code changes, a complete source code backup was created at `data/recovery_backups/source_backup_20261015_182800_step22d`.

**Conclusion:** Strict archival integrity of historical benchmark data has been maintained.

---

## 4. Required Fixes Before Any Benchmark Can Be Justified

To achieve production readiness and permit a valid benchmark run, the following remediation tasks must be completed:

### Fix 1: Repair Evidence Delivery on Retrieval-Memory Hit
- **Location:** [`app/adaptive_retrieval/controller.py:172-180`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L172-L180) and [`app/retrieval_memory/memory.py`](file:///e:/aeris-rag/app/retrieval_memory/memory.py)
- **Required Action:**
  1. Modify `RetrievalMemory.record_query()` and internal storage to store the retrieved `EvidenceItem` objects (or store full chunk payloads), not merely string IDs.
  2. In `AdaptiveRetrievalController.retrieve_for_requirement()`, when a cache hit occurs:
     ```python
     if enable_retrieval_memory and memory is not None and memory.has_query_attempt(...):
         cached_items = memory.get_cached_evidence(query=query, candidate_k=candidate_k, document_id=document_id)
         all_evidence.extend(cached_items)
         for item in cached_items:
             if item.chunk_id not in all_chunk_ids:
                 all_chunk_ids.append(item.chunk_id)
         continue
     ```
  3. Ensure that after loading cached items, coverage evaluation correctly evaluates whether the cached items satisfy the requirement, rather than leaving `all_evidence` empty.

### Fix 2: Upgrade Gate Check 4 to Test End-to-End Evidence Delivery
- **Location:** [`scripts/step22d_preflight_gate.py:254-285`](file:///e:/aeris-rag/scripts/step22d_preflight_gate.py#L254-L285)
- **Required Action:**
  Update Gate Check 4 so that it exercises `AdaptiveRetrievalController.retrieve_for_requirement()` across two sequential calls for the same requirement:
  - First call: Cache miss, retrieves chunk `chk_1`, returns `len(res1.evidence) == 1`.
  - Second call: Cache hit, must verify `res2.attempts` records hit **AND** `len(res2.evidence) == 1` with chunk `chk_1` present.
  - Assert that downstream `evidence` is NOT empty on a cache hit.

### Fix 3: Add Thread-Safety and Capacity Bounds to `RetrievalMemoryRegistry`
- **Location:** [`app/retrieval_memory/memory.py:126-160`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L126-L160)
- **Required Action:**
  Add a `threading.Lock()` to `RetrievalMemoryRegistry.get_scoped_memory()` and implement a bounded LRU eviction (e.g. `max_entries=1000`) to prevent unbound memory leakage during repeated evaluations.

### Fix 4: Note Multilingual Benchmark Limitations in Experimental Protocol
- **Location:** Experimental protocol and ablation design documents.
- **Required Action:**
  Explicitly state that the current benchmark index (`test_document`) is monolingual English. If multilingual claims are to be made in scientific publications, an index with genuine cross-lingual document pairs must be created and evaluated.

---

## 5. Benchmark Recommendation

> [!IMPORTANT]
> **Definitive Recommendation: DO NOT LAUNCH BENCHMARK.**  
> A rerun of the 224-record benchmark is **NOT JUSTIFIED** at this time.
>
> While 4 of the 6 defect areas from the historical audit have been remediated, launching a benchmark with the current Workstream 3 defect would result in any cache-hitting query delivering empty evidence, triggering artificial downgrades and producing invalid ablation metrics.
>
> **Action items:**
> 1. Execute **Fix 1** and **Fix 2** above.
> 2. Re-run `scripts/step22d_preflight_gate.py` with the updated end-to-end Gate 4 assertions.
> 3. Once Gate 4 passes with verified non-empty evidence delivery on cache hits, a fresh benchmark run may proceed.
