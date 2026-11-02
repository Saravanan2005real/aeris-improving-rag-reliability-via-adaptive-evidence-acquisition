import json
import os
import time
import contextvars

current_question_id = contextvars.ContextVar("current_question_id", default="UNKNOWN")
current_variant = contextvars.ContextVar("current_variant", default="UNKNOWN")

DIAGNOSTICS_FILE = "data/results/generation_diagnostics.jsonl"

def log_generation_attempt(stage: str, question_id: str, variant: str, attempt: int,
                           model: str, context_size: int, latency: float,
                           parse_success: bool, schema_success: bool,
                           repair_invoked: bool, retry_invoked: bool):
    os.makedirs(os.path.dirname(DIAGNOSTICS_FILE), exist_ok=True)
    
    q_id = current_question_id.get() if question_id == "UNKNOWN" else question_id
    var = current_variant.get() if variant == "UNKNOWN" else variant
    
    record = {
        "timestamp": time.time(),
        "stage": stage,
        "question_id": q_id,
        "variant": var,
        "attempt": attempt,
        "model": model,
        "context_size": context_size,
        "latency": latency,
        "parse_success": parse_success,
        "schema_success": schema_success,
        "repair_invoked": repair_invoked,
        "retry_invoked": retry_invoked
    }
    with open(DIAGNOSTICS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
