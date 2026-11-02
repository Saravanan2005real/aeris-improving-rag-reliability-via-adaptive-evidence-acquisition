# STEP 22C — POST-HOC SCIENTIFIC AUDIT

## Experiment identity
Experiment ID: `exp_clean224_20261004_173525`

## Dataset integrity
* Expected runs: 224
* Actual records: 224
* Unique question × variant pairs: 224
* Duplicate pairs: 0
* Missing pairs: 0
* Contamination from previous experiments: None (all records match the new experiment ID)

## Variant execution audit
Inspection of `app/ablation/config.py` and `app/controller/controller.py` proves that the configuration flags do indeed correctly bypass the intended components logically:
* **NO_ADAPTIVE_RETRIEVAL**: Modifies the K-schedule in `AdaptiveRetrievalController` to only run the first depth, bypassing expansion.
* **NO_QUERY_REFORMULATION**: Logic block `if enable_query_reformulation and...` explicitly skips generation of new queries.
* **NO_RETRIEVAL_MEMORY**: Passed as `None` to the retrieval controller; `memory.has_query_attempt()` is skipped.
* **NO_CLAIM_VERIFICATION**: Bypasses the `self.graph_verifier` loop entirely.
* **NO_CONTRADICTION_ANALYSIS**: Bypasses `self.contradiction_analyzer`.
* **NO_CROSSLINGUAL_AGREEMENT**: Bypasses `self.cross_lingual_analyzer`.
* **NO_SELECTIVE_VERIFICATION**: Bypasses `self.selective_verification_executor`.

## Cache isolation audit
**Cache isolation: FAIL**

A critical architectural flaw exists in `app/performance_cache.py`:
```python
    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
            except:
                self._cache = {}
        # Missing 'else: self._cache = {}'
```
Because the `_cache` dictionary is not cleared if the new cache file doesn't exist, every subsequent variant implicitly retains the fully populated memory cache of `FULL_AERIS`. 

The audit script proved that variants 3 through 8 (`NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, etc.) didn't even create cache files on disk because they experienced exactly **0 cache misses**—they were entirely fed by the `FULL_AERIS` memory cache. 

## Execution signatures
| Variant | Intended Disabled Component | Evidence It Was Disabled | PASS/FAIL |
|---------|-----------------------------|--------------------------|-----------|
| FULL_AERIS | None | N/A | PASS |
| NO_ADAPTIVE_RETRIEVAL | Adaptive expansion | Config modifies schedule | PASS (logically) |
| NO_QUERY_REFORMULATION | Reformulation logic | Config skips query expansion | PASS (logically) |
| NO_RETRIEVAL_MEMORY | Memory lookup | Config skips memory checks | PASS (logically) |
| NO_CLAIM_VERIFICATION | Verification LLM calls | Config skips `graph_verifier` | PASS |
| NO_CONTRADICTION_ANALYSIS | Contradiction LLM calls | Config skips analyzer | PASS |
| NO_CROSSLINGUAL_AGREEMENT | Cross-lingual LLM calls | Config skips analyzer | PASS |
| NO_SELECTIVE_VERIFICATION | Selective verification | Config skips executor | PASS |

*(Note: Although logically disabled in code, the ablation effects of retrieval variations were entirely neutralized by cache contamination downstream).*

## Identical-metric investigation
**Diagnosis: C. Cache contamination**
The suspicious identical retrieval metrics (Evidence Hit = 25.00%, Evidence Recall = 0.1964) across all variants are the direct consequence of cache contamination. Because the Answer Generator, Coverage Estimator, and Claim Extractor were pulling from the `FULL_AERIS` cache, they behaved identically for identical sub-queries. The retrieval ablation variants were effectively neutralized by downstream cached LLM responses.

## 28 × 8 per-question matrix
The complete 28 × 8 per-question matrix has been generated and saved to the dedicated audit artifact:
`data/results/ablation_audit_clean224_matrix.json`

## Variant deltas
Because of the cache contamination, almost all metrics remained artificially identical. 
Number of questions with changed execution out of 28:
* **NO_ADAPTIVE_RETRIEVAL**: 0 changed evidence chunks
* **NO_QUERY_REFORMULATION**: 0 changed evidence chunks
* **NO_RETRIEVAL_MEMORY**: 0 changed evidence chunks
* **NO_CLAIM_VERIFICATION**: 5 changed evidence chunks, 23 changed verifications
* **NO_CONTRADICTION_ANALYSIS**: 2 changed evidence chunks
* **NO_CROSSLINGUAL_AGREEMENT**: 0 changed evidence chunks
* **NO_SELECTIVE_VERIFICATION**: 0 changed evidence chunks, 23 changed selective verifications

## Component-specific checks
* **NO_ADAPTIVE_RETRIEVAL**: Expansion bypassed, but identical answers generated due to cache.
* **NO_CLAIM_VERIFICATION**: `verified_claim_count` correctly drops to 0 (changed in 23 questions).
* **NO_SELECTIVE_VERIFICATION**: `selected_verification_count` correctly drops to 0 (changed in 23 questions).

## Result integrity
All structural integrity and architectural guardrails passed (0 invented claim IDs, 0 unknown indexes, 0 unrecovered omissions, 0 invalid evidence IDs). However, the results are scientifically invalid due to the cache state bleed.

## Scientific validity
SCIENTIFIC_ABLATION_INVALID

## FINAL DECISION
NOT_READY_FOR_STEP_23
