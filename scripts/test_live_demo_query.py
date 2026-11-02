"""
AERIS-RAG Single Live Demo Query Test
Executes a single demonstration query against test_document to verify end-to-end integration.
"""

import sys
import json
import time
import urllib.request

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("Executing single live demo query via POST /api/query...")
    payload = {
        "document_id": "test_document",
        "question": "What library is used for Maximum Inner Product Search (MIPS)?"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/query",
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AERIS-Demo-Test/1.0"}
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as resp:
        elapsed = time.perf_counter() - t0
        res = json.loads(resp.read().decode("utf-8"))

    print(f"\nLive query completed in {elapsed:.2f}s:")
    print(f"Status           : {res.get('answer_status')}")
    print(f"Confidence       : {res.get('answer_confidence')}")
    print(f"Final Answer     : {res.get('final_answer')}")
    print(f"Supporting Chunks: {res.get('supporting_chunk_ids')}")
    print(f"Citations Count  : {len(res.get('citations', []))}")
    print(f"Retrieved Count  : {len(res.get('retrieved_evidence', []))}")
    print(f"Stages Reported  : {len(res.get('stages', []))}")

    assert res.get("answer_status") in ["SUPPORTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE"], f"Unexpected status: {res.get('answer_status')}"
    assert len(res.get("stages", [])) > 0, "Expected stage telemetry in result"
    print("\n[SUCCESS] Single live demo query verified successfully!")

if __name__ == "__main__":
    main()
