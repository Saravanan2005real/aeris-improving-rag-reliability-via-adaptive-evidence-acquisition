import sys
import os
from types import SimpleNamespace

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from app.controller.controller import AERISController
from app.controller.schemas import (
    ControllerConfig,
    ControllerRequest,
    StageStatus,
)


class FakePlanner:

    def plan(self, question):
        requirement = SimpleNamespace(
            requirement_id="R1",
            description="What retrieval mechanism is used?",
            retrieval_queries=[
                "What retrieval mechanism is used?"
            ],
        )

        return SimpleNamespace(
            question=question,
            requirements=[requirement],
        )


class FakeAdaptiveRetrieval:

    def retrieve_for_requirement(
        self,
        document_id,
        question,
        requirement,
    ):
        evidence = SimpleNamespace(
            chunk_id="chunk_1",
            document_id=document_id,
            text=(
                "The system uses hybrid retrieval "
                "combining dense retrieval and BM25."
            ),
            language="en",
        )

        return SimpleNamespace(
            evidence=[evidence],
            coverage_score=1.0,
            success=True,
        )


class FakeClaim:

    def __init__(
        self,
        claim_id,
        text,
        source_chunk_id,
        claim_type="METHOD",
    ):
        self.claim_id = claim_id
        self.text = text
        self.source_chunk_id = source_chunk_id
        self.claim_type = claim_type


class FakeClaimExtractor:

    def extract(
        self,
        chunk_id,
        document_id,
        text,
    ):
        return SimpleNamespace(
            claims=[
                FakeClaim(
                    claim_id="C1",
                    text="The system uses hybrid retrieval.",
                    source_chunk_id=chunk_id,
                )
            ]
        )


class FakeClaimNormalizer:

    def normalize_and_deduplicate(
        self,
        claims,
    ):
        return claims


class FakeClaimTyper:

    def type_claims(self, claims):
        return claims


class FakeGraphBuilder:

    def __init__(self, document_id):
        self.document_id = document_id
        self.claims = []
        self.evidence = []

    def add_claim(
        self,
        claim_id,
        text,
        claim_type,
        source_chunk_id,
    ):
        self.claims.append(
            SimpleNamespace(
                claim_id=claim_id,
                text=text,
                claim_type=claim_type,
                source_chunk_id=source_chunk_id,
            )
        )

    def add_evidence(
        self,
        chunk_id,
        text,
    ):
        self.evidence.append(
            SimpleNamespace(
                chunk_id=chunk_id,
                text=text,
                document_id=self.document_id,
            )
        )

    def auto_link_claims_to_evidence(self):
        return None

    def build(self):
        return SimpleNamespace(
            document_id=self.document_id,
            claims=self.claims,
            evidence=self.evidence,
            edges=[],
            evidence_relations=[],
        )


class FakeGraphVerifier:

    def verify_claim(
        self,
        graph,
        claim_id,
    ):
        return SimpleNamespace(
            claim_id=claim_id,
            label="SUPPORTS",
            confidence=0.90,
        )


class FakeContradictionAnalyzer:

    def __call__(self, graph):
        return SimpleNamespace(
            contradiction_pairs=[],
            contradiction_count=0,
        )


class FakeContradictionIntegrator:

    def integrate(
        self,
        graph,
        report,
    ):
        return None


class FakeCrossLingualAnalyzer:

    def __call__(self, graph):
        return []


class FakeCrossLingualIntegrator:

    def integrate(
        self,
        graph,
        result,
        evidence_pairs,
    ):
        return None


class FakeCalibrator:

    def calibrate_records(self, records):
        return records


class FakeSelectiveExecutor:

    def execute(
        self,
        graph,
        claims,
        budget,
    ):
        selected = min(
            len(claims),
            budget,
        )

        return SimpleNamespace(
            selected_count=selected,
            verified_count=selected,
        )


def build_controller():
    return AERISController(
        planner=FakePlanner(),
        adaptive_retrieval_controller=FakeAdaptiveRetrieval(),
        claim_extractor=FakeClaimExtractor(),
        claim_normalizer=FakeClaimNormalizer(),
        claim_typer=FakeClaimTyper(),
        graph_builder_factory=FakeGraphBuilder,
        graph_verifier=FakeGraphVerifier(),
        contradiction_analyzer=FakeContradictionAnalyzer(),
        contradiction_integrator=FakeContradictionIntegrator(),
        cross_lingual_analyzer=FakeCrossLingualAnalyzer(),
        cross_lingual_integrator=FakeCrossLingualIntegrator(),
        calibrator=FakeCalibrator(),
        selective_verification_executor=FakeSelectiveExecutor(),
    )


