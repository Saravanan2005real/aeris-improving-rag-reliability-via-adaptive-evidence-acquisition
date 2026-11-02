# AERIS-RAG — Final Read-Only Scientific Validity Gate Audit (Step 22C)

**Experiment ID:** `exp_final224_20261011_113501`  
**Audit Timestamp:** 2026-10-11  
**Final Verdict:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`

## Gate Verdicts Summary

| Gate | Focus Area | Verdict | Primary Evidence |
|---|---|:---:|---|
| **Audit A** | Exact Experiment Identity | **PASS** | Raw & manifest variants match all 8 intended ablations character-for-character. |
| **Audit B** | Benchmark Identity | **PASS** | Loaded `aeris_benchmark.json` (SHA256: `ce9a86b6b4ea3542...`). `benchmark_questions_v2.json` never existed. |
| **Audit C** | Metric Semantics (Retrieval vs Citation) | **NOT VERIFIABLE** (Retrieval) <br> **PASS** (Citation & Failed Run) | `runner.py` line 104 used cited chunks (`result.supporting_chunk_ids`) instead of retrieved chunks. Raw JSON does not persist retrieved chunk IDs. |
| **Audit D** | Ablation Activation & Causality | **PASS** | Telemetry and code tracing prove all 7 components deactivated; retrieval attempts vary (12 vs 4 vs 3). |
| **Audit E** | Final Synthesis | **ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED** | Engineering and safety gates PASS; scientific retrieval claim blocked by metric logging defect. |

---

## Audit A: Exact Experiment Identity
- **Raw Result Variants:** `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_SELECTIVE_VERIFICATION`
- **Manifest Variants:** `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`
- **Intended Variants:** `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`
- **Investigation of Alternative Names:** `NO_CLAIM_GRAPH`, `NO_CROSS_EXAMINATION`, and `NO_ADAPTIVE_DEPTH` were reporting-level misnomers used in earlier conversational summaries. They do not exist in the code, schema enum, manifest, or raw results.
- **Code Mapping:** Every executed variant strictly toggles its corresponding `ControllerConfig` attribute in `app/ablation/config.py`.

---

## Audit B: Benchmark Identity
- **Executed Benchmark:** `data/benchmark/aeris_benchmark.json`
- **File Hash (SHA256):** `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`
- **Total Questions:** 28 (20 Answerable, 8 Unanswerable)
- **Status of `benchmark_questions_v2.json`:** Verified nonexistent in both disk and git history. Confirmed as an uncommitted documentation reference.

---

## Audit C: Metric Semantics & Failed-Run Recomputation
### 1. Code Implementation Trace
In `app/ablation/runner.py` lines 103-109:
```python
expected_chunks = set(record.supporting_chunk_ids)
retrieved_chunks = set(result.supporting_chunk_ids)  # <--- BUG: result.supporting_chunk_ids are CITED chunks
evidence_hit = len(expected_chunks.intersection(retrieved_chunks)) > 0
evidence_recall = len(expected_chunks.intersection(retrieved_chunks)) / len(expected_chunks)
```
- `ControllerResult` outputs `supporting_chunk_ids` (the chunks backing verified claims cited in the answer).
- The raw checkpoint persists `evidence_count: int` (e.g. 24 chunks retrieved), but **does not persist `retrieved_chunk_ids: List[str]`**.
- **Conclusion:** The reported 35% Hit Rate and 0.2750 Recall are **Citation Metrics** (Cited Chunk Hit Rate and Cited Evidence Coverage), NOT Retriever Hit Rate or Retriever Recall.
- **Retrieval Metric Status:** **NOT VERIFIABLE** from the raw checkpoint.

### 2. Full 8-Variant Recomputation (Accounting for `FULL_AERIS / q_mh_04` Failure)
| Variant | Total Runs | Completed Runs | Ans Completed | Citation Hits | Citation Hit Rate (N=20) | Citation Hit Rate (Completed) | Citation Recall (N=20) | Citation Recall (Completed) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 28 | 27 | 19 | 7 | 35.00% | 36.84% | 0.2750 | 0.2895 |
| `NO_ADAPTIVE_RETRIEVAL` | 28 | 28 | 20 | 7 | 35.00% | 35.00% | 0.2750 | 0.2750 |
| `NO_QUERY_REFORMULATION` | 28 | 28 | 20 | 7 | 35.00% | 35.00% | 0.2750 | 0.2750 |
| `NO_RETRIEVAL_MEMORY` | 28 | 28 | 20 | 7 | 35.00% | 35.00% | 0.2750 | 0.2750 |
| `NO_CLAIM_VERIFICATION` | 28 | 28 | 20 | 7 | 35.00% | 35.00% | 0.2750 | 0.2750 |
| `NO_CONTRADICTION_ANALYSIS` | 28 | 28 | 20 | 7 | 35.00% | 35.00% | 0.2750 | 0.2750 |
| `NO_CROSSLINGUAL_AGREEMENT` | 28 | 28 | 20 | 7 | 35.00% | 35.00% | 0.2750 | 0.2750 |
| `NO_SELECTIVE_VERIFICATION` | 28 | 28 | 20 | 7 | 35.00% | 35.00% | 0.2750 | 0.2750 |

- `FULL_AERIS / q_mh_04` failed due to `ClaimTypingError`. Under strict intent-to-treat ($N=20$), Citation Hit Rate is 35.00% and Recall is 0.2750. When evaluated over valid completed runs ($N=19$), Citation Hit Rate is 36.84% and Recall is 0.2895.

---

## Audit D: Ablation Activation & Causal Interpretability
### 1. Component Deactivation Telemetry
| Variant | Target Deactivation | Verified Metric | Result |
|---|---|---|:---:|
| `NO_CLAIM_VERIFICATION` | Claim verification disabled | Verification calls = 0 (vs 64 in Full) | **ACTIVE** |
| `NO_CONTRADICTION_ANALYSIS` | Contradiction analysis disabled | Contradiction calls = 0 (vs 27 in Full) | **ACTIVE** |
| `NO_CROSSLINGUAL_AGREEMENT` | Multilingual analysis disabled | Cross-lingual calls = 0 (vs 27 in Full) | **ACTIVE** |
| `NO_SELECTIVE_VERIFICATION` | Selective verification disabled | Selective calls = 0 (vs 21 in Full) | **ACTIVE** |
| `NO_RETRIEVAL_MEMORY` | Cross-requirement memory disabled | Memory lookups = 0 (vs 64 in Full) | **ACTIVE** |
| `NO_ADAPTIVE_RETRIEVAL` | Candidate depth expansion disabled | Depth expansions = 0 (vs 8 in Full) | **ACTIVE** |
| `NO_QUERY_REFORMULATION` | Query reformulator disabled | Attempts on `q_unans_01` = 3 (vs 12 in Full) | **ACTIVE** |

### 2. Telemetry Naming Quirk
- `app/adaptive_retrieval/controller.py` assigned query types as `f'reformulation_{i}'` (`reformulation_1`), while `controller.py` checked `if att.query_type == 'reformulated'`. Because of this string mismatch, `reformulation_triggered` remained False in the summary metadata, but execution attempts prove query reformulation executed.

### 3. Causal Architecture Boundary
- Downstream components run in Stages 8-12. In AERIS, there is no back-edge from Stage 8+ to Stage 2. Downstream ablations cannot and should not affect retrieval chunk sets.

---

## Audit E: Final Verdict
### Final Decision: `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`
- **Engineering & Safety Validity:** **100% PASSED** (0/64 false supports, 100% cache isolation, zero provenance defects, all 7 ablations activated and causally isolated).
- **Scientific Interpretability:** **BLOCKED** on retrieval claims because the runner evaluated cited chunks rather than retrieved chunks, and the raw checkpoint does not store retrieved chunk IDs.

Deliverables generated:
- `data/results/ablation_final224_final_gate_audit.json`
- `data/results/ablation_final224_final_gate_audit.md`
