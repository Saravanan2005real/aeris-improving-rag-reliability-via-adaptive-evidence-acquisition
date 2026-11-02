"""
AERIS-RAG — Interactive Research Demonstration Backend Server
Exposes secure REST API endpoints and serves the research dashboard frontend.

Architecture:
- Lightweight FastAPI server with lifespan initialization.
- Reuses the authentic AERISController pipeline via build_real_controller().
- Enforces request serialization via asyncio.Lock to prevent GPU/LLM race conditions.
- Uses an isolated demo cache namespace (data/cache_interactive_demo.json).
- Restricts document access to verified indexed documents in data/indexes/.
"""

import os
import sys
import json
import time
import asyncio
import logging
import urllib.request
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.controller.schemas import (
    ControllerConfig,
    ControllerRequest,
    ControllerResult,
    StageStatus,
)
from app.performance_cache import aeris_cache
from scripts.run_ablation import build_real_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aeris_demo_api")

# Isolated demo cache file
DEMO_CACHE_PATH = str(PROJECT_ROOT / "data" / "cache_interactive_demo.json")
INDEX_BASE_DIR = PROJECT_ROOT / "data" / "indexes"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Isolate performance cache for demo
aeris_cache.cache_file = DEMO_CACHE_PATH
aeris_cache._load()
logger.info(f"Demo cache initialized at isolated path: {DEMO_CACHE_PATH}")

# Global lock to serialize controller queries (prevents GPU / Ollama concurrent memory collisions)
query_lock = asyncio.Lock()

# Global controller reference
controller_instance: Optional[Any] = None
controller_init_time: Optional[float] = None
controller_init_error: Optional[str] = None


def get_allowed_documents() -> Dict[str, Path]:
    """Scans data/indexes/ and returns dictionary of verified, indexed document directories."""
    allowed = {}
    if not INDEX_BASE_DIR.exists():
        return allowed
    for entry in INDEX_BASE_DIR.iterdir():
        if entry.is_dir():
            metadata_file = entry / "metadata.json"
            embeddings_file = entry / "embeddings.npy"
            if metadata_file.exists() and embeddings_file.exists():
                allowed[entry.name] = entry
    return allowed


