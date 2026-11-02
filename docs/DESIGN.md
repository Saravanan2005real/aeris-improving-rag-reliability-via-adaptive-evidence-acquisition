# AERIS Design Specification & Theoretical Foundations

This document provides the theoretical background, design rationale, algorithmic pseudocode, and mathematical formulations governing the **AERIS (Adaptive Evidence Retrieval and Information System)** architecture.

---

## 1. Problem Statement & Motivation

### 1.1 Limitations of Standard RAG Systems
Conventional Retrieval-Augmented Generation (RAG) architectures follow a static, single-pass paradigm:
$$\text{Query} \xrightarrow{\text{Embed}} \text{Top-}k \text{ Retrieval} \xrightarrow{\text{Concatenate}} \text{LLM Generator} \to \text{Answer}$$

In complex scientific, medical, and legal domains, this paradigm suffers from four systemic failure modes:
1. **Fixed-Depth Retrieval Blindness:** Choosing a fixed $k$ (e.g., $k=5$) causes under-retrieval when questions require synthesizing disparate sections of a paper, or over-retrieval (distractor contamination) when simple direct facts are requested.
2. **Ungrounded Hallucinations & Surface-Level Agreement:** LLMs frequently produce factually plausible answers by relying on pre-trained parametric world knowledge rather than the cited document context, fabricating page numbers and citations.
3. **Silent Contradiction Blindness:** When different sections or cited works in a paper express conflicting findings (e.g., benchmark score discrepancies across baselines), conventional RAG silently averages or arbitrarily picks one claim without notifying the user.
4. **Uncalibrated Model Confidence:** LLMs consistently express 100% subjective confidence even when answering completely unanswerable questions or hallucinating non-existent training hardware.

### 1.2 AERIS Design Objectives
AERIS was engineered around three non-negotiable scientific design principles:
- **Zero False Support ($0.0000$ False Support Rate):** A strict requirement that unanswerable or ungrounded questions must trigger a conservative refusal (`INSUFFICIENT_EVIDENCE`), completely suppressing hallucinated completions.
- **Adaptive Evidence Acquisition:** Dynamically measuring whether retrieved evidence is sufficient to answer the prompt across 4 objective dimensions before generating an answer.
- **Bipartite Verification Graphs:** Decoupling factual verification from generator prose by grounding atomic claims directly to document chunk provenance.

---

## 2. Core Architectural Subsystems

### 2.1 Information Requirement Planning
Complex user queries are often composite (e.g., *"What is the architecture of the retriever and what library is used for MIPS search?"*).
Rather than passing this query directly to a single vector index lookup, the **Requirement Planner** decomposes the query $Q$ into atomic requirements:
$$Q \mapsto \mathcal{R} = \{r_1, r_2, \dots, r_m\}$$
Each requirement $r_i$ defines:
- A semantic target description $d_i$.
- An expected entity type $T_i \in \{\text{entity}, \text{quantitative}, \text{procedural}, \text{comparative}\}$.
- A priority score $p_i \in \{1, 2\}$ ($1 = \text{essential}, 2 = \text{supplementary}$).
- Sub-queries $\{q_{i,1}, q_{i,2}\}$ designed for distinct retrieval channels.

### 2.2 4-Dimensional Evidence Coverage Estimation
For each requirement $r \in \mathcal{R}$ and candidate evidence pool $\mathcal{E}$, AERIS computes a composite coverage score:
$$\text{Coverage}(r, \mathcal{E}) = \sum_{j=1}^4 w_j \cdot S_j(r, \mathcal{E}), \quad \sum_{j=1}^4 w_j = 1.0$$
Where the four sub-scores are defined as:
1. **Directness ($S_{\text{dir}}$):** Proportion of target entity tokens appearing in explicit assertions rather than peripheral mentions.
2. **Relevance ($S_{\text{rel}}$):** Cosine similarity between requirement embeddings and reranked chunk embeddings:
   $$S_{\text{rel}} = \max_{e \in \mathcal{E}} \frac{\mathbf{e}_r \cdot \mathbf{e}_e}{\|\mathbf{e}_r\| \|\mathbf{e}_e\|}$$
3. **Completeness ($S_{\text{comp}}$):** Ratio of matched requirement facets to total declared facets.
4. **Type Match ($S_{\text{type}}$):** Binary or fuzzy indicator that evidence contains the required data format (e.g., integers/percentages for quantitative queries; named authors for attribution queries).

**Adaptation Threshold Policy:**
$$\text{Action}(r, \mathcal{E}) = \begin{cases}
\text{Proceed to Claim Extraction}, & \text{if } \text{Coverage}(r, \mathcal{E}) \ge \tau_{\text{cov}} \\
\text{Expand Depth } (k \gets 10 \to 25 \to 50), & \text{if } \text{Coverage}(r, \mathcal{E}) < \tau_{\text{cov}} \land \text{depth} < \text{depth}_{\max} \\
\text{Reformulate Query via LLM}, & \text{if } \text{Coverage}(r, \mathcal{E}) < \tau_{\text{cov}} \land \text{depth} = \text{depth}_{\max}
\end{cases}$$

