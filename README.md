# AERIS: Improving RAG Reliability via Adaptive Evidence Acquisition

AERIS (Adaptive Evidence Retrieval and Information System) is a research-focused Retrieval-Augmented Generation (RAG) architecture designed to systematically address missing evidence, resolve contradictions, avoid hallucinations, and optimize retrieval reliability through adaptive mechanisms.

Instead of relying on single-pass retrieval or naive "retrieve more" strategies, AERIS dynamically models what information is actually required, rigorously estimates the coverage of acquired evidence, adaptively adjusts its retrieval strategy, builds a claim-evidence graph, verifies claims selectively based on a budget, handles cross-lingual information, and generates grounded answers that avoid hallucination.

## 🚀 Key Architectural Innovations

1. **Information Requirement Planner**  
   Decomposes complex user questions into atomic, distinct information requirements. Instead of one broad query, AERIS generates targeted queries for each specific requirement (e.g., *methodology*, *quantitative results*, *baselines*).

2. **Adaptive Retrieval & Coverage Estimation**  
   AERIS employs a strict **4-dimensional scoring model** for evidence coverage (Directness, Relevance, Completeness, Evidence Type Match). If the coverage threshold is not met, the Adaptive Controller dynamically expands the candidate pool (e.g., `candidate_k` 10 → 25 → 50) and reformulates queries using an active memory guard to prevent cyclic redundant fetching.

3. **Claim Extraction & Graph Building**  
   Extracted evidence is distilled into atomic claims, which are normalized using dense embeddings and typed (`FACT`, `METHOD`, `QUANTITATIVE`, etc.). These form a bipartite **Claim-Evidence Graph**, connecting verifiable claims directly to their document provenance.

4. **Contradiction & Cross-Lingual Handlers**  
   - Contextual differences and semantic contradictions across multiple chunks are evaluated using NLI cross-encoders.
   - Cross-lingual evidence pairs are automatically identified, and translations are handled iteratively within the graph to guarantee consistency.

5. **Calibration & Selective Verification**  
   AERIS evaluates historical model confidence distributions (calibration) and uses a knapsack-based optimization algorithm to select which claims should be rigorously verified given a specific LLM context/compute budget.

6. **Grounded Answer Generation**  
   The final generator strictly adheres to the verified claims, enforcing answerability checks and preserving robust provenance chunks to prevent hallucination.

## 🏗️ Architecture Design

Please see the comprehensive [ARCHITECTURE.md](ARCHITECTURE.md) for detailed workflow diagrams, component interactions, schemas, and orchestration logic.

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:Saravanan2005real/aeris-improving-rag-reliability-via-adaptive-evidence-acquisition.git
   cd aeris-improving-rag-reliability-via-adaptive-evidence-acquisition
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   # On Windows: 
   .\venv\Scripts\Activate.ps1
   # On Mac/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Setup Ollama**
   AERIS relies on local LLMs for planning, extraction, and generation. Ensure you have [Ollama](https://ollama.com/) installed and running.
   ```bash
   ollama pull llama3.2:latest
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3.2:latest
   ```

## 🧪 Testing & Execution

To observe the various components of AERIS in action:

- **End-to-End Orchestration Integration Test:**
  ```bash
  python scripts/test_controller_integration.py data/raw/test_document.pdf "What datasets were used in the experiments?"
  ```

- **Selective Verification & Budgets:**
  ```bash
  python scripts/test_selective_verification_e2e.py data/raw/test_document.pdf "How does the retriever work?"
  ```
  
- **Benchmarks and Baselines (Dense, BM25, Hybrid, Hybrid-Rerank):**
  ```bash
  python scripts/validate_benchmark.py
  python scripts/run_baselines.py
  python scripts/evaluate_baselines.py
  ```

## 📊 Benchmarks
The `data/benchmark/` directory contains an initial structured dataset for evaluating the specific architectural strengths of AERIS vs naive retrieval implementations. Baselines implemented in `app/baselines/` guarantee reproducible testing against `DENSE`, `BM25`, `HYBRID`, and `HYBRID_RERANKED` pipelines without arbitrary adaptations.