def check_ollama_status() -> Dict[str, Any]:
    """Pings local Ollama service and checks availability of required models."""
    host = settings.ollama_host.rstrip("/")
    url = f"{host}/api/tags"
    req = urllib.request.Request(url, headers={"User-Agent": "AERIS-Demo/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            detected_models = [m.get("name", "") for m in data.get("models", [])]
            gen_model = settings.ollama_model
            emb_model = settings.embedding_model
            return {
                "ollama_running": True,
                "models_detected": detected_models,
                "generation_model": gen_model,
                "generation_model_available": any(m.startswith(gen_model.split(":")[0]) for m in detected_models),
                "embedding_model": emb_model,
                "embedding_model_available": any(m.startswith(emb_model.split(":")[0]) for m in detected_models),
                "error": None
            }
    except Exception as e:
        return {
            "ollama_running": False,
            "models_detected": [],
            "generation_model": settings.ollama_model,
            "generation_model_available": False,
            "embedding_model": settings.embedding_model,
            "embedding_model_available": False,
            "error": str(e)
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes the controller once at server startup in a worker thread."""
    global controller_instance, controller_init_time, controller_init_error
    logger.info("Initializing AERIS real controller pipeline...")
    t0 = time.perf_counter()
    loop = asyncio.get_running_loop()
    try:
        # Run synchronous initialization in background thread to avoid blocking server boot
        controller_instance = await loop.run_in_executor(None, build_real_controller)
        controller_init_time = time.perf_counter() - t0
        controller_init_error = None
        logger.info(f"AERISController successfully initialized in {controller_init_time:.2f}s.")
    except Exception as e:
        controller_init_error = str(e)
        controller_instance = None
        logger.error(f"Failed to initialize AERISController: {e}")
    yield
    logger.info("AERIS Demo server shutting down.")


app = FastAPI(
    title="AERIS-RAG Research Demo API",
    description="Interactive REST API for Adaptive Evidence Retrieval and Verification",
    version="1.0.0",
    lifespan=lifespan
)

# Narrow CORS configuration for local development and demonstration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "null",  # file:// origin for local testing
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# Pydantic Schemas
# ----------------------------------------------------------------------

class DocumentInfo(BaseModel):
    document_id: str
    title: str
    authors: Optional[str] = None
    chunk_count: int
    total_pages: int
    embedding_model: str
    status: str
    is_ready: bool
    description: str


class SampleQueryItem(BaseModel):
    id: str
    question: str
    document_id: str
    category: str
    expected_status: str
    is_validated: bool
    description: str


class QueryRequest(BaseModel):
    document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Allowed document identifier (e.g. 'test_document')"
    )
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language question to evaluate"
    )


class CitationItem(BaseModel):
    chunk_id: str
    pages: List[int] = Field(default_factory=list)
    text: Optional[str] = None
    relevant_claim_ids: List[str] = Field(default_factory=list)
    is_cited: bool = True
    provenance_valid: bool = True


class RetrievedEvidenceItem(BaseModel):
    chunk_id: str
    pages: List[int] = Field(default_factory=list)
    text: str = ""
    is_cited: bool = False


class StageTelemetryItem(BaseModel):
    stage: str
    status: str
    message: Optional[str] = None
    output_count: int = 0
    latency_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    question: str
    document_id: str
    final_answer: Optional[str] = None
    answer_status: str
    answer_confidence: Optional[float] = None
    supporting_claims: List[str] = Field(default_factory=list)
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    citations: List[CitationItem] = Field(default_factory=list)
    retrieved_evidence: List[RetrievedEvidenceItem] = Field(default_factory=list)
    downgrade_details: List[Dict[str, Any]] = Field(default_factory=list)
    downgrade_reasons: List[str] = Field(default_factory=list)
    conflict_information: Optional[str] = None
    insufficiency_information: Optional[str] = None
    stages: List[StageTelemetryItem] = Field(default_factory=list)
    total_execution_seconds: float = 0.0
    is_busy: bool = False
    error: Optional[str] = None


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Returns application health, controller status, and Ollama model checks."""
    allowed_docs = list(get_allowed_documents().keys())
    ollama_info = check_ollama_status()
    is_ready = bool(
        controller_instance is not None
        and ollama_info["ollama_running"]
        and ollama_info["generation_model_available"]
        and len(allowed_docs) > 0
    )

    return {
        "status": "ok" if is_ready else "degraded",
        "backend_initialized": True,
        "controller_initialized": controller_instance is not None,
        "controller_init_time_seconds": controller_init_time,
        "controller_init_error": controller_init_error,
        "query_lock_active": query_lock.locked(),
        "ollama": ollama_info,
        "indexed_documents": allowed_docs,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get("/api/documents", response_model=List[DocumentInfo])
async def list_documents():
    """Lists available pre-indexed documents for demonstration."""
    allowed = get_allowed_documents()
    docs: List[DocumentInfo] = []

    for doc_id, doc_path in allowed.items():
        meta_file = doc_path / "metadata.json"
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            chunk_count = len(meta)
            pages = set()
            emb_model = "unknown"
            sample_text = ""
            for item in meta:
                pages.update(item.get("pages", []))
                if "embedding_model" in item:
                    emb_model = item["embedding_model"]
                if not sample_text and item.get("text"):
                    sample_text = item["text"][:300]

            title = "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" if doc_id == "test_document" else f"Document: {doc_id}"
            authors = "Patrick Lewis et al. (Facebook AI Research / UCL / NYU)" if doc_id == "test_document" else None
            description = (
                "Seminal RAG research paper evaluated in the closed AERIS benchmark. "
                "Covers parametric seq2seq models (BART), dense passage retrieval (DPR), and Wikipedia vector indices."
                if doc_id == "test_document" else "Pre-indexed research document."
            )

            docs.append(DocumentInfo(
                document_id=doc_id,
                title=title,
                authors=authors,
                chunk_count=chunk_count,
                total_pages=max(pages) if pages else 1,
                embedding_model=emb_model,
                status="INDEXED",
                is_ready=True,
                description=description
            ))
        except Exception as e:
            logger.error(f"Error reading metadata for document {doc_id}: {e}")

    return docs


@app.post("/api/upload_document")
async def upload_and_index_document(file: UploadFile = File(...)):
    """
    Uploads a research PDF document and executes the real AERIS indexing pipeline
    (PyMuPDF text extraction, semantic chunking, dense embedding generation, and vector index persistence).
    The document is only marked ready and queryable once indexing succeeds completely.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) are supported."
        )

    import re
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", Path(file.filename).stem).strip("_")
    if not clean_stem:
        clean_stem = f"doc_{int(time.time())}"

    upload_dir = PROJECT_ROOT / "data" / "demo_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = upload_dir / f"{clean_stem}.pdf"

    try:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="PDF file size exceeds 50MB limit."
            )
        with open(pdf_path, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # Execute build_index synchronously in worker thread
    loop = asyncio.get_running_loop()
    try:
        from app.indexing.index_builder import build_index
        index_result = await loop.run_in_executor(None, build_index, str(pdf_path))
    except Exception as e:
        logger.error(f"Failed to index uploaded PDF {pdf_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )

    return {
        "status": "INDEXED",
        "document_id": index_result["document_id"],
        "total_chunks": index_result["total_chunks"],
        "embedded_chunks": index_result["embedded_chunks"],
        "failed_chunks": index_result["failed_chunks"],
        "message": f"Document '{index_result['document_id']}' indexed successfully with {index_result['total_chunks']} chunks."
    }


@app.get("/api/sample_queries", response_model=List[SampleQueryItem])
async def list_sample_queries():
    """
    Returns verified demonstration questions evaluated against data/indexes/test_document.
    Distinguishes benchmark-verified questions from exploratory suggestions.
    """
    samples = [
        SampleQueryItem(
            id="q_df_01",
            question="What is the full title of the paper?",
            document_id="test_document",
            category="Direct Fact",
            expected_status="SUPPORTED",
            is_validated=True,
            description="Tests gold title retrieval from Page 1 and verifies full factual grounding."
        ),
        SampleQueryItem(
            id="q_df_02",
            question="What architecture does the dense passage retriever (DPR) use?",
            document_id="test_document",
            category="Direct Fact",
            expected_status="SUPPORTED",
            is_validated=True,
            description="Tests multi-chunk architectural extraction and verification of bi-encoder DPR."
        ),
        SampleQueryItem(
            id="q_df_05",
            question="What library is used for Maximum Inner Product Search (MIPS)?",
            document_id="test_document",
            category="Direct Fact",
            expected_status="SUPPORTED",
            is_validated=True,
            description="Verifies exact entity identification (FAISS library) and high-confidence citation."
        ),
        SampleQueryItem(
            id="q_comp_01",
            question="Do people prefer RAG or purely parametric BART?",
            document_id="test_document",
            category="Comparative",
            expected_status="SUPPORTED",
            is_validated=True,
            description="Exercises comparative claim typing (with demo-era COMPARE alias) and human evaluation extraction."
        ),
        SampleQueryItem(
            id="q_unans_02",
            question="What hardware was used to train the RAG models?",
            document_id="test_document",
            category="Conservative Rejection",
            expected_status="INSUFFICIENT_EVIDENCE",
            is_validated=True,
            description="Demonstrates conservative refusal when evidence lacks target hardware concepts (GPU/TPU/compute)."
        ),
        SampleQueryItem(
            id="q_unans_04",
            question="How many days did it take to build the December 2016 Wikipedia dump?",
            document_id="test_document",
            category="Conservative Rejection",
            expected_status="INSUFFICIENT_EVIDENCE",
            is_validated=True,
            description="Demonstrates refusal on ungrounded temporal metrics absent from the published paper text."
        ),
        SampleQueryItem(
            id="q_meth_02",
            question="How does the system fuse dense and sparse retrieval?",
            document_id="test_document",
            category="Method / Partial Support",
            expected_status="INSUFFICIENT_EVIDENCE",
            is_validated=True,
            description="Demonstrates requirement validation when hybrid sparse/dense fusion is not covered in the document."
        ),
    ]
    return samples


@app.post("/api/query", response_model=QueryResponse)
async def execute_query(req: QueryRequest):
    """
    Executes a question through the authentic AERIS-RAG controller.
    Enforces serialization and isolates caches.
    """
    global controller_instance

    # 1. Validate document ID strictly against allowed indexed documents
    allowed_docs = get_allowed_documents()
    if req.document_id not in allowed_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{req.document_id}' is not an allowed indexed document. Available: {list(allowed_docs.keys())}"
        )

    # 2. Check controller initialization
    if controller_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AERIS controller is not initialized. Error: {controller_init_error or 'Still initializing'}"
        )

    # 3. Check question sanity
    clean_question = req.question.strip()
    if len(clean_question) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question is too short (minimum 3 characters required)."
        )

    # 4. Serialize query execution via asyncio.Lock to avoid GPU / Ollama collisions
    logger.info(f"Received query for document '{req.document_id}': {clean_question[:80]}...")
    t_start = time.perf_counter()

    async with query_lock:
        logger.info(f"Acquired execution lock for query: '{clean_question[:50]}'")
        controller_request = ControllerRequest(
            document_id=req.document_id,
            question=clean_question,
            config=ControllerConfig(
                session_id=f"demo_session_{int(time.time())}",
                scoped_retrieval_memory=True,
                verification_budget=3,
                enable_adaptive_retrieval=True,
                enable_query_reformulation=True,
                enable_retrieval_memory=True,
                enable_claim_verification=True,
                enable_contradiction_analysis=True,
                enable_cross_lingual_analysis=True,
                enable_calibration=True,
                enable_selective_verification=True,
                answer_generation_enabled=True,
            )
        )

        loop = asyncio.get_running_loop()
        try:
            # Execute controller run synchronously in a worker thread
            result: ControllerResult = await loop.run_in_executor(
                None,
                controller_instance.run,
                controller_request
            )
            total_time = time.perf_counter() - t_start
        except Exception as e:
            total_time = time.perf_counter() - t_start
            logger.error(f"Controller execution exception: {e}", exc_info=True)
            return QueryResponse(
                question=clean_question,
                document_id=req.document_id,
                final_answer="A pipeline error occurred while processing the query.",
                answer_status="FAILED",
                answer_confidence=0.0,
                total_execution_seconds=total_time,
                error=f"Execution error: {str(e)}"
            )

    # 5. Enrich results with document chunk text and metadata
    doc_path = allowed_docs[req.document_id]
    chunk_map: Dict[str, Dict[str, Any]] = {}
    try:
        with open(doc_path / "metadata.json", "r", encoding="utf-8") as f:
            raw_meta = json.load(f)
            for item in raw_meta:
                chunk_map[item["chunk_id"]] = item
    except Exception as e:
        logger.warning(f"Could not load chunk metadata for {req.document_id}: {e}")

    # Build enriched citations list
    citations: List[CitationItem] = []
    for prov in result.provenance:
        cid = prov.get("chunk_id", "")
        pages = prov.get("pages") or chunk_map.get(cid, {}).get("pages", [])
        text = chunk_map.get(cid, {}).get("text", "")
        is_defect = cid in result.provenance_defects
        citations.append(CitationItem(
            chunk_id=cid,
            pages=pages,
            text=text,
            relevant_claim_ids=prov.get("relevant_claim_ids", []),
            is_cited=True,
            provenance_valid=not is_defect
        ))

    # Build full retrieved evidence list (all candidates considered)
    retrieved_evidence: List[RetrievedEvidenceItem] = []
    for cid in result.retrieved_chunk_ids:
        chunk_info = chunk_map.get(cid, {})
        retrieved_evidence.append(RetrievedEvidenceItem(
            chunk_id=cid,
            pages=chunk_info.get("pages", []),
            text=chunk_info.get("text", ""),
            is_cited=cid in result.supporting_chunk_ids
        ))

    # Extract downgrade rationales
    downgrade_details = result.metadata.get("downgrade_details", [])
    downgrade_reasons: List[str] = []
    for dd in downgrade_details:
        rationales = dd.get("validator_rationales", [])
        if rationales:
            downgrade_reasons.extend(rationales)
        dtype = dd.get("downgrade_type")
        if dtype and dtype not in downgrade_reasons:
            downgrade_reasons.append(f"Downgrade Trigger: {dtype}")

    # Convert stage telemetry
    telemetry_stages: List[StageTelemetryItem] = []
    for stg in result.stages:
        telemetry_stages.append(StageTelemetryItem(
            stage=stg.stage.value if hasattr(stg.stage, "value") else str(stg.stage),
            status=stg.status.value if hasattr(stg.status, "value") else str(stg.status),
            message=stg.message,
            output_count=stg.output_count,
            latency_seconds=stg.latency_seconds,
            metadata=stg.metadata
        ))

    # Determine safe normalized status string
    status_str = result.answer_status or (result.status.value if result.status else "UNKNOWN")

    return QueryResponse(
        question=result.question,
        document_id=result.document_id,
        final_answer=result.final_answer,
        answer_status=status_str,
        answer_confidence=result.answer_confidence,
        supporting_claims=result.supporting_claim_ids,
        supporting_chunk_ids=result.supporting_chunk_ids,
        citations=citations,
        retrieved_evidence=retrieved_evidence,
        downgrade_details=downgrade_details,
        downgrade_reasons=downgrade_reasons,
        conflict_information=result.conflict_information,
        insufficiency_information=result.insufficiency_information,
        stages=telemetry_stages,
        total_execution_seconds=total_time,
        error=None
    )


# ----------------------------------------------------------------------
# Frontend Static Files Mount
# ----------------------------------------------------------------------

# Ensure frontend directory exists
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

# Mount frontend at root (after API routes) so index.html, style.css, and app.js are served directly
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.server:app", host="127.0.0.1", port=8000, reload=False)
