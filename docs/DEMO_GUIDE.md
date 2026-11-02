# AERIS-RAG — Research Demonstration User Guide

This guide describes how to launch, navigate, and present the **AERIS-RAG** (Adaptive Evidence Retrieval and Grounded Information System) research demonstration application.

---

## 1. System Requirements & Prerequisites

Ensure the following prerequisites are met before launching:

1. **Python Environment:** Python 3.10+ with dependencies installed:
   ```bash
   pip install -r requirements.txt
   pip install fastapi uvicorn python-multipart
   ```
2. **Local LLM Service (Ollama):**
   - Ensure Ollama is active on `http://localhost:11434`.
   - Verify the required generation and embedding models are pulled:
     ```bash
     ollama list
     ```
     Required:
     - `llama3.2:latest` (Generation, claim extraction, and verification)
     - `nomic-embed-text:latest` (Dense passage and query embeddings)

---

## 2. Launching the Application

### Start the Demonstration Server:
From the project root (`E:\aeris-rag`):

```powershell
python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000
```

- **Startup Time:** The server takes approximately 25–40 seconds to initialize local Cross-Encoder, NLI verifier, and calibrator weights into memory.
- **Accessing the UI:** Open your browser and navigate to:
  ```
  http://127.0.0.1:8000
  ```

---

## 3. Dashboard Navigation & Demo Features

### A. System Header & Health Indicators
- **Header Badges:** Displays real-time connection status (`Controller Ready`), target LLM model (`llama3.2`), and active indexed document (`test_document`).
- **Research Prototype Disclaimer:** Clarifies that the system is an academic research prototype evaluating evidence grounding, not certified for clinical or life-critical applications.

### B. Document Management & Ingestion
- **Document Selector:** Select from verified pre-indexed documents (default: `test_document`, the 2020 Lewis et al. RAG paper).
- **Document Ingestion Drawer (`+ Upload PDF`):**
  1. Click **`+ Upload PDF`** in the Document Card.
  2. Drag & drop or select any research PDF paper.
  3. Click **`Build Index`**.
  4. The system extracts text using PyMuPDF, chunks semantically, and computes dense vectors via `nomic-embed-text`.
  5. Once indexing completes, the new document is automatically added to the dropdown and ready for queries.

### C. Submitting Questions
1. **Using Verified Presets (Recommended for Presentations):**
   - Click any of the 7 curated preset buttons above the question input:
     - **Direct Fact:** *"What is the full title of the paper?"* (Expected: `SUPPORTED`)
     - **Architecture:** *"What architecture does the dense passage retriever (DPR) use?"* (Expected: `SUPPORTED`)
     - **Component (FAISS):** *"What library is used for Maximum Inner Product Search (MIPS)?"* (Expected: `SUPPORTED`)
     - **Comparative:** *"Do people prefer RAG or purely parametric BART?"* (Expected: `SUPPORTED`)
     - **Conservative Rejection:** *"What hardware was used to train the RAG models?"* (Expected: `INSUFFICIENT_EVIDENCE`)
     - **Ungrounded Metric:** *"How many days did it take to build the December 2016 Wikipedia dump?"* (Expected: `INSUFFICIENT_EVIDENCE`)
     - **Partial Support:** *"How does the system fuse dense and sparse retrieval?"* (Expected: `INSUFFICIENT_EVIDENCE`)
2. **Submitting Custom Inquiries:**
   - Type your question in the textarea and click **`Execute AERIS Pipeline`** (or press `Ctrl + Enter`).
   - An execution stopwatch starts while the 10-stage pipeline processes your query.

### D. Inspecting Answers & Citations
- **Status Badges:**
  - `SUPPORTED` (Emerald): Fully grounded answer.
  - `PARTIALLY_SUPPORTED` (Amber): Some sub-facets satisfied, but essential requirements missing.
  - `INSUFFICIENT_EVIDENCE` (Indigo): Conservative refusal when evidence lacks target concepts.
  - `CONFLICTED` (Rose): Contextual or cross-claim contradiction detected.
- **Interactive Citations:**
  - Answer text includes clickable citation pills like `[p.1, test_document_p001_c001]`.
  - Clicking a citation immediately switches to the **Evidence Inspector**, expands the referenced chunk, and flashes a highlight animation around the passage!

### E. Evidence Inspector (Tab 1)
- **Filters:** Toggle between:
  - *Cited Passages Only:* Only chunks cited in the generated answer.
  - *All Retrieved Pool:* Complete candidate pool returned by adaptive hybrid retrieval.
- **Passage Cards:** Expandable cards showing Chunk ID, Page number, Provenance validity (`VALID PROVENANCE` vs `PROVENANCE DEFECT`), and the full raw text snippet from the document index.

### F. Requirement Support Panel (Tab 2)
- **Summary Metrics:** Total requirements planned, satisfied count, and unsupported sub-facets.
- **Validator Rationales:** Explicit explanations from the deterministic requirement validator explaining why evidence entailed or failed to entail specific query facets.

### G. Pipeline Telemetry Panel (Tab 3)
- **Duration Chart:** Total end-to-end execution time with per-stage breakdown:
  - Planning
  - Adaptive Retrieval
  - Evidence Coverage
  - Claim Extraction
  - Claim Verification
  - Contradiction Analysis
  - Cross-Lingual Analysis
  - Confidence Calibration
  - Selective Verification
  - Answer Generation
- **Metrics:** Displays output counts (e.g. number of claims, evidence chunks, verified pairs) and latency in seconds.

---

## 4. Troubleshooting Common Issues

| Issue | Cause | Resolution |
|---|---|---|
| **Header shows "Controller Initializing..."** | Local PyTorch weights are still loading into memory. | Wait ~30–40 seconds for startup to complete; the status pill will turn green (`Controller Ready`). |
| **Header shows "Ollama Degraded"** | Ollama service is not running or missing models. | Ensure Ollama is running (`ollama serve`) and pull required models (`ollama pull llama3.2` and `ollama pull nomic-embed-text`). |
| **Execution takes ~60–80 seconds** | Normal behavior on local consumer GPUs for multi-stage LLM pipelines. | The pipeline performs planning, per-chunk claim extraction, typing, verification, and grounded generation. The UI shows an active spinner and stopwatch. |
| **"Another query is in progress" / Lock Delay** | Request serialization prevents GPU VRAM collisions. | The server processes queries sequentially. Wait for the active query to finish. |
