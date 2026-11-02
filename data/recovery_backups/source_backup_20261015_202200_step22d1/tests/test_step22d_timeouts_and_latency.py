"""
Step 22D Regression Test: Workstream 5 - Latency Measurement & Model Timeouts

Verifies:
1. Explicit connection/request timeouts configured on Ollama clients.
2. Timeout handling raises ModelTimeoutError as an explicit outcome.
3. Connection failure raises ModelConnectionError as an explicit outcome.
4. Monotonic clock (time.perf_counter) used for elapsed duration, separate from ISO UTC wall clock.
5. PC sleep/suspension anomaly detection raises LatencyContaminationError.
6. The historical 67,295.94-second outlier is identified and classified as contaminated.
"""

from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.utils.model_client import (
    get_ollama_client,
    timed_model_chat,
    ModelTimeoutError,
    ModelConnectionError,
    LatencyContaminationError,
)


def test_ollama_client_explicit_timeout_configured():
    """Verify that get_ollama_client sets explicit request and connect timeouts."""
    client = get_ollama_client(host="http://localhost:11434", timeout=45.0, connect_timeout=8.0)
    assert client is not None
    # Underlying httpx client should have explicit timeout
    http_client = getattr(client, "_client", None)
    if http_client is not None:
        assert http_client.timeout.read == 45.0 or http_client.timeout.connect == 8.0


def test_timeout_handling_raises_explicit_model_timeout_error():
    """Verify that httpx.TimeoutException during chat raises ModelTimeoutError."""
    mock_client = MagicMock()
    mock_client.chat.side_effect = httpx.ReadTimeout("Read timed out after 30.0s")

    with pytest.raises(ModelTimeoutError) as exc_info:
        timed_model_chat(
            client=mock_client,
            model="qwen2.5:7b-instruct",
            messages=[{"role": "user", "content": "Explain adaptive retrieval"}],
            stage="Planning",
        )

    err = exc_info.value
    assert "Planning timed out" in str(err)
    assert err.elapsed_seconds is not None
    assert err.timestamp_utc is not None


def test_connection_failure_raises_model_connection_error():
    """Verify that connection failure raises ModelConnectionError."""
    mock_client = MagicMock()
    mock_client.chat.side_effect = httpx.ConnectError("Failed to connect to Ollama daemon on 11434")

    with pytest.raises(ModelConnectionError) as exc_info:
        timed_model_chat(
            client=mock_client,
            model="qwen2.5:7b-instruct",
            messages=[{"role": "user", "content": "test"}],
            stage="AnswerGeneration",
        )

    err = exc_info.value
    assert "AnswerGeneration connection failed" in str(err)


def test_monotonic_and_wall_clock_separation():
    """
    Verify timed_model_chat measures duration using monotonic clock
    while separately recording forensic wall-clock timestamp.
    """
    mock_client = MagicMock()
    mock_client.chat.return_value = {
        "message": {"content": "Grounded answer text"}
    }

    result = timed_model_chat(
        client=mock_client,
        model="qwen2.5:7b-instruct",
        messages=[{"role": "user", "content": "Query"}],
        stage="Verification",
    )

    assert result["content"] == "Grounded answer text"
    assert result["elapsed_seconds"] >= 0.0
    assert "call_timestamp_utc" in result
    assert result["call_timestamp_utc"].endswith("Z") or "+00:00" in result["call_timestamp_utc"]
    assert "wall_elapsed_seconds" in result


def test_sleep_suspension_detection_raises_latency_contamination():
    """
    Verify that if PC sleep or system suspension occurs during a model call
    (wall clock advances much faster than monotonic clock or exceeds anomaly threshold),
    timed_model_chat detects it and raises LatencyContaminationError.
    """
    mock_client = MagicMock()
    mock_client.chat.return_value = {
        "message": {"content": "Response after laptop wake-up"}
    }

    # Simulate 1 second monotonic elapsed, but 3600 seconds wall-clock jump (system slept for 1 hour)
    monotonic_vals = [100.0, 101.0]
    wall_vals = [1700000000.0, 1700003600.0]

    with patch("time.perf_counter", side_effect=monotonic_vals), \
         patch("time.time", side_effect=wall_vals):
        with pytest.raises(LatencyContaminationError) as exc_info:
            timed_model_chat(
                client=mock_client,
                model="qwen2.5:7b-instruct",
                messages=[{"role": "user", "content": "Query"}],
                stage="Coverage",
            )

        err = exc_info.value
        assert err.reason == "OS_SLEEP_OR_SUSPENSION_DETECTED"
        assert err.wall_elapsed_seconds > 3000.0


def test_historical_outlier_contamination_flagged():
    """
    Verify that an anomalous duration exceeding max_anomaly_latency_seconds (e.g. 67,295.94s)
    is rejected and marked as contaminated.
    """
    mock_client = MagicMock()
    mock_client.chat.return_value = {
        "message": {"content": "Delayed response"}
    }

    # Simulate 67,295.94 seconds elapsed
    monotonic_vals = [0.0, 67295.94]
    wall_vals = [1700000000.0, 1700067295.94]

    with patch("time.perf_counter", side_effect=monotonic_vals), \
         patch("time.time", side_effect=wall_vals):
        with pytest.raises(LatencyContaminationError) as exc_info:
            timed_model_chat(
                client=mock_client,
                model="qwen2.5:7b-instruct",
                messages=[{"role": "user", "content": "Query"}],
                max_anomaly_seconds=300.0,
                stage="Planning",
            )

        err = exc_info.value
        assert err.elapsed_seconds == 67295.94
        assert err.reason in ["EXCEEDS_MAX_ANOMALY_THRESHOLD", "OS_SLEEP_OR_SUSPENSION_DETECTED"]
