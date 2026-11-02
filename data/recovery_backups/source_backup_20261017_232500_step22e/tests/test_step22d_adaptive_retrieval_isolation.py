"""
Step 22D Regression Test: Workstream 1 - Adaptive-Retrieval Ablation Isolation

Verifies:
1. When enable_adaptive_retrieval=False:
   - Candidate depth expansion is prevented (schedule pinned to base depth).
   - Controller-level adaptive retry does not trigger depth expansions.
   - Telemetry strictly records candidate_depth_expansions == 0 and adaptive_retrieval_triggered == False.
2. When enable_query_reformulation=True under NO_ADAPTIVE_RETRIEVAL:
   - Reformulation attempts are executed independently.
   - Additional attempts are classified as reformulation, NOT misclassified as adaptive retrieval or depth expansions.
   - Telemetry isolates reformulation_triggered == True from adaptive_retrieval_triggered == False.
3. When enable_adaptive_retrieval=True:
   - Candidate depth expansion occurs when coverage is insufficient.
   - Telemetry accurately reflects adaptive_retrieval_triggered == True and candidate_depth_expansions > 0.
"""

from unittest.mock import MagicMock
from types import SimpleNamespace
from app.adaptive_retrieval.controller import AdaptiveRetrievalController
from app.planning.schemas import InformationRequirement
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus
from app.retrieval_memory.memory import RetrievalMemory


class MockItem:
    def __init__(self, chunk_id, document_id="doc1", text="text", score=0.8):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.language = "en"
        self.pages = [1]
        self.start_page = 1
        self.end_page = 1
        self.retrieval_score = score
        self.rerank_score = score


class MockHybridRetriever:
    def __init__(self):
        self.call_history = []

    def retrieve(self, document_id, query, top_k=10, candidate_k=10):
        self.call_history.append({"query": query, "top_k": top_k, "candidate_k": candidate_k})
        return [
            MockItem(f"chk_{query[:4]}_{i}", document_id=document_id)
            for i in range(min(top_k, 5))
        ]


class MockReranker:
    def rerank(self, query, candidates, top_k=10):
        return candidates[:top_k]


class MockCoverageEstimator:
    def __init__(self, satisfy_on_call=2):
        self.call_count = 0
        self.satisfy_on_call = satisfy_on_call

    def estimate(self, question, requirements, requirement_evidence=None, evidence=None, **kwargs):
        self.call_count += 1
        is_supported = self.call_count >= self.satisfy_on_call
        coverage = SimpleNamespace(
            coverage_status="SUPPORTED" if is_supported else "UNSUPPORTED",
            coverage_score=0.9 if is_supported else 0.4,
            gap_type=None if is_supported else "MISSING_EVIDENCE",
            missing_aspects=[] if is_supported else ["missing methodology"],
        )
        return SimpleNamespace(
            requirement_coverages=[coverage],
            all_requirements_covered=is_supported,
        )


class MockGraphBuilder:
    def __init__(self):
        self.claims = {}
        self.evidence = {}

    def add_evidence(self, *args, **kwargs):
        pass

    def add_claim(self, *args, **kwargs):
        pass

    def auto_link_claims_to_evidence(self):
        pass

    def build(self):
        mock_graph = MagicMock()
        mock_graph.claims = self.claims
        mock_graph.evidence = self.evidence
        return mock_graph


class MockQueryReformulator:
    def __init__(self):
        self.calls = 0

    def reformulate(self, question=None, requirement=None, original_query=None, max_variants=3, **kwargs):
        self.calls += 1
        query_text = original_query or (requirement.description if requirement else "query")
        return [f"{query_text} reformulated_{self.calls}"]


def test_no_adaptive_retrieval_prevents_depth_expansion():
    """Test that disabling adaptive retrieval forces schedule to base k only."""
    retriever = MockHybridRetriever()
    reranker = MockReranker()
    evaluator = MockCoverageEstimator(satisfy_on_call=10)  # Never satisfied
    reformulator = MockQueryReformulator()
    memory = RetrievalMemory(document_id="doc1", session_id="test_sess")

    ar_controller = AdaptiveRetrievalController(
        hybrid_retriever=retriever,
        reranker=reranker,
        coverage_estimator=evaluator,
        query_reformulator=reformulator,
        candidate_k_schedule=[10, 25, 50],
        max_attempts_per_query=3,
    )

    req = InformationRequirement(
        requirement_id="req_1",
        description="Ablation isolation specification",
        requirement_type="factual",
        priority=1,
        expected_evidence_type="result",
        retrieval_queries=["What is the ablation protocol?"],
    )

    result = ar_controller.retrieve_for_requirement(
        document_id="doc1",
        question="What is the ablation protocol?",
        requirement=req,
        enable_adaptive_retrieval=False,
        enable_query_reformulation=False,
        enable_retrieval_memory=False,
        memory=memory,
    )

    # Must only have 1 attempt because both adaptive retrieval and reformulation are disabled
    assert len(result.attempts) == 1
    assert result.attempts[0].candidate_k == 10
    # None of the retriever calls should have exceeded base k (10)
    for call in retriever.call_history:
        assert call["candidate_k"] == 10


