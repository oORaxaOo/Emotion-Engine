"""Publish only non-content reflection lifecycle metadata to KIE."""
from __future__ import annotations

import json
from pathlib import Path
import socket
from typing import Any
from uuid import uuid4

_MAX_MESSAGE_BYTES = 64 * 1024
_ALLOWED_STATUSES = frozenset({"completed", "budget_exhausted"})


def publish_reflection_completed(socket_path: str | Path | None, cascade: Any) -> bool:
    """Send a bounded reflection summary; never send findings, hypotheses, or evidence."""
    if not isinstance(socket_path, (str, Path)) or not str(socket_path).strip():
        return False
    path = Path(socket_path).expanduser()
    if not path.is_absolute():
        return False
    try:
        steps = tuple(cascade.steps)
        payload = {
            "status": cascade.status.value,
            "step_count": len(steps),
            "steps_remaining": cascade.steps_remaining,
            "hypothesis_count": sum(len(step.causal_hypotheses) for step in steps),
            "limitations_count": sum(len(step.limitations) for step in steps),
            "follow_up_pending": cascade.next_question is not None,
        }
        if (
            payload["status"] not in _ALLOWED_STATUSES
            or isinstance(payload["step_count"], bool)
            or not isinstance(payload["step_count"], int)
            or not 0 <= payload["step_count"] <= 4
            or isinstance(payload["steps_remaining"], bool)
            or not isinstance(payload["steps_remaining"], int)
            or not 0 <= payload["steps_remaining"] <= 4
            or isinstance(payload["hypothesis_count"], bool)
            or not isinstance(payload["hypothesis_count"], int)
            or not 0 <= payload["hypothesis_count"] <= 12
            or isinstance(payload["limitations_count"], bool)
            or not isinstance(payload["limitations_count"], int)
            or not 0 <= payload["limitations_count"] <= 20
            or not isinstance(payload["follow_up_pending"], bool)
            or payload["step_count"] + payload["steps_remaining"] > 4
        ):
            return False
        message = {
            "event_id": str(uuid4()),
            "engine_id": "emotion",
            "event_type": "emotion.reflection_completed",
            "payload": payload,
        }
        encoded = json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > _MAX_MESSAGE_BYTES:
            return False
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(0.15)
            client.connect(str(path))
            client.sendall(encoded + b"\n")
            response = client.makefile("rb").readline(1024)
        return json.loads(response.decode("utf-8")).get("ok") is True
    except (AttributeError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


__all__ = ["publish_reflection_completed"]
