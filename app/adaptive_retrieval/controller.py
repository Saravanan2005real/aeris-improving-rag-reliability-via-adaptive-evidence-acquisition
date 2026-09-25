from typing import Dict, List

from app.coverage.evidence_coverage import (
    EvidenceCoverageEstimator,
    EvidenceItem,
)
from app.planning.schemas import InformationRequirement
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker

from app.adaptive_retrieval.schemas import (
    AdaptiveRetrievalResult,
    RetrievalAttempt,
)
from app.adaptive_retrieval.query_reformulator import QueryReformulator


class AdaptiveRetrievalController:
    """
    Adaptive evidence acquisition controller.

    Strategy:
        1. Retrieve with an initial candidate pool.
        2. Rerank the retrieved evidence.
        3. Estimate evidence coverage.
        4. Stop if the requirement is sufficiently supported.
        5. Otherwise expand the candidate pool.
        6. Repeat until the maximum retrieval depth is reached.

    This first implementation intentionally keeps the adaptation policy
    simple and deterministic. Query reformulation and evidence
    diversification can be added as later extensions.
    """

    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        reranker: Reranker,
        coverage_estimator: EvidenceCoverageEstimator,
        query_reformulator: QueryReformulator | None = None,
        candidate_k_schedule: List[int] | None = None,
        rerank_top_k: int = 5,
        max_attempts_per_query: int | None = None,
        max_query_variants: int = 3,
        support_threshold: float = 0.70,
    ):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.coverage_estimator = coverage_estimator
        self.query_reformulator = query_reformulator or QueryReformulator()

        self.candidate_k_schedule = (
            candidate_k_schedule
            if candidate_k_schedule is not None
            else [10, 25, 50]
        )

        self.rerank_top_k = rerank_top_k

        self.max_attempts_per_query = (
            max_attempts_per_query
            if max_attempts_per_query is not None
            else len(self.candidate_k_schedule)
        )
        
        self.max_query_variants = max_query_variants

        self.support_threshold = support_threshold

    def _is_sufficient(
        self,
        status: str | None,
        score: float | None,
    ) -> bool:
        """
        Determine whether the current evidence is sufficient to stop.
        """

        if status == "SUPPORTED":
            return True

        if score is not None and score >= self.support_threshold:
            return True

        return False

    def _build_evidence_items(
        self,
        reranked_items,
    ) -> List[EvidenceItem]:
        """
        Convert reranker results into EvidenceItem objects expected
        by the Step 9 coverage estimator.
        """

        evidence_items = []

        for item in reranked_items:
            evidence_items.append(
                EvidenceItem(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    text=item.text,
                    language=item.language,
                    pages=item.pages,
                    start_page=item.start_page,
                    end_page=item.end_page,
                    retrieval_score=item.retrieval_score,
                    rerank_score=item.rerank_score,
                )
            )

        return evidence_items

    def retrieve_for_requirement(
        self,
        document_id: str,
        question: str,
        requirement: InformationRequirement,
    ) -> AdaptiveRetrievalResult:
        """
        Perform adaptive retrieval for one information requirement.
        """

        if not requirement.retrieval_queries:
            return AdaptiveRetrievalResult(
                requirement_id=requirement.requirement_id,
                original_query=requirement.description,
                final_query=requirement.description,
                final_candidate_k=0,
                total_unique_chunks=0,
                final_coverage_status="UNSUPPORTED",
                final_coverage_score=0.0,
                success=False,
                stop_reason="No retrieval queries available.",
            )

        original_query = requirement.retrieval_queries[0]
        queries_to_try = [(original_query, "original")]

        attempts: List[RetrievalAttempt] = []
        all_evidence: Dict[str, EvidenceItem] = {}

        final_status = "UNSUPPORTED"
        final_score = 0.0
        final_candidate_k = 0
        stop_reason = "Maximum adaptive retrieval depth reached."
        global_attempt_number = 1
        success = False
        final_query = original_query

        for query_idx, (current_query, query_type) in enumerate(queries_to_try):
            query_sufficient = False
            
            for attempt_number, candidate_k in enumerate(
                self.candidate_k_schedule[: self.max_attempts_per_query],
                start=1,
            ):

                final_candidate_k = candidate_k
                final_query = current_query

                # ---------------------------------------------------------
                # 1. Hybrid retrieval
                # ---------------------------------------------------------

                candidates = self.hybrid_retriever.retrieve(
                    document_id=document_id,
                    query=current_query,
                    top_k=candidate_k,
                    candidate_k=candidate_k,
                )

                # ---------------------------------------------------------
                # 2. Cross-encoder reranking
                # ---------------------------------------------------------

                reranked = self.reranker.rerank(
                    current_query,
                    candidates,
                    top_k=self.rerank_top_k,
                )

                # ---------------------------------------------------------
                # 3. Convert evidence
                # ---------------------------------------------------------

                evidence_items = self._build_evidence_items(
                    reranked
                )

                # ---------------------------------------------------------
                # 4. Add newly discovered evidence
                # ---------------------------------------------------------

                new_chunk_ids = []

                for evidence in evidence_items:
                    if evidence.chunk_id not in all_evidence:
                        all_evidence[evidence.chunk_id] = evidence
                        new_chunk_ids.append(evidence.chunk_id)

                # ---------------------------------------------------------
                # 5. Evaluate coverage
                # ---------------------------------------------------------

                coverage_result = self.coverage_estimator.estimate(
                    question=question,
                    requirements=[requirement],
                    requirement_evidence={
                        requirement.requirement_id: list(
                            all_evidence.values()
                        )
                    },
                )

                requirement_coverage = (
                    coverage_result.requirement_coverages[0]
                )

                final_status = requirement_coverage.coverage_status
                final_score = requirement_coverage.coverage_score

                # ---------------------------------------------------------
                # 6. Determine stopping condition
                # ---------------------------------------------------------

                sufficient = self._is_sufficient(
                    final_status,
                    final_score,
                )

                attempt = RetrievalAttempt(
                    attempt_number=global_attempt_number,
                    requirement_id=requirement.requirement_id,
                    query=current_query,
                    query_type=query_type,
                    candidate_k=candidate_k,
                    rerank_top_k=self.rerank_top_k,
                    retrieved_chunk_ids=[
                        item.chunk_id for item in reranked
                    ],
                    new_chunk_ids=new_chunk_ids,
                    coverage_status=final_status,
                    coverage_score=final_score,
                    stopped=sufficient,
                    stop_reason=(
                        "Evidence requirement sufficiently supported."
                        if sufficient
                        else None
                    ),
                )

                attempts.append(attempt)
                global_attempt_number += 1

                if sufficient:
                    stop_reason = (
                        "Evidence requirement sufficiently supported."
                    )
                    query_sufficient = True
                    success = True
                    break

            if query_sufficient:
                break
                
            if query_type == "original" and not query_sufficient:
                reformulated = self.query_reformulator.reformulate(
                    question=question,
                    requirement=requirement,
                    original_query=original_query,
                    max_variants=self.max_query_variants,
                )
                for i, r_query in enumerate(reformulated, start=1):
                    queries_to_try.append((r_query, f"reformulation_{i}"))

        all_chunk_ids = list(all_evidence.keys())

        return AdaptiveRetrievalResult(
            requirement_id=requirement.requirement_id,
            original_query=requirement.description,
            final_query=final_query,
            attempts=attempts,
            all_chunk_ids=all_chunk_ids,
            final_candidate_k=final_candidate_k,
            total_unique_chunks=len(all_chunk_ids),
            final_coverage_status=final_status,
            final_coverage_score=final_score,
            success=success,
            stop_reason=stop_reason,
        )
