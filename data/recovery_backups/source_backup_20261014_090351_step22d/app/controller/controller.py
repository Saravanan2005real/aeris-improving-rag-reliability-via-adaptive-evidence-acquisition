from __future__ import annotations
import time

from typing import Any, Callable, Dict, Iterable, List, Optional
from app.retrieval_memory.memory import RetrievalMemory
from app.verification.requirement_support import RequirementSupportValidator
from app.verification.requirement_support import RequirementSupportValidator

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
        requirement_validator=None,
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
        self.requirement_validator = requirement_validator or RequirementSupportValidator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, request: ControllerRequest) -> ControllerResult:
        stages: List[ControllerStageResult] = []

        try:
            # ----------------------------------------------------------
            # 1. PLANNING
            # ----------------------------------------------------------
            t0 = time.perf_counter()
            plan = self.planner.plan(request.question)
            t_plan = time.perf_counter() - t0

            stages.append(
                self._stage(
                    ControllerStage.PLANNING,
                    StageStatus.COMPLETED,
                    "Information requirements generated.",
                    len(plan.requirements),
                    latency_seconds=t_plan,
                )
            )

            # ----------------------------------------------------------
            # 2. ADAPTIVE RETRIEVAL
            # ----------------------------------------------------------

            t0 = time.perf_counter()
            retrieval_results = []
            
            memory = RetrievalMemory(request.document_id, request.question) if request.config.enable_retrieval_memory else None

            for requirement in plan.requirements:
                result = (
                    self.adaptive_retrieval_controller
                    .retrieve_for_requirement(
                        document_id=request.document_id,
                        question=request.question,
                        requirement=requirement,
                        enable_adaptive_retrieval=request.config.enable_adaptive_retrieval,
                        enable_query_reformulation=request.config.enable_query_reformulation,
                        enable_retrieval_memory=request.config.enable_retrieval_memory,
                        memory=memory,
                    )
                )

                retrieval_results.append(result)

            evidence_items = self._collect_evidence(
                retrieval_results
            )
            # Ordered, deterministic deduplication of retrieved chunk IDs
            retrieved_chunk_ids = []
            for item in evidence_items:
                cid = item.get("chunk_id")
                if cid and cid not in retrieved_chunk_ids:
                    retrieved_chunk_ids.append(cid)

            retrieval_attempts_history = []
            for res in retrieval_results:
                for att in res.attempts:
                    if hasattr(att, "model_dump"):
                        retrieval_attempts_history.append(att.model_dump())
                    elif hasattr(att, "dict"):
                        retrieval_attempts_history.append(att.dict())
                    else:
                        retrieval_attempts_history.append(dict(att))

            t_retrieval = time.perf_counter() - t0

            stages.append(
                self._stage(
                    ControllerStage.RETRIEVAL,
                    StageStatus.COMPLETED,
                    "Adaptive requirement-directed retrieval completed.",
                    len(evidence_items),
                    latency_seconds=t_retrieval,
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

            t0 = time.perf_counter()
            coverage_metadata = self._collect_coverage_metadata(
                retrieval_results
            )
            t_coverage = time.perf_counter() - t0

            stages.append(
                self._stage(
                    ControllerStage.COVERAGE,
                    StageStatus.COMPLETED,
                    "Evidence coverage evaluated during adaptive retrieval.",
                    len(evidence_items),
                    coverage_metadata,
                    latency_seconds=t_coverage,
                )
            )

            # ----------------------------------------------------------
            # 4. CLAIM EXTRACTION
            # ----------------------------------------------------------

            t0 = time.perf_counter()
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
            t_claim_graph = time.perf_counter() - t0

            stages.append(
                self._stage(
                    ControllerStage.CLAIM_GRAPH,
                    StageStatus.COMPLETED,
                    "Claim-evidence graph constructed.",
                    len(typed_claims),
                    latency_seconds=t_claim_graph,
                )
            )

            # ----------------------------------------------------------
            # 8. INITIAL CLAIM VERIFICATION
            # ----------------------------------------------------------

            t_start = time.perf_counter()
            verification_results = []
            verified_count = 0

            if request.config.enable_claim_verification:
                for claim in typed_claims:
                    if not graph_builder.get_claim_evidence(claim.claim_id):
                        continue

                    result = self.graph_verifier.verify_claim(
                        graph_builder,
                        claim.claim_id,
                    )

                    verification_results.append(result)

                verified_count = len(verification_results)
                t_verify = time.perf_counter() - t_start

                stages.append(
                    self._stage(
                        ControllerStage.VERIFICATION,
                        StageStatus.COMPLETED,
                        "Initial claim verification completed.",
                        verified_count,
                        latency_seconds=t_verify,
                    )
                )
            else:
                t_verify = time.perf_counter() - t_start
                stages.append(
                    self._stage(
                        ControllerStage.VERIFICATION,
                        StageStatus.SKIPPED,
                        "Claim verification was disabled for ablation.",
                        0,
                        latency_seconds=t_verify,
                    )
                )

            # ----------------------------------------------------------
            # 9. CONTRADICTION ANALYSIS
            # ----------------------------------------------------------

            t0 = time.perf_counter()
            contradiction_count = 0
            contradiction_report = None

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
                t_contra = time.perf_counter() - t0

                stages.append(
                    self._stage(
                        ControllerStage.CONTRADICTION,
                        StageStatus.COMPLETED,
                        "Contextual contradiction analysis completed.",
                        contradiction_count,
                        latency_seconds=t_contra,
                    )
                )
            else:
                t_contra = time.perf_counter() - t0
                stages.append(
                    self._stage(
                        ControllerStage.CONTRADICTION,
                        StageStatus.SKIPPED,
                        "Contradiction analysis was not configured.",
                        0,
                        latency_seconds=t_contra,
                    )
                )

            # ----------------------------------------------------------
            # 10. CROSS-LINGUAL ANALYSIS
            # ----------------------------------------------------------

            t0 = time.perf_counter()
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
                t_cross = time.perf_counter() - t0

                stages.append(
                    self._stage(
                        ControllerStage.CROSS_LINGUAL,
                        StageStatus.COMPLETED,
                        "Cross-lingual evidence analysis completed.",
                        cross_lingual_count,
                        latency_seconds=t_cross,
                    )
                )
            else:
                t_cross = time.perf_counter() - t0
                stages.append(
                    self._stage(
                        ControllerStage.CROSS_LINGUAL,
                        StageStatus.SKIPPED,
                        "Cross-lingual analysis was not configured.",
                        0,
                        latency_seconds=t_cross,
                    )
                )

            # ----------------------------------------------------------
            # 11. CALIBRATION
            # ----------------------------------------------------------

            t0 = time.perf_counter()
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
                    t_calib = time.perf_counter() - t0

                    stages.append(
                        self._stage(
                            ControllerStage.CALIBRATION,
                            StageStatus.COMPLETED,
                            "Calibration applied to available records.",
                            calibrated_count,
                            latency_seconds=t_calib,
                        )
                    )
                else:
                    t_calib = time.perf_counter() - t0
                    stages.append(
                        self._stage(
                            ControllerStage.CALIBRATION,
                            StageStatus.SKIPPED,
                            "No calibration records were available.",
                            0,
                            latency_seconds=t_calib,
                        )
                    )
            else:
                t_calib = time.perf_counter() - t0
                stages.append(
                    self._stage(
                        ControllerStage.CALIBRATION,
                        StageStatus.SKIPPED,
                        "Calibration was not configured.",
                        0,
                        latency_seconds=t_calib,
                    )
                )

            # ----------------------------------------------------------
            # 12. SELECTIVE VERIFICATION
            # ----------------------------------------------------------

            t0 = time.perf_counter()
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
                t_selective = time.perf_counter() - t0

                stages.append(
                    self._stage(
                        ControllerStage.SELECTIVE_VERIFICATION,
                        StageStatus.COMPLETED,
                        "Budget-aware selective verification completed.",
                        selected_count,
                        latency_seconds=t_selective,
                    )
                )
            else:
                t_selective = time.perf_counter() - t0
                stages.append(
                    self._stage(
                        ControllerStage.SELECTIVE_VERIFICATION,
                        StageStatus.SKIPPED,
                        "Selective verification was not configured.",
                        0,
                        latency_seconds=t_selective,
                    )
                )

            # ----------------------------------------------------------
            # 13. ANSWER GENERATION
            # ----------------------------------------------------------

            t0 = time.perf_counter()
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

                # Requirement-level support validation
                if answer_status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]:
                    claims_texts = [graph_builder.claims[cid].text for cid in supporting_claim_ids if cid in graph_builder.claims]
                    
                    if plan and plan.requirements:
                        req_results = []
                        for req in plan.requirements:
                            val_res = self.requirement_validator.validate(
                                question=request.question,
                                requirement=req.description,
                                answer=final_answer,
                                claims=claims_texts
                            )
                            req_results.append(val_res.is_supported)
                        
                        if not any(req_results):
                            # None of the requirements are supported by the claims
                            answer_status = "INSUFFICIENT_EVIDENCE"
                            insufficiency_info = "The extracted claims do not actually support any information requirements for the given question."

                # Enforce citation provenance validation: every cited chunk must belong to retrieved_chunk_ids
                provenance_defects = [
                    cid for cid in supporting_chunk_ids if cid not in retrieved_chunk_ids
                ]
                if provenance_defects:
                    defect_msg = f"Provenance defect: cited chunk(s) {provenance_defects} not in retrieved evidence pool."
                    insufficiency_info = f"{insufficiency_info} | {defect_msg}" if insufficiency_info else defect_msg
                    if answer_status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]:
                        answer_status = "INSUFFICIENT_EVIDENCE"

                t_ans = time.perf_counter() - t0

                stages.append(
                    self._stage(
                        ControllerStage.ANSWER_GENERATION,
                        StageStatus.COMPLETED,
                        "Grounded answer generation completed.",
                        1,
                        latency_seconds=t_ans,
                    )
                )
            else:
                provenance_defects = []
                supporting_claim_ids = []
                supporting_chunk_ids = []
                provenance = []
                conflict_info = None
                insufficiency_info = "Answer generation was not configured or missing generator."
                t_ans = time.perf_counter() - t0
                stages.append(
                    self._stage(
                        ControllerStage.ANSWER_GENERATION,
                        StageStatus.SKIPPED,
                        "Answer generation was not configured or missing generator.",
                        0,
                        latency_seconds=t_ans,
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

            # Telemetry Tracking
            ar_calls = 0
            cand_expansions = 0
            ar_triggered = False
            ref_calls = 0
            ref_triggered = False
            
            for res in retrieval_results:
                ar_calls += len(res.attempts)
                if len(res.attempts) > 1:
                    ar_triggered = True
                for att in res.attempts:
                    if att.candidate_k > request.config.candidate_k:
                        cand_expansions += 1
                    if att.query_type == "reformulated" or str(att.query_type).startswith("reformulation"):
                        ref_calls += 1
                        ref_triggered = True

            mem_hits = memory.hit_count if memory else 0
            mem_lookups = memory.lookup_count if memory else 0
            mem_skips = memory.skip_count if memory else 0
            
            verification_call_count = len(verification_results) if request.config.enable_claim_verification else 0
            verification_skipped_count = len(typed_claims) - verification_call_count if request.config.enable_claim_verification else 0
            
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
                retrieved_chunk_ids=retrieved_chunk_ids,
                retrieval_attempts_history=retrieval_attempts_history,
                provenance_defects=provenance_defects,
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
                    "provenance_defects": provenance_defects,
                    "retrieved_chunk_count": len(retrieved_chunk_ids),
                    
                    "adaptive_retrieval_triggered": ar_triggered,
                    "retrieval_attempt_count": ar_calls,
                    "candidate_depth_expansions": cand_expansions,
                    
                    "reformulation_triggered": ref_triggered,
                    "reformulation_attempt_count": ref_calls,
                    
                    "memory_lookup_count": mem_lookups,
                    "memory_hit_count": mem_hits,
                    "memory_skip_count": mem_skips,
                    
                    "verification_call_count": verification_call_count,
                    "claims_verified": verified_count,
                    "verification_skipped_count": verification_skipped_count,
                    
                    "contradiction_call_count": 1 if (request.config.enable_contradiction_analysis and contradiction_report) else 0,
                    "contradiction_pairs_evaluated": len(contradiction_report.conflicts) if contradiction_report and hasattr(contradiction_report, 'conflicts') else 0,
                    
                    "cross_lingual_call_count": 1 if request.config.enable_cross_lingual_analysis else 0,
                    "cross_lingual_pairs_evaluated": cross_lingual_count,
                    
                    "selective_verification_call_count": 1 if (request.config.enable_selective_verification and selected_count > 0) else 0,
                    "selected_claim_count": selected_count,
                    "skipped_claim_count": len(typed_claims) - selected_count if request.config.enable_selective_verification else 0,
                },
            )

        except Exception as exc:
            import traceback
            error_msg = f"{str(exc)}\n{traceback.format_exc()}"
            stages.append(
                self._stage(
                    ControllerStage.FAILED,
                    StageStatus.FAILED,
                    error_msg,
                    0,
                )
            )

            return ControllerResult(
                document_id=request.document_id,
                question=request.question,
                status=StageStatus.FAILED,
                stages=stages,
                final_answer=None,
                retrieved_chunk_ids=[],
                retrieval_attempts_history=[],
                provenance_defects=[],
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

            for item in candidates[:3]:
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
        latency_seconds: float = 0.0,
    ) -> ControllerStageResult:
        return ControllerStageResult(
            stage=stage,
            status=status,
            message=message,
            output_count=output_count,
            metadata=metadata or {},
            latency_seconds=latency_seconds,
        )
