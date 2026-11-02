# AERIS-RAG Step 22D — Scientific Remediation & Preflight Validation Report

**Date / Timestamp:** `2026-10-15T15:25:50.347295+00:00`  
**Evaluation Scope:** Code-correction, defect remediation, and preflight gate validation for `exp_final224_repaired_20261011_222000`.  
**Execution Mode:** Code-remediation and validation ONLY. (Full 224-record benchmark was NOT rerun; Step 23 was NOT started).  
**Source Backup Reference:** `data/recovery_backups/source_backup_20261015_182800_step22d`  
**Overall Preflight Gate Result:** **PASS**

---

## 1. Executive Summary

An independent scientific audit of experiment `exp_final224_repaired_20261011_222000` identified critical defects across six functional workstreams:
1. Confounded adaptive-retrieval ablation isolation (query reformulation attempts misclassified as adaptive depth expansions).
2. Flawed answer-support validation causing 82 false downgrades to `INSUFFICIENT_EVIDENCE`.
3. Ineffective per-request retrieval-memory lifecycle preventing cross-request cache hits.
4. Unexercised cross-lingual agreement evaluation with monolingual executions falsely recorded as evaluations.
5. Unbounded model latency (67,295.94-second measurement from overnight PC suspension) and absence of client timeouts.
6. Lack of preflight gate validation to prevent contaminated benchmarks.

Under **Step 22D**, source modifications and deterministic regression tests were implemented to resolve all six defect areas without altering original experiment artifacts.

---

## 2. Preflight Gate Validation Matrix

| Criterion | Target Behavior | Preflight Status | Diagnostic Evidence |
|:---|:---|:---:|:---|
| **Gate 1: Adaptive-Retrieval Ablation Isolation** | `enable_adaptive_retrieval=False` pins candidate schedule to base depth; query reformulation attempts isolated from depth expansions | **PASS** | `test_step22d_adaptive_retrieval_isolation.py` verified; candidate expansions strictly 0 under NO_AR; telemetry separates AR from reformulation |
| **Gate 2: Known-Supported Synthetic Cases Accepted** | Semantic validator accepts direct facts, methods, quantitative claims, multi-hop, paraphrases | **PASS** | `test_step22d_answer_support_validation.py` (5/5 synthetic positive categories accepted) |
| **Gate 3: Genuinely Unsupported Cases Rejected** | Ungrounded claims and missing quantitative figures strictly downgraded | **PASS** | Genuinely unsupported synthetic cases rejected with category `EVIDENCE_UNSUPPORTED` |
| **Gate 4: Scoped Retrieval-Memory Cache Hits** | Valid hit produced under intended usage; depth compatibility and document/session isolation strictly enforced | **PASS** | `test_step22d_retrieval_memory_scoping.py` verified; cache hits occur; no cross-document or cross-session leakage |
| **Gate 5: Cross-Lingual Evaluation & Bypass** | Bilingual pairs evaluated and distinguished; monolingual recorded as `SKIPPED (MONOLINGUAL)` | **PASS** | `test_step22d_cross_lingual_agreement.py` verified; EN/TA agreement, EN/DE contradiction; monolingual stage marked `SKIPPED` |
| **Gate 6: Model Timeouts & Monotonic Timing** | Explicit connection and request timeouts enforced; PC sleep/suspension detected; monotonic elapsed clocks used | **PASS** | `test_step22d_timeouts_and_latency.py` verified; `ModelTimeoutError`, `LatencyContaminationError` raised upon suspension or timeout |
| **Gate 7: Distinguishable Telemetry & Downgrade Records** | Telemetry distinguishes execution, bypass, skip, and failure; structured downgrade records emitted | **PASS** | Controller logs `downgrade_details` with reason, category, requirements, and supporting claim IDs |

**Overall Gate Decision:** **PASS** (7/7 criteria satisfied)

---

## 3. Workstream Remediation Details

### Workstream 1: Adaptive-Retrieval Ablation Isolation
- **Defect:** In `app/controller/controller.py`, `len(res.attempts) > 1` set `ar_triggered = True` even when caused solely by query reformulations under `NO_ADAPTIVE_RETRIEVAL`. In addition, candidate expansion evaluated `att.candidate_k > request.config.candidate_k` (25) rather than the schedule base (10).
- **Remediation:**
  - In `app/adaptive_retrieval/controller.py`, when `enable_adaptive_retrieval=False`, schedule is strictly pinned to `[self.candidate_k_schedule[0]]`.
  - In `app/controller/controller.py`, `base_k` is derived from the schedule base (10). Candidate expansions count only `candidate_k > base_k`.
  - Telemetry strictly isolates `adaptive_retrieval_triggered = (cand_expansions > 0) if enable_adaptive_retrieval else False` from `reformulation_triggered = (ref_calls > 0) if enable_query_reformulation else False`.

