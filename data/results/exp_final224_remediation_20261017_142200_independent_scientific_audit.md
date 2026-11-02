# AERIS-RAG — Independent Scientific Audit of Benchmark Experiment

**Experiment ID:** `exp_final224_remediation_20261017_142200`  
**Audit Protocol:** Strictly Read-Only Independent Scientific Audit & Forensic Analysis  
**Audit Timestamp:** `2026-10-17T20:56:00+05:30`  
**Evaluation Mode:** Complete 224-Record Raw Data Recomputation & Causal Tracing  
**Host & Model:** Local Ollama `http://localhost:11434`, `llama3.2:latest` (Deterministic, $T=0.0$)  
**Independent Audit Verdict:** **`FAIL`**  
**Acceptance Status:** **`SCIENTIFICALLY BLOCKED — REMEDIATION REQUIRED`**

---

## 1. Executive Verdict & Core Determination

An exhaustive, strictly read-only independent scientific audit was conducted on the 224 completed execution records of experiment `exp_final224_remediation_20261017_142200`.

### Official Audit Verdict: `FAIL`

The benchmark experiment **FAILS** scientific acceptance criteria due to a catastrophic violation of **Acceptance Gate 3 (Answerability & False-Support Safety)**:

$$\text{False Support Rate (FSR)} = \frac{31}{64} = \mathbf{48.44\%} \quad (\text{Threshold: } \le \mathbf{5.00\%})$$

While the engineering remediations delivered in Step 22D and Step 22D.1 functioned with complete structural fidelity—eliminating the empty-evidence cache deserialization defect (10,336 successful memory hits), strictly isolating the adaptive retrieval candidate loop (0 expansions under `NO_ADAPTIVE_RETRIEVAL`), decoupling retrieval candidate recall from citation recall, and preventing latency anomalies—the relaxed answer-support validation pipeline introduced in Step 22D has produced an unacceptable trade-off:

1. **Answerable Coverage Recovery (+352%):** Grounded supported answers on answerable questions recovered from 17/160 (10.63%) in historical Step 22C to **77/160 (48.13%)** in this experiment.
2. **False Support Collapse:** Unanswerable questions incorrectly accepted as `SUPPORTED` collapsed from 0/64 (0.00%) in Step 22C to **31/64 (48.44%)** in this experiment.
3. **Correlated Observation Concentration:** The 31 false-supported runs are not random failures across 224 independent questions; they are concentrated entirely in **4 specific unanswerable questions** (`q_meth_02`, `q_quant_03`, `q_unans_01`, and `q_multi_01`) where the pipeline repeatedly accepted hallucinated or ungrounded claims across 7 to 8 ablation variants. At the unique question level, **50.0% of unanswerable benchmark questions (4 of 8)** suffered from false support.

The automated scientific validity audit previously reported `BLOCKED`. This independent audit **strictly upholds that block**. Under no circumstances may Gate 3 be waived or discounted because answerable coverage improved.

