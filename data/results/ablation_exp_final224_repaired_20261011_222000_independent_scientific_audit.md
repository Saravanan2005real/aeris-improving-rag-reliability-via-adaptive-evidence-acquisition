# AERIS-RAG — Independent Scientific Audit Report (Step 22C)

**Audit Target:** `exp_final224_repaired_20261011_222000`  
**Audit Scope:** Read-Only Independent Scientific & Engineering Audit  
**Date of Audit:** 2026-10-14  
**Audit Status:** **SCIENTIFICALLY INVALID (REJECTED)**  
**Audit Gate Verdicts:** 2 PASS, 4 FAIL, 0 UNRESOLVED  

---

## Executive Summary & Audit Matrix

This independent scientific audit was conducted in `E:\aeris-rag` on the repaired 224-run scientific ablation experiment `exp_final224_repaired_20261011_222000`. The experiment was evaluated strictly in read-only mode against the benchmark dataset [`data/benchmark/aeris_benchmark.json`](file:///E:/aeris-rag/data/benchmark/aeris_benchmark.json) and raw execution telemetry in [`data/results/ablation_results_exp_final224_repaired_20261011_222000.json`](file:///E:/aeris-rag/data/results/ablation_results_exp_final224_repaired_20261011_222000.json).

While previous internal audits labeled this experiment `SCIENTIFICALLY_VALID`, this comprehensive review identifies multiple critical defects that invalidate the experiment's scientific claims.

| Check # | Audit Area | Verdict | Primary Finding / Root Cause |
|:---:|:---|:---:|:---|
| 1 | **Answerability Integrity** | **PASS** | True labels match benchmark perfectly: 20 answerable ($20 \times 8 = 160$), 8 unanswerable ($8 \times 8 = 64$). 0 label mismatches across all 224 records. |
| 2 | **Independent Metric Recomputation** | **PASS** | Retriever Hit (90.0%), Retriever Recall (0.7917), Citation Hit (35.0%), Citation Recall (0.2750), False Support Rate (0.0000), and Supported Rate (10.625%) verified with 100% precision. Decoupled candidate vs citation evaluation confirmed. |
| 3 | **Ablation Activation & Component Bypass** | **FAIL** | `NO_ADAPTIVE_RETRIEVAL` telemetry records 55 attempts and 3 triggered runs. The bypass audit checked only candidate depth expansion ($k \in [10, 25, 50]$), completely missing that query reformulation remained active and triggered multi-attempt retrieval loops. |
| 4 | **Feature Engagement** | **FAIL** | Retrieval memory hits were 0 across all 77 lookups due to ephemeral per-request memory scoping. Cross-lingual pairs were 0 across all 28 calls because the document index is 100% monolingual English (`language: 'en'`). Neither feature was tested by the benchmark. |
| 5 | **Latency Integrity & Outlier Forensics** | **FAIL** | Max latency of 67,295.9s (18.69 hours) on `q_comp_02` was caused by an un-timeout-protected Ollama call during an overnight system sleep/suspension, corrupting the planning mean (2,408s) and variant mean (2,532s, +2,484% delta). |
| 6 | **Answer Utility & Over-Conservatism** | **FAIL** | Pathological over-rejection: only 17 of 160 answerable evaluations (10.6%) were supported, 15 of which came from just two comparative questions (`q_comp_01`, `q_comp_02`). 82 answerable runs (51.2%) were validly generated but post-hoc rejected by `RequirementSupportValidator`. 0% answer rate across 4 question categories. |
| 7 | **Audit Conclusion & Scientific Validity** | **NOT VALID** | Experiment cannot be certified as scientifically valid. Multiple paper claims must be withheld until pipeline and benchmark defects are rectified. |

---

## 1. Answerability Integrity Audit

### Benchmark Label Derivation
A direct audit of the benchmark dataset [`data/benchmark/aeris_benchmark.json`](file:///E:/aeris-rag/data/benchmark/aeris_benchmark.json) establishes the following ground-truth distribution across the 28 unique questions:
- **Total Questions:** 28
- **Answerable Questions (`answerability: True`):** 20
- **Unanswerable Questions (`answerability: False`):** 8
- **Other / Undefined:** 0

The 8 unanswerable benchmark questions span multiple categories:
1. `q_meth_02` (Category: `METHOD`, `supporting_chunk_ids: []`)
2. `q_comp_03` (Category: `COMPARATIVE`, `supporting_chunk_ids: []`)
3. `q_quant_03` (Category: `QUANTITATIVE`, `supporting_chunk_ids: []`)
4. `q_unans_01` (Category: `UNANSWERABLE`, `supporting_chunk_ids: []`)
5. `q_unans_02` (Category: `UNANSWERABLE`, `supporting_chunk_ids: []`)
6. `q_unans_03` (Category: `UNANSWERABLE`, `supporting_chunk_ids: []`)
7. `q_unans_04` (Category: `UNANSWERABLE`, `supporting_chunk_ids: []`)
8. `q_multi_01` (Category: `MULTILINGUAL`, `supporting_chunk_ids: []`)

### Denominator Reconciliation
Each question is evaluated across 8 ablation variants:
- **Total Answerable Evaluations:** $20 \text{ questions} \times 8 \text{ variants} = \mathbf{160}$
- **Total Unanswerable Evaluations:** $8 \text{ questions} \times 8 \text{ variants} = \mathbf{64}$
- **Total Records:** $160 + 64 = \mathbf{224}$

### Raw Result Comparison
Every raw execution record in [`data/results/ablation_results_exp_final224_repaired_20261011_222000.json`](file:///E:/aeris-rag/data/results/ablation_results_exp_final224_repaired_20261011_222000.json) was compared against `aeris_benchmark.json`.
- **Mismatched `is_answerable` flags:** 0
- **Mismatched `expected_answerability` flags:** 0
- **Integrity Status:** **PASS**

---

## 2. Independent Metric Recomputation

### Metric Formulas and Denominators
In accordance with the measurement repair specification in [`data/results/ablation_final224_measurement_repair_implementation.md`](file:///E:/aeris-rag/data/results/ablation_final224_measurement_repair_implementation.md), retrieval and citation metrics are evaluated strictly on the **answerable question subset** ($N = 20$ per variant, $N = 160$ globally):

1. **Retriever Hit Rate:**
   $$\text{Retriever Hit Rate} = \frac{1}{N_{\text{ans}}} \sum_{i=1}^{N_{\text{ans}}} \mathbb{I}\left( \text{GoldChunks}_i \cap \text{RetrievedChunks}_i \neq \emptyset \right)$$
   *Evaluated on `retrieved_chunk_ids` (all candidate chunks returned by the hybrid retriever and reranker).*

2. **Retriever Recall:**
   $$\text{Retriever Recall} = \frac{1}{N_{\text{ans}}} \sum_{i=1}^{N_{\text{ans}}} \frac{|\text{GoldChunks}_i \cap \text{RetrievedChunks}_i|}{|\text{GoldChunks}_i|}$$

3. **Citation Hit Rate:**
   $$\text{Citation Hit Rate} = \frac{1}{N_{\text{ans}}} \sum_{i=1}^{N_{\text{ans}}} \mathbb{I}\left( \text{GoldChunks}_i \cap \text{SupportingChunks}_i \neq \emptyset \right)$$
   *Evaluated on `supporting_chunk_ids` (the subset of chunks actually cited in the generated answer).*

4. **Citation Recall:**
   $$\text{Citation Recall} = \frac{1}{N_{\text{ans}}} \sum_{i=1}^{N_{\text{ans}}} \frac{|\text{GoldChunks}_i \cap \text{SupportingChunks}_i|}{|\text{GoldChunks}_i|}$$

5. **False Support Rate:**
   $$\text{False Support Rate} = \frac{\sum_{j \in \text{Unanswerable}} \mathbb{I}\left(\text{Status}_j \in \{\text{SUPPORTED, COMPLETED, PARTIALLY\_SUPPORTED}\}\right)}{N_{\text{unans}} = 64}$$

6. **Supported-Answer Rate (Answerable Coverage):**
   $$\text{Supported Rate} = \frac{\sum_{i \in \text{Answerable}} \mathbb{I}\left(\text{Status}_i \in \{\text{SUPPORTED, COMPLETED, PARTIALLY\_SUPPORTED}\}\right)}{N_{\text{ans}} = 160}$$

### Recomputation Results vs Reported Metrics

| Variant | Recomputed Retr. Hit | Reported Retr. Hit | Recomputed Retr. Recall | Reported Retr. Recall | Recomputed Cite. Hit | Reported Cite. Hit | Recomputed Cite. Recall | Reported Cite. Recall | Supported Runs (N=20) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | **0.9000** | 0.9000 | **0.7917** | 0.7917 | **0.3500** | 0.3500 | **0.2750** | 0.2750 | 2 (10.0%) |
| `NO_ADAPTIVE_RETRIEVAL` | **0.9000** | 0.9000 | **0.7917** | 0.7917 | **0.3500** | 0.3500 | **0.2750** | 0.2750 | 2 (10.0%) |
| `NO_CLAIM_VERIFICATION` | **0.9000** | 0.9000 | **0.7917** | 0.7917 | **0.4000** | 0.4000 | **0.3000** | 0.3000 | 3 (15.0%) |
| `NO_CONTRADICTION_ANALYSIS` | **0.9000** | 0.9000 | **0.7917** | 0.7917 | **0.3000** | 0.3000 | **0.2500** | 0.2500 | 1 (5.0%) |
| `NO_CROSSLINGUAL_AGREEMENT` | **0.9000** | 0.9000 | **0.7917** | 0.7917 | **0.3000** | 0.3000 | **0.2250** | 0.2250 | 2 (10.0%) |
| `NO_QUERY_REFORMULATION` | **0.9000** | 0.9000 | **0.7917** | 0.7917 | **0.3500** | 0.3500 | **0.2750** | 0.2750 | 2 (10.0%) |
| `NO_RETRIEVAL_MEMORY` | **0.9000** | 0.9000 | **0.7917** | 0.7917 | **0.3500** | 0.3500 | **0.2750** | 0.2750 | 2 (10.0%) |
| `NO_SELECTIVE_VERIFICATION` | **0.9000** | 0.9000 | **0.7667** | 0.7667 | **0.3500** | 0.3500 | **0.2500** | 0.2500 | 3 (15.0%) |

- **Decoupled Evaluation Verification:** In all 160 answerable records, `retrieved_chunk_ids` and `supporting_chunk_ids` were non-identical ($0 / 160$ identical sets). Candidates and citations are strictly separated.
- **Global False Support Rate:** Recomputed: $0 / 64 = \mathbf{0.0000}$ (Reported: 0.0000).
- **Global Supported-Answer Rate:** Recomputed: $17 / 160 = \mathbf{0.10625}$ (Reported: 10.625%).
- **Overall Answerability Accuracy:** Recomputed: $(17 + 64) / 224 = \mathbf{36.1607\%}$ (Reported: 36.16%).
- **Verification Status:** **PASS**

---

## 3. Ablation Activation & Component Bypass Audit

### Telemetry vs Code Path Analysis
Ablation integrity requires that when a component is disabled, its code execution path is 100% bypassed and generates zero activations in runtime telemetry.

| Variant | Expected Disabled Feature | Actual Per-Record Telemetry | Code Implementation Path | Bypass Audit Claim | True Bypass Status |
|:---|:---|:---|:---|:---:|:---:|
| `NO_ADAPTIVE_RETRIEVAL` | Adaptive Retrieval Depth & Loops | **55 attempts, 3 triggered runs, 0 depth expansions** | [`app/adaptive_retrieval/controller.py:164-166`](file:///E:/aeris-rag/app/adaptive_retrieval/controller.py#L164-L166), [`app/ablation/config.py:12-13`](file:///E:/aeris-rag/app/ablation/config.py#L12-L13) | PASS (0 activations) | **FAIL (Leakage)** |
| `NO_QUERY_REFORMULATION` | Query Reformulation | 0 attempts, 0 triggered runs | [`app/adaptive_retrieval/controller.py:352`](file:///E:/aeris-rag/app/adaptive_retrieval/controller.py#L352) | PASS | **PASS** |
| `NO_RETRIEVAL_MEMORY` | Retrieval Memory | 0 lookups, 0 hits | [`app/controller/controller.py:99`](file:///E:/aeris-rag/app/controller/controller.py#L99) | PASS | **PASS** |
| `NO_CLAIM_VERIFICATION` | Claim Verification | 0 verification calls, 0 verified claims | [`app/controller/controller.py:254-288`](file:///E:/aeris-rag/app/controller/controller.py#L254-L288) | PASS | **PASS** |
| `NO_CONTRADICTION_ANALYSIS` | Contradiction Analysis | 0 calls, 0 pairs evaluated | [`app/controller/controller.py:299-336`](file:///E:/aeris-rag/app/controller/controller.py#L299-L336) | PASS | **PASS** |
| `NO_CROSSLINGUAL_AGREEMENT` | Cross-Lingual Analysis | 0 calls, 0 pairs evaluated | [`app/controller/controller.py:346-383`](file:///E:/aeris-rag/app/controller/controller.py#L346-L383) | PASS | **PASS** |
| `NO_SELECTIVE_VERIFICATION` | Selective Verification | 0 calls, 0 claims selected | [`app/controller/controller.py:451-494`](file:///E:/aeris-rag/app/controller/controller.py#L451-L494) | PASS | **PASS** |

### Forensics on `NO_ADAPTIVE_RETRIEVAL` Failure
The internal audit [`ablation_exp_final224_repaired_20261011_222000_activation_audit.json`](file:///E:/aeris-rag/data/results/ablation_exp_final224_repaired_20261011_222000_activation_audit.json) asserted:
```json
"bypass_verifications": {
  "NO_ADAPTIVE_RETRIEVAL": true
}
```
**Why this audit claim is false:**
1. In [`app/ablation/config.py`](file:///E:/aeris-rag/app/ablation/config.py#L12-L13):
   ```python
   elif variant == AblationVariant.NO_ADAPTIVE_RETRIEVAL:
       config.enable_adaptive_retrieval = False
   ```
   Note that `config.enable_query_reformulation` was **not** disabled; it remained `True`.
2. In [`app/adaptive_retrieval/controller.py`](file:///E:/aeris-rag/app/adaptive_retrieval/controller.py#L163-L166):
   ```python
   schedule = self.candidate_k_schedule[: self.max_attempts_per_query]
   if not enable_adaptive_retrieval:
       schedule = [schedule[0]] if schedule else [25]
   ```
   Disabling adaptive retrieval only pinned the candidate depth schedule to `[10]`, preventing candidate depth expansions ($k=25, 50$).
3. At lines 352-361:
   ```python
   if enable_query_reformulation and query_type == "original" and not query_sufficient:
       reformulated = self.query_reformulator.reformulate(...)
       for i, r_query in enumerate(reformulated, start=1):
           queries_to_try.append((r_query, f"reformulation_{i}"))
   ```
   When the initial retrieval attempt failed coverage sufficiency, query reformulation generated alternative queries and executed subsequent retrieval attempts.
4. In [`app/controller/controller.py`](file:///E:/aeris-rag/app/controller/controller.py#L611-L614):
   ```python
   for res in retrieval_results:
       ar_calls += len(res.attempts)
       if len(res.attempts) > 1:
           ar_triggered = True
   ```
   Because multiple attempts were executed via reformulated queries, `len(res.attempts) > 1`, setting `adaptive_retrieval_triggered = True`.
   Specifically, for questions `q_mh_01` (8 attempts, 6 reformulations), `q_unans_01` (4 attempts, 3 reformulations), and `q_unans_03` (4 attempts, 3 reformulations), adaptive multi-attempt retrieval actively executed.
5. In [`scripts/audit_final_224.py`](file:///E:/aeris-rag/scripts/audit_final_224.py#L311):
   ```python
   bypass_checks["NO_ADAPTIVE_RETRIEVAL"] = variant_telemetry.get("NO_ADAPTIVE_RETRIEVAL", {}).get("candidate_depth_expansions", 0) == 0
   ```
   The audit script arbitrarily defined bypass as `candidate_depth_expansions == 0`, deliberately masking the 55 retrieval attempts and 3 triggered adaptive loops.
- **Activation Integrity Status:** **FAIL**

---

## 4. Feature Engagement & Benchmark Suitability Audit

The ablation report claims that all 8 components are integrated and functioning in `FULL_AERIS`. However, deep inspection of runtime telemetry and system state reveals that two major components were **never meaningfully exercised**:

```
+-------------------------------------------------------------------------------+
| Feature Engagement Analysis: FULL_AERIS                                       |
+------------------------------------+------------------+-----------------------+
| Component                          | Invocations/Calls| Meaningful Engagement |
+------------------------------------+------------------+-----------------------+
| Retrieval Memory                   | 77 Lookups       | 0 Cache Hits (0.0%)   |
| Cross-Lingual Consistency Analysis | 28 Calls         | 0 Pairs (0.0%)        |
+------------------------------------+------------------+-----------------------+
```

### 1. Retrieval Memory: Zero Hits (77 Lookups, 0 Hits, 0 Skips)
- **Root Cause in Code:** In [`app/controller/controller.py`](file:///E:/aeris-rag/app/controller/controller.py#L99):
  ```python
  memory = RetrievalMemory(request.document_id, request.question) if request.config.enable_retrieval_memory else None
  ```
  `RetrievalMemory` is instantiated as an ephemeral in-memory object on a **per-request** basis. It has zero persistence across benchmark questions.
- **Within-Request Behavior:** In [`app/adaptive_retrieval/controller.py`](file:///E:/aeris-rag/app/adaptive_retrieval/controller.py#L172-L177):
  ```python
  if enable_retrieval_memory and memory is not None and memory.has_query_attempt(
      query=current_query,
      requirement_id=requirement.requirement_id,
      candidate_k=candidate_k,
  ):
      continue
  ```
  Within a single question, information requirements have unique IDs (`req_1`, `req_2`), candidate depth schedule monotonically increases ($10 \rightarrow 25 \rightarrow 50$), and query reformulations produce distinct strings. A duplicate `(query, requirement_id, candidate_k)` tuple is **structurally impossible** within a single run.
- **Scientific Implication:** The 77 lookups were guaranteed to return `False`. Retrieval memory was never engaged, and its ablation delta ($+2.28$s, $+0.0\%$ hit/recall) measures pure random noise.

### 2. Cross-Lingual Agreement: Zero Pairs (28 Calls, 0 Pairs Evaluated)
- **Root Cause in Benchmark Corpus:** Inspection of [`data/indexes/test_document/metadata.json`](file:///E:/aeris-rag/data/indexes/test_document/metadata.json) reveals that all 42 chunks composing `test_document` are strictly English:
  ```json
  "languages in index": ["en"]
  ```
- **Monolingual Bypass in Code:** In [`app/verification/cross_lingual_claim.py`](file:///E:/aeris-rag/app/verification/cross_lingual_claim.py#L117-L134):
  ```python
  # OPTIMIZATION: Monolingual Bypass
  if len(languages) <= 1:
      return ClaimCrossLingualResult(..., pair_count=0, rationale="SKIPPED (MONOLINGUAL)")
  ```
  Because no chunk in the document is non-English, every single claim is bypassed as `SKIPPED (MONOLINGUAL)`.
- **Benchmark Question `q_multi_01`:** The only multilingual question in the benchmark (`q_multi_01`) is an **unanswerable** question written in English ("Does the RAG paper evaluate on multilingual tasks?") with empty gold chunks (`supporting_chunk_ids: []`).
- **Scientific Implication:** Cross-lingual agreement was never tested against a multilingual evidence pool. Claiming cross-lingual validation from this benchmark is scientifically invalid.
- **Feature Engagement Status:** **FAIL**

---

## 5. Latency Integrity & Outlier Forensics

### The 67,295.9-Second Outlier in `NO_ADAPTIVE_RETRIEVAL`
Reported metrics in [`ablation_exp_final224_repaired_20261011_222000_metrics.json`](file:///E:/aeris-rag/data/results/ablation_exp_final224_repaired_20261011_222000_metrics.json) show:
- `NO_ADAPTIVE_RETRIEVAL` Mean Latency: **2,532.15s** (+2,484.0% delta vs `FULL_AERIS`)
- `NO_ADAPTIVE_RETRIEVAL` Planning Mean: **2,408.29s**
- `NO_ADAPTIVE_RETRIEVAL` Max Latency: **67,295.94s**

### Forensics Identification
Inspection of [`data/results/ablation_results_exp_final224_repaired_20261011_222000.json`](file:///E:/aeris-rag/data/results/ablation_results_exp_final224_repaired_20261011_222000.json) pinpoints the exact record:
- **Variant:** `NO_ADAPTIVE_RETRIEVAL`
- **Question ID:** `q_comp_02`
- **Question:** *"Does RAG hallucinate more or less compared to other models?"*
- **Total Latency:** `67295.94343948364` seconds (18 hours, 41 minutes, 35.9 seconds)
- **Planning Stage Latency:** `67274.52637080004` seconds
- **All other stages for `q_comp_02`:** Retrieval: 36.70s, Claim Graph: 28.65s, Verification: 4.41s, Answer Gen: 8.61s.

### Diagnostic Evidence & Timeline
Correlating timestamps across files reveals what occurred:
1. Record 16 (`q_comp_01`) completed on: `2026-10-11T23:53:15.127032` (Sunday night)
2. Record 17 (`q_comp_02`) completed on: `2026-10-12T18:34:51.082931` (Monday evening)
3. Wall-clock elapsed time between Record 16 and Record 17: **67,295.96 seconds**.
4. In [`data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl`](file:///E:/aeris-rag/data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl) (line 1253):
   ```json
   {
     "timestamp": 1791810209.51,
     "stage": "Planning",
     "question_id": "q_comp_02",
     "variant": "NO_ADAPTIVE_RETRIEVAL",
     "attempt": 1,
     "model": "llama3.2:latest",
     "context_size": 5749,
     "latency": 67214.37,
     "parse_success": true,
     "schema_success": true
   }
   ```
5. In [`app/planning/requirement_planner.py`](file:///E:/aeris-rag/app/planning/requirement_planner.py#L30):
   ```python
   self.client = ollama.Client(host=self.host)
   ```
   The `ollama.Client` was initialized with **no timeout**.
6. When the host workstation was put to sleep / suspended overnight on Sunday, October 11, at ~23:53, the HTTP socket in `self.client.chat()` remained open without timing out. When the machine woke and resumed on Monday evening, October 12, at ~18:34, the call returned.
7. Both `time.time()` ([`requirement_planner.py:316`](file:///E:/aeris-rag/app/planning/requirement_planner.py#L316)) and `time.perf_counter()` ([`controller.py:80`](file:///E:/aeris-rag/app/controller/controller.py#L80)) measured the entire 18.67-hour sleep window as elapsed planning runtime.

### Impact on Variant Statistics
This single observation severely distorted the entire dataset:
- If `q_comp_02`'s planning stage took its normal ~5.5s, the mean planning latency for `NO_ADAPTIVE_RETRIEVAL` would be **5.81s** (not 2,408.29s).
- The true mean latency for `NO_ADAPTIVE_RETRIEVAL` would be **128.53s** (not 2,532.15s).
- The reported latency delta of $+2,484.0\%$ is an **instrumentation artifact of system suspension**, not an algorithmic property of adaptive retrieval.
- **Latency Integrity Status:** **FAIL**

---

## 6. Answer Utility & Over-Conservatism Analysis

### The Answerability Paradox: 17 Supported Outcomes out of 160
The experiment reported a **False Support Rate of 0.0000** (0/64 unanswerables answered), which Gate 3 hailed as a success. However, an analysis of answer utility reveals that this safety was achieved via **pathological over-rejection**:

```
Answerable Evaluations Breakdown (N = 160)
+-------------------------------------------------------------+
| Supported Outcomes:                      17 ( 10.6%)        |
| Post-hoc Downgraded by Requirement Validator: 82 ( 51.2%)   |
| Direct Insufficient from Generator:      61 ( 38.1%)        |
+-------------------------------------------------------------+
```

### Breakdown by Category

| Question Category | Total Runs | Answerable Runs | Supported Runs | Supported Rate (%) | Unanswerable Runs | False Support Runs |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **COMPARATIVE** | 24 | 16 | **15** | **93.8%** | 8 | 0 |
| **MULTI_HOP** | 40 | 40 | **2** | **5.0%** | 0 | 0 |
| **DIRECT_FACT** | 48 | 48 | **0** | **0.0%** | 0 | 0 |
| **METHOD** | 32 | 24 | **0** | **0.0%** | 8 | 0 |
| **QUANTITATIVE** | 24 | 16 | **0** | **0.0%** | 8 | 0 |
| **CONTRADICTION** | 16 | 16 | **0** | **0.0%** | 0 | 0 |
| **MULTILINGUAL** | 8 | 0 | **0** | N/A | 8 | 0 |
| **UNANSWERABLE** | 32 | 0 | **0** | N/A | 32 | 0 |
| **TOTAL** | **224** | **160** | **17** | **10.6%** | **64** | **0** |

### Per-Question Distribution
Out of 20 answerable questions, supported outcomes were concentrated in just **4 questions**:
- `q_comp_01`: Supported in 7 of 8 variants
- `q_comp_02`: Supported in 8 of 8 variants
- `q_mh_01`: Supported in 1 of 8 variants (`NO_SELECTIVE_VERIFICATION`)
- `q_mh_04`: Supported in 1 of 8 variants (`NO_CLAIM_VERIFICATION`)
- **Remaining 16 answerable questions:** **0 of 8 variants supported (0/128 runs)!**

### The Root Cause: Requirement Support Validator Downgrade
Why did 143 out of 160 answerable questions fail?
1. In 61 runs (38.1%), the generator produced `INSUFFICIENT_EVIDENCE` directly because the retriever failed to return necessary chunks or confidence was below threshold.
2. In **82 runs (51.2%)**, the generator successfully produced a coherent, grounded answer with high confidence (0.65 to 0.90) and valid claim/chunk provenance.
3. However, in [`app/controller/controller.py`](file:///E:/aeris-rag/app/controller/controller.py#L530-L549):
   ```python
   if answer_status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]:
       claims_texts = [graph_builder.claims[cid].text for cid in supporting_claim_ids if cid in graph_builder.claims]
       if plan and plan.requirements:
           req_results = []
           for req in plan.requirements:
               val_res = self.requirement_validator.validate(
                   question=request.question,
                   requirement=req.description,
                   answer=final_answer,
                   claims=claims_texts
               )
               req_results.append(val_res.is_supported)
           if not any(req_results):
               answer_status = "INSUFFICIENT_EVIDENCE"
   ```
   The `RequirementSupportValidator` compared the extracted claims against the planner's abstract requirement descriptions. Because planner requirements were frequently phrased using abstract concepts while claims were literal document sentences, `not any(req_results)` evaluated to `True`, silently overriding valid answers to `INSUFFICIENT_EVIDENCE`.
- **Answer Utility Status:** **FAIL**

---

## 7. Audit Conclusion & Paper Claims Guidance

### Issue Assignment Summary

| Audit Item | Verdict | Key Code / Artifact References |
|---|:---:|---|
| **Issue 1: Answerability Label Integrity** | **PASS** | [`data/benchmark/aeris_benchmark.json`](file:///E:/aeris-rag/data/benchmark/aeris_benchmark.json#L1-L150); [`ablation_results_exp_final224_repaired_20261011_222000.json`](file:///E:/aeris-rag/data/results/ablation_results_exp_final224_repaired_20261011_222000.json#L1-L50) |
| **Issue 2: Metric Recomputation & Decoupling** | **PASS** | [`app/ablation/runner.py:118-129`](file:///E:/aeris-rag/app/ablation/runner.py#L118-L129); [`ablation_exp_final224_repaired_20261011_222000_metrics.json`](file:///E:/aeris-rag/data/results/ablation_exp_final224_repaired_20261011_222000_metrics.json#L1-L100) |
| **Issue 3: Ablation Activation Integrity** | **FAIL** | [`app/ablation/config.py:12-13`](file:///E:/aeris-rag/app/ablation/config.py#L12-L13); [`app/adaptive_retrieval/controller.py:164-166,352`](file:///E:/aeris-rag/app/adaptive_retrieval/controller.py#L164-L166); [`scripts/audit_final_224.py:311`](file:///E:/aeris-rag/scripts/audit_final_224.py#L311) |
| **Issue 4: Feature Engagement (Memory & Cross-Lingual)** | **FAIL** | [`app/controller/controller.py:99`](file:///E:/aeris-rag/app/controller/controller.py#L99); [`app/verification/cross_lingual_claim.py:118`](file:///E:/aeris-rag/app/verification/cross_lingual_claim.py#L118); [`data/indexes/test_document/metadata.json`](file:///E:/aeris-rag/data/indexes/test_document/metadata.json#L1-L20) |
| **Issue 5: Latency Integrity & Outlier Artifact** | **FAIL** | [`app/planning/requirement_planner.py:30,307-316`](file:///E:/aeris-rag/app/planning/requirement_planner.py#L30); [`ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl:1253`](file:///E:/aeris-rag/data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl#L1253) |
| **Issue 6: Answer Utility & False-Negative Pathology** | **FAIL** | [`app/controller/controller.py:530-549`](file:///E:/aeris-rag/app/controller/controller.py#L530-L549); [`app/answer_generation/answer_generator.py:166-175`](file:///E:/aeris-rag/app/answer_generation/answer_generator.py#L166-L175) |

---

### Claims Supported by the Evidence
1. **Retriever Effectiveness:** The hybrid retriever + reranker achieves high evidence recall on answerable scientific queries (Retriever Hit Rate = 90.0%, Retriever Recall = 0.7917).
2. **Strict Hallucination Resistance:** The AERIS verification and provenance pipeline demonstrates zero false support on unanswerable queries (False Support Rate = 0.0000; 64/64 unanswerables rejected).
3. **Citation Provenance Integrity:** 100% of cited chunks in generated answers exist within the retrieved evidence pool; zero citation provenance defects were detected across all 224 runs.
4. **Decoupled Metric Architecture:** Retrieval capability and generative citation precision can be cleanly separated and measured independently.

---

### Claims That MUST Be Withheld
1. **DO NOT claim that `NO_ADAPTIVE_RETRIEVAL` exhibits a +2,484% latency penalty.** This figure is a complete instrumentation artifact caused by host workstation sleep during a blocking call to Ollama.
2. **DO NOT claim that Adaptive Retrieval was cleanly ablated.** In `NO_ADAPTIVE_RETRIEVAL`, query reformulation remained active and triggered multi-attempt adaptive loops for 3 questions (55 total attempts).
3. **DO NOT claim that Retrieval Memory improves efficiency or reduces latency.** Retrieval memory was instantiated with local request scope, never persisted across questions, and experienced a 0.0% hit rate across 77 lookups.
4. **DO NOT claim that Cross-Lingual Agreement was validated.** The benchmark corpus is 100% monolingual English; all 28 cross-lingual analysis calls were bypassed with 0 pairs evaluated.
5. **DO NOT claim that AERIS is an effective general QA system.** The pipeline suffers from an 89.4% false-negative rate on answerable questions (10.6% answer utility), failing 100% of direct fact, method, quantitative, and contradiction questions due to hyper-conservative post-hoc validator rejection.
6. **DO NOT claim that Step 22C is scientifically valid.** The experiment cannot be certified for paper submission until the identified instrumentation, ablation configuration, memory scoping, and validator bugs are resolved.

---

### Recommended Remediation Actions Prior to Step 23
1. **Ablation Configuration Fix:** Ensure `config.enable_query_reformulation = False` when `AblationVariant.NO_ADAPTIVE_RETRIEVAL` is selected ([`app/ablation/config.py`](file:///E:/aeris-rag/app/ablation/config.py#L12-L13)).
2. **Timeout & Outlier Guard:** Add explicit `timeout=120.0` to `ollama.Client` in all modules ([`app/planning/requirement_planner.py`](file:///E:/aeris-rag/app/planning/requirement_planner.py#L30), [`app/answer_generation/answer_generator.py`](file:///E:/aeris-rag/app/answer_generation/answer_generator.py#L17)). Add heartbeat detection in the runner to flag system suspensions.
3. **Memory Scoping Fix:** Elevate `RetrievalMemory` to session/document scope across questions to enable cross-query caching and reuse.
4. **Multilingual Benchmark Expansion:** Ingest genuine multilingual document chunks (e.g., German, French, Spanish) to create non-trivial cross-lingual evidence pairs.
5. **Calibrate Requirement Validator:** Relax `RequirementSupportValidator` or use semantic embedding similarity rather than strict LLM classification to prevent the false rejection of 51.2% of valid answers.
