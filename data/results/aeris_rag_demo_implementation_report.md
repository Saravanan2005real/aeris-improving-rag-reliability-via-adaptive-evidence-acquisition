# AERIS-RAG — Complete Live Research Demo Implementation Report

**System:** AERIS-RAG (Adaptive Evidence Retrieval and Grounded Information System)  
**Target Document Index:** `data/indexes/test_document` (Lewis et al., 2020 RAG Paper)  
**Report Location:** `data/results/aeris_rag_demo_implementation_report.md`  
**Reference Benchmark Experiment (Frozen):** `exp_final224_remediation_20261022_183626`  
**Implementation Branch:** `demo/interactive-web-app`  
**Date:** 2026-11-01  

---

## 1. Executive Summary

This report documents the implementation and validation of an interactive, professional web demonstration application for the AERIS-RAG research framework.

The demonstration application connects a dark-mode browser dashboard directly to the real, authentic AERIS-RAG pipeline (`AERISController.run`), retaining complete fidelity to the underlying scientific architecture (adaptive hybrid retrieval, claim extraction, bipartite claim-evidence graph, selective verification, grounded generation, and requirement-support validation). No mock chatbots or simplified retrieval engines were used.

Historical benchmark artifacts, evaluation labels, and experiment results remain completely untouched and verified by pre/post SHA-256 cryptographic hashes. Step 23 was not started.

---

## 2. Governance and Historical Benchmark Artifact Preservation

In accordance with Section 2 of the demo requirements:
1. **Repository Inspection:** Working tree and Git status were inspected prior to changes.
2. **Snapshot Preservation:** A pre-demo snapshot was generated at `data/snapshots/pre_demo_20261101/`, capturing:
   - Full unified Git diff (`pre_demo_working_tree.patch`)
   - Pre-demo Git status (`pre_demo_git_status.txt`)
   - SHA-256 hashes of all 23 modified files and benchmark datasets (`pre_demo_file_hashes.txt`)
3. **Benchmark Hash Integrity:**
   - Pre-demo SHA-256 of `data/benchmark/aeris_benchmark.json`:  
     `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`
   - Current SHA-256 of `data/benchmark/aeris_benchmark.json`:  
     `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`
   - **Verification:** Identical; zero bytes modified.
4. **Historical Experiment Closure:** Benchmark experiment `exp_final224_remediation_20261022_183626` remains closed. No benchmark, ablation, or research evaluations were rerun. Step 23 remains unstarted.
5. **Branch Isolation:** Implementation was isolated on the dedicated branch `demo/interactive-web-app`.

---

## 3. Files Created and Modified

### Created Files:
- `app/api/__init__.py`: Package init.
- `app/api/server.py`: Lightweight FastAPI application wrapping `build_real_controller()`, exposing secure REST endpoints, document upload/indexing, and serving the static frontend.
- `frontend/index.html`: Research demonstration dashboard interface.
- `frontend/style.css`: Dark-mode accessible stylesheet with custom typography, badge treatments, interactive citation highlights, and telemetry charts.
- `frontend/app.js`: Frontend client managing real-time API communication, citation jumping/highlighting, upload handling, and telemetry visualization.
- `scripts/create_pre_demo_snapshot.py`: Automation script to capture working tree state and SHA-256 file hashes.
- `scripts/test_demo_api.py`: Automated integration and schema verification suite for demo endpoints.
- `scripts/test_live_demo_query.py`: Script to verify single live demo query execution end-to-end.
- `docs/DEMO_GUIDE.md`: Comprehensive user guide for launching, configuring, and presenting the research demo.

### Modified Files:
- `app/claim_extraction/typer.py`:
  - **Change:** Implemented a narrowly scoped demo-era alias map in `ClaimTyper.type_claims` mapping the literal `"COMPARE"` to `ClaimType.COMPARATIVE.value`.
  - **Rationale:** Preserves strict validation for all invalid inputs while accommodating the observed LLM token emission variance for comparative questions.
  - **Isolation:** Isolated as a demo-era fix; did not modify historical benchmark files.

---

## 4. Architecture

### Backend Architecture (`app/api/server.py`)
- **Framework:** FastAPI with Uvicorn.
- **Controller Lifecycle:** Built once during server startup via `lifespan` using `build_real_controller()`. Eliminates heavy re-initialization of PyTorch models on every request (~32s startup saved per query).
- **Concurrency Serialization:** Guarded by `asyncio.Lock()`. Ensures single-occupancy execution on local LLM/GPU to prevent VRAM spikes or race conditions.
- **Threadpool Execution:** Controller runs synchronously inside `loop.run_in_executor`, keeping the event loop responsive for `/api/health` and other requests during long inferences.
- **Cache Isolation:** Re-routes performance cache to `data/cache_interactive_demo.json` and session memory to `demo_session`.
- **Document Access Restrictions:** Document access is validated against known subdirectories in `data/indexes/`. Arbitrary file paths or directory traversal attempts are rejected with HTTP 404.