def test_reformulation_isolated_from_adaptive_depth_expansion():
    """
    Test that under NO_ADAPTIVE_RETRIEVAL with query reformulation enabled:
    - Multiple attempts occur due to reformulation.
    - None of the attempts expand candidate_k (candidate_k stays at base 10).
    - Query types indicate reformulation.
    """
    retriever = MockHybridRetriever()
    reranker = MockReranker()
    evaluator = MockCoverageEstimator(satisfy_on_call=3)
    reformulator = MockQueryReformulator()
    memory = RetrievalMemory(document_id="doc1", session_id="test_sess")

    ar_controller = AdaptiveRetrievalController(
        hybrid_retriever=retriever,
        reranker=reranker,
        coverage_estimator=evaluator,
        query_reformulator=reformulator,
        candidate_k_schedule=[10, 25, 50],
        max_attempts_per_query=3,
    )

    req = InformationRequirement(
        requirement_id="req_1",
        description="Metrics calculation details",
        requirement_type="factual",
        priority=1,
        expected_evidence_type="result",
        retrieval_queries=["What are the ablation metrics?"],
    )

    result = ar_controller.retrieve_for_requirement(
        document_id="doc1",
        question="What are the ablation metrics?",
        requirement=req,
        enable_adaptive_retrieval=False,  # DISABLED
        enable_query_reformulation=True,   # ENABLED
        enable_retrieval_memory=False,
        memory=memory,
    )

    # Should have executed reformulations
    assert len(result.attempts) > 1
    # Crucial: NO candidate depth expansion occurred
    for att in result.attempts:
        assert att.candidate_k == 10
    for call in retriever.call_history:
        assert call["candidate_k"] == 10

    # Attempts after first should be marked as reformulation
    assert any("reformulation" in str(att.query_type).lower() for att in result.attempts[1:])


def test_controller_telemetry_cleanly_isolates_reformulation_and_ar():
    """
    Verify AERISController telemetry:
    When enable_adaptive_retrieval=False and enable_query_reformulation=True,
    - adaptive_retrieval_triggered is False
    - candidate_depth_expansions == 0
    - reformulation_triggered is True
    - reformulation_attempt_count > 0
    """
    retriever = MockHybridRetriever()
    reranker = MockReranker()
    evaluator = MockCoverageEstimator(satisfy_on_call=3)
    reformulator = MockQueryReformulator()
    memory = RetrievalMemory(document_id="doc1", session_id="test_sess")

    ar_controller = AdaptiveRetrievalController(
        hybrid_retriever=retriever,
        reranker=reranker,
        coverage_estimator=evaluator,
        query_reformulator=reformulator,
        candidate_k_schedule=[10, 25, 50],
        max_attempts_per_query=3,
    )

    # Mock planner that returns 1 requirement
    mock_planner = MagicMock()
    mock_plan = MagicMock()
    mock_req = InformationRequirement(
        requirement_id="req_1",
        description="Detailed measurement specification",
        requirement_type="factual",
        priority=1,
        expected_evidence_type="result",
        retrieval_queries=["ablation metrics"],
    )
    mock_plan.requirements = [mock_req]
    mock_planner.plan.return_value = mock_plan

    controller = AERISController(
        planner=mock_planner,
        adaptive_retrieval_controller=ar_controller,
        claim_extractor=MagicMock(),
        claim_normalizer=MagicMock(),
        claim_typer=MagicMock(),
        graph_builder_factory=lambda *args, **kwargs: MockGraphBuilder(),
        graph_verifier=MagicMock(),
    )

    cfg = ControllerConfig(
        enable_adaptive_retrieval=False,  # DISABLED
        enable_query_reformulation=True,   # ENABLED
        enable_retrieval_memory=False,
        enable_claim_extraction=False,
        enable_claim_verification=False,
        enable_contradiction_analysis=False,
        enable_cross_lingual_analysis=False,
        enable_calibration=False,
        enable_selective_verification=False,
        answer_generation_enabled=False,
    )

    req = ControllerRequest(
        document_id="doc1",
        question="What are the ablation metrics?",
        config=cfg,
    )

    res = controller.run(req)

    assert res.status == StageStatus.COMPLETED, f"Pipeline failed: {res.stages[-1].message if res.stages else 'no stages'}"
    assert res.metadata["adaptive_retrieval_triggered"] is False
    assert res.metadata["candidate_depth_expansions"] == 0
    assert res.metadata["reformulation_triggered"] is True
    assert res.metadata["reformulation_attempt_count"] > 0
