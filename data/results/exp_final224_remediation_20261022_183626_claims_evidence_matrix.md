# AERIS-RAG — Research Claims and Evidence Matrix

**Target Experiment:** `exp_final224_remediation_20261022_183626`  
**Execution Timestamp:** 2026-10-22 18:36:26 UTC – 2026-10-23 01:11:46 UTC (Runtime: 23,676.7s / ~394.6 mins)  
**Evaluator & Auditor:** Independent Scientific Audit Agent  
**Benchmark SHA-256:** `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` (Verified Byte-for-Byte Immutable)  
**Document Purpose:** Rigorous research-grade claims and evidence matrix mapping potential scientific claims to empirical evidence, metrics, audit artifacts, and known limitations.

---

## 1. Classification Framework & Methodology

Every research claim evaluated in this matrix is classified into one of three mutually exclusive evidentiary categories:

- **SUPPORTED:** The claim is directly and unambiguously demonstrated by existing experimental records and telemetry within the tested benchmark scope.
- **PARTIALLY SUPPORTED:** Empirical evidence supports aspects of the claim (such as pipeline execution or component bypass), but critical qualifications, limited metrics, or unexercised pathways prevent full substantiation.
- **NOT ESTABLISHED:** The claim is either refuted by the empirical data (e.g., high coverage claims refuted by 21.25% coverage) or lacks empirical evidence because the benchmark did not evaluate the necessary conditions (e.g., cross-lingual corpora, external baselines).

### Epistemic Baseline & Known Benchmark Constraints
All claims must be interpreted within the boundaries of the audited experimental setup:
- **Corpus & Queries:** 28 questions evaluated over chunks of Lewis et al. (2020) (`test_document`).
- **Sample Distribution:** 20 answerable questions ($N_{\text{ans}}=160$) and 8 unanswerable questions ($N_{\text{unans}}=64$) across 8 variants.
- **Answerable Outcomes:** 34 fully supported (21.25%), 14 partially supported (8.75%), 104 conservatively rejected (65.00%), 8 failed (5.00%).
- **Execution Failures:** Exactly 8 failures (3.57% total attrition), all isolated to `q_mh_04` due to an LLM enum mismatch (`'COMPARE'`).
- **Effective Unanswerable Degrees of Freedom:** $N_{\text{distinct}} = 8$ distinct questions repeated across 8 variants.
- **Environment Status:** Missing exact Ollama binary commit and unpinned transitive package versions.

---

## 2. Research Claims and Evidence Matrix