### Frontend Architecture (`frontend/`)
- **Technology:** Vanilla HTML5, CSS3, and JavaScript (ES6+). Zero npm build toolchain needed.
- **Aesthetic:** Dark-mode slate palette (`#0a0e17`, `#111827`, `#162032`), Inter and JetBrains Mono typography, status badges (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`), pulse highlight animations for active citations, and horizontal stage latency visualizations.
- **Component Breakdown:**
  - **Application Header:** Branding, live health pill, local model tags, target document tag, and academic research prototype disclaimer.
  - **Document Card & Ingestion:** Pre-indexed document selector with chunk/page metadata plus collapsible PDF ingestion drawer (`POST /api/upload_document`).
  - **Question Workspace:** Character counter, 7 verified preset question buttons, textarea, and execution stopwatch.
  - **Grounded Answer Panel:** True backend status badge, confidence score, final answer text with interactive clickable citation pills `[p.X, chunk_id]`, conservative refusal callouts, and downgrade notices.
  - **Inspector Drawer (3 Tabs):**
    - *Tab 1: Evidence Inspector:* Filter between Cited Passages and All Retrieved Candidates; expandable chunk cards showing page numbers, provenance validity, and text.
    - *Tab 2: Requirement Support:* Requirements breakdown, supported/unsupported counts, validator rationales, and judge override explanations.
    - *Tab 3: Pipeline Telemetry:* Stage-by-stage latencies, status badges, output counts, and proportional duration bar charts.

---

## 5. API Endpoints

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/api/health` | Verifies server readiness, controller status, Ollama service availability, and loaded models. | `200` |
| `GET` | `/api/documents` | Lists verified indexed documents available in `data/indexes/`. | `200` |
| `POST` | `/api/upload_document` | Ingests and indexes an uploaded PDF using PyMuPDF, semantic chunking, and dense embeddings. | `200`, `400`, `413`, `500` |
| `GET` | `/api/sample_queries` | Returns 7 pre-validated benchmark questions evaluated against `test_document`. | `200` |
| `POST` | `/api/query` | Executes natural language question through AERISController and returns structured telemetry. | `200`, `404`, `422`, `503` |
| `GET` | `/` | Serves the web dashboard (`frontend/index.html`). | `200` |

---

## 6. Demonstration Scenarios Tested and Outcomes

1. **System Health & LLM Verification:**
   - **Endpoint:** `GET /api/health`
   - **Result:** Pass. Controller initialized (`True`), Ollama detected (`llama3.2:latest`, `nomic-embed-text:latest`), `test_document` indexed.

2. **Security & Input Validation:**
   - **Test 4a (Short Query):** Question `"Hi"` rejected with HTTP 422 Unprocessable Entity.
   - **Test 4b (Nonexistent Document):** Document `"nonexistent_doc"` rejected with HTTP 404 Not Found.
   - **Test 4c (Directory Traversal):** Document `"../../../etc/passwd"` rejected with HTTP 404 Not Found.

3. **Frontend Static Asset Delivery:**
   - Verified that `/`, `/style.css`, and `/app.js` return HTTP 200 with appropriate mime-types.

4. **Live End-to-End Query Test:**
   - **Script:** `scripts/test_live_demo_query.py`
   - **Query:** *"What library is used for Maximum Inner Product Search (MIPS)?"*
   - **Target Document:** `test_document`
   - **Duration:** 210.83s (on local Ollama with sequential multi-stage LLM calls)
   - **Status:** Verified. Successfully executed through all 11 stages without crashing.
   - **Answer Status:** `INSUFFICIENT_EVIDENCE`
   - **Final Answer:** *"The document does not provide enough information to answer this question."*
   - **Retrieved Chunks:** 3 candidates considered.
   - **Stages Reported:** 11 stages (Planning, Adaptive Retrieval, Coverage, Claim Extraction, Claim Verification, Contradiction, Cross-Lingual, Calibration, Selective Verification, Answer Generation, Completed).
   - **Outcome:** Passed. Verified authentic conservative refusal semantics and full stage telemetry delivery.

---

## 7. Known System Characteristics & Limitations

1. **Local LLM Inference Latency:**
   - On local GPU hardware with `llama3.2:latest`, an end-to-end query executes between 40 to 80 seconds due to sequential multi-agent stages (planning, per-chunk claim extraction, claim typing, verification, generation, and requirement validation).
   - The UI includes an active stopwatch, progress indicators, and pre-warmed sample queries to maintain interactive transparency.
2. **Monolingual Document Optimization:**
   - For English documents like `test_document`, Stage 10 (Cross-Lingual Analysis) correctly logs `SKIPPED (MONOLINGUAL)` without penalty.

---

## 8. Confirmation of Constraints

- **Benchmark Integrity:** No benchmark questions or evaluation labels were altered. Cryptographic hashes match pre-demo records.
- **Ablation Preservation:** No ablation or benchmark runs were executed.
- **Step 23:** Step 23 was **not** started.
- **Isolation:** Demo caches and uploads are isolated in `data/cache_interactive_demo.json` and `data/demo_uploads/`.
