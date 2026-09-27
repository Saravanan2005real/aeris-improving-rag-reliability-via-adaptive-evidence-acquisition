# AERIS-RAG Benchmark

## Purpose
This dataset is the initial benchmark for evaluating the AERIS-RAG pipeline. It assesses the architecture's ability to plan requirements, perform adaptive retrieval, verify claims, handle contradictions, and generate grounded answers.

## Document Source
The benchmark is currently grounded in a single test document: `test_document.pdf` (Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks by Lewis et al.).

## Categories
- **DIRECT_FACT**: Simple questions explicitly answered in one chunk.
- **MULTI_HOP**: Questions requiring the synthesis of evidence across multiple chunks or pages.
- **METHOD**: Questions about architectural details or algorithms.
- **COMPARATIVE**: Questions requiring comparing results, models, or configurations.
- **QUANTITATIVE**: Questions regarding metrics, percentages, or numbers.
- **UNANSWERABLE**: Questions not present in the document to test anti-hallucination.
- **CONTRADICTION**: Questions where the document has varying contextual claims.
- **MULTILINGUAL**: Multilingual evidence synthesis (if present).

## Annotation Fields
- `question_id`: Unique identifier.
- `document_id`: Source document.
- `question`: Query text.
- `category` & `difficulty`: Categorization properties.
- `information_requirements`: Expected planner output semantics.
- `expected_answer`: The final expected grounded answer.
- `expected_claims`: Expected intermediate claims for verification.
- `supporting_chunk_ids`: Ground-truth evidence chunks.
- `answerability`: Whether the document contains the answer.
- `expected_status`: Expected final AnswerStatus (e.g., SUPPORTED, INSUFFICIENT_EVIDENCE).

## Limitations
This is an initial, compact, research-grade benchmark to validate the architectural components. It is not yet a statistically comprehensive benchmark for large-scale performance or regression testing. It currently relies on a single source document.
