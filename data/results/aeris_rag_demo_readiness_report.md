# AERIS-RAG — Demo Readiness and Existing Application Inspection Report

**Target System:** AERIS-RAG (Adaptive Evidence Retrieval and Information System)  
**Inspection Type:** Strictly Read-Only Architecture & Interface Inspection  
**Output Path:** [`data/results/aeris_rag_demo_readiness_report.md`](file:///e:/aeris-rag/data/results/aeris_rag_demo_readiness_report.md)  
**Reference Experiment:** `exp_final224_remediation_20261022_183626`  
**Current Date/Time:** 2026-10-23  

---

## 1. Executive Summary

A comprehensive read-only inspection was performed across the `E:\aeris-rag` codebase to assess its readiness for an interactive research demonstration.

### Key Inspection Findings:
1. **Core Pipeline Maturity:** The core Python backend pipeline—comprising query requirement planning, adaptive hybrid retrieval (dense + BM25), neural reranking, claim extraction, claim typing, claim-evidence graph construction, selective verification, grounded answer generation, and requirement-support validation—is **fully implemented, functional, and verified** through 101 passing unit/integration tests and a completed 224-run benchmark evaluation.
2. **Current Interface Status:** The repository currently operates strictly as a **library and CLI-driven research framework**. **No web interface, HTTP API server, or frontend application currently exists** in the repository:
   - `main.py` is an unpopulated stub (`pass`).
   - No web frameworks (FastAPI, Flask, Streamlit, Gradio, etc.) are currently installed or implemented.
   - The primary execution entry points are CLI scripts (`scripts/run_ablation.py`, `scripts/test_controller_integration.py`).
3. **Demo Feasibility:** All required demonstration behaviors (grounded QA, conservative insufficient-evidence rejection, partial-support downgrading, provenance citations, and stage telemetry) are **natively exposed by `ControllerResult`**.
4. **Implementation Path:** A live demo can be realized with **zero modifications to the core scientific pipeline** by introducing a lightweight, non-invasive API wrapper and a focused, modern web UI that visualizes the existing `ControllerResult` schema.

---

## 2. Existing Application Architecture & Entry Points

```
+---------------------------------------------------------------------------------------------------+
|                                  AERIS-RAG APPLICATION ARCHITECTURE                               |
+---------------------------------------------------------------------------------------------------+

   [ Document Ingestion ]                 [ Query Execution Pipeline ]
   data/raw/*.pdf                         User Query + document_id
         |                                           |
         v                                           v
   [ app/ingestion/pdf_loader.py ]        [ app/planning/requirement_planner.py ]
   (PyMuPDF text & page extraction)       (Decomposes into InformationRequirements)
         |                                           |
         v                                           v
   [ app/chunking/semantic_chunker.py ]   [ app/adaptive_retrieval/controller.py ]
   (Chunk ID: doc_pXXX_cYYY)              (Hybrid Dense Nomic + BM25 + CrossEncoder)
         |                                           |
         v                                           v
   [ app/indexing/index_builder.py ]      [ app/coverage/evidence_coverage.py ]
   - EmbeddingService (nomic-embed-text)  (4-D Coverage Scoring: Directness, Type, etc.)
   - VectorStore (embeddings.npy)                    | (Expands candidate_k if coverage low)
   - Metadata (metadata.json)                        v
         |                                [ app/claim_extraction/extractor.py & typer.py ]
         +-------------------------------> (Extracts atomic claims & assigns ClaimType)
                                                     |
                                                     v
                                          [ app/claim_graph/graph.py ]
                                          (Bipartite Claim-Evidence Graph)
                                                     |
                                                     v
                                          [ app/verification/claim_verifier.py & graph_verifier.py ]
                                          (NLI entailment checks + Contradiction Analysis)
                                                     |
                                                     v
                                          [ app/answer_generation/answer_generator.py ]
                                          (Grounded generation strictly adhering to claims)
                                                     |
                                                     v
                                          [ app/verification/requirement_support.py ]
                                          (4-state evaluation: SUPPORTED / PARTIAL / INSUFFICIENT)
                                                     |
                                                     v
                                          [ ControllerResult ]
                                          - final_answer
                                          - answer_status (SUPPORTED / PARTIALLY_SUPPORTED / etc.)
                                          - supporting_chunk_ids & provenance
                                          - stages (per-stage latencies & statuses)
                                          - metadata (downgrade_details, rationales)
```

### Existing Code Entry Points

| Role | File Path | Function / Class | Description |
|:---|:---|:---|:---|
| **Pipeline Controller** | [`app/controller/controller.py`](file:///e:/aeris-rag/app/controller/controller.py) | `AERISController.run(ControllerRequest) -> ControllerResult` | Central orchestrator executing the 10-stage pipeline. |
| **Controller Builder** | [`scripts/run_ablation.py:L74-138`](file:///e:/aeris-rag/scripts/run_ablation.py#L74-L138) | `build_real_controller()` | Wires all real production components with Ollama and vector store. |
| **Interactive CLI Runner** | [`scripts/test_controller_integration.py`](file:///e:/aeris-rag/scripts/test_controller_integration.py) | `main()` | CLI execution: `python scripts/test_controller_integration.py <document_id> "<question>"`. |
| **Document Ingestion** | [`app/indexing/index_builder.py`](file:///e:/aeris-rag/app/indexing/index_builder.py) | `build_index(pdf_path: str)` | Extracts text, generates embeddings, and saves to `data/indexes/<doc_id>/`. |
| **PDF Parser** | [`app/ingestion/pdf_loader.py`](file:///e:/aeris-rag/app/ingestion/pdf_loader.py) | `load_pdf(file_path: str) -> Document` | PyMuPDF text and page extraction with language detection. |
| **Hybrid Retrieval** | [`app/retrieval/hybrid_retriever.py`](file:///e:/aeris-rag/app/retrieval/hybrid_retriever.py) | `HybridRetriever.retrieve(...)` | RRF fusion of dense cosine similarity and BM25 lexical search. |
| **Answer Support Validator** | [`app/verification/requirement_support.py`](file:///e:/aeris-rag/app/verification/requirement_support.py) | `RequirementSupportValidator.validate(...)` | Deterministic concept/facet validation with judge override. |

---

## 3. Existing Capabilities: Implemented vs. Internal vs. Missing

The table below catalogs every capability required for a live research demonstration, distinguishing what is natively exposed, what exists internally, and what is currently missing.

| Capability | Current Status | Exposure in Existing Artifacts | Implementation Details & Location |
|:---|:---:|:---|:---|
| **Grounded Answer Generation** | **Natively Exposed** | `ControllerResult.final_answer` | Generates answer text strictly grounded in verified claims ([`answer_generator.py`](file:///e:/aeris-rag/app/answer_generation/answer_generator.py)). |
| **Answer Status Classification** | **Natively Exposed** | `ControllerResult.answer_status` | Returns `"SUPPORTED"`, `"PARTIALLY_SUPPORTED"`, `"INSUFFICIENT_EVIDENCE"`, or `"CONFLICTED"`. |
| **Answer Confidence** | **Natively Exposed** | `ControllerResult.answer_confidence` | Normalized confidence score ($0.0 \le c \le 1.0$) ([`calibrator.py`](file:///e:/aeris-rag/app/calibration/calibrator.py)). |
| **Citation Identifiers** | **Natively Exposed** | `ControllerResult.supporting_chunk_ids` | List of chunk IDs (e.g. `['test_document_p003_c006']`) cited by the answer. |
| **Retrieved Passage Pool** | **Natively Exposed** | `ControllerResult.retrieved_chunk_ids` | Ordered list of all candidate chunks returned by adaptive retrieval. |
| **Provenance Passages & Pages** | **Natively Exposed** | `ControllerResult.provenance` | List of dicts containing `chunk_id`, `pages` (e.g. `[3]`), and passage text snippets. |
| **Provenance Defect Detection** | **Natively Exposed** | `ControllerResult.provenance_defects` | Empty list (`[]`) if all citations are valid; lists unretrieved chunk IDs if invalid. |
| **Stage-by-Stage Telemetry** | **Natively Exposed** | `ControllerResult.stages` | List of `ControllerStageResult` objects with stage name, status, `output_count`, and `latency_seconds`. |
| **Partial-Support Downgrades** | **Natively Exposed** | `ControllerResult.metadata['downgrade_details']` | Dict listing `downgrade_type="REQUIREMENT_PARTIALLY_UNSUPPORTED"`, supported count, total requirements, and unsupported IDs. |
| **Validator Rationales** | **Natively Exposed** | `ControllerResult.metadata['downgrade_details'][...]['validator_rationales']` | Explicit reasons explaining why evidence failed to entail requirements (including Judge Override text). |
| **Insufficient Evidence Reason** | **Natively Exposed** | `ControllerResult.insufficiency_information` | High-level summary of evidence insufficiency or contradiction. |
| **Full Claim Texts & Graph Edges** | **Internal Only** | Retained in internal graph object | `ControllerResult` exposes `claim_count` and `supporting_claim_ids`, but the full claim texts are stored on the in-memory graph builder. |
| **Raw Candidate Texts (Non-Cited)** | **Internal Only** | Resolved via index metadata | `ControllerResult` returns `retrieved_chunk_ids`; resolving full text requires reading `data/indexes/<doc_id>/metadata.json`. |
| **Interactive Web UI** | **Missing** | None | No web interface exists in the codebase. |
| **HTTP API Endpoints** | **Missing** | None | No REST or WebSocket server is currently implemented. |
| **Multi-Document Routing** | **Missing** | None | Controller currently accepts a single target `document_id`. |

---

## 4. Demonstration Scenarios Feasibility

Using existing functional code and verified index artifacts (`data/indexes/test_document`), the system is ready to demonstrate the following core research scenarios:

### Scenario 1: Evidence-Grounded Question Answering
- **Test Query:** *"What is the primary motivation for introducing RAG models?"* (`q_df_01`)
- **System Behavior:** Retrieval locates gold passage `test_document_p001_c001`; claim extraction extracts motivation claims; validator confirms semantic support.
- **Expected Demo Output:**
  - `answer_status: "SUPPORTED"`
  - Clear answer explaining parametric vs. non-parametric memory.
  - Active citation: `[p.1, test_document_p001_c001]`.
  - Provenance panel displaying the exact text snippet from page 1.

### Scenario 2: Conservative Rejection on Insufficient Evidence
- **Test Query:** *"What hardware was used to train the RAG models?"* (`q_unans_02`)
- **System Behavior:** Retrieval returns model architecture chunks (DPR/latent variables); hardware facet check verifies that GPU/TPU/accelerator concepts are absent; judge override fires.
- **Expected Demo Output:**
  - `answer_status: "INSUFFICIENT_EVIDENCE"`
  - Final answer: Conservative refusal or `None`.
  - Inspector reveals: `[Judge override: Target requirement specifies hardware or compute infrastructure, but no hardware concepts appear in cited evidence]`.

### Scenario 3: Partial-Support Detection on Multi-Part Queries
- **Test Query:** *"How does the inference latency of dense retrieval compare to BM25 in terms of milliseconds and throughput?"* (`q_comp_01`)
- **System Behavior:** Evidence covers throughput/latency advantages conceptually but lacks exact millisecond benchmarks for both systems; multi-requirement aggregation establishes 1 of 2 requirements.
- **Expected Demo Output:**
  - `answer_status: "PARTIALLY_SUPPORTED"` (Amber badge).
  - Clear downgrade notification: `Partial requirement support: 1/2 requirements established`.
  - Specific identification of which sub-requirement was ungrounded.

### Scenario 4: Retrieval and Verification Transparency
- **User Action:** User expands the "Pipeline Telemetry" drawer.
- **Expected Demo Output:**
  - Stage execution stepper: Planning (6.1s) $\rightarrow$ Retrieval (3.2s) $\rightarrow$ Coverage (0.001s) $\rightarrow$ Claim Graph (78.6s) $\rightarrow$ Verification (4.1s) $\rightarrow$ Answer Generation (6.3s).
  - Total latency breakdown.
  - Candidate depth expansions count: 0 (or expansions if triggered).

---

## 5. Recommended Architecture for a Professional Local Demo

To keep implementation strictly minimal, clean, and professional without destabilizing the research repository:

```
+-----------------------------------------------------------------------------------------+
|                                RECOMMENDED DEMO ARCHITECTURE                            |
+-----------------------------------------------------------------------------------------+

  [ Browser Client ]
  Modern Single-Page Dashboard (Vanilla HTML5 / Modern CSS / Vanilla JS)
  - Dark-mode glassmorphic interface
  - Interactive Question Bar + Preloaded Sample Queries
  - Real-time Stage Pipeline Stepper
  - Grounded Answer Card with Status Badges (SUPPORTED / PARTIALLY_SUPPORTED / INSUFFICIENT)
  - Verification & Downgrade Inspector (Validator rationales)
  - Interactive Evidence & Provenance Explorer (Clickable citations, page numbers, text)
  - Telemetry Drawer (per-stage latencies)
         |
         | HTTP POST /api/query
         v
  [ Lightweight API Server ] -> app/api/server.py (FastAPI / Uvicorn)
  - GET  /api/health      -> Server & Ollama connectivity status
  - GET  /api/documents   -> Lists available document IDs in data/indexes/
  - POST /api/query       -> Calls AERISController.run() in threadpool; returns ControllerResult
         |
         v
  [ Existing AERISController ] -> app/controller/controller.py
  (Reuses 100% of existing, verified codebase with ZERO modifications to core logic)
```

### Recommended UI Layout (Single-Screen Dashboard)

```
+-----------------------------------------------------------------------------------------+
|  AERIS-RAG: Adaptive Evidence Retrieval & Grounded Information System         [Status]  |
+-----------------------------------------------------------------------------------------+
|  Document: [test_document (RAG Paper) v]    Query: [ Enter question or select preset v ]|
|  [ Preset: Grounded Fact ]  [ Preset: Unanswerable Hardware ]  [ Preset: Partial Latency ] |
|  [ > Execute Query ]                                                                    |
+-----------------------------------------------------------------------------------------+
|  PIPELINE PROGRESS                                                                      |
|  (v) Planning  ->  (v) Retrieval  ->  (v) Coverage  ->  (v) Verification  -> (v) Answer |
+-----------------------------------------------------------------------------------------+
|  GROUNDED ANSWER                           |  VERIFICATION & PROVENANCE INSPECTOR       |
|                                            |                                            |
|  Status: [ SUPPORTED / INSUFFICIENT / ... ]|  [ Tab 1: Cited Passages ] [ Tab 2: Audit ]|
|  Confidence: [ 0.88                       ]|                                            |
|                                            |  * Passage 1 [Page 3, Chunk p003_c006]:    |
|  "Retriever-Augmented Generation combines  |    "DPR provides strong initial retrieval  |
|  pre-trained parametric memory with        |    scores by indexing document embeddings  |
|  non-parametric dense vector lookup..."    |    using dense representations..."         |
|                                            |                                            |
|  Citations: [p.1, c001] [p.3, c006]        |  * Validator Rationale:                    |
|                                            |    "Requirement factually entailed by      |
|                                            |     cited passages. 2/2 requirements met." |
+-----------------------------------------------------------------------------------------+
|  LATENCY & TELEMETRY                                                                    |
|  End-to-End: 98.4s | Planning: 6.1s | Retrieval: 3.2s | Verification: 4.1s | Gen: 6.3s  |
+-----------------------------------------------------------------------------------------+
```

---

## 6. Minimal Implementation Plan

The entire demo can be implemented with **two isolated additions**, completely decoupling the presentation layer from the research core:

### Phase 1: API Layer (`app/api/server.py`)
- Introduce a single FastAPI server script:
  - Initializes `AERISController` once at startup using [`build_real_controller()`](file:///e:/aeris-rag/scripts/run_ablation.py#L74-L138).
  - Route `POST /api/query`: Receives `{"document_id": str, "question": str}`, executes in a threadpool (avoiding event loop blocking), enriches `provenance` with chunk text from `VectorStore`, and returns JSON.
  - Route `GET /api/documents`: Inspects `data/indexes/` and returns available indexed documents.
  - Route `GET /api/sample_queries`: Returns preloaded scenario questions (grounded, unanswerable, partial-support) for rapid demonstration.

### Phase 2: Web Dashboard (`frontend/index.html` + `frontend/app.js` + `frontend/style.css`)
- Pure Vanilla HTML5/CSS3/JavaScript (no complex node build toolchain required):
  - Modern aesthetic: curated dark palette, glassmorphism, responsive typography.
  - Live query execution indicator with stage progress animation.
  - Color-coded status badges for `SUPPORTED` (emerald), `PARTIALLY_SUPPORTED` (amber), `INSUFFICIENT_EVIDENCE` (slate/blue).
  - Expandable citation inspector linking claim text to document chunk text.
  - Telemetry dashboard graphing stage latencies.

### Launch Commands (to be created):
```powershell
# Start Demo Backend Server
uvicorn app.api.server:app --host 127.0.0.1 --port 8000 --reload

# Serve Frontend Dashboard
python -m http.server 3000 --directory frontend
```

---

## 7. Safe Demo Testing Plan (Preserving Benchmark Integrity)

To ensure that launching and testing the demo cannot contaminate the closed benchmark results or historical artifacts:

1. **Read-Only Dataset Guard:**
   - The demo API will never write to or read from `data/benchmark/`.
   - The demo will only interact with the existing pre-indexed document in `data/indexes/test_document/`.
2. **Dedicated Demo Cache Namespace:**
   - Configure the demo controller with a dedicated, isolated cache file:
     `data/cache_interactive_demo.json`
   - Never use or modify benchmark cache namespaces (`cache_exp_final224_*`).
3. **No Results Directory Writes:**
   - The demo API serves queries ephemerally in-memory; it does not write result files to `data/results/`.
4. **Pre/Post Test Verification:**
   - Verify before and after running the demo that `data/benchmark/aeris_benchmark.json` SHA-256 remains strictly `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`.

---

## 8. Unresolved Technical Questions & Practical Considerations

1. **Interactive Demo Latency Management:**
   - *Observation:* On local hardware (NVIDIA RTX 4050 Laptop GPU with `llama3.2:latest`), an end-to-end query takes ~60–90 seconds due to multiple sequential LLM calls (planning, claim extraction, claim typing, verification, answer generation, and support validation).
   - *Recommendation:* The UI must feature an active stage progress stepper and pre-warmed cache presets so an audience is not left staring at a static blank spinner during a live presentation.
2. **Taxonomy Aliasing (`COMPARE` vs `COMPARATIVE`):**
   - *Observation:* As documented in the independent audit, `ClaimTyper` fails if the LLM emits `"COMPARE"` instead of `"COMPARATIVE"`.
   - *Recommendation:* Before demonstrating free-form user queries, add a simple 1-line alias map in `typer.py` (`{"COMPARE": ClaimType.COMPARATIVE}`) so spontaneous user comparative queries do not trigger an unhandled exception.
3. **Dependencies:**
   - *Observation:* `fastapi` and `uvicorn` are needed for the demo API server.
   - *Recommendation:* Check if `fastapi` and `uvicorn` are already available in the Python environment, or install them in the virtual environment without altering the project's core research dependencies.

---

## 9. Conclusion & Next Step

The AERIS-RAG system possesses a complete, scientifically validated, and telemetry-rich backend pipeline that is immediately suitable for an interactive research demo. 

**Recommended Immediate Next Step:**
When authorized by the user, proceed to implement the lightweight API wrapper (`app/api/server.py`) and single-page dashboard (`frontend/`), enabling live interactive demonstration of AERIS-RAG without altering the core scientific engine.
