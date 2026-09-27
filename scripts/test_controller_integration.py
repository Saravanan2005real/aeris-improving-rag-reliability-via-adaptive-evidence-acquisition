import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.planning.requirement_planner import RequirementPlanner
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.coverage.evidence_coverage import EvidenceCoverageEstimator
from app.adaptive_retrieval.controller import AdaptiveRetrievalController

from app.claim_extraction.extractor import ClaimExtractor
from app.claim_extraction.normalizer import ClaimNormalizer
from app.claim_extraction.typer import ClaimTyper

from app.claim_graph.graph import ClaimEvidenceGraphBuilder

from app.verification.claim_verifier import ClaimVerifier
from app.verification.graph_verifier import GraphClaimVerifier

from app.verification.contradiction_graph import ContradictionGraphIntegrator
from app.verification.cross_claim_contradiction import CrossClaimContradictionAnalyzer

from app.verification.cross_lingual_agreement import CrossLingualEvidenceClassifier
from app.verification.cross_lingual_claim import ClaimCrossLingualAnalyzer
from app.verification.cross_lingual_graph import CrossLingualGraphIntegrator

from app.calibration.calibrator import ConfidenceCalibrator
from app.verification.selective_verification import SelectiveVerificationSelector
from app.verification.selective_executor import SelectiveVerificationExecutor

from app.answer_generation.answer_generator import AnswerGenerator
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus

class RealCrossLingualAnalyzer:
    def __init__(self):
        self.classifier = CrossLingualEvidenceClassifier()
        self.analyzer = ClaimCrossLingualAnalyzer(classifier=self.classifier)

    def __call__(self, graph_builder):
        results = []
        languages = {}
        # Simple heuristic to grab language if available, else 'English'
        for chunk_id, ev in graph_builder.evidence.items():
            languages[chunk_id] = getattr(ev, "language", "English")

        for claim_id in graph_builder.claims.keys():
            if not graph_builder.get_claim_evidence(claim_id):
                continue
                
            result = self.analyzer.analyze_claim(
                graph_builder,
                claim_id,
                evidence_languages=languages
            )
            if result.pair_count > 0:
                pairs = []
                for p in result.pair_results:
                    pairs.append({
                        "evidence_a_chunk_id": p.evidence_a_chunk_id,
                        "evidence_b_chunk_id": p.evidence_b_chunk_id,
                        "label": p.label.value,
                        "confidence": p.confidence,
                        "rationale": p.rationale,
                        "source_claim_a_id": claim_id,
                        "source_claim_b_id": claim_id,
                    })
                results.append((result, pairs))
        return results


def build_real_controller():
    print("  -> Initializing Planner")
    planner = RequirementPlanner()
    
    print("  -> Initializing Retrieval Components")
    hybrid = HybridRetriever()
    reranker = Reranker()
    coverage_estimator = EvidenceCoverageEstimator()
    
    adaptive_retrieval_controller = AdaptiveRetrievalController(
        hybrid_retriever=hybrid,
        reranker=reranker,
        coverage_estimator=coverage_estimator,
        candidate_k_schedule=[10, 25, 50],
        rerank_top_k=5,
        max_attempts_per_query=3,
        support_threshold=0.70,
    )

    print("  -> Initializing Extraction Components")
    extractor = ClaimExtractor()
    normalizer = ClaimNormalizer()
    typer = ClaimTyper()

    print("  -> Initializing Graph Components")
    def graph_builder_factory(document_id):
        return ClaimEvidenceGraphBuilder(document_id=document_id)

    print("  -> Initializing Verification Components")
    verifier = ClaimVerifier()
    graph_verifier = GraphClaimVerifier(verifier)

    print("  -> Initializing Contradiction Components")
    contradiction_analyzer = CrossClaimContradictionAnalyzer()
    contradiction_integrator = ContradictionGraphIntegrator()

    print("  -> Initializing Cross-Lingual Components")
    cross_lingual_analyzer = RealCrossLingualAnalyzer()
    cross_lingual_integrator = CrossLingualGraphIntegrator()

    print("  -> Initializing Calibration & Selective Verification Components")
    calibrator = ConfidenceCalibrator()
    selective_selector = SelectiveVerificationSelector()
    selective_executor = SelectiveVerificationExecutor(
        verifier=graph_verifier,
        selector=selective_selector
    )
    answer_generator = AnswerGenerator()

    return AERISController(
        planner=planner,
        adaptive_retrieval_controller=adaptive_retrieval_controller,
        claim_extractor=extractor,
        claim_normalizer=normalizer,
        claim_typer=typer,
        graph_builder_factory=graph_builder_factory,
        graph_verifier=graph_verifier,
        contradiction_analyzer=contradiction_analyzer.analyze,
        contradiction_integrator=contradiction_integrator,
        cross_lingual_analyzer=cross_lingual_analyzer,
        cross_lingual_integrator=cross_lingual_integrator,
        calibrator=calibrator,
        selective_verification_executor=selective_executor,
        answer_generator=answer_generator,
    )

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_controller_integration.py <document_id> \"<question>\"")
        sys.exit(1)

    document_id = sys.argv[1]
    question = sys.argv[2]

    print("=" * 80)
    print("STEP 19C — FULL AERIS CONTROLLER INTEGRATION TEST")
    print("=" * 80)

    print("Building controller with real dependencies...")
    controller = build_real_controller()

    request = ControllerRequest(
        document_id=document_id,
        question=question,
        config=ControllerConfig(
            verification_budget=3,
            enable_contradiction_analysis=True,
            enable_cross_lingual_analysis=True,
            enable_calibration=True,
            enable_selective_verification=True,
        )
    )

    print(f"\nDocument ID : {document_id}")
    print(f"Question    : {question}")
    
    print("\nRunning controller (this may take a while)...")
    result = controller.run(request)

    print("\n" + "=" * 80)
    print("CONTROLLER RESULTS")
    print("=" * 80)
    
    print(f"Status                  : {result.status.value}")
    print(f"Final Answer            : {result.final_answer}")
    print(f"Total Claims            : {result.claim_count}")
    print(f"Total Evidence          : {result.evidence_count}")
    print(f"Verified Claims         : {result.verified_claim_count}")
    print(f"Selected (budget-aware) : {result.selected_verification_count}")
    print("\nMetadata:")
    for k, v in result.metadata.items():
        print(f"  {k}: {v}")

    print("\nStage Pipeline Log:")
    for stage in result.stages:
        print(f"  [{stage.stage.value}] -> {stage.status.value}: {stage.message} (output: {stage.output_count})")

    if result.status == StageStatus.FAILED:
        sys.exit(1)

if __name__ == "__main__":
    main()
