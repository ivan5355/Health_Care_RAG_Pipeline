import contextvars
import logging
import json
import sys
from datetime import datetime, timezone

correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")

EXTRA_KEYS = (
    "correlation_id",
    "method", "path", "status_code", "duration_ms",
    "document_id", "question",
    "prompt_version", "model_id", "input_tokens", "output_tokens",
    "total_tokens", "cost_estimate", "input_hash", "latency_ms",
    "user", "role", "action", "resource", "phi_accessed", "audit",
)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        cid = correlation_id_var.get("")
        if cid:
            log_entry["correlation_id"] = cid
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        for key in EXTRA_KEYS:
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").addHandler(handler)
