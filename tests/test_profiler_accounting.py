import pytest
from unittest.mock import MagicMock, patch
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus

def test_successful_pipeline():
    controller = AERISController(
        planner=MagicMock(),
        adaptive_retrieval_controller=MagicMock(),
        claim_extractor=MagicMock(),
        claim_normalizer=MagicMock(),
        claim_typer=MagicMock(),
        graph_builder_factory=MagicMock(),
        graph_verifier=MagicMock()
    )
    req = ControllerRequest(document_id="d1", question="q1", config=ControllerConfig())
    res = controller.run(req)
    assert res.status == StageStatus.COMPLETED

def test_failed_claim_extraction():
    extractor = MagicMock()
    extractor.extract.side_effect = Exception("JSONParsingError in extraction")
    
    # We must mock adaptive retrieval to return some evidence so extraction is called
    adaptive = MagicMock()
    adaptive.retrieve_for_requirement.return_value = MagicMock(
        evidence=[MagicMock(chunk_id="c1", text="text")]
    )
    
    planner = MagicMock()
    planner.plan.return_value = MagicMock(requirements=[MagicMock(requirement_id="r1")])
    
    controller = AERISController(
        planner=planner,
        adaptive_retrieval_controller=adaptive,
        claim_extractor=extractor,
        claim_normalizer=MagicMock(),
        claim_typer=MagicMock(),
        graph_builder_factory=MagicMock(),
        graph_verifier=MagicMock()
    )
    req = ControllerRequest(document_id="d1", question="q1", config=ControllerConfig())
    res = controller.run(req)
    assert res.status == StageStatus.FAILED
    assert res.metadata.get("error_type") == "Exception"