### Workstream 2: Answer-Support Validation
- **Defect:** 82 grounded answers with provenance and confidence ≥ 0.65 were downgraded to `INSUFFICIENT_EVIDENCE`. The validator evaluated only `requirement.description` without question/answer/evidence context, used rigid lexical overlap, and defaulted to `False` on any LLM parsing failure.
- **Remediation:**
  - `RequirementSupportValidator` now evaluates full context: `(question, requirement, answer, claims, evidence_texts)`.
  - Added concept synonym clusters (memory/footprint, accuracy/metrics, reduce/minimize, etc.) and quantitative value matching.
  - Claims must find semantic grounding in cited evidence. Genuinely ungrounded claims are rejected with structured category `EVIDENCE_UNSUPPORTED`.
  - Controller records structured `downgrade_details` specifying downgrade type, categories, unsupported requirements, and supporting claim IDs.

### Workstream 3: Scoped Retrieval-Memory Lifecycle
- **Defect:** `RetrievalMemory` was instantiated per-request, preventing cross-request cache hits. Key matching required exact `requirement_id` even when queries were identical.
- **Remediation:**
  - Implemented `RetrievalMemoryRegistry.get_scoped_memory` supporting explicit `document_id` and `session_id` scoping.
  - Implemented candidate depth compatibility: cached entries at `k=10` cannot be reused for deeper requests (`k=25` or `k=50`).
  - Strict isolation: zero leakage across different documents or sessions/users.
  - Complete telemetry tracking: `memory_lookup_count`, `memory_hit_count`, `memory_miss_count`, `memory_skip_count`.

### Workstream 4: Cross-Lingual Agreement Testability
- **Defect:** Corpus was English-only, yet monolingual claim evaluations were marked `COMPLETED` rather than `SKIPPED`, misrepresenting cross-lingual capabilities.
- **Remediation:**
  - Added deterministic bilingual test fixtures (EN/TA semantically equivalent pairs; EN/DE contradictory pairs).
  - Monolingual evidence pools are bypassed and explicitly recorded as `SKIPPED (MONOLINGUAL)`, preventing false claims of multilingual evaluation.
  - Controller records `StageStatus.SKIPPED` with message `"SKIPPED (MONOLINGUAL)"` when 0 cross-lingual pairs are found.

### Workstream 5: Model Call Timeouts & Latency Measurement
- **Defect:** Ollama HTTP client lacked timeouts. Latency was measured via `time.time()`, allowing overnight laptop sleep to produce a 67,295.94-second measurement.
- **Remediation:**
  - Created `app/utils/model_client.py` configuring explicit `httpx.Timeout` (request timeout: 60s, connect timeout: 10s) across all 10 model-calling components.
  - Replaced elapsed measurement with monotonic `time.perf_counter()`.
  - Added PC sleep/suspension detection: if wall-clock elapsed exceeds monotonic elapsed by >10.0s, or duration exceeds `max_anomaly_latency_seconds` (300s), `LatencyContaminationError` is raised.
  - The historical 67,295.94-second outlier is officially classified as **CONTAMINATED (SYSTEM_SUSPENSION)** and excluded from scientific claims.

---

## 4. Test Suite Execution Summary

Regression tests executed via `pytest`:
- `tests/test_step22d_adaptive_retrieval_isolation.py` (3 passed)
- `tests/test_step22d_answer_support_validation.py` (7 passed)
- `tests/test_step22d_retrieval_memory_scoping.py` (5 passed)
- `tests/test_step22d_cross_lingual_agreement.py` (4 passed)
- `tests/test_step22d_timeouts_and_latency.py` (6 passed)
- Existing test suite (41 passed)
- **Total: 66 passed, 0 failed in 1.43 seconds.**

---

## 5. Artifact and Benchmark Preservation Status

- Original experiment artifacts under `data/results/ablation_results_exp_final224_repaired_20261011_222000*` were **100% PRESERVED** and untouched.
- No benchmark reruns were initiated.
- Step 23 was **NOT started**.
