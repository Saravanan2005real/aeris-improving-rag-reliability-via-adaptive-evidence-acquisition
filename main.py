"""
AERIS-RAG: Improving RAG Reliability via Adaptive Evidence Acquisition
Main Application Entry Point

Usage:
    # Run Web Demonstration & REST API Server (Default):
    python main.py
    python main.py --host 127.0.0.1 --port 8000

    # Run CLI Query Mode:
    python main.py --query "What architecture does the dense passage retriever (DPR) use?" --doc test_document
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def print_banner(host: str, port: int):
    banner = f"""
========================================================================
   AERIS-RAG: Adaptive Evidence Retrieval and Grounded Information System
========================================================================
   - Web UI & API : http://{host}:{port}
   - Documentation: docs/DEMO_GUIDE.md & ARCHITECTURE.md
   - Target Index : data/indexes/test_document
========================================================================
"""
    print(banner)

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    import uvicorn
    print_banner(host, port)
    print(f"Starting AERIS-RAG Web Dashboard and API on http://{host}:{port}...")
    uvicorn.run("app.api.server:app", host=host, port=port, reload=reload)

def run_cli_query(question: str, document_id: str = "test_document"):
    print(f"\n[AERIS CLI] Running query against document '{document_id}':")
    print(f"Question: {question}\n")
    from scripts.run_ablation import build_real_controller
    from app.controller.schemas import ControllerRequest, ControllerConfig

    controller = build_real_controller()
    request = ControllerRequest(
        document_id=document_id,
        question=question,
        config=ControllerConfig(
            session_id="cli_session",
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
    result = controller.run(request)
    print("\n" + "=" * 50)
    print(f"Status           : {result.answer_status or result.status.value}")
    print(f"Confidence       : {result.answer_confidence}")
    print(f"Final Answer     :\n{result.final_answer}")
    print(f"Supporting Chunks: {result.supporting_chunk_ids}")
    print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description="AERIS-RAG Runner")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"), help="Host to bind server")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Port to bind server")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload")
    parser.add_argument("--query", type=str, default=None, help="Run a single question via CLI instead of starting server")
    parser.add_argument("--doc", type=str, default="test_document", help="Document ID for CLI query (default: test_document)")

    args = parser.parse_args()

    if args.query:
        run_cli_query(args.query, args.doc)
    else:
        run_server(host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
