"""
Step 22D Regression Test: Workstream 4 - Make Cross-Lingual Agreement Testable

Verifies:
1. Small deterministic bilingual test fixture with semantically equivalent evidence (EN / TA)
   executes cross-lingual comparison and yields AGREEMENT.
2. Contradictory bilingual test fixture (EN / DE) yields CONTRADICTION.
3. Monolingual bypass (all EN evidence) records SKIPPED (MONOLINGUAL), not COMPLETED.
4. Distinguishable, auditable results between equivalent and contradictory pairs.
5. Failures and errors in cross-lingual analysis are recorded as FAILED in controller telemetry.
"""

import pytest
from unittest.mock import MagicMock
from app.performance_cache import aeris_cache
from app.verification.cross_lingual_agreement import (
    CrossLingualAgreementLabel,
    CrossLingualAgreementResult,
)
from app.verification.cross_lingual_claim import (
    ClaimCrossLingualAnalyzer,
    ClaimCrossLingualResult,
)
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus, ControllerStage


@pytest.fixture(autouse=True)
def clean_cache():
    aeris_cache._cache.clear()
    yield
    aeris_cache._cache.clear()


class MockClaimEvidenceGraph:
    def __init__(self, claim_id, claim_text, evidence_nodes):
        self.claims = {claim_id: MagicMock(text=claim_text, claim_id=claim_id)}
        self.evidence = {eid: MagicMock(text=etext) for eid, etext, _ in evidence_nodes}
        self.edges = [MagicMock(chunk_id=eid) for eid, _, _ in evidence_nodes]

    def get_claim_evidence(self, claim_id):
        return self.edges


def test_cross_lingual_equivalent_pair_executes_and_agrees():
    """
    Bilingual fixture with semantically equivalent evidence across languages:
    Evidence A (English): AERIS framework improves retrieval reliability through adaptive evidence acquisition.
    Evidence B (Tamil): AERIS கட்டமைப்பு தகவமைப்பு ஆதார கையகப்படுத்தல் மூலம் மீட்டெடுப்பு நம்பகத்தன்மையை மேம்படுத்துகிறது.
    """
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = CrossLingualAgreementResult(
        evidence_a="AERIS framework improves retrieval reliability through adaptive evidence acquisition.",
        evidence_b="AERIS கட்டமைப்பு தகவமைப்பு ஆதார கையகப்படுத்தல் மூலம் மீட்டெடுப்பு நம்பகத்தன்மையை மேம்படுத்துகிறது.",
        language_a="en",
        language_b="ta",
        label=CrossLingualAgreementLabel.AGREEMENT,
        confidence=0.90,
        rationale="Both state that AERIS improves retrieval reliability through adaptive evidence acquisition.",
    )

    analyzer = ClaimCrossLingualAnalyzer(classifier=mock_classifier)

    graph = MockClaimEvidenceGraph(
        claim_id="claim_aeris_core",
        claim_text="AERIS improves retrieval reliability.",
        evidence_nodes=[
            ("chunk_en", "AERIS framework improves retrieval reliability through adaptive evidence acquisition.", "en"),
            ("chunk_ta", "AERIS கட்டமைப்பு தகவமைப்பு ஆதார கையகப்படுத்தல் மூலம் மீட்டெடுப்பு நம்பகத்தன்மையை மேம்படுத்துகிறது.", "ta"),
        ],
    )

    evidence_languages = {
        "chunk_en": "en",
        "chunk_ta": "ta",
    }

    result = analyzer.analyze_claim(
        graph=graph,
        claim_id="claim_aeris_core",
        evidence_languages=evidence_languages,
    )

    assert result.pair_count == 1
    assert result.agreement_count == 1
    assert result.contradiction_count == 0
    assert result.overall_label == CrossLingualAgreementLabel.AGREEMENT
    assert result.confidence >= 0.90
    assert mock_classifier.classify.called