def test_successful_orchestration():

    controller = build_controller()

    request = ControllerRequest(
        document_id="test_document",
        question="How does the retriever work?",
        config=ControllerConfig(
            verification_budget=1,
            enable_contradiction_analysis=True,
            enable_cross_lingual_analysis=True,
            enable_calibration=True,
            enable_selective_verification=True,
        ),
    )

    result = controller.run(request)

    assert result.status == StageStatus.COMPLETED

    assert result.claim_count == 1

    assert result.evidence_count == 1

    assert result.verified_claim_count == 1

    assert result.selected_verification_count == 1

    stages = {
        stage.stage: stage.status
        for stage in result.stages
    }

    assert stages["PLANNING"] == StageStatus.COMPLETED
    assert stages["RETRIEVAL"] == StageStatus.COMPLETED
    assert stages["COVERAGE"] == StageStatus.COMPLETED
    assert stages["CLAIM_GRAPH"] == StageStatus.COMPLETED
    assert stages["VERIFICATION"] == StageStatus.COMPLETED
    assert stages["CONTRADICTION"] == StageStatus.COMPLETED
    assert stages["CROSS_LINGUAL"] == StageStatus.COMPLETED
    assert stages["SELECTIVE_VERIFICATION"] == StageStatus.COMPLETED
    assert stages["COMPLETED"] == StageStatus.COMPLETED


def test_optional_stage_skipping():

    controller = AERISController(
        planner=FakePlanner(),
        adaptive_retrieval_controller=FakeAdaptiveRetrieval(),
        claim_extractor=FakeClaimExtractor(),
        claim_normalizer=FakeClaimNormalizer(),
        claim_typer=FakeClaimTyper(),
        graph_builder_factory=FakeGraphBuilder,
        graph_verifier=FakeGraphVerifier(),
    )

    request = ControllerRequest(
        document_id="test_document",
        question="How does the retriever work?",
        config=ControllerConfig(
            verification_budget=0,
            enable_contradiction_analysis=False,
            enable_cross_lingual_analysis=False,
            enable_calibration=False,
            enable_selective_verification=False,
        ),
    )

    result = controller.run(request)

    assert result.status == StageStatus.COMPLETED

    stages = {
        stage.stage: stage.status
        for stage in result.stages
    }

    assert stages["CONTRADICTION"] == StageStatus.SKIPPED
    assert stages["CROSS_LINGUAL"] == StageStatus.SKIPPED
    assert stages["CALIBRATION"] == StageStatus.SKIPPED
    assert stages["SELECTIVE_VERIFICATION"] == StageStatus.SKIPPED


def test_controller_failure_state():

    class BrokenPlanner:

        def plan(self, question):
            raise RuntimeError(
                "intentional planner failure"
            )

    controller = AERISController(
        planner=BrokenPlanner(),
        adaptive_retrieval_controller=FakeAdaptiveRetrieval(),
        claim_extractor=FakeClaimExtractor(),
        claim_normalizer=FakeClaimNormalizer(),
        claim_typer=FakeClaimTyper(),
        graph_builder_factory=FakeGraphBuilder,
        graph_verifier=FakeGraphVerifier,
    )

    request = ControllerRequest(
        document_id="test_document",
        question="How does the retriever work?",
    )

    result = controller.run(request)

    assert result.status == StageStatus.FAILED

    failed_stages = [
        stage
        for stage in result.stages
        if stage.stage.value == "FAILED"
    ]

    assert len(failed_stages) == 1


def main():

    print("=" * 80)
    print("STEP 19B — AERIS CONTROLLER ORCHESTRATION TEST")
    print("=" * 80)

    print("\nTEST 1 — Full controller orchestration")
    test_successful_orchestration()
    print("PASS")

    print("\nTEST 2 — Optional stage skipping")
    test_optional_stage_skipping()
    print("PASS")

    print("\nTEST 3 — Controller failure handling")
    test_controller_failure_state()
    print("PASS")

    print("\n" + "=" * 80)
    print("STEP 19B TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
