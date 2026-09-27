from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

from app.controller.schemas import (
    ControllerConfig,
    ControllerRequest,
    ControllerResult,
    ControllerStage,
    ControllerStageResult,
    StageStatus,
)


class AERISController:
    """
    Step 19B — End-to-end AERIS orchestration layer.

    This class coordinates the already validated AERIS components.
    It intentionally does not reimplement retrieval, verification,
    contradiction detection, multilingual analysis, or calibration.
    """

    def __init__(
        self,
        planner,
        adaptive_retrieval_controller,
        claim_extractor,
        claim_normalizer,
        claim_typer,
        graph_builder_factory,
        graph_verifier,
        contradiction_analyzer=None,
        contradiction_integrator=None,
        cross_lingual_analyzer=None,
        cross_lingual_integrator=None,
        calibrator=None,
        selective_verification_executor=None,
        answer_generator=None,
    ):
        self.planner = planner
        self.adaptive_retrieval_controller = adaptive_retrieval_controller

        self.claim_extractor = claim_extractor
        self.claim_normalizer = claim_normalizer
        self.claim_typer = claim_typer

        self.graph_builder_factory = graph_builder_factory
        self.graph_verifier = graph_verifier

        self.contradiction_analyzer = contradiction_analyzer
        self.contradiction_integrator = contradiction_integrator

        self.cross_lingual_analyzer = cross_lingual_analyzer
        self.cross_lingual_integrator = cross_lingual_integrator

        self.calibrator = calibrator
        self.selective_verification_executor = selective_verification_executor
        self.answer_generator = answer_generator

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, request: ControllerRequest) -> ControllerResult:
        stages: List[ControllerStageResult] = []

        try:
            # ----------------------------------------------------------
            # 1. PLANNING
            # ----------------------------------------------------------

            plan = self.planner.plan(request.question)

            stages.append(
                self._stage(
                    ControllerStage.PLANNING,
                    StageStatus.COMPLETED,
                    "Information requirements generated.",
                    len(plan.requirements),
                )
            )

            # ----------------------------------------------------------
            # 2. ADAPTIVE RETRIEVAL
            # ----------------------------------------------------------

            retrieval_results = []

            for requirement in plan.requirements:
                result = (
                    self.adaptive_retrieval_controller
                    .retrieve_for_requirement(
                        document_id=request.document_id,
                        question=request.question,
                        requirement=requirement,
                    )
                )

                retrieval_results.append(result)

            evidence_items = self._collect_evidence(
                retrieval_results
            )

            stages.append(
                self._stage(
                    ControllerStage.RETRIEVAL,
                    StageStatus.COMPLETED,
                    "Adaptive requirement-directed retrieval completed.",
                    len(evidence_items),
                )
            )

            # ----------------------------------------------------------
            # 3. COVERAGE
            #
            # Coverage is already executed inside the adaptive
            # retrieval controller. We expose the resulting evidence
            # acquisition state here rather than running the estimator
            # a second time.
            # ----------------------------------------------------------

            coverage_metadata = self._collect_coverage_metadata(
                retrieval_results
            )

            stages.append(
                self._stage(
                    ControllerStage.COVERAGE,
                    StageStatus.COMPLETED,
                    "Evidence coverage evaluated during adaptive retrieval.",
                    len(evidence_items),
                    coverage_metadata,
                )
            )

            # ----------------------------------------------------------
            # 4. CLAIM EXTRACTION
            # ----------------------------------------------------------

            raw_claims = []

            for evidence in evidence_items:
                extraction = self.claim_extractor.extract(
                    chunk_id=evidence["chunk_id"],
                    document_id=request.document_id,
                    text=evidence["text"],
                )

                claims = getattr(extraction, "claims", [])

                raw_claims.extend(claims)

            # ----------------------------------------------------------
            # 5. CLAIM NORMALIZATION
            # ----------------------------------------------------------

            normalized_claims = (
                self.claim_normalizer.normalize_and_deduplicate(
                    raw_claims
                )
            )

            # ----------------------------------------------------------
            # 6. CLAIM TYPING
            # ----------------------------------------------------------

            typed_claims = self.claim_typer.type_claims(
                normalized_claims
            )

            # ----------------------------------------------------------
            # 7. CLAIM-EVIDENCE GRAPH
            # ----------------------------------------------------------

            graph_builder = self.graph_builder_factory(
                request.document_id
            )

            for claim in typed_claims:
                graph_builder.add_claim(
                    claim_id=claim.claim_id,
                    text=claim.text,
                    claim_type=claim.claim_type,
                    source_chunk_id=claim.source_chunk_id,
                )

            for evidence in evidence_items:
                graph_builder.add_evidence(
                    chunk_id=evidence["chunk_id"],
                    text=evidence["text"],
                )

            graph_builder.auto_link_claims_to_evidence()

            stages.append(
                self._stage(
                    ControllerStage.CLAIM_GRAPH,
                    StageStatus.COMPLETED,
                    "Claim-evidence graph constructed.",
                    len(typed_claims),
                )
            )

            # ----------------------------------------------------------
            # 8. INITIAL CLAIM VERIFICATION
            # ----------------------------------------------------------

            verification_results = []

            for claim in typed_claims:
                if not graph_builder.get_claim_evidence(claim.claim_id):
                    continue

                result = self.graph_verifier.verify_claim(
                    graph_builder,
                    claim.claim_id,
                )

                verification_results.append(result)

            verified_count = len(verification_results)

            stages.append(
                self._stage(
                    ControllerStage.VERIFICATION,
                    StageStatus.COMPLETED,
                    "Initial claim verification completed.",
                    verified_count,
                )
            )

            # ----------------------------------------------------------
            # 9. CONTRADICTION ANALYSIS
            # ----------------------------------------------------------

            contradiction_count = 0

            if (
                request.config.enable_contradiction_analysis
                and self.contradiction_analyzer is not None
                and self.contradiction_integrator is not None
            ):
                contradiction_report = (
                    self.contradiction_analyzer(graph_builder)
                )

                self.contradiction_integrator.integrate(
                    graph_builder,
                    contradiction_report,
                )

                contradiction_count = self._count_contradictions(
                    contradiction_report
                )

                stages.append(
                    self._stage(
                        ControllerStage.CONTRADICTION,
                        StageStatus.COMPLETED,
                        "Contextual contradiction analysis completed.",
                        contradiction_count,
                    )
                )
            else:
                stages.append(
                    self._stage(
                        ControllerStage.CONTRADICTION,
                        StageStatus.SKIPPED,
                        "Contradiction analysis was not configured.",
                        0,
                    )
                )

            # ----------------------------------------------------------
            # 10. CROSS-LINGUAL ANALYSIS
            # ----------------------------------------------------------

            cross_lingual_count = 0

            if (
                request.config.enable_cross_lingual_analysis
                and self.cross_lingual_analyzer is not None
                and self.cross_lingual_integrator is not None
            ):
                cross_lingual_results = (
                    self.cross_lingual_analyzer(graph_builder)
                )

                for result, evidence_pairs in cross_lingual_results:
                    self.cross_lingual_integrator.integrate(
                        graph_builder,
                        result,
                        evidence_pairs,
                    )

                    cross_lingual_count += 1

                stages.append(
                    self._stage(
                        ControllerStage.CROSS_LINGUAL,
                        StageStatus.COMPLETED,
                        "Cross-lingual evidence analysis completed.",
                        cross_lingual_count,
                    )
                )
            else:
                stages.append(
                    self._stage(
                        ControllerStage.CROSS_LINGUAL,
                        StageStatus.SKIPPED,
                        "Cross-lingual analysis was not configured.",
                        0,
                    )
                )

            # ----------------------------------------------------------
            # 11. CALIBRATION
            # ----------------------------------------------------------

            calibrated_count = 0

            if (
                request.config.enable_calibration
                and self.calibrator is not None
            ):
                calibration_records = (
                    self._build_calibration_records(
                        verification_results
                    )
                )

                if calibration_records:
                    self.calibrator.calibrate_records(
                        calibration_records
                    )
                    calibrated_count = len(
                        calibration_records
                    )

                    stages.append(
                        self._stage(
                            ControllerStage.CALIBRATION,
                            StageStatus.COMPLETED,
                            "Calibration applied to available records.",
                            calibrated_count,
                        )
                    )
                else:
                    stages.append(
                        self._stage(
                            ControllerStage.CALIBRATION,
                            StageStatus.SKIPPED,
                            "No calibration records were available.",
                            0,
                        )
                    )
            else:
                stages.append(
                    self._stage(
                        ControllerStage.CALIBRATION,
                        StageStatus.SKIPPED,
                        "Calibration was not configured.",
                        0,
                    )
                )

            # ----------------------------------------------------------
            # 12. SELECTIVE VERIFICATION
            # ----------------------------------------------------------

            selected_count = 0

            if (
                request.config.enable_selective_verification
                and self.selective_verification_executor is not None
            ):
                selector_claims = self._build_selector_claims(
                    typed_claims,
                    graph_builder,
                    verification_results,
                )

                selective_report = (
                    self.selective_verification_executor.execute(
                        graph=graph_builder,
                        claims=selector_claims,
                        budget=request.config.verification_budget,
                    )
                )

                selected_count = getattr(
                    selective_report,
                    "selected_count",
                    0,
                )

                stages.append(
                    self._stage(
                        ControllerStage.SELECTIVE_VERIFICATION,
                        StageStatus.COMPLETED,
                        "Budget-aware selective verification completed.",
                        selected_count,
                    )
                )
            else:
                stages.append(
                    self._stage(
                        ControllerStage.SELECTIVE_VERIFICATION,
                        StageStatus.SKIPPED,
                        "Selective verification was not configured.",
                        0,
                    )
                )

            # ----------------------------------------------------------
            # 13. ANSWER GENERATION
            # ----------------------------------------------------------

            final_answer = None
            answer_status = None
            answer_confidence = None
            supporting_claim_ids = []
            supporting_chunk_ids = []
            provenance = []
            conflict_info = None
            insufficiency_info = None

            if (
                getattr(request.config, "answer_generation_enabled", True)
                and self.answer_generator is not None
            ):
                answer_result = self.answer_generator.generate(
                    question=request.question,
                    graph=graph_builder,
                    verification_results=verification_results,
                    contradiction_report=contradiction_report,
                )

                final_answer = answer_result.answer
                answer_status = answer_result.status.value if answer_result.status else None
                answer_confidence = answer_result.confidence
                supporting_claim_ids = answer_result.supporting_claim_ids
                supporting_chunk_ids = answer_result.supporting_chunk_ids
                provenance = [p.dict() for p in answer_result.provenance]
                conflict_info = answer_result.conflict_information
                insufficiency_info = answer_result.insufficiency_reason

                stages.append(
                    self._stage(
                        ControllerStage.ANSWER_GENERATION,
                        StageStatus.COMPLETED,
                        "Grounded answer generation completed.",
                        1,
                    )
                )
            else:
                stages.append(
                    self._stage(
                        ControllerStage.ANSWER_GENERATION,
                        StageStatus.SKIPPED,
                        "Answer generation was not configured or missing generator.",
                        0,
                    )
                )

            # ----------------------------------------------------------
            # COMPLETE
            # ----------------------------------------------------------

            stages.append(
                self._stage(
                    ControllerStage.COMPLETED,
                    StageStatus.COMPLETED,
                    "AERIS orchestration completed.",
                    0,
                )
            )

            graph = graph_builder.build()

            return ControllerResult(
                document_id=request.document_id,
                question=request.question,
                status=StageStatus.COMPLETED,
                stages=stages,
                final_answer=final_answer,
                answer_status=answer_status,
                answer_confidence=answer_confidence,
                supporting_claim_ids=supporting_claim_ids,
                supporting_chunk_ids=supporting_chunk_ids,
                provenance=provenance,
                conflict_information=conflict_info,
                insufficiency_information=insufficiency_info,
                claim_count=len(graph.claims),
                evidence_count=len(graph.evidence),
                verified_claim_count=verified_count,
                selected_verification_count=selected_count,
                metadata={
                    "contradiction_relations": contradiction_count,
                    "cross_lingual_relations": cross_lingual_count,
                    "calibrated_records": calibrated_count,
                    "coverage": coverage_metadata,
                },
            )

        except Exception as exc:
            stages.append(
                self._stage(
                    ControllerStage.FAILED,
                    StageStatus.FAILED,
                    str(exc),
                    0,
                )
            )

            return ControllerResult(
                document_id=request.document_id,
                question=request.question,
                status=StageStatus.FAILED,
                stages=stages,
                final_answer=None,
                claim_count=0,
                evidence_count=0,
                verified_claim_count=0,
                selected_verification_count=0,
                metadata={
                    "error_type": type(exc).__name__,
                },
            )

    # ------------------------------------------------------------------
    # Evidence handling
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_evidence(retrieval_results) -> List[Dict[str, Any]]:
        """
        Normalize AdaptiveRetrievalResult evidence into a controller-level
        representation.

        The retrieval module can expose evidence through different
        collection attributes; this method intentionally handles the
        validated result structure without modifying it.
        """

        unique: Dict[str, Dict[str, Any]] = {}

        for result in retrieval_results:
            candidates = []

            for attr in (
                "evidence",
                "retrieved_evidence",
                "results",
                "retrieved_chunks",
                "final_results",
            ):
                value = getattr(result, attr, None)

                if value:
                    candidates = value
                    break

            for item in candidates:
                chunk_id = getattr(item, "chunk_id", None)

                if not chunk_id:
                    continue

                unique[chunk_id] = {
                    "chunk_id": chunk_id,
                    "document_id": getattr(
                        item,
                        "document_id",
                        None,
                    ),
                    "text": getattr(
                        item,
                        "text",
                        "",
                    ),
                    "language": getattr(
                        item,
                        "language",
                        None,
                    ),
                    "pages": getattr(
                        item,
                        "pages",
                        None,
                    ),
                }

        return list(unique.values())

    @staticmethod
    def _collect_coverage_metadata(
        retrieval_results,
    ) -> Dict[str, Any]:
        metadata = {}

        for index, result in enumerate(retrieval_results):
            for attr in (
                "coverage",
                "coverage_result",
                "coverage_score",
                "final_coverage",
                "success",
            ):
                value = getattr(result, attr, None)

                if value is not None:
                    metadata[f"requirement_{index + 1}_{attr}"] = value

        return metadata

    # ------------------------------------------------------------------
    # Verification helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_calibration_records(
        verification_results,
    ) -> list:
        """
        Calibration requires ground-truth labels.

        Therefore this method only accepts records already carrying
        ground truth. It does not invent labels from verifier output.
        """

        records = []

        for result in verification_results:
            record = getattr(
                result,
                "calibration_record",
                None,
            )

            if record is not None:
                records.append(record)

        return records

    @staticmethod
    def _build_selector_claims(
        typed_claims,
        graph_builder,
        verification_results,
    ) -> List[Dict[str, Any]]:
        """
        Convert typed claims into the dictionary contract expected by
        SelectiveVerificationExecutor.
        """

        verification_by_claim = {}

        for result in verification_results:
            claim_id = getattr(result, "claim_id", None)

            if claim_id:
                verification_by_claim[claim_id] = result

        graph = graph_builder.build()

        status_by_claim = {}

        for claim in graph.claims:
            status = getattr(
                claim,
                "verification_status",
                None,
            )

            if status is not None:
                status_by_claim[claim.claim_id] = status

        output = []

        for claim in typed_claims:
            verification = verification_by_claim.get(
                claim.claim_id
            )

            raw_confidence = getattr(
                verification,
                "confidence",
                0.0,
            )

            output.append(
                {
                    "claim_id": claim.claim_id,
                    "claim": claim.text,
                    "status": status_by_claim.get(
                        claim.claim_id,
                        "UNVERIFIED",
                    ),
                    "raw_confidence": raw_confidence,
                    "calibrated_confidence": None,
                }
            )

        return output

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_contradictions(report) -> int:
        for attr in (
            "contradiction_count",
            "contradictions",
            "contradiction_pairs",
        ):
            value = getattr(report, attr, None)

            if value is None:
                continue

            if isinstance(value, int):
                return value

            try:
                return len(value)
            except TypeError:
                pass

        return 0

    @staticmethod
    def _stage(
        stage: ControllerStage,
        status: StageStatus,
        message: str,
        output_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ControllerStageResult:
        return ControllerStageResult(
            stage=stage,
            status=status,
            message=message,
            output_count=output_count,
            metadata=metadata or {},
        )
