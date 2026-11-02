# AERIS-RAG Step 22D.1 — Independent Audit of Retrieval Memory Repair

**Date / Timestamp:** `2026-10-17T13:45:00+05:30`  
**Evaluation Scope:** Independent audit of the Step 22D.1 Retrieval Memory Evidence-Delivery repair, implementation files, test suites, and benchmark readiness.  
**Auditor Mode:** Read-only independent audit. (No benchmark executed; Step 23 NOT started; historical artifacts preserved).  
**Primary Target Report:** [`data/results/step22d1_memory_repair_20261015_205800.md`](file:///e:/aeris-rag/data/results/step22d1_memory_repair_20261015_205800.md)  
**Historical Defect Trigger:** [`data/results/step22d_independent_remediation_audit_20261015_202000.md`](file:///e:/aeris-rag/data/results/step22d_independent_remediation_audit_20261015_202000.md)  
**Overall Verdict:** **READY FOR A NEW BENCHMARK**

---

## 1. Executive Summary & Verification Matrix

The Step 22D remediation previously resolved 5 out of 6 defect areas, but its independent audit identified a critical regression in Workstream 3 (Retrieval Memory): when a cache hit occurred in `AdaptiveRetrievalController.retrieve_for_requirement()`, the controller executed `continue` without populating `all_evidence` or `all_chunk_ids`, starving downstream stages and causing false downgrades to `INSUFFICIENT_EVIDENCE`.

Under **Step 22D.1**, source code fixes were implemented in [`app/retrieval_memory/schemas.py`](file:///e:/aeris-rag/app/retrieval_memory/schemas.py), [`app/retrieval_memory/memory.py`](file:///e:/aeris-rag/app/retrieval_memory/memory.py), [`app/adaptive_retrieval/controller.py`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py), and validated in [`scripts/step22d_preflight_gate.py`](file:///e:/aeris-rag/scripts/step22d_preflight_gate.py) and [`tests/test_step22d1_retrieval_memory_repair.py`](file:///e:/aeris-rag/tests/test_step22d1_retrieval_memory_repair.py).

This audit independently inspected the entire implementation, challenged the test suite, verified concurrency and LRU safety, ran targeted validation scripts, and checked historical benchmark integrity.

### Audit Criteria Status Matrix

| # | Audit Criterion | Status | Implementation Reference | Key Audit Finding |
|:---:|:---|:---:|:---|:---|
| **1** | **Cache-Hit Path Tracing & Evidence Delivery** | **PASS** | [`app/adaptive_retrieval/controller.py:172-276`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L172-L276) | Valid `EvidenceItem` reconstruction, `all_evidence` & `all_chunk_ids` populated, deduplicated, downstream consumption verified. |
| **2** | **Cache Compatibility & Isolation** | **PASS** | [`app/retrieval_memory/memory.py:159-231`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L159-L231) | Normalized query matching, strict document/session isolation, candidate depth compatibility (`cached_k >= req_k`), malformed entry fallback. |
| **3** | **Concurrency & LRU Boundedness** | **PASS** | [`app/retrieval_memory/memory.py:356-432`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L356-L432) | Thread-safe `threading.RLock()` in `RetrievalMemoryRegistry`, bounded `OrderedDict` eviction (`max_capacity=1000`), Python reference safety. |
| **4** | **Test Challenge & Regression Rigor** | **PASS** | [`tests/test_step22d1_retrieval_memory_repair.py:1-525`](file:///e:/aeris-rag/tests/test_step22d1_retrieval_memory_repair.py#L1-L525) | Tests exercise real production code; negative control strictly fails on historical empty-evidence defect; Gate Check 4 invokes real controller. |
| **5** | **Benchmark & Artifact Integrity** | **PASS** | `data/benchmark/` & `data/results/` | SHA256 hashes of original Step 22C benchmark files match manifest and prior audit records exactly; 0 files modified. |

---

## 2. Trace of the Cache-Hit Path

### 2.1 Memory Lookup through Result Construction
In [`app/adaptive_retrieval/controller.py:167-276`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L167-L276), the retrieval loop iterates over the candidate schedule:
1. **Lookup:**
   ```python
   cached_attempt = memory.get_compatible_query_attempt(
       query=current_query,
       candidate_k=candidate_k,
       requirement_id=requirement.requirement_id,
       document_id=document_id,
       session_id=getattr(memory, "session_id", None),
       require_evidence=True,
   )
   ```
2. **Deserialization & Reconstruction (Lines 184–197):**
   Iterates through `cached_attempt.cached_evidence`:
   - If already `EvidenceItem`, keeps as-is.
   - If `dict`, instantiates `EvidenceItem(**item_data)`.
   - If empty or corrupted, catches exception, records fallback via `memory.record_fallback(...)`, and seamlessly diverts to live hybrid retrieval.
3. **Population & Deduplication (Lines 203–208):**
   ```python
   new_chunk_ids = []
   for evidence in cached_items:
       if evidence.chunk_id not in all_evidence:
           all_evidence[evidence.chunk_id] = evidence
           new_chunk_ids.append(evidence.chunk_id)
   ```
   `all_evidence` is keyed by `chunk_id`, guaranteeing chunk-level deduplication.
4. **Preservation of Coverage Semantics & Scoring (Lines 211–245):**
   - Candidate evidence is sorted by `rerank_score` and truncated to `rerank_top_k` (identical to the uncached live retrieval branch at lines 339–347).
   - Evaluated via `self.coverage_estimator.estimate(...)` (leveraging `_last_coverage_signature` caching to prevent duplicate LLM calls).
   - Generates a full `RetrievalAttempt` record (lines 248–266) logging `retrieved_chunk_ids`, `new_chunk_ids`, `coverage_status`, `coverage_score`, and stopping criteria.
5. **AdaptiveRetrievalResult Packaging (Lines 466–481):**
   - `evidence=list(all_evidence.values())`
   - `all_chunk_ids=list(all_evidence.keys())`
   - `total_unique_chunks=len(all_chunk_ids)`
   - Full diagnostic telemetry delivered to caller.

### 2.2 Direct Comparison: Live Retrieval vs. Cache Hit
An independent end-to-end trace script executed the same fixture under live retrieval followed by cache hit:
```
Retriever calls: 1 (Live call: 1, Cached call: 0 additional)
Res1 evidence count: 2, Res2 evidence count: 2
Res1 chunk_ids: ['chunk_1', 'chunk_2'], Res2 chunk_ids: ['chunk_1', 'chunk_2']
Item 0: chunk_id: chunk_1 == chunk_1 -> True | text match: True | scores: retrieval=0.91, rerank=0.91 | model_dump match: True
Item 1: chunk_id: chunk_2 == chunk_2 -> True | text match: True | scores: retrieval=0.84, rerank=0.84 | model_dump match: True
Coverage match: True (SUPPORTED vs SUPPORTED, score: 0.92 vs 0.92)
Telemetry: Memory hit count: 1, Cached evidence count: 2
```

### 2.3 Usability by Downstream Claim Extraction & Answer Generation
In [`app/controller/controller.py:130-139, 195-205, 548-565`](file:///e:/aeris-rag/app/controller/controller.py):
- `AERISController._collect_evidence(retrieval_results)` extracts `chunk_id`, `document_id`, `text`, `language`, and `pages` from `result.evidence`.
- `claim_extractor.extract(chunk_id=..., text=...)` consumes the reconstructed text.
- Claims and evidence nodes are inserted into `graph_builder`.
- Verified in an end-to-end controller execution: with the repaired cache-hit path, `AERISController` completed all 11 stages without error, producing `answer_status: "SUPPORTED"` and delivering non-empty provenance.

---

## 3. Cache Compatibility, Scoping, and Isolation

### 3.1 Normalized Query Matching
In [`app/retrieval_memory/memory.py:198-202`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L198-L202):
`normalized_query = query.strip().lower()`
Compared against `item.query.strip().lower()`. This handles extraneous leading/trailing whitespace and case variances while preventing accidental semantic drift.

### 3.2 Requirement Identity Isolation
In [`app/retrieval_memory/memory.py:205-209`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L205-L209):
When `match_requirement=True` and `requirement_id` is supplied:
`if item.requirement_id is not None and item.requirement_id != requirement_id: self.incompatibility_count += 1; continue`
Queries belonging to distinct information requirements cannot cross-contaminate.

### 3.3 Document and Session Isolation
In [`app/retrieval_memory/memory.py:186-197`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L186-L197):
- Explicit checks reject queries if `document_id != self.state.document_id` or `session_id != self.session_id`, incrementing `incompatibility_count` and `skip_count`.
- In `RetrievalMemoryRegistry`, keys are composite: `f"{document_id}::{session_id or 'default'}"`.
- Verified by [`tests/test_step22d1_retrieval_memory_repair.py:335-388`](file:///e:/aeris-rag/tests/test_step22d1_retrieval_memory_repair.py#L335-L388): queries by user `Alice` on `doc_alpha` do not hit for user `Bob` or on `doc_beta`.

### 3.4 Candidate-Depth Compatibility
In [`app/retrieval_memory/memory.py:212-215`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L212-L215):
```python
if item.candidate_k < candidate_k:
    self.incompatibility_count += 1
    continue
```
An entry cached at initial shallow depth ($k=10$) is strictly rejected when the adaptive loop requests deeper depth ($k=25$ or $k=50$), forcing live retrieval expansion. Conversely, an entry retrieved at depth $k=50$ can satisfy $k=10$.

### 3.5 Malformed-Entry Fallback
In [`app/retrieval_memory/memory.py:217-227`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L217-L227) and [`app/adaptive_retrieval/controller.py:190-197`](file:///e:/aeris-rag/app/adaptive_retrieval/controller.py#L190-L197):
If `cached_evidence` is `None`, empty, non-list, or fails Pydantic validation, the system records `fallback_count += 1` and executes live retrieval rather than raising an exception or returning empty evidence.

### 3.6 Invalidation Lifecycle
In [`app/retrieval_memory/memory.py:338-351, 404-432`](file:///e:/aeris-rag/app/retrieval_memory/memory.py):
- `invalidate_for_document(document_id)` removes document-scoped instances.
- `invalidate(document_id, session_id)` provides granular scope removal.
- `clear()` resets all history and counters.

---

## 4. Concurrency and LRU Behavior

### 4.1 Locking Scope in `RetrievalMemoryRegistry`
In [`app/retrieval_memory/memory.py:356-432`](file:///e:/aeris-rag/app/retrieval_memory/memory.py#L356-L432):
- `_lock = threading.RLock()` protects all registry operations: `set_capacity`, `get_capacity`, `get_scoped_memory`, `invalidate`, and `clear`.
- Re-entrant locking prevents deadlocks if nested registry operations occur within the same thread.

### 4.2 Bounded LRU Capacity
- Registry stores instances in `_instances: OrderedDict[str, RetrievalMemory]`.
- On access via `get_scoped_memory()`, existing keys are refreshed with `move_to_end(key)`.
- If `len(_instances) >= _max_capacity`, the oldest entry is popped via `cls._instances.popitem(last=False)`.
- Default `max_capacity = 1000`, configurable via `set_capacity()`. Capacity remains strictly bounded.

### 4.3 In-Use Eviction Safety
- If an instance is evicted from `_instances` while an ongoing request holds a reference, Python's reference counting keeps the `RetrievalMemory` instance valid in memory until the request completes. The thread never encounters a `KeyError` or dangling pointer.
- Subsequent requests for the evicted key simply instantiate a fresh `RetrievalMemory`.

### 4.4 Concurrent Execution Testing
Tested via `test_registry_thread_safety_under_concurrent_access` with 10 threads, 50 queries each (500 total operations) across multiple documents and sessions. Completed with 0 errors.

---

## 5. Test Suite Rigor & Challenge Analysis

### 5.1 Real Production Code Execution
The regression test [`tests/test_step22d1_retrieval_memory_repair.py`](file:///e:/aeris-rag/tests/test_step22d1_retrieval_memory_repair.py) imports and exercises:
- Real `AdaptiveRetrievalController`
- Real `RetrievalMemory`
- Real `RetrievalMemoryRegistry`
- Real `InformationRequirement`
- Real `EvidenceItem`, `RequirementCoverage`, and `EvidenceCoverageResult`

Only external I/O (vector DB retrieval and LLM chat) is replaced with deterministic mock counters to enable automated regression testing.

### 5.2 Verification of Cache-Hit Branch
In `test_first_call_populates_memory_and_second_call_hits_with_evidence`:
- First call: `retriever.call_count == 1`, `len(res1.evidence) == 2`, `mem1.query_count() == 1`.
- Second call: `retriever.call_count == 1` (static, proving no live retrieval), `len(res2.evidence) == 2` (non-empty), `mem1.hit_count >= 1`, `mem1.cached_evidence_count == 2`.

### 5.3 Negative Control Validation
In `test_gate_check_4_fails_if_cache_hit_skips_without_returning_evidence` ([lines 480–525](file:///e:/aeris-rag/tests/test_step22d1_retrieval_memory_repair.py#L480-L525)):
Simulates the historical defect where the controller returned empty evidence on cache hit. The test verifies that `AssertionError` is raised by the Gate Check 4 conditions, confirming that the test suite cannot produce a false pass if the historical defect resurfaces.

### 5.4 Preflight Gate Check 4 Verification
In [`scripts/step22d_preflight_gate.py:252-368`](file:///e:/aeris-rag/scripts/step22d_preflight_gate.py#L252-L368):
Gate Check 4 instantiates `AdaptiveRetrievalController` and tests:
- Live retrieval populates memory and returns 2 chunk IDs (`chk_1`, `chk_2`).
- Second call hits cache, retriever calls do not increment, returns identical chunk IDs and valid text.
- Candidate depth incompatibility (`k=25` requested vs `k=10` cached) returns `False`.
- Session isolation (`sess2` vs `sess1`) returns `False`.
- Document isolation (`docB` vs `docA`) returns `False`.
- Malformed cache entry triggers fallback to live retrieval with `fallback_count >= 1`.

### 5.5 Full Test Suite Run
Pytest execution verified all 75 tests passing in 1.56s:
```
tests/test_answer_guardrail.py ...                                       [  4%]
tests/test_cache_isolation.py .......                                    [ 13%]
tests/test_integration_measurement_repair.py .....                       [ 20%]
tests/test_json_parsing.py .....                                         [ 26%]
tests/test_profiler_accounting.py ..                                     [ 29%]
tests/test_requirement_support.py .                                      [ 30%]
tests/test_retrieval_vs_citation_metrics.py ....                         [ 36%]
tests/test_scientific_validity.py ....                                   [ 41%]
tests/test_semantic_robustness.py ..........                             [ 54%]
tests/test_step22d1_retrieval_memory_repair.py .........                 [ 66%]
tests/test_step22d_adaptive_retrieval_isolation.py ...                   [ 70%]
tests/test_step22d_answer_support_validation.py .......                  [ 80%]
tests/test_step22d_cross_lingual_agreement.py ....                       [ 85%]
tests/test_step22d_retrieval_memory_scoping.py .....                     [ 92%]
tests/test_step22d_timeouts_and_latency.py ......                        [100%]
============================== 75 passed in 1.56s ==============================
```

---

## 6. Historical Benchmark & Experiment Integrity

Cryptographic SHA-256 hashes and byte lengths were calculated directly against all benchmark artifacts.

| File Path | Recorded / Manifest Hash | Computed SHA256 Hash | Size (Bytes) | Integrity Status |
|:---|:---|:---|:---:|:---:|
| `data/benchmark/aeris_benchmark.json` | `CE9A86B6...` (in manifest) | `CE9A86B6B4EA354217C54DB4B23A5251E97065DE53773CF154BB95DACCC8E974` | 33,522 | **MATCH (UNTOUCHED)** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000.json` | `A043DADD...` (in audit report) | `A043DADD00685E59310564FFABA14A697EB3EBCD6C3879F2A619F829F9039BF3` | 754,943 | **MATCH (UNTOUCHED)** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl` | `BDB0D362...` | `BDB0D362BFB4066741449FE4C74631ED065F6DD7B8EC55ACF534D86A69A69643` | 1,303,274 | **MATCH (UNTOUCHED)** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_manifest.json` | `043C1E14...` | `043C1E14F663656C0B4BDCCC6C34DF6D8E7050D7BA6E96B77723F50CE0A32714` | 1,029 | **MATCH (UNTOUCHED)** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000.md` | `77D91955...` | `77D91955B9118847812F690845E79522F54667D73BE4C091F6AE457BA6138618` | 5,640 | **MATCH (UNTOUCHED)** |

- **Pre-Remediation Source Backups Verified:**
  - `data/recovery_backups/source_backup_20261015_182800_step22d/`
  - `data/recovery_backups/source_backup_20261015_202200_step22d1/`
- **Execution Constraints Respected:**
  - Full 224-record benchmark was **NOT** executed.
  - Step 23 was **NOT** started.

---

## 7. Audit Verdict & Recommendation

### Recommendation: **READY FOR A NEW BENCHMARK**

### Scientific Rationale
1. **Core Defect Fully Remediated:** The empty-evidence delivery defect on cache hits has been eliminated. The cache-hit path now fully reconstructs `EvidenceItem` objects, preserves metadata and rerank scores, recalculates coverage consistently, deduplicates chunk IDs, and supplies valid evidence to downstream claim extraction and answer generation stages.
2. **Robust Fallback & Strict Isolation:** Any malformed, unparseable, or legacy cache entry without evidence triggers safe fallback to live hybrid retrieval with explicit telemetry recording (`fallback_count`). Session, document, and candidate-depth boundaries are strictly enforced.
3. **Thread Safety & Resource Boundedness:** Reentrant locking (`threading.RLock()`) and LRU capacity bounds (`max_capacity=1000`) protect the memory registry against memory leaks and concurrency hazards.
4. **Comprehensive Test Suite & Integrity Gates:** All 75 unit/regression tests and all 7 preflight gate checks pass deterministically. Negative controls confirm that empty-evidence regressions strictly fail.
5. **Zero Data Contamination:** All historical Step 22C benchmark files remain bit-for-bit identical to their recorded hashes.

The codebase is now scientifically sound and ready to support an uncontaminated benchmark rerun.
