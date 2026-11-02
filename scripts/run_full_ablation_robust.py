import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.planning.requirement_planner import RequirementPlanner
from app.adaptive_retrieval.controller import AdaptiveRetrievalController
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.coverage.evidence_coverage import EvidenceCoverageEstimator
from app.adaptive_retrieval.query_reformulator import QueryReformulator
from app.retrieval_memory.memory import RetrievalMemory

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
from app.ablation.runner import AblationRunner


class RealCrossLingualAnalyzer:
    def __init__(self):
        self.classifier = CrossLingualEvidenceClassifier()
        self.analyzer = ClaimCrossLingualAnalyzer(classifier=self.classifier)

    def __call__(self, graph_builder):
        results = []
        languages = {}
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
    print("Initializing Controller Components...")
    planner = RequirementPlanner()
    hybrid = HybridRetriever()
    reranker = Reranker()
    coverage_estimator = EvidenceCoverageEstimator()
    query_reformulator = QueryReformulator()
    
    adaptive_retrieval_controller = AdaptiveRetrievalController(
        hybrid_retriever=hybrid,
        reranker=reranker,
        coverage_estimator=coverage_estimator,
        query_reformulator=query_reformulator,
        candidate_k_schedule=[10, 25, 50],
        rerank_top_k=5,
        max_attempts_per_query=3,
        support_threshold=0.70,
    )

    extractor = ClaimExtractor()
    normalizer = ClaimNormalizer()
    typer = ClaimTyper()

    def graph_builder_factory(document_id):
        return ClaimEvidenceGraphBuilder(document_id=document_id)

    verifier = ClaimVerifier()
    graph_verifier = GraphClaimVerifier(verifier)

    contradiction_analyzer = CrossClaimContradictionAnalyzer()
    contradiction_integrator = ContradictionGraphIntegrator()

    cross_lingual_analyzer = RealCrossLingualAnalyzer()
    cross_lingual_integrator = CrossLingualGraphIntegrator()

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
    print("==================================================")
    print("AERIS-RAG ABLATION EXPERIMENT RUNNER (ROBUST)")
    print("==================================================")
    
    start_idx = 0
    end_idx = None
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_idx = int(sys.argv[2])
        
    print(f"Batch Range: {start_idx} to {end_idx}")
    
    import app.utils.diagnostics as diag
    diag.DIAGNOSTICS_FILE = "data/results/generation_diagnostics_full_robust.jsonl"
    
    from app.ablation.schemas import AblationVariant
    from app.benchmark.dataset import BenchmarkDataset
    dataset = BenchmarkDataset("data/benchmark/aeris_benchmark.json")
    
    # Validation at startup
    expected_variants = len(list(AblationVariant))
    expected_questions = len(dataset.records)
    expected_runs = expected_variants * expected_questions
    
    print(f"Verification at startup:")
    print(f"  Expected Runs: {expected_runs}")
    print(f"  Variants: {expected_variants}")
    print(f"  Questions: {expected_questions}")
    print(f"  Unique pairs expected: {expected_runs}")
    
    if expected_runs != 224 or expected_variants != 8 or expected_questions != 28:
        print("ERROR: Startup validation failed!")
        sys.exit(1)
        
    # Isolate cache
    from app.performance_cache import aeris_cache
    aeris_cache.cache_file = "data/aeris_cache_full_robust.json"
    
    controller = build_real_controller()
    runner = AblationRunner(controller)
    
    benchmark_path = "data/benchmark/aeris_benchmark.json"
    output_path = "data/results/ablation_results_full_robust.json"
    
    runner.run_experiment(benchmark_path, output_path, start_idx, end_idx)
    
    # After run validation
    import json
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            results = json.load(f)
            
        total_records = len(results)
        unique_pairs = set((r["variant"], r["question_id"]) for r in results)
        
        q_counts = {}
        v_counts = {}
        for r in results:
            v, q = r["variant"], r["question_id"]
            q_counts[q] = q_counts.get(q, 0) + 1
            v_counts[v] = v_counts.get(v, 0) + 1
            
        print("\nVerification at completion:")
        print(f"  Total records: {total_records}")
        print(f"  Unique pairs: {len(unique_pairs)}")
        print(f"  Duplicate pairs: {total_records - len(unique_pairs)}")
        print(f"  Are all variants having 28 questions? {all(c == 28 for c in v_counts.values())}")
        print(f"  Are all questions having 8 variants? {all(c == 8 for c in q_counts.values())}")

if __name__ == "__main__":
    main()
