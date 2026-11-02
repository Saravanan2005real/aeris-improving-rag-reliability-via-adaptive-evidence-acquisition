"""
Step 22E Verification Suite: ClaimExtractor Timeout, Telemetry, and Retry Limits Tests

Validates:
1. Default timeout configuration is 180 seconds (overriding 60s global default).
2. Explicit custom timeout overrides are respected.
3. Timeout errors (ModelTimeoutError) are re-raised when retries are exhausted (failures remain visible).
4. Deliberate bounded retry succeeds when transient failure occurs on attempt 1.
5. Telemetry via log_generation_attempt records attempt, stage, latency, and success flags.
6. Retrying does not produce duplicate or partial claims.
"""

from unittest.mock import MagicMock, patch
import pytest

from app.claim_extraction.extractor import ClaimExtractor, DEFAULT_EXTRACTION_TIMEOUT
from app.claim_extraction.schemas import ClaimExtractionResult
from app.utils.model_client import ModelTimeoutError
from app.performance_cache import aeris_cache


@pytest.fixture(autouse=True)
def clean_cache():
    """Ensure cache does not return stale results across tests."""
    aeris_cache._cache = {}
    yield
    aeris_cache._cache = {}


def test_claim_extractor_default_timeout():
    """Verify that default ClaimExtractor timeout is 180.0 seconds."""
    extractor = ClaimExtractor()
    assert extractor.timeout == 180.0
    assert extractor.timeout == DEFAULT_EXTRACTION_TIMEOUT
    # Verify underlying httpx client has 180s read timeout
    client = extractor.client
    assert client._client.timeout.read == 180.0


def test_claim_extractor_custom_timeout_override():
    """Verify that caller can explicitly configure a custom timeout."""
    extractor = ClaimExtractor(timeout=240.0)
    assert extractor.timeout == 240.0
    assert extractor.client._client.timeout.read == 240.0


def test_claim_extractor_timeout_error_raised_when_exhausted():
    """
    When model call consistently times out, ModelTimeoutError must be raised
    so failure remains completely visible to the controller and runner.
    """
    extractor = ClaimExtractor(max_retries=1)

    timeout_err = ModelTimeoutError(
        "Claim Extraction timed out after 180.00s: timed out",
        stage="Claim Extraction",
        elapsed_seconds=180.0,
    )

    with patch("app.claim_extraction.extractor.timed_model_chat", side_effect=timeout_err) as mock_chat:
        with pytest.raises(ModelTimeoutError) as exc_info:
            extractor.extract(
                chunk_id="chunk_test_timeout",
                document_id="doc_test",
                text="Some dense text that takes too long to process.",
            )

        assert "Claim Extraction timed out after 180.00s" in str(exc_info.value)
        # Bounded retry: 1 initial attempt + 1 retry = 2 attempts total
        assert mock_chat.call_count == 2


def test_claim_extractor_retry_success_after_transient_failure():
    """
    When attempt 1 fails with a transient error but attempt 2 succeeds,
    the extractor should return the valid result without duplicates.
    """
    extractor = ClaimExtractor(max_retries=1)

    fail_err = ValueError("Malformed JSON received")
    success_res = {
        "content": '{"claims": ["The model uses DPR for retrieval.", "The generator is BART."]}',
        "elapsed_seconds": 15.2,
    }

    with patch("app.claim_extraction.extractor.timed_model_chat", side_effect=[fail_err, success_res]) as mock_chat:
        result = extractor.extract(
            chunk_id="chunk_test_retry",
            document_id="doc_test",
            text="Evidence text describing DPR and BART.",
        )

        assert mock_chat.call_count == 2
        assert isinstance(result, ClaimExtractionResult)
        assert len(result.claims) == 2
        assert result.claims[0].text == "The model uses DPR for retrieval."
        assert result.claims[1].text == "The generator is BART."
        assert result.claims[0].claim_id == "chunk_test_retry_claim_1"
        assert result.claims[1].claim_id == "chunk_test_retry_claim_2"


def test_claim_extractor_telemetry_recorded():
    """
    Verify that log_generation_attempt is called with accurate stage, attempt,
    and success/retry flags for every extraction call.
    """
    extractor = ClaimExtractor(max_retries=1)

    success_res = {
        "content": '{"claims": ["Claim A.", "Claim B."]}',
        "elapsed_seconds": 12.5,
    }

    with patch("app.claim_extraction.extractor.log_generation_attempt") as mock_log:
        with patch("app.claim_extraction.extractor.timed_model_chat", return_value=success_res):
            extractor.extract(
                chunk_id="chunk_test_telemetry",
                document_id="doc_test",
                text="Text for telemetry test.",
            )

        assert mock_log.call_count == 1
        args, kwargs = mock_log.call_args
        assert kwargs.get("stage") == "Claim Extraction" or (len(args) > 0 and args[0] == "Claim Extraction")
        assert kwargs.get("parse_success") is True or (len(args) > 7 and args[7] is True)
        assert kwargs.get("schema_success") is True or (len(args) > 8 and args[8] is True)
        assert kwargs.get("retry_invoked") is False or (len(args) > 10 and args[10] is False)


def test_claim_extractor_retry_limit_enforced():
    """Verify that retries strictly respect max_retries limit."""
    extractor = ClaimExtractor(max_retries=0)  # No retries allowed

    timeout_err = ModelTimeoutError("Timed out", stage="Claim Extraction")

    with patch("app.claim_extraction.extractor.timed_model_chat", side_effect=timeout_err) as mock_chat:
        with pytest.raises(ModelTimeoutError):
            extractor.extract(
                chunk_id="chunk_no_retry",
                document_id="doc_test",
                text="Text with max_retries=0.",
            )

        assert mock_chat.call_count == 1