```
+-----------------------------------------------------------------------------------------------+
|                                      FINAL AUDIT STATUS                                       |
|                                                                                               |
|                       SCIENTIFICALLY BLOCKED — REMEDIATION REQUIRED                           |
|                                                                                               |
|  * Acceptance Gate 1 (Structural Integrity):            PASS (224/224 records, 0 defects)     |
|  * Acceptance Gate 2 (Cache Isolation):                 PASS (Isolated per-variant namespaces) |
|  * Acceptance Gate 3 (Answerability & False Support):   FAIL (48.44% FSR vs <= 5.0% threshold) |
|  * Acceptance Gate 4 (Provenance Integrity):            PASS (0 orphan or unretrieved chunks) |
|  * Acceptance Gate 5 (Decoupled Denominators):          PASS (Answerable-only N=160 metrics)   |
|  * Acceptance Gate 6 (Ablation Component Isolation):    PASS (100% bypass on disabled flags)  |
|  * Acceptance Gate 7 (Monotonic Latency Instrumentation):PASS (0 timeouts, 0 sleep outliers)  |
|                                                                                               |
|  STEP 23 HARD STOP ENFORCED: NO PIPELINE MODIFICATIONS OR BENCHMARK ADVANCEMENT PERMITTED.    |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Independent Record Accounting & Metric Recomputation

All metrics were recomputed from the raw execution results in [`data/results/ablation_results_exp_final224_remediation_20261017_142200.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261017_142200.json) and cross-verified against the authoritative benchmark definition in [`data/benchmark/aeris_benchmark.json`](file:///e:/aeris-rag/data/benchmark/aeris_benchmark.json).

### 2.1 Benchmark Identity & Denominator Justification

The benchmark comprises exactly **28 unique questions**:
- **Answerable Questions ($N_{\text{ans\_unique}} = 20$):** Questions having document-grounded answers (`answerability: true`, `expected_status: "SUPPORTED"`). Evaluated across 8 variants $\rightarrow \mathbf{160}$ total answerable evaluations.
- **Unanswerable Questions ($N_{\text{unans\_unique}} = 8$):** Questions that cannot be answered from the document (`answerability: false`, `expected_status: "INSUFFICIENT_EVIDENCE"`). Evaluated across 8 variants $\rightarrow \mathbf{64}$ total unanswerable evaluations.
- **Total Executions:** $20 \times 8 + 8 \times 8 = 160 + 64 = \mathbf{224}$ runs.

### 2.2 Recomputed Confusion Matrix

The answerability decision matrix across all 224 runs is defined as follows:

| Actual Benchmark Label \ System Decision | System: `SUPPORTED` (Positive) | System: `INSUFFICIENT_EVIDENCE` (Negative) | Total Evaluated |
|:---|:---:|:---:|:---:|
| **Answerable Question** (`answerability: true`) | **True Positive (TP) = 77** | **False Negative (FN) = 83** | **$N_{\text{ans}} = 160$** |
| **Unanswerable Question** (`answerability: false`) | **False Positive (FP) = 31** | **True Negative (TN) = 33** | **$N_{\text{unans}} = 64$** |
| **Total Benchmark Decisions** | **108** | **116** | **224** |

### 2.3 Formal Metric Definitions & Calculated Values

$$\begin{aligned}
\text{Accuracy} &= \frac{\text{TP} + \text{TN}}{\text{Total}} = \frac{77 + 33}{224} = \mathbf{49.11\%} \\[6pt]
\text{Answerable Recall (Coverage)} &= \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{77}{160} = \mathbf{48.13\%} \\[6pt]
\text{Answerable Precision} &= \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{77}{108} = \mathbf{71.30\%} \\[6pt]
\text{Unanswerable Specificity (Rejection Rate)} &= \frac{\text{TN}}{\text{TN} + \text{FP}} = \frac{33}{64} = \mathbf{51.56\%} \\[6pt]
\mathbf{\text{False Support Rate (FSR)}} &= \frac{\mathbf{FP}}{\mathbf{FP} + \mathbf{TN}} = \frac{\mathbf{31}}{\mathbf{64}} = \mathbf{48.44\%} \quad (\text{Threshold } \le 5.00\%) \\[6pt]
\text{F1 Score} &= 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = 2 \times \frac{0.7130 \times 0.4813}{0.7130 + 0.4813} = \mathbf{0.5746}
\end{aligned}$$

### 2.4 Recomputed Variant-Level Performance & Telemetry

Metrics evaluated strictly with record-level denominators ($N=20$ answerable per variant, $N=8$ unanswerable per variant, $N=28$ total per variant):

| Ablation Variant | Retriever Hit ($N=20$) | Retriever Recall ($N=20$) | Citation Hit ($N=20$) | Citation Recall ($N=20$) | Supported Answerable (TP) | False Supported (FP) | Mean Latency (s) | Memory Hits Accumulated | Depth Expansions |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 90.0% | 0.7917 | 35.0% | 0.2750 | **9 / 20** (45.0%) | **4 / 8** (50.0%) | 99.30 | 0 | 25 |
| `NO_ADAPTIVE_RETRIEVAL` | 90.0% | 0.7917 | 35.0% | 0.2750 | **10 / 20** (50.0%) | **4 / 8** (50.0%) | 96.09 | 718 | **0** |
| `NO_CLAIM_VERIFICATION` | 90.0% | 0.7917 | 40.0% | 0.3000 | **10 / 20** (50.0%) | **3 / 8** (37.5%) | 92.32 | 3,868 | 25 |
| `NO_CONTRADICTION_ANALYSIS` | 90.0% | 0.7917 | 30.0% | 0.2500 | **8 / 20** (40.0%) | **4 / 8** (50.0%) | 93.26 | 6,024 | 25 |
| `NO_CROSSLINGUAL_AGREEMENT` | 90.0% | 0.7917 | 35.0% | 0.2750 | **10 / 20** (50.0%) | **4 / 8** (50.0%) | 94.30 | 8,180 | 25 |
| `NO_QUERY_REFORMULATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | **10 / 20** (50.0%) | **4 / 8** (50.0%) | 94.13 | 2,162 | 7 |
| `NO_RETRIEVAL_MEMORY` | 90.0% | 0.7917 | 35.0% | 0.2750 | **10 / 20** (50.0%) | **4 / 8** (50.0%) | 100.87 | **0** | 25 |
| `NO_SELECTIVE_VERIFICATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | **10 / 20** (50.0%) | **4 / 8** (50.0%) | 92.44 | 10,336 | 25 |
| **Global / Summary** | **90.0%** | **0.7917** | **35.0%** | **0.2750** | **77 / 160** (48.1%) | **31 / 64** (48.4%) | **95.38** | **10,336** | — |

### 2.5 Recomputed Category-Level Breakdown

| Category | Total Runs | Ans Evaluated | Unans Evaluated | Supported Ans (TP) | Insufficient Ans (FN) | False Supported (FP) | Correctly Rejected (TN) | Category Accuracy |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `COMPARATIVE` | 24 | 16 | 8 | 14 / 16 (87.5%) | 2 / 16 (12.5%) | **0 / 8 (0.0%)** | **8 / 8 (100.0%)** | **91.67%** (22/24) |
| `CONTRADICTION` | 16 | 16 | 0 | 16 / 16 (100.0%) | 0 / 16 (0.0%) | 0 / 0 | 0 / 0 | **100.0%** (16/16) |
| `DIRECT_FACT` | 48 | 48 | 0 | 8 / 48 (16.7%) | 40 / 48 (83.3%) | 0 / 0 | 0 / 0 | **16.67%** (8/48) |
| `METHOD` | 32 | 24 | 8 | 22 / 24 (91.7%) | 2 / 24 (8.3%) | **8 / 8 (100.0%)** | **0 / 8 (0.0%)** | **68.75%** (22/32) |
| `MULTILINGUAL` | 8 | 0 | 8 | 0 / 0 | 0 / 0 | **7 / 8 (87.5%)** | **1 / 8 (12.5%)** | **12.50%** (1/8) |
| `MULTI_HOP` | 40 | 40 | 0 | 9 / 40 (22.5%) | 31 / 40 (77.5%) | 0 / 0 | 0 / 0 | **22.50%** (9/40) |
| `QUANTITATIVE` | 24 | 16 | 8 | 8 / 16 (50.0%) | 8 / 16 (50.0%) | **8 / 8 (100.0%)** | **0 / 8 (0.0%)** | **33.33%** (8/24) |
| `UNANSWERABLE` | 32 | 0 | 32 | 0 / 0 | 0 / 0 | **8 / 32 (25.0%)** | **24 / 32 (75.0%)** | **75.00%** (24/32) |
| **Total Benchmark** | **224** | **160** | **64** | **77 / 160** | **83 / 160** | **31 / 64** | **33 / 64** | **49.11%** (110/224) |

### 2.6 Mismatches Documented in Automated Reporting

The independent audit uncovered two significant documentation errors in the prior automated summary report [`exp_final224_remediation_20261017_142200_completion_review.md`](file:///e:/aeris-rag/data/results/exp_final224_remediation_20261017_142200_completion_review.md):

1. **Transposition of `COMPARATIVE` and `QUANTITATIVE`:**
   - *Automated Summary Stated:* `COMPARATIVE` had 8/8 (100%) False Support and 37.5% Answerable Support; `QUANTITATIVE` had 0/8 (0%) False Support and 100% Answerable Support.
   - *Independent Raw Verification Proves:* Exactly the reverse! `COMPARATIVE` had **0/8 (0.0%)** False Support (all 8 runs of `q_comp_03` were correctly rejected) and 87.5% (14/16) Answerable Support. `QUANTITATIVE` had **8/8 (100.0%)** False Support (all 8 runs of `q_quant_03` were falsely supported) and 50.0% (8/16) Answerable Support.
2. **Variant Supported Answerable Count Discrepancies:**
   - *Automated Summary Stated:* `FULL_AERIS` = 10, `NO_CONTRADICTION` = 9, `NO_SELECTIVE` = 9.
   - *Independent Raw Verification Proves:* `FULL_AERIS` = **9**, `NO_CONTRADICTION` = **8**, `NO_SELECTIVE` = **10**. The global sum of 77 was correct, but internal variant allocations in the narrative table were inaccurate.

---

## 3. Forensic Investigation of the 31 False-Supported Unanswerable Cases

The 31 false-supported records originate from exactly **4 unique unanswerable benchmark questions**. Below is the exhaustive evidence-based audit for all 31 cases.

### Case Group 1: `q_meth_02` — Fused Retrieval Hallucination (8 Records)

- **Question:** "How does the system fuse dense and sparse retrieval?"
- **Category / Difficulty:** `METHOD` / `MEDIUM`
- **Benchmark Answerability:** `answerability: false`, `expected_status: "INSUFFICIENT_EVIDENCE"`
- **Authoritative Document Fact:** Lewis et al. (2020) uses *purely dense retrieval* (Dense Passage Retriever / DPR). The paper does not implement or evaluate BM25, sparse retrieval, or hybrid dense-sparse fusion. The question is genuinely unanswerable from the document.
- **Affected Variants (8 / 8):** `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`.
- **Generated Answer (Identical across all 8 variants):**
  > "The system fuses dense and sparse retrieval by leveraging a retrieval module to augment pre-trained, generative language models."
- **Supporting Claim Cited:** `test_document_p009_c020_claim_5`
  > *"Our work aims to expand the space of possible tasks with a single, unified architecture, by learning a retrieval module to augment pre-trained, generative language models."*
- **Supporting Chunk Cited:** `test_document_p009_c020` (Page 9, Section on General-Purpose Architectures for NLP).
- **Entailment Analysis:**
  - The cited chunk and claim state that the work augments language models with a retrieval module. They make **zero mention** of sparse retrieval or fusion mechanisms.
  - The generator fabricated an answer by parroting the question predicate ("fuses dense and sparse retrieval by...") and grafting it onto the general claim text.
- **Validator Decision & Mechanism:**
  - `RequirementSupportValidator._evaluate_semantic_support` evaluates requirements $R_1$, $R_2$, $R_3$ ("How does the system fuse dense retrieval?", etc.).
  - At line 214, `combined_claim_text` concatenates `claims`, `answer`, and `evidence_str`.
  - Because `answer` contains "dense", "sparse", "retrieval", and "system", the concept matching algorithm matched 80% ($0.80 \ge 0.20$) of the target concepts against the generated answer itself!
  - Grounding ratio against `p009_c020` exceeded 0.15 because the chunk contains "retrieval", "models", and "augment".
- **Defensible Classification:** **`FALSE SUPPORT`** (Hallucinated answer validated via circular self-matching).

---

### Case Group 2: `q_quant_03` — FEVER Dataset Size Hallucination (8 Records)

- **Question:** "What is the number of instances for the FEVER dataset?"
- **Category / Difficulty:** `QUANTITATIVE` / `EASY`
- **Benchmark Answerability:** `answerability: false`, `expected_status: "INSUFFICIENT_EVIDENCE"`
- **Authoritative Document Fact:** The RAG paper cites the FEVER dataset in its bibliography (Thorne et al., 2018), but nowhere in the body text or tables does it state the total number of instances in FEVER. The question is unanswerable from the document.
- **Affected Variants (8 / 8):** `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`.
- **Generated Answer (Identical across all 8 variants):**
  > "The FEVER dataset contains 1,000 instances."
- **Supporting Claim Cited:** `test_document_p015_c034_claim_1`
  > *"FEVER: a large-scale dataset for fact extraction and verification."*
- **Supporting Chunk Cited:** `test_document_p015_c034` (Page 15, Reference [56]).
- **Entailment Analysis:**
  - Reference [56] in chunk `p015_c034` contains the citation title and metadata ("In Proceedings of the 2018 Conference... Volume 1...").
  - The figure "1,000 instances" is pure fabrication by the generator (the actual FEVER dataset has over 185,000 claims; 1,000 does not appear anywhere in relation to FEVER instances).
- **Validator Decision & Mechanism:**
  - Target requirement: "The number of instances in the FEVER dataset".
  - Concepts matched: `dataset`, `fever`, `instances` (match ratio $0.75 \ge 0.20$).
  - Grounding check: Chunk `p015_c034` contains "1" (from Volume 1) and "FEVER", satisfying the numerical overlap check and passing with `is_supported=True`.
- **Defensible Classification:** **`FALSE SUPPORT`** (Hallucinated quantitative statistic accepted via bibliography citation).

---

### Case Group 3: `q_unans_01` — Out-of-Domain Distractor / World Knowledge Leakage (8 Records)

- **Question:** "What is the capital of Japan?"
- **Category / Difficulty:** `UNANSWERABLE` / `EASY`
- **Benchmark Answerability:** `answerability: false`, `expected_status: "INSUFFICIENT_EVIDENCE"`
- **Authoritative Document Fact:** Explicit negative control distractor. The paper on RAG has no relationship to geography, Japan, or Tokyo.
- **Affected Variants (8 / 8):** `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`.
- **Generated Answer (Identical across all 8 variants):**
  > "Tokyo"
- **Supporting Claim Cited:** `test_document_p011_c025_claim_1`
  > *"Knowledge-powered conversational agents."*
- **Supporting Chunk Cited:** `test_document_p011_c025` (Page 11, Reference [10] to SearchQA and Wizard of Wikipedia).
- **Entailment Analysis:**
  - Chunk `p011_c025` has zero lexical or semantic connection to Tokyo or Japan.
  - The generator completely ignored the prompt instruction ("Answer ONLY from the provided DOCUMENT EVIDENCE") and answered from parametric pre-training weights.
- **Validator Decision & Mechanism:**
  - Deterministic evaluation rejected the claim (0% concept overlap).
  - However, in the benchmark run, the live LLM validator was executed (`timed_model_chat` in `RequirementSupportValidator.validate()`).
  - Independent execution of the LLM validator prompt revealed that the LLM returned:
    > `is_supported: True`  
    > `rationale: "The GROUNDED ANSWER 'Tokyo' directly addresses the INFORMATION REQUIREMENT 'The capital of Japan', providing a clear and concise answer."`
  - The validator prompt failed to enforce document grounding, allowing the LLM judge to validate the answer using its own world knowledge rather than checking document entailment!
- **Defensible Classification:** **`FALSE SUPPORT`** (Pure parametric hallucination validated by judge LLM world knowledge leakage).

---

### Case Group 4: `q_multi_01` — Multilingual Evaluation Hallucination (7 Records)

- **Question:** "Does the RAG paper evaluate on multilingual tasks?"
- **Category / Difficulty:** `MULTILINGUAL` / `MEDIUM`
- **Benchmark Answerability:** `answerability: false`, `expected_status: "INSUFFICIENT_EVIDENCE"`
- **Authoritative Document Fact:** Lewis et al. (2020) evaluates exclusively on English datasets (Natural Questions, TriviaQA, WebQuestions, CuratedTrec, MS-MARCO, Jeopardy, FEVER). Multilingual evaluation is not performed. The question is unanswerable.
- **Affected Variants (7 / 8):** `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`.
- **Correctly Rejected Variant (1 / 8):** `NO_CLAIM_VERIFICATION` (rejected because `supporting_claim_ids` was empty, triggering automatic fallback to `INSUFFICIENT_EVIDENCE`).
- **Generated Answer (Identical across all 7 supported variants):**
  > "The RAG paper evaluates on multilingual tasks."
- **Supporting Claim Cited:** `test_document_p004_c010_claim_6`
  > *"RAG models can go beyond simple extractive QA and answer questions with free-form, abstractive text generation."*
- **Supporting Chunk Cited:** `test_document_p004_c010` (Page 4, Section 3.2 on Abstractive Question Answering).
- **Entailment Analysis:**
  - Chunk `p004_c010` discusses MS-MARCO and Jeopardy abstractive QA in English. It does not mention multilingual tasks.
  - The generated answer directly contradicts the paper's actual methodology by asserting an untrue affirmative claim.
- **Validator Decision & Mechanism:**
  - Target requirement: "Did the RAG paper evaluate on multilingual tasks?"
  - Because `answer` ("The RAG paper evaluates on multilingual tasks.") repeats the question tokens verbatim, the concept overlap match ratio evaluated to **1.00 (100% match)**!
  - Grounding ratio passed because chunk `p004_c010` contains "rag", "paper", "models", and "tasks".
- **Defensible Classification:** **`FALSE SUPPORT`** (False affirmative assertion accepted via question-echo concept matching).

---

## 4. Audit of the 77 Supported Answerable Cases

An inspection was conducted on all 77 answerable records marked `SUPPORTED` (spanning 11 unique questions):

### 4.1 High-Quality Grounded Recoveries (6 Questions / 43 Runs)

The following 6 questions represent legitimate, grounded answer recoveries where the evidence genuinely entails the answer:
1. **`q_quant_02` (QUANTITATIVE, 8/8 variants):** "How many latent documents are models trained with?" $\rightarrow$ Answer: "5 or 10", citing `test_document_p008_c019`. Correctly supported and grounded.
2. **`q_meth_01` (METHOD, 6/8 variants):** "How are the CT and WQ models initialized?" $\rightarrow$ Answer: "initialized with the NQ RAG model", citing `test_document_p004_c010`. Grounded in DPR initialization section.
3. **`q_comp_02` (COMPARATIVE, 8/8 variants):** "Does RAG hallucinate more or less compared to other models?" $\rightarrow$ Answer: "hallucinates less", citing `test_document_p006_c014`. Directly grounded.
4. **`q_contra_01` (CONTRADICTION, 8/8 variants):** "Do models hallucinate more or less?" $\rightarrow$ Answer: "models hallucinate less", citing `test_document_p006_c014`. Correctly grounded.
5. **`q_contra_02` (CONTRADICTION, 8/8 variants):** "Does the system retrieve 5, 10, or 1000 documents?" $\rightarrow$ Answer: cites `test_document_p008_c019` explaining 5, 10, and 1000 document regimes.
6. **`q_mh_05` (MULTI_HOP, 7/8 variants):** "Was the 2016 Wikipedia dump used in combination with 5 or 10 retrieved latent documents?" $\rightarrow$ Answer combines Wikipedia dump and document counts from `p018_c040` and `p008_c019`.

### 4.2 False Acceptances Among Answerable Questions (3 Questions / 22 Runs)

The loosened validator also accepted factually incorrect or misattributed answers to answerable questions:
1. **`q_df_01` (DIRECT_FACT, 8/8 variants):**
   - *Question:* "What is the full title of the paper?"
   - *Expected:* "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
   - *Generated Answer:* *"Avoiding catastrophic forgetting in mitigating model biases in sentence-pair classification with elastic weight consolidation"*
   - *Cited Chunk:* `test_document_p015_c034` (Reference [57]).
   - *Audit Finding:* The model retrieved a random reference paper title from the bibliography and claimed it was the paper's title. The validator accepted it because the answer matched the requirement words ("title of the paper")!
2. **`q_meth_03` (METHOD, 8/8 variants):**
   - *Question:* "How does the system avoid running additional forward passes?"
   - *Expected:* Minimizing negative marginal log-likelihood via stochastic gradient descent.
   - *Generated Answer:* "The system avoids running additional forward passes by leveraging bi-directional attention in the encoder-decoder model, similar to BART and T5."
   - *Cited Chunk:* `test_document_p009_c020`.
   - *Audit Finding:* Factually incorrect mechanism accepted due to concept overlap.
3. **`q_meth_04` (METHOD, 8/8 variants):**
   - *Question:* "How do concurrent works handle entity embeddings?"
   - *Generated Answer:* Explains null document embeddings from `p018_c040`, conflating entity embeddings with document retrieval biases.

### 4.3 Severe Over-Rejection in Answerable Categories (83 Runs)

The pipeline still suffers from severe false rejection on 9 answerable questions:
- **`DIRECT_FACT` (40/48 runs rejected):** Questions `q_df_02` (DPR architecture), `q_df_03` (datasets used), `q_df_04` (Wikipedia dump date), `q_df_05` (FAISS MIPS library), and `q_df_06` (1986 World Cup example) were rejected in 100% of variants despite valid chunks being retrieved in candidate sets.
- **`MULTI_HOP` (31/40 runs rejected):** Questions `q_mh_01`, `q_mh_02`, and `q_mh_03` were 100% rejected.
- **`QUANTITATIVE` (8/16 runs rejected):** Question `q_quant_01` (retrieval accuracy percentage) was 100% rejected.

---

## 5. Causal Analysis of Validator Failure Modes

Tracing the execution path from claim extraction through the support validator to the final answer status identifies **four distinct architectural defects**:

```
[Retrieved Evidence Chunks]
             │
             ▼
   [Extracted Claims] ───┐
             │            │
             ▼            │
     [Answer Generator]   │
   (Repeats Q keywords)   │
             │            │
             ▼            ▼
 ┌─────────────────────────────────────────────────────────┐
 │       RequirementSupportValidator Pipeline              │
 │                                                         │
 │  Defect 1: combined_claim_text includes 'answer'        │
 │            (app/verification/requirement_support.py:214)│
 │                                                         │
 │  Defect 2: 15% Grounding Ratio too permissive           │
 │            (app/verification/requirement_support.py:194)│
 │                                                         │
 │  Defect 3: LLM Judge World-Knowledge Leakage            │
 │            (app/verification/requirement_support.py:97) │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │          AERISController Requirement Aggregation        │
 │                                                         │
 │  Defect 4: Disjunctive 'any()' Aggregation              │
 │            (app/controller/controller.py:589-590)       │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
         [Final Status: SUPPORTED (False Support!)]
```

### Defect 1: Tautological Self-Matching via Concatenation of Generated Answer
- **Source File & Line:** [`app/verification/requirement_support.py:214-215`](file:///e:/aeris-rag/app/verification/requirement_support.py#L214-L215)
- **Code:**
  ```python
  combined_claim_text = " ".join(claims) + " " + answer + " " + evidence_str
  claim_tokens = get_semantic_tokens(combined_claim_text)
  ```
- **Causal Mechanism:** The validator evaluates whether claims support the requirement by matching tokens in `combined_target_tokens` against `claim_tokens`. Because `answer` is concatenated into `combined_claim_text`, whenever the generator echoes or parrots the question in the answer (e.g. "The system fuses dense and sparse retrieval by..."), all target question tokens appear in `claim_tokens` by definition! This creates an immediate 80% to 100% concept overlap ratio regardless of whether the extracted claims or evidence support the statement.

### Defect 2: Under-Calibrated Grounding Check (15% Threshold)
- **Source File & Line:** [`app/verification/requirement_support.py:193-194`](file:///e:/aeris-rag/app/verification/requirement_support.py#L193-L194)
- **Code:**
  ```python
  grounding_ratio = len(claim_grounded_tokens) / len(claim_only_tokens)
  if grounding_ratio < 0.15:
      return RequirementSupportResult(is_supported=False, ...)
  ```
- **Causal Mechanism:** A grounding ratio threshold of 0.15 is trivially satisfied. Any long reference, appendix, or bibliography chunk that contains general terminology (`model`, `paper`, `rag`, `tasks`) provides enough token overlap to clear 15%, allowing completely ungrounded claims to pass.

### Defect 3: LLM Judge Evaluates Answer Plausibility Instead of Document Entailment
- **Source File & Line:** [`app/verification/requirement_support.py:96-100`](file:///e:/aeris-rag/app/verification/requirement_support.py#L96-L100)
- **Code:**
  ```text
  EVALUATION RULES:
  1. Semantic Fulfillment: The requirement is satisfied if the claims or answer provide relevant, factual information that directly answers or addresses the requirement.
  ```
- **Causal Mechanism:** Prompting the LLM to decide whether "the claims OR answer provide relevant factual information" instructs the judge LLM to treat the answer as standalone truth. When evaluating `q_unans_01` ("What is the capital of Japan?"), the judge LLM sees that "Tokyo" answers the question factually according to its parametric training weights, completely ignoring the fact that the cited document evidence mentions only SearchQA and conversational agents.

### Defect 4: Disjunctive Aggregation Across Multiple Information Requirements
- **Source File & Line:** [`app/controller/controller.py:589-590`](file:///e:/aeris-rag/app/controller/controller.py#L589-L590)
- **Code:**
  ```python
  any_supported = any(res.is_supported for _, res in req_val_results)
  if not any_supported:
      answer_status = "INSUFFICIENT_EVIDENCE"
  ```
- **Causal Mechanism:** When planning produces multiple information requirements ($R_1, R_2, R_3$), the controller uses disjunctive OR-logic (`any()`). If *even one* requirement registers spurious semantic overlap, the entire answer is preserved as `SUPPORTED`, overriding the fact that other critical requirements are completely unsatisfied.

---

## 6. Honest Comparative Assessment: Step 22C vs. Step 22D Benchmark

> [!WARNING]
> Historical benchmark `exp_final224_repaired_20261011_222000` (Step 22C) was audited and certified as **SCIENTIFICALLY INVALID — REJECTED**. It is referenced here exclusively as diagnostic context to trace defect evolution.

| Evaluation Metric | Step 22C Defective Benchmark (`exp_final224_repaired`) | Step 22D Fresh Benchmark (`exp_final224_remediation`) | Scientific Meaning & Audit Conclusion |
|:---|:---:|:---:|:---|
| **Answerable Supported Runs (TP)** | 17 / 160 (10.63%) | **77 / 160 (48.13%)** | **Substantial Recovery (+352%).** Step 22D successfully fixed the empty-cache bug that dropped 82 valid answers. |
| **Quantitative Category Support** | 0 / 16 (0.00%) | **8 / 16 (50.00%)** | Fixed false rejection on numerical metrics (`q_quant_02` fully recovered). |
| **Contradiction Category Support** | 0 / 16 (0.00%) | **16 / 16 (100.00%)** | Fully recovered grounded contradiction answers. |
| **False Support on Unanswerable (FP)** | **0 / 64 (0.00%)** | **31 / 64 (48.44%)** | **Severe Scientific Regression.** Step 22C had 0% false support only because it rejected almost everything. Step 22D swung the pendulum too far, accepting 48.44% ungrounded answers. |
| **Unanswerable Rejection Rate (TN)** | 64 / 64 (100.00%) | **33 / 64 (51.56%)** | Degraded by nearly half. |
| **Overall Accuracy** | 36.16% (81 / 224) | **49.11% (110 / 224)** | Modest net gain, but invalid due to safety failure. |
| **Retrieval Memory Delivery** | 0 hits (cache hit dropped evidence) | **10,336 valid hits** | Engineering fix fully confirmed. |
| **Adaptive Retrieval Isolation** | FAILED (55 expansions under `NO_AR`) | **PASS (0 expansions under `NO_AR`)** | Component isolation fully confirmed. |
| **Latency Instrumentation** | Contaminated (max 67,295.9s) | **Clean (max 297.1s, monotonic)** | Timing guards fully confirmed. |

---

## 7. Recommended Next Investigation (Read-Only Directives)

To achieve scientific validity without reintroducing catastrophic over-rejection, the subsequent engineering iteration must investigate:

1. **Strict Decoupling of Claim Evidence from Generated Answer:**
   - Modify the deterministic validator to compute concept overlap exclusively between target requirements and `claims + evidence_str`, strictly excluding `answer` from the target match pool.
2. **Strict Entailment Prompting for LLM Judge:**
   - Revise the judge prompt in `app/verification/requirement_support.py` to: *"Evaluate whether the CITED EVIDENCE strictly entails the answer. If the answer introduces facts not present in the cited evidence, mark is_supported as FALSE even if the answer is factually true in the real world."*
3. **Calibrating Grounding Ratio Threshold:**
   - Increase the minimum grounding ratio from 0.15 to a more discriminative threshold ($\ge 0.40$), and require that key noun phrases from the answer appear in the supporting chunks.
4. **Conjunctively Constrained Requirement Aggregation:**
   - Replace disjunctive `any()` in `app/controller/controller.py` with requirement-type-aware aggregation (e.g. require *all* priority-1 requirements to be supported for `SUPPORTED` status, or downgrade to `PARTIALLY_SUPPORTED`).
5. **Separate Tuning Set:**
   - Establish a separate development/calibration set rather than tuning thresholds against the 28 benchmark questions.

---

## 8. Final Acceptance Gate Decision & Hard Stop

### Formal Acceptance Gate Determination

| Gate # | Gate Description | Threshold | Recomputed Value | Gate Result |
|:---:|:---|:---:|:---:|:---:|
| **Gate 1** | Structural & Record Integrity | 100% (224 / 224) | 224 / 224 (0 errors) | **PASS** |
| **Gate 2** | Experiment & Cache Isolation | Isolated Namespaces | Verified Isolated | **PASS** |
| **Gate 3** | **Answerability & False Support Safety** | **$\le \mathbf{5.00\%}$** | **$\mathbf{48.44\%}$ (31 / 64)** | **FAIL** |
| **Gate 4** | Provenance Integrity | 0 Defects | 0 Defects | **PASS** |
| **Gate 5** | Decoupled Evaluation Denominators | $N=160$ Answerable | Strictly Decoupled | **PASS** |
| **Gate 6** | Ablation Component Isolation | 100% Bypass | 100% Bypass Verified | **PASS** |
| **Gate 7** | Latency Instrumentation | Monotonic, No Sleep | Clean, Max 297.1s | **PASS** |

Because **Gate 3 Fails**, the benchmark experiment cannot be accepted as scientifically valid.

---

# **`SCIENTIFICALLY BLOCKED — REMEDIATION REQUIRED`**

**Hard Stop Notice:** Do not advance to Step 23. Do not run further benchmarks or modify production code until the answer-support validator entailment defect is formally remediated.
