"""
AERIS-RAG Demo API Verification Suite
Tests the FastAPI server endpoints, validation constraints, and error handling.
Does NOT run any benchmark or evaluation experiments.
"""

import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "AERIS-Test/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        content = resp.read().decode("utf-8")
        try:
            return resp.status, json.loads(content)
        except Exception:
            return resp.status, content

def post(path, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AERIS-Test/1.0"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 70)
    print("AERIS-RAG DEMO API INTEGRATION & SCHEMA VERIFICATION")
    print("=" * 70)

    # 1. Health Endpoint Check
    print("\n[TEST 1] Testing GET /api/health...")
    status, health = get("/api/health")
    assert status == 200, f"Expected 200, got {status}"
    print(f"  -> HTTP Status: {status}")
    print(f"  -> System Status: {health.get('status')}")
    print(f"  -> Controller Initialized: {health.get('controller_initialized')}")
    print(f"  -> Ollama Running: {health.get('ollama', {}).get('ollama_running')}")
    print(f"  -> Generation Model: {health.get('ollama', {}).get('generation_model')} (Available: {health.get('ollama', {}).get('generation_model_available')})")
    print(f"  -> Indexed Documents: {health.get('indexed_documents')}")
    assert "test_document" in health.get("indexed_documents", []), "test_document must be in indexed_documents"
    print("  [PASS] /api/health schema verified.")

    # 2. Documents Listing Check
    print("\n[TEST 2] Testing GET /api/documents...")
    status, docs = get("/api/documents")
    assert status == 200, f"Expected 200, got {status}"
    assert isinstance(docs, list) and len(docs) > 0, "Expected non-empty list of documents"
    test_doc = next((d for d in docs if d["document_id"] == "test_document"), None)
    assert test_doc is not None, "test_document not found in documents listing"
    print(f"  -> Document ID: {test_doc['document_id']}")
    print(f"  -> Title: {test_doc['title']}")
    print(f"  -> Chunks: {test_doc['chunk_count']}, Total Pages: {test_doc['total_pages']}")
    print(f"  -> Embedding Model: {test_doc['embedding_model']}")
    print("  [PASS] /api/documents verified.")

    # 3. Sample Queries Check
    print("\n[TEST 3] Testing GET /api/sample_queries...")
    status, samples = get("/api/sample_queries")
    assert status == 200, f"Expected 200, got {status}"
    assert len(samples) >= 5, f"Expected at least 5 sample queries, got {len(samples)}"
    print(f"  -> Retrieved {len(samples)} sample queries.")
    for s in samples:
        print(f"     - [{s['category']}] (Expected: {s['expected_status']}) {s['question']}")
        assert s["is_validated"] is True, "Sample queries for test_document must be validated"
    print("  [PASS] /api/sample_queries verified.")

    # 4. Input Validation & Security Checks
    print("\n[TEST 4] Testing security & schema validations...")
    # 4a. Short question rejection (<3 chars)
    try:
        post("/api/query", {"document_id": "test_document", "question": "Hi"})
        print("  [FAIL] Expected 422 for question < 3 chars, but succeeded")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        assert e.code == 422, f"Expected 422, got {e.code}"
        print(f"  -> Short question rejected with HTTP {e.code} as expected.")

    # 4b. Invalid document ID rejection
    try:
        post("/api/query", {"document_id": "nonexistent_doc", "question": "What is RAG?"})
        print("  [FAIL] Expected 404 for nonexistent document, but succeeded")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        assert e.code == 404, f"Expected 404, got {e.code}"
        print(f"  -> Nonexistent document ID rejected with HTTP {e.code} as expected.")

    # 4c. Path traversal rejection
    try:
        post("/api/query", {"document_id": "../../../etc/passwd", "question": "What is RAG?"})
        print("  [FAIL] Expected 404 for path traversal attempt, but succeeded")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        assert e.code == 404, f"Expected 404, got {e.code}"
        print(f"  -> Path traversal attempt rejected with HTTP {e.code} as expected.")

    print("  [PASS] Security & input validation constraints verified.")

    # 5. Frontend Static Files Check
    print("\n[TEST 5] Testing frontend static file delivery...")
    status, _ = get("/")
    assert status == 200, f"Expected 200 for /, got {status}"
    status, _ = get("/style.css")
    assert status == 200, f"Expected 200 for /style.css, got {status}"
    status, _ = get("/app.js")
    assert status == 200, f"Expected 200 for /app.js, got {status}"
    print("  -> index.html, style.css, and app.js served successfully.")
    print("  [PASS] Frontend static files delivery verified.")

    print("\n" + "=" * 70)
    print("ALL DEMO API VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