| Claim ID | Category | Proposed Research Claim | Supporting Evidence | Exact Metric or Observation | Evidence Artifact & Path | Strength of Evidence | Limitations | Recommended Paper Wording |
|:---:|:---|:---|:---|:---|:---|:---:|:---|:---|
| **C-01** | **Provenance & Grounding** | AERIS-RAG enforces strict citation provenance, preventing hallucinations by ensuring cited passages strictly originate from retrieved candidates. | Independent audit verified that all cited chunk IDs exist within the retrieved candidate pool with zero duplicate IDs or orphaned citations. | 0 provenance defects across 224 runs; 0 duplicate claim IDs; 0 duplicate chunk IDs; 0 supported answers without claims. | [`ablation_exp_final224_remediation_20261022_183626_scientific_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_scientific_audit.json) | **SUPPORTED** | Evaluated on a single document corpus (`test_document`). Does not evaluate dynamic index corruption or external web search. | *"AERIS-RAG strictly enforces citation provenance across evaluated runs, with zero observed instances of unretrieved passage citations or duplicate provenance identifiers."* |
| **C-02** | **Safety & False Support** | AERIS-RAG prevents false support on unanswerable questions, satisfying the empirical safety gate of $\le 5.0\%$. | In all 64 unanswerable evaluations, the system safely refused to answer, achieving a 0.0% false support rate. | False Support Rate: **0 / 64 = 0.0000%**; Unanswerable Rejection Rate: **64 / 64 = 100.0000%**. | [`ablation_exp_final224_remediation_20261022_183626_scientific_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_scientific_audit.json) | **SUPPORTED** | Sample size limitation: 64 evaluations derive from only 8 distinct unanswerable queries ($N_{\text{distinct}}=8$). Clopper-Pearson 95% CI upper bound is $\le 4.57\%$. | *"Within the evaluated 28-question benchmark, AERIS-RAG reliably rejected all unanswerable queries (0/64 false support), satisfying the $\le 5.0\%$ empirical safety threshold."* |
| **C-03** | **Hallucination Risk** | AERIS-RAG eliminates hallucination risk and guarantees zero false assertions in open-domain deployment. | Zero false support observed across the 64 unanswerable evaluations in this benchmark. | 0 false supports observed out of 64 runs. | [`exp_final224_remediation_20261022_183626_reproducibility_package.md`](file:///e:/aeris-rag/data/results/exp_final224_remediation_20261022_183626_reproducibility_package.md) | **NOT ESTABLISHED** | Statistical bounds on 64 Bernoulli trials cannot prove zero probability ($p_{\text{upper}} \approx 4.57\%$). Unseen out-of-domain prompts may produce hallucinations. | *"Do not claim zero risk. State: 'While zero false supports were observed across the 64 evaluations, statistical confidence intervals (95% upper bound: 4.57%) and limited question diversity ($N=8$) preclude claims of universal hallucination elimination.'"* |
| **C-04** | **Requirement Support** | Requirement-level validation distinguishes partial evidence from full support, preventing partial answers from masquerading as fully grounded. | Multi-part queries with incomplete evidence were automatically downgraded to `PARTIALLY_SUPPORTED` and excluded from the supported numerator. | 14 answerable evaluations downgraded to `PARTIALLY_SUPPORTED`; 0 unanswerables received partial or full support. | [`ablation_results_exp_final224_remediation_20261022_183626.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261022_183626.json) | **SUPPORTED** | Keyword and concept facet matching relies on predefined synonym lists and local LLM judge calls; edge cases with novel semantic phrasing may trigger conservative rejection. | *"Requirement-level semantic validation successfully detects partial evidence coverage in multi-part queries, downgrading incomplete answers to PARTIALLY_SUPPORTED and excluding them from fully supported accuracy metrics."* |
| **C-05** | **Fusion Defect Remediation** | AERIS-RAG prevents judge hallucinations from validating dense-sparse fusion when only dense retrieval text is present. | On question `q_meth_02`, deterministic facet checking identified the absence of `sparse` and `fusion`, triggering judge overrides in all 8 variants. | 8 / 8 variants returned `INSUFFICIENT_EVIDENCE` with downgrade category `REQUIREMENT_UNSUPPORTED`. | [`exp_final224_remediation_20261022_183626_final_independent_audit.md`](file:///e:/aeris-rag/data/results/exp_final224_remediation_20261022_183626_final_independent_audit.md) | **SUPPORTED** | Specific to the concept facets configured in the validator; requires facet specifications for other multi-modal retrieval tasks. | *"Explicit facet verification prevents LLM judge hallucination on dense-sparse retrieval queries, ensuring that dense-only evidence cannot establish hybrid fusion claims."* |
| **C-06** | **Contradiction Resolution** | AERIS-RAG detects and resolves cross-passage contradictions, improving answer accuracy on conflicting evidence corpora. | Contradiction pipeline executed (27 calls, 41 pairs evaluated), but zero contradiction edges or conflict resolutions were triggered. | `contradiction_count: 0` across `q_contra_01` and `q_contra_02`; accuracy identical between `FULL_AERIS` and `NO_CONTRADICTION_ANALYSIS`. | [`ablation_exp_final224_remediation_20261022_183626_activation_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_activation_audit.json) | **PARTIALLY SUPPORTED** | The pipeline runs cleanly, but the benchmark corpus contains insufficient conflicting evidence pairs to empirically demonstrate accuracy benefits from conflict resolution. | *"AERIS-RAG incorporates a contradiction analysis pipeline that executes cross-claim NLI checks without pipeline errors, but the current benchmark corpus lacks sufficient conflicting evidence pairs to empirically demonstrate accuracy benefits from conflict resolution."* |
| **C-07** | **Cross-Lingual Consistency** | AERIS-RAG ensures cross-lingual evidence alignment and multi-language factual consistency. | None. Exactly 0 cross-lingual pairs were evaluated across the entire 224-run benchmark. | `cross_lingual_pairs: 0` in telemetry; `q_multi_01` evaluated an English query on an English corpus. | [`ablation_exp_final224_remediation_20261022_183626_activation_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_activation_audit.json) | **NOT ESTABLISHED** | The benchmark corpus is exclusively English. Cross-lingual classifiers and alignment modules were never exercised on multilingual document pairs. | *"Do not claim multilingual capability. State: 'Although AERIS-RAG includes architectural hooks for cross-lingual verification, the evaluation was conducted on an English-only corpus with zero cross-lingual pair evaluations; multilingual efficacy remains unestablished.'"* |
| **C-08** | **Ablation Component Bypass** | AERIS-RAG's modular architecture achieves 100% component isolation and bypass with measurable execution latency savings. | Telemetry verified 0 invocations for disabled modules across all 7 ablation variants; stage-level latency drops confirmed. | 0 depth expansions; 0 reformulations; 0 memory lookups; 0 verification calls; latency reduced by up to 10.40s (-9.2%). | [`ablation_exp_final224_remediation_20261022_183626_activation_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_activation_audit.json), [`metrics.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_metrics.json) | **SUPPORTED** | Retrieval hit rate (85.0%) was flat across variants; latency gains reflect bypassed pipeline stages rather than retrieval trade-offs. | *"Ablation experiments confirm 100% component bypass for all disabled modules, demonstrating significant stage-level latency reductions (up to 9.2% end-to-end runtime reduction when verification stages are bypassed)."* |
| **C-09** | **Adaptive Retrieval Superiority** | Adaptive depth expansion and query reformulation significantly improve retrieval hit rate over fixed-depth retrieval. | None. Retrieval hit rate (85.0%) and recall (0.7167) were identical across `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, and `NO_QUERY_REFORMULATION`. | Retriever Hit Rate: 85.0% for all variants; Retriever Recall: 0.7167 for all variants. | [`ablation_exp_final224_remediation_20261022_183626_metrics.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_metrics.json) | **NOT ESTABLISHED** | On this single-turn corpus, base hybrid retrieval captures gold chunks on attempt 1 for 85% of queries. The benchmark lacks queries that fail at $k=10$ but succeed at $k=50$. | *"On the evaluated 28-question single-turn benchmark, base hybrid retrieval dominates performance (85% hit rate), and ablation of adaptive depth expansion or query reformulation did not produce measurable retrieval hit-rate differentials."* |
| **C-10** | **Retrieval Effectiveness** | Hybrid dense-sparse retrieval achieves robust candidate passage recall on domain literature queries. | Decoupled retrieval metrics on answerable queries ($N=20$) show high candidate pool coverage. | Retriever Hit Rate: **85.0%** (17 / 20); Retriever Recall: **0.7167** on answerable queries. | [`ablation_exp_final224_remediation_20261022_183626_metrics.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_metrics.json) | **SUPPORTED** | Citation hit rate is significantly lower (35.0%) because downstream generation selects only a small subset of passages. | *"Hybrid dense-sparse retrieval achieved an 85.0% passage hit rate and 0.7167 recall on answerable benchmark queries, while downstream generation cited gold passages in 35.0% of evaluations."* |
| **C-11** | **Answerable Coverage** | AERIS-RAG achieves high generative coverage and answers the vast majority of answerable domain queries. | Refuted by empirical data: strict verification thresholds conservatively reject 65% of answerable queries. | Fully Supported Coverage: **21.2500%** (34 / 160); Partially Supported: **8.7500%** (14 / 160); Conservatively Rejected: **65.0000%** (104 / 160). | [`exp_final224_remediation_20261022_183626_final_independent_audit.md`](file:///e:/aeris-rag/data/results/exp_final224_remediation_20261022_183626_final_independent_audit.md) | **NOT ESTABLISHED** *(Refuted)* | Strict verification heavily prioritizes precision over recall, causing high conservative refusal on multi-hop or numerical queries. | *"AERIS-RAG operates in a high-precision, conservative regime where strict verification thresholds result in low answerable coverage (21.25% fully supported, 8.75% partially supported, 65.00% conservatively rejected)."* |
| **C-12** | **Execution Reliability** | AERIS-RAG operates with complete execution reliability and zero runtime exceptions. | Refuted by empirical data: 8 runs failed on question `q_mh_04` due to an unhandled LLM claim type string (`'COMPARE'`). | Execution Attrition: **8 / 224 = 3.5714%** (Answerables: 8 / 160 = 5.0000%; Unanswerables: 0 / 64 = 0.0000%). | [`ablation_results_exp_final224_remediation_20261022_183626.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261022_183626.json) | **PARTIALLY SUPPORTED** | Attrition remained within the $\le 5.0\%$ tolerance, but the taxonomy parsing vulnerability in `typer.py` caused systematic failure on `q_mh_04`. | *"While overall attrition remained within acceptable tolerance (3.57%, 8/224), systematic claim-typing failures on question q_mh_04 highlight the need for robust taxonomy aliasing in LLM output parsing."* |
| **C-13** | **Experimental Reproducibility** | The experiment maintains complete benchmark dataset immutability and transparent audit artifact logging. | Pre- and post-run benchmark SHA-256 verified identical; all 224 evaluation records, diagnostics, and manifests preserved. | Benchmark SHA-256: `ce9a86b6...` (Exact match); 224 records; 8 cache namespaces; 11 preserved artifact files. | [`data/benchmark/aeris_benchmark.json`](file:///e:/aeris-rag/data/benchmark/aeris_benchmark.json), [`exp_final224_remediation_20261022_183626_reproducibility_package.md`](file:///e:/aeris-rag/data/results/exp_final224_remediation_20261022_183626_reproducibility_package.md) | **SUPPORTED** | Missing pinned `requirements.lock`, exact Ollama server git commit, and model revision commit hashes constrain bitwise external re-execution. | *"Benchmark dataset immutability and complete audit trail preservation are established, though exact third-party re-execution is constrained by unpinned environment dependencies."* |
| **C-14** | **Comparative SOTA Performance** | AERIS-RAG outperforms external state-of-the-art systems (e.g. Self-RAG, Corrective RAG, GraphRAG) on hallucination reduction and accuracy. | None. No external baselines or competitive systems were evaluated in this experiment. | Zero comparative baseline metrics available in existing artifacts. | [`ablation_results_exp_final224_remediation_20261022_183626_manifest.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261022_183626_manifest.json) | **NOT ESTABLISHED** | The experiment is strictly an internal component ablation on a single corpus, not a comparative multi-model benchmark. | *"Do not assert comparative superiority or SOTA performance. State: 'While internal ablations establish the operational contribution of individual pipeline modules, comparative evaluation against external systems (e.g., Self-RAG, CRAG) remains future work.'"* |

---

## 3. Summary of Strongest Supported Claims

The following core findings represent the strongest empirically defensible claims established by experiment `exp_final224_remediation_20261022_183626`:

1. **Zero Observed False Support on the Benchmark Contract (Claim C-02):**
   - AERIS-RAG achieved **0 / 64 false supports (0.0000%)** on the evaluated unanswerable questions, satisfying the predefined $\le 5.0\%$ safety threshold.
   - All 64 unanswerable evaluations were conservatively rejected as `INSUFFICIENT_EVIDENCE` (100.0% rejection rate).
2. **Strict Citation and Provenance Guardrails (Claim C-01):**
   - In all 224 evaluations, 100% of cited passage chunks were verified to exist within the retrieved candidate pool.
   - Zero duplicate claim IDs, zero duplicate chunk IDs, and zero ungrounded assertions were observed.
3. **Requirement-Level Partial Support Discrimination (Claim C-04 & C-05):**
   - The Requirement Support Validator successfully intercepted multi-part requirements where only partial evidence was retrieved, downgrading 14 answerable evaluations to `PARTIALLY_SUPPORTED` and excluding them from fully supported accuracy.
   - The dense/sparse fusion defect on `q_meth_02` was completely remediated via deterministic facet checking, preventing LLM judges from hallucinating support in all 8 variants.
4. **Complete Ablation Isolation and Bypass (Claim C-08):**
   - Telemetry established 100% component bypass for all 7 ablation variants with zero leakage across disabled modules.
   - Bypassing claim verification stages reduced end-to-end execution latency by up to 9.2% (10.40s).
5. **Benchmark Immutability and Dataset Integrity (Claim C-13):**
   - The benchmark dataset SHA-256 (`ce9a86b6...`) remained byte-for-byte immutable throughout execution, audit, and packaging.

---

## 4. Summary of Claims That Are NOT Established

The following claims are **NOT ESTABLISHED** by the existing experimental artifacts and must be explicitly avoided in any scientific paper or public documentation:

1. **Claims of "Zero Risk" or "Universal Hallucination Elimination" (Claim C-03):**
   - While 0 false supports were observed across the 64 evaluations, the sample size ($N_{\text{distinct}}=8$) yields an empirical 95% confidence upper bound of $\le 4.57\%$. Universal absence of hallucination cannot be claimed.
2. **Claims of "High Answer Coverage" (Claim C-11):**
   - High coverage is refuted by the data. The system operates in a high-precision, conservative regime where 65.00% of answerable questions were conservatively rejected, resulting in 21.25% full answerable coverage.
3. **Claims of "Multilingual and Cross-Lingual Verification Superiority" (Claim C-07):**
   - The evaluation corpus was English-only. Zero cross-lingual pairs were evaluated (`cross_lingual_pairs: 0`). Multilingual efficacy is unestablished.
4. **Claims of "Contradiction Resolution Efficacy" (Claim C-06):**
   - Although the contradiction analysis module executed without errors, zero contradiction graph edges were integrated (`contradiction_count: 0`), and ablation of the module did not alter accuracy.
5. **Claims of "Adaptive Retrieval Superiority Over Fixed Retrieval" on this Benchmark (Claim C-09):**
   - Retriever hit rate (85.0%) and recall (0.7167) were identical between `FULL_AERIS` and `NO_ADAPTIVE_RETRIEVAL`. The single-turn benchmark did not exercise deep candidate expansion.
6. **Claims of "State-of-the-Art" or "Superiority Over External Baselines" (Claim C-14):**
   - No external baseline models (e.g. Self-RAG, CRAG) were evaluated. The experiment was an internal ablation only.
7. **Claims of "100% Execution Reliability" (Claim C-12):**
   - An unhandled enum mapping (`"COMPARE"` vs `"COMPARATIVE"`) in `typer.py` caused systematic failure on question `q_mh_04` (3.57% total attrition).

---

## 5. Methodological Guidelines for Paper Authors

When reporting the results of AERIS-RAG in academic literature, authors must adhere to the following principles:

1. **State Exact Denominators:** Always report the exact sample size and effective degrees of freedom ($N_{\text{ans}}=160$, $N_{\text{unans}}=64$, $N_{\text{distinct}}=8$, $N_{\text{total}}=224$).
2. **Distinguish Precision from Coverage:** Clearly articulate the engineering trade-off: AERIS-RAG achieves high precision (0.0% false support) by adopting an aggressive conservative rejection policy (65.0% answerable rejection, 21.25% coverage).
3. **Report Intent-to-Treat Metrics:** Include the 8 execution failures on `q_mh_04` as zero scores in all overall accuracy and retrieval calculations (overall accuracy: 43.75%).
4. **Acknowledge Environment Gaps:** Explicitly disclose that third-party exact re-execution requires pin-locking transitive Python packages and Ollama server build revisions.
5. **Avoid Over-Generalization:** Restrict empirical conclusions to the evaluated 28-question single-turn corpus.

---

## 6. Audit Sign-Off & Strict Compliance Certification

- **Strictly Read-Only Execution:** No benchmark, evaluation, model inference, or background job was executed.
- **Artifact Immutability:** No source code, configuration files, dataset files, labels, or historical results were modified.
- **New File Created:** Only the requested claims-and-evidence matrix was written.
- **Step 23:** Step 23 has not been started.