### 2.3 Atomic Claim Extraction & Deduplication
To prevent hallucinations from leaking through unverified paragraph context, text chunks are distilled into atomic factual claims:
- **Atomicity Constraint:** Each claim must express a single factual proposition (one subject, predicate, and object/measurement).
- **Dense Embedding Normalization:** Every candidate claim $c$ is embedded using `all-MiniLM-L6-v2`. Pairs $(c_i, c_j)$ exceeding cosine threshold $\tau_{\text{dup}} = 0.88$ are deduplicated into a canonical claim node:
  $$c_{\text{canonical}} = \text{select\_most\_informative}(c_i, c_j)$$
  Attribution edges from all source chunks are merged onto $c_{\text{canonical}}$.

### 2.4 Semantic Claim Typing
Claims are classified into a 4-class taxonomy:
$$\text{Type}(c) \in \{\text{FACT}, \text{METHOD}, \text{QUANTITATIVE}, \text{COMPARATIVE}\}$$
- `FACT`: Specific factual assertions (authors, affiliations, dataset names, library tools).
- `METHOD`: Algorithmic steps, architecture configurations, preprocessing procedures.
- `QUANTITATIVE`: Numeric metrics, percentages, sample counts, parameters, performance tables.
- `COMPARATIVE`: Relative rankings between models (e.g., *"Model A outperformed Model B"*).

---

## 3. Verification & Optimization Algorithms

### 3.1 Bipartite Claim-Evidence Graph
A directed bipartite graph $\mathcal{G} = (V_C, V_E, E)$ represents the evidentiary foundation:
- $V_C$: Verified, typed, and normalized claim nodes.
- $V_E$: Concrete document chunk nodes containing `chunk_id`, `document_id`, `pages`, and verbatim text.
- $E \subseteq V_C \times V_E$: Weighted directed edges where weight $w(c, e)$ represents NLI entailment confidence.

### 3.2 Confidence Calibration
Raw model probabilities from LLM verifiers are notoriously uncalibrated. AERIS applies calibration mappings:
$$\hat{p} = \sigma(a \cdot z + b)$$
Where $z$ is the verifier logit, and parameters $(a, b)$ are optimized via isotonic regression to minimize **Expected Calibration Error (ECE)**:
$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
Calibrated probabilities ensure that a confidence of 0.90 corresponds to an empirical accuracy of 90%.

### 3.3 Budget-Constrained Selective Verification (Knapsack)
Exhaustively verifying all extracted claims with an NLI cross-encoder or LLM is computationally prohibitive ($O(|C|)$ LLM calls).
AERIS formulates selective verification as a 0-1 Knapsack optimization problem:
$$\max_{\mathbf{x} \in \{0, 1\}^n} \sum_{i=1}^n u(c_i) \cdot x_i \quad \text{s.t.} \quad \sum_{i=1}^n \text{cost}(c_i) \cdot x_i \le B$$
Where:
- Utility $u(c_i) = (1 - \text{conf}_{\text{prior}}(c_i)) \cdot \text{priority}(c_i)$ prioritizes claims with high uncertainty and high requirement importance.
- $\text{cost}(c_i)$ reflects token length and inference overhead.
- $B$ is the user-configured verification budget (default $B = 3$).

### 3.4 Contextual Contradiction Detection
When two evidence chunks $e_a, e_b$ support different claims on the same topic, AERIS evaluates pairwise contradiction:
$$\text{Contra}(e_a, e_b) = \text{CrossEncoderNLI}(e_a, e_b)$$
- If the cross-encoder classifies the pair as `CONTRADICTION`, the conflicting claims are tagged.
- **Generator Presentation:** The generator is provided with explicit conflict rationale and instructed to either present both viewpoints or set status to `CONFLICTED`.

---

## 4. Grounded Generation & Validation Guardrails

### 4.1 Grounded Answer Generator
The generator is provided with:
1. Retrieved document chunks with explicit ID tags (`Chunk (chunk_id) [Pages: X]`).
2. Verified factual claims (`Claim (claim_id): text [Confidence: Y]`).
3. Active contradiction reports (if genuine conflicts exist).
4. The exact target question.

The LLM is constrained to output strict JSON conforming to `GroundedAnswer`:
```json
{
  "is_answerable_from_evidence": true,
  "answer": "Grounded natural language answer",
  "status": "SUPPORTED",
  "confidence": 0.90,
  "supporting_claim_ids": ["claim_id_1"],
  "supporting_chunk_ids": ["chunk_id_1"]
}
```

### 4.2 Requirement-Support Validation Guardrails (Firewall)
Before returning the result to the user or API client, the response passes through a **Requirement Support Validator**:
1. **Entity Grounding Verification:** Verifies that specific requirement keywords (e.g. author names, numerical scores, architecture names) appear in the cited chunks.
2. **Preventing Question Parroting:** If the answer merely parrots the question text without evidence support, the status is overridden to `NOT_ESTABLISHED`.
3. **Conservative Refusal Downgrade:** If required facts are absent:
   - Status is downgraded to `INSUFFICIENT_EVIDENCE`.
   - Confidence is reset to `0.0`.
   - A structured refusal rationale is attached.
   - Provenance citations are emptied to prevent misleading citations.

---

## 5. Experimental Verification & Acceptance Standards

AERIS undergoes continuous validation against three acceptance criteria:
1. **Zero False Support ($0.0000$):** Under no circumstance may the system answer an unanswerable query with status `SUPPORTED`.
2. **Provenance Validity:** Every cited chunk must exist in the target index and correlate with the cited claim.
3. **Execution Reproducibility:** Every run outputs full telemetry (stage latencies, token counts, claim counts) stored in structured JSON logs.