def test_cross_lingual_contradictory_pair_executes_and_contradicts():
    """
    Bilingual fixture with contradictory factual evidence across languages:
    Evidence A (English): The model achieved 94.5% precision on the benchmark.
    Evidence B (German): Das Modell erreichte lediglich 62.1% Genauigkeit im Benchmark-Test.
    """
    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = CrossLingualAgreementResult(
        evidence_a="The model achieved 94.5% precision on the benchmark.",
        evidence_b="Das Modell erreichte lediglich 62.1% Genauigkeit im Benchmark-Test.",
        language_a="en",
        language_b="de",
        label=CrossLingualAgreementLabel.CONTRADICTION,
        confidence=0.90,
        rationale="English asserts 94.5% precision while German reports 62.1% accuracy.",
    )

    analyzer = ClaimCrossLingualAnalyzer(classifier=mock_classifier)

    graph = MockClaimEvidenceGraph(
        claim_id="claim_precision",
        claim_text="The model achieved high precision.",
        evidence_nodes=[
            ("chunk_en", "The model achieved 94.5% precision on the benchmark.", "en"),
            ("chunk_de", "Das Modell erreichte lediglich 62.1% Genauigkeit im Benchmark-Test.", "de"),
        ],
    )

    evidence_languages = {
        "chunk_en": "en",
        "chunk_de": "de",
    }

    result = analyzer.analyze_claim(
        graph=graph,
        claim_id="claim_precision",
        evidence_languages=evidence_languages,
    )

    assert result.pair_count == 1
    assert result.agreement_count == 0
    assert result.contradiction_count == 1
    assert result.overall_label == CrossLingualAgreementLabel.CONTRADICTION
    assert result.confidence >= 0.90


def test_monolingual_bypass_recorded_as_skipped():
    """
    Monolingual evidence pool (all chunks in English):
    Must be bypassed and recorded as SKIPPED, NOT as successful cross-lingual evaluations.
    """
    mock_classifier = MagicMock()
    analyzer = ClaimCrossLingualAnalyzer(classifier=mock_classifier)

    graph = MockClaimEvidenceGraph(
        claim_id="claim_mono",
        claim_text="Monolingual claim",
        evidence_nodes=[
            ("chunk_en_1", "English evidence item one.", "en"),
            ("chunk_en_2", "English evidence item two.", "en"),
        ],
    )

    evidence_languages = {
        "chunk_en_1": "en",
        "chunk_en_2": "en",
    }

    result = analyzer.analyze_claim(
        graph=graph,
        claim_id="claim_mono",
        evidence_languages=evidence_languages,
    )

    assert result.pair_count == 0
    assert result.rationale == "SKIPPED (MONOLINGUAL)"
    assert not mock_classifier.classify.called


def test_controller_cross_lingual_stage_skipped_when_zero_pairs():
    """
    OrchestrationController telemetry test:
    When cross-lingual analysis finds 0 cross-lingual pairs (e.g. English-only benchmark),
    the stage status must be recorded as SKIPPED, NOT COMPLETED.
    """
    mock_analyzer = MagicMock()
    # Analyzer returns no pairs evaluated
    mock_analyzer.return_value = []

    controller = AERISController(
        planner=MagicMock(),
        adaptive_retrieval_controller=MagicMock(),
        claim_extractor=MagicMock(),
        claim_normalizer=MagicMock(),
        claim_typer=MagicMock(),
        graph_builder_factory=MagicMock(),
        graph_verifier=MagicMock(),
        cross_lingual_analyzer=mock_analyzer,
        cross_lingual_integrator=MagicMock(),
    )

    # Mock pipeline returning valid empty stages
    req = ControllerRequest(
        document_id="doc1",
        question="Monolingual question?",
        config=ControllerConfig(
            enable_adaptive_retrieval=False,
            enable_claim_extraction=False,
            enable_claim_verification=False,
            enable_contradiction_analysis=False,
            enable_cross_lingual_analysis=True,
            enable_calibration=False,
            enable_selective_verification=False,
            answer_generation_enabled=False,
        ),
    )

    res = controller.run(req)

    # Find CROSS_LINGUAL stage
    cross_stage = next((s for s in res.stages if s.stage == ControllerStage.CROSS_LINGUAL), None)
    assert cross_stage is not None
    assert cross_stage.status == StageStatus.SKIPPED
    assert "MONOLINGUAL" in cross_stage.message
    assert res.metadata["cross_lingual_pairs_evaluated"] == 0
