import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
import ollama

from app.config import settings


class ModelCallError(Exception):
    """Base exception for model call failures."""
    def __init__(
        self,
        message: str,
        stage: str = "unknown",
        elapsed_seconds: float = 0.0,
        timestamp_utc: Optional[str] = None,
    ):
        super().__init__(message)
        self.stage = stage
        self.elapsed_seconds = elapsed_seconds
        self.timestamp_utc = timestamp_utc or datetime.now(timezone.utc).isoformat()


class ModelTimeoutError(ModelCallError):
    """Raised when a model call exceeds its configured timeout."""
    pass


class ModelConnectionError(ModelCallError):
    """Raised when connecting to the model host fails."""
    pass


class LatencyContaminationError(ModelCallError):
    """Raised when system sleep/suspension is detected during model execution."""
    def __init__(
        self,
        message: str,
        stage: str = "unknown",
        elapsed_seconds: float = 0.0,
        wall_elapsed_seconds: float = 0.0,
        reason: str = "CONTAMINATION_DETECTED",
        timestamp_utc: Optional[str] = None,
    ):
        super().__init__(
            message,
            stage=stage,
            elapsed_seconds=elapsed_seconds,
            timestamp_utc=timestamp_utc,
        )
        self.wall_elapsed_seconds = wall_elapsed_seconds
        self.reason = reason


def get_ollama_client(
    host: Optional[str] = None,
    timeout: Optional[float] = None,
    connect_timeout: Optional[float] = None,
) -> ollama.Client:
    """
    Creates an Ollama client with explicit connection, read, and write timeouts.
    """
    effective_host = host or settings.ollama_host
    effective_timeout = timeout if timeout is not None else settings.ollama_timeout
    effective_connect_timeout = (
        connect_timeout if connect_timeout is not None else settings.ollama_connect_timeout
    )

    httpx_timeout = httpx.Timeout(
        timeout=effective_timeout,
        connect=effective_connect_timeout,
        read=effective_timeout,
        write=effective_timeout,
        pool=effective_connect_timeout,
    )
    return ollama.Client(host=effective_host, timeout=httpx_timeout)


def timed_model_chat(
    client: ollama.Client,
    model: str,
    messages: List[Dict[str, str]],
    options: Optional[Dict[str, Any]] = None,
    format: Optional[str] = None,
    stage: str = "unknown",
    max_anomaly_seconds: Optional[float] = None,
    raise_on_contamination: bool = True,
) -> Dict[str, Any]:
    """
    Executes a chat call with monotonic duration measurement, wall-clock forensic
    timestamps, and sleep/suspension detection.
    """
    start_wall_ts = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()
    t0_mono = time.perf_counter()

    try:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if options is not None:
            kwargs["options"] = options
        if format is not None:
            kwargs["format"] = format

        response = client.chat(**kwargs)

        t1_mono = time.perf_counter()
        end_wall_ts = time.time()
        end_iso = datetime.now(timezone.utc).isoformat()

        mono_elapsed = t1_mono - t0_mono
        wall_elapsed = end_wall_ts - start_wall_ts

        anomaly_threshold = (
            max_anomaly_seconds
            if max_anomaly_seconds is not None
            else settings.max_anomaly_latency_seconds
        )

        # Detect system sleep/suspension anomaly:
        # If wall clock elapsed significantly exceeds monotonic time (>10s divergence)
        # or exceeds the configured anomaly ceiling, flag it.
        suspension_detected = False
        contamination_reason = None

        if (wall_elapsed - mono_elapsed) > 10.0:
            suspension_detected = True
            contamination_reason = "OS_SLEEP_OR_SUSPENSION_DETECTED"
        elif mono_elapsed > anomaly_threshold:
            suspension_detected = True
            contamination_reason = "EXCEEDS_MAX_ANOMALY_THRESHOLD"

        if suspension_detected and raise_on_contamination:
            raise LatencyContaminationError(
                f"Latency measurement contaminated in stage '{stage}': {contamination_reason} "
                f"(monotonic={mono_elapsed:.2f}s, wall={wall_elapsed:.2f}s)",
                stage=stage,
                elapsed_seconds=mono_elapsed,
                wall_elapsed_seconds=wall_elapsed,
                reason=contamination_reason,
                timestamp_utc=start_iso,
            )

        return {
            "response": response,
            "content": response["message"]["content"],
            "elapsed_seconds": mono_elapsed,
            "wall_elapsed_seconds": wall_elapsed,
            "call_timestamp_utc": start_iso,
            "start_time_iso": start_iso,
            "end_time_iso": end_iso,
            "suspension_detected": suspension_detected,
            "contamination_reason": contamination_reason,
            "stage": stage,
        }

    except httpx.TimeoutException as e:
        mono_elapsed = time.perf_counter() - t0_mono
        msg = f"{stage} timed out after {mono_elapsed:.2f}s: {e}"
        raise ModelTimeoutError(
            msg,
            stage=stage,
            elapsed_seconds=mono_elapsed,
            timestamp_utc=start_iso,
        ) from e
    except httpx.ConnectError as e:
        mono_elapsed = time.perf_counter() - t0_mono
        msg = f"{stage} connection failed after {mono_elapsed:.2f}s: {e}"
        raise ModelConnectionError(
            msg,
            stage=stage,
            elapsed_seconds=mono_elapsed,
            timestamp_utc=start_iso,
        ) from e
    except LatencyContaminationError:
        raise
    except Exception as e:
        mono_elapsed = time.perf_counter() - t0_mono
        raise e
