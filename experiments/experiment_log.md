# AERIS-RAG Experiment Log

## EXP-000 — Environment Validation

Date: 2026-09-25

### Objective
Validate the local development and inference environment.

### Components
- Python: 3.x
- Ollama: Local Instance
- Generation model: llama3.2
- Operating system: Windows

### Result
The `test_ollama.py` script successfully executed, establishing communication with the local Ollama instance and returning a generated response from `llama3.2`.

### Status
PASSED

---

## EXP-001 — Core Components & Adaptive Controller Validation

Date: 2026-09-26

### Objective
Implement and validate the core RAG pipeline components: requirement planning, hybrid retrieval, cross-encoder reranking, coverage estimation, and adaptive retrieval with memory state tracking.

### Components Built & Tested
1. **Requirement Planner**: Uses LLM to decompose questions into structured requirements.
2. **Hybrid Retriever**: BM25 (sparse) + MiniLM (dense) fused with Reciprocal Rank Fusion (RRF).
3. **Cross-Encoder Reranker**: `ms-marco-MiniLM-L-6-v2` for precise relevance scoring.
4. **Evidence Coverage Estimator**: Uses LLM to grade evidence on Directness, Relevance, Completeness, and Type Match.
5. **Adaptive Retrieval Controller**: Automatically expands candidate depths (`k=10, 25, 50`) and triggers query reformulation if coverage is unmet.
6. **Retrieval Memory**: Tracks previously attempted query-depth configurations and merges evidence observations to avoid redundant execution.

### Result
All components integrated seamlessly. The adaptive controller successfully triggers depth expansions and semantic reformulations for unmet requirements, successfully skipping duplicate executions upon subsequent identical runs (memory reuse).

### Status
PASSED
