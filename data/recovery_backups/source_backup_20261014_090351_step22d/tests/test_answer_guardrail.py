import pytest
import sys
from unittest.mock import MagicMock
sys.modules['sentence_transformers'] = MagicMock()

from app.answer_generation.answer_generator import AnswerGenerator
from app.answer_generation.schemas import GroundedAnswer, AnswerStatus
from app.claim_graph.graph import ClaimEvidenceGraphBuilder

class DummyChunk:
    def __init__(self, chunk_id):
        self.chunk_id = chunk_id
        self.document_id = "doc1"
        self.text = "test"
        self.pages = [1]

def setup_generator_with_mock(mock_json_response):
    generator = AnswerGenerator()
    
    # Mock the ollama client
    mock_client = MagicMock()
    mock_response = {"message": {"content": mock_json_response}}
    mock_client.chat.return_value = mock_response
    generator.client = mock_client
    
    # Setup dummy graph
    graph = ClaimEvidenceGraphBuilder('doc1')
    graph.claims = {"claim1": MagicMock(text="c1")}
    graph.evidence = {"chunk1": DummyChunk("chunk1")}
    
    # Add dummy edge
    edge = MagicMock()
    edge.chunk_id = "chunk1"
    graph.get_claim_evidence = MagicMock(return_value=[edge])
    
    return generator, graph

def test_supported_empty_provenance():
    gen, graph = setup_generator_with_mock('{"status": "SUPPORTED", "supporting_chunk_ids": [], "answer": "yes"}')
    ans = gen.generate("q", graph, [])
    assert ans.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert ans.answer == "The document does not provide enough information to answer this question."
    assert ans.insufficiency_reason == "Model provided unsupported or hallucinatory provenance."

def test_supported_nonexistent_chunk():
    gen, graph = setup_generator_with_mock('{"status": "SUPPORTED", "supporting_chunk_ids": ["chunk99"], "answer": "yes"}')
    ans = gen.generate("q", graph, [])
    assert ans.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert ans.answer == "The document does not provide enough information to answer this question."

def test_supported_valid_provenance():
    gen, graph = setup_generator_with_mock('{"status": "SUPPORTED", "supporting_chunk_ids": ["chunk1"], "supporting_claim_ids": ["claim1"], "answer": "yes"}')
    ans = gen.generate("q", graph, [])
    assert ans.status == AnswerStatus.SUPPORTED
    assert ans.answer == "yes"
    assert "chunk1" in ans.supporting_chunk_ids
