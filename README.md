# AERIS: Improving RAG Reliability via Adaptive Evidence Acquisition

AERIS (Adaptive Evidence Retrieval and Information System) is a research-focused Retrieval-Augmented Generation (RAG) architecture designed to systematically address missing evidence and improve retrieval reliability. 

Instead of relying on single-pass retrieval or naive "retrieve more" strategies, AERIS dynamically models what information is actually required, rigorously estimates the coverage of acquired evidence, and adaptively adjusts its retrieval strategy (via candidate depth expansion and semantic query reformulation) only when evidence is genuinely missing.

## 🚀 Key Architectural Innovations

1. **Information Requirement Planner**  
   Decomposes complex user questions into atomic, distinct information requirements. Instead of one broad query, AERIS generates targeted queries for each specific requirement (e.g., *methodology*, *quantitative results*, *baselines*).

2. **Evidence Coverage Estimator**  
   Rather than treating retrieval as a black box or using simple LLM relevance judgments, AERIS employs a strict **4-dimensional scoring model**:
   - `Directness` (0.3)
   - `Relevance` (0.25)
   - `Completeness` (0.25)
   - `Evidence Type Match` (0.2)
   
   Evidence must exceed a strict threshold to be marked as `SUPPORTED`. If it doesn't, it triggers the Adaptive Controller.

3. **Retrieval Memory & State Tracking**  
   AERIS maintains an active, in-memory state of all retrieval attempts (tracking the combination of Query, Requirement ID, and Candidate Depth) as well as the evidence acquired across those attempts. This memory allows the system to seamlessly recognize and skip duplicate retrieval operations (e.g., repeating a retrieval depth that has already been evaluated), thus saving compute and preventing cyclic redundant fetching without altering the adaptive workflow.

4. **Adaptive Retrieval Controller**  
   The core engine for handling evidence failures. It implements a multi-tiered adaptive recovery strategy with early stopping:
   - **Tier 1 (Depth Expansion):** Automatically expands the candidate pool (e.g., `candidate_k` from 10 → 25 → 50) if initial retrieval misses the chunk.
   - **Tier 2 (Query Reformulation):** If depth expansion fails, it triggers the Query Reformulator to semantically rewrite the query.
   - **Duplicate Guard:** Bypasses retrieval entirely if the `RetrievalMemory` detects the attempt was previously made.
   - **Early Stopping:** Stops retrieval immediately upon hitting the `SUPPORTED` threshold to minimize computational cost, latency, and context noise.

5. **Hybrid Retrieval + Cross-Encoder Reranking**  
   - **Dense Retrieval:** `all-MiniLM-L6-v2`
   - **Sparse Retrieval:** BM25
   - **Fusion:** Reciprocal Rank Fusion (RRF)
   - **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`

## 🏗️ Architecture Diagram

```mermaid
graph TD
    UserQ[User Question] --> Planner[Requirement Planner]
    
    Planner --> R1[Requirement 1]
    Planner --> R2[Requirement 2]
    
    R1 --> MemCheck{Memory Guard}
    MemCheck -->|Not Attempted| InitialRet[Hybrid Retrieval<br>k=10]
    MemCheck -->|Already Attempted| Skip[Skip & Try Next State]
    
    InitialRet --> Rerank[Cross-Encoder Reranking]
    Rerank --> Coverage[Evidence Coverage Estimator]
    Coverage --> MemStore[Record Attempt & Evidence in Memory]
    
    MemStore -->|SUPPORTED| Stop[STOP & Proceed]
    MemStore -->|UNSUPPORTED| AdaptDepth[Candidate Depth Expansion<br>k=25, 50]
    
    AdaptDepth --> MemCheck
    
    AdaptDepth -->|Still UNSUPPORTED| Reformulate[Query Reformulator]
    Reformulate --> NewQuery[New Retrieval Query]
    NewQuery --> MemCheck
```

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
   AERIS relies on local LLMs for planning and evidence estimation. Ensure you have [Ollama](https://ollama.com/) installed and running.
   ```bash
   ollama pull llama3.2:latest
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3.2:latest
   ```

## 🧪 Running the Tests

To observe the various components of AERIS in action:

- **Adaptive Candidate Expansion & Reformulation:**
  ```bash
  python scripts/test_adaptive_retrieval.py data/raw/test_document.pdf "How does the retriever work?"
  ```
  
- **Memory Integration & State Tracking:**
  ```bash
  python scripts/test_retrieval_memory_integration.py data/raw/test_document.pdf "How does the retriever work?"
  ```
  
- **Memory Reuse & Duplicate Skipping:**
  ```bash
  python scripts/test_memory_reuse.py data/raw/test_document.pdf "How does the retriever work?"
  ```
