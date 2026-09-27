import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.controller.schemas import (
    ControllerConfig,
    ControllerRequest,
    ControllerResult,
    ControllerStage,
    ControllerStageResult,
    StageStatus,
)


def test_controller_request():

    request = ControllerRequest(
        document_id="test_document",
        question="How does the retriever work?",
    )

    assert request.document_id == "test_document"
    assert request.question == "How does the retriever work?"

    assert request.config.retrieval_top_k == 5
    assert request.config.candidate_k == 25
    assert request.config.verification_budget == 3

    print(
        "TEST 1 — Controller request schema: PASS"
    )


def test_controller_config():

    config = ControllerConfig(
        retrieval_top_k=10,
        candidate_k=50,
        verification_budget=5,
    )

    assert config.retrieval_top_k == 10
    assert config.candidate_k == 50
    assert config.verification_budget == 5

    print(
        "TEST 2 — Controller configuration: PASS"
    )


def test_stage_result():

    result = ControllerStageResult(
        stage=ControllerStage.RETRIEVAL,
        status=StageStatus.COMPLETED,
        message="Retrieval completed.",
        output_count=25,
        metadata={
            "candidate_k": 25,
        },
    )

    assert result.stage == ControllerStage.RETRIEVAL
    assert result.status == StageStatus.COMPLETED
    assert result.output_count == 25
    assert result.metadata["candidate_k"] == 25

    print(
        "TEST 3 — Stage result schema: PASS"
    )


def test_complete_controller_result():

    result = ControllerResult(
        document_id="test_document",
        question="How does the retriever work?",
        status=StageStatus.COMPLETED,
        stages=[
            ControllerStageResult(
                stage=ControllerStage.PLANNING,
                status=StageStatus.COMPLETED,
                output_count=2,
            ),
            ControllerStageResult(
                stage=ControllerStage.RETRIEVAL,
                status=StageStatus.COMPLETED,
                output_count=25,
            ),
            ControllerStageResult(
                stage=ControllerStage.CLAIM_GRAPH,
                status=StageStatus.COMPLETED,
                output_count=6,
            ),
        ],
        final_answer="The retriever uses hybrid retrieval.",
        claim_count=6,
        evidence_count=25,
        verified_claim_count=6,
        selected_verification_count=2,
    )

    assert result.status == StageStatus.COMPLETED
    assert len(result.stages) == 3
    assert result.claim_count == 6
    assert result.evidence_count == 25
    assert result.verified_claim_count == 6
    assert result.selected_verification_count == 2
    assert result.final_answer is not None

    print(
        "TEST 4 — Complete controller result: PASS"
    )


def test_invalid_request():

    try:
        ControllerRequest(
            document_id="",
            question="test",
        )
    except Exception:
        print(
            "TEST 5 — Invalid request rejection: PASS"
        )
        return

    raise AssertionError(
        "Invalid document ID was not rejected"
    )


def test_invalid_budget():

    try:
        ControllerConfig(
            verification_budget=-1,
        )
    except Exception:
        print(
            "TEST 6 — Invalid verification budget rejection: PASS"
        )
        return

    raise AssertionError(
        "Negative verification budget was not rejected"
    )


def test_stage_enum():

    expected_stages = {
        "PLANNING",
        "RETRIEVAL",
        "COVERAGE",
        "CLAIM_GRAPH",
        "VERIFICATION",
        "CONTRADICTION",
        "CROSS_LINGUAL",
        "CALIBRATION",
        "SELECTIVE_VERIFICATION",
        "COMPLETED",
        "FAILED",
    }

    actual_stages = {
        stage.value
        for stage in ControllerStage
    }

    assert expected_stages == actual_stages

    print(
        "TEST 7 — Controller stage definitions: PASS"
    )


if __name__ == "__main__":

    print("\n=== STEP 19A TEST ===")

    test_controller_request()
    test_controller_config()
    test_stage_result()
    test_complete_controller_result()
    test_invalid_request()
    test_invalid_budget()
    test_stage_enum()

    print("\nSTEP 19A TEST COMPLETE")
