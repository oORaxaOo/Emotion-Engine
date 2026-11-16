import json
import socketserver
import threading
from types import SimpleNamespace

from emotion_engine.kie_events import publish_reflection_completed


class _CaptureServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def test_publisher_sends_only_reflection_lifecycle_metadata(tmp_path):
    path = tmp_path / "kie.sock"
    received = []

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            received.append(json.loads(self.rfile.readline(65537)))
            self.wfile.write(b'{"ok":true}\n')
            self.wfile.flush()

    server = _CaptureServer(str(path), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        cascade = SimpleNamespace(
            status=SimpleNamespace(value="completed"),
            steps_remaining=2,
            next_question=None,
            steps=(
                SimpleNamespace(
                    causal_hypotheses=(SimpleNamespace(statement="private hypothesis"),),
                    limitations=("private limitation text",),
                ),
                SimpleNamespace(causal_hypotheses=(), limitations=("another private note",)),
            ),
        )
        assert publish_reflection_completed(path, cascade) is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    message = received[0]
    assert message["engine_id"] == "emotion"
    assert message["event_type"] == "emotion.reflection_completed"
    assert message["payload"] == {
        "status": "completed",
        "step_count": 2,
        "steps_remaining": 2,
        "hypothesis_count": 1,
        "limitations_count": 2,
        "follow_up_pending": False,
    }
    assert "private hypothesis" not in json.dumps(message)
    assert "private limitation" not in json.dumps(message)


def test_publisher_is_disabled_without_socket_path():
    cascade = SimpleNamespace(
        status=SimpleNamespace(value="completed"),
        steps_remaining=0,
        next_question=None,
        steps=(),
    )
    assert publish_reflection_completed(None, cascade) is False


def test_publisher_fails_open_when_kie_is_unavailable(tmp_path):
    cascade = SimpleNamespace(
        status=SimpleNamespace(value="completed"),
        steps_remaining=0,
        next_question=None,
        steps=(),
    )
    assert publish_reflection_completed(tmp_path / "missing.sock", cascade) is False


def test_publisher_rejects_inconsistent_step_budget(tmp_path):
    cascade = SimpleNamespace(
        status=SimpleNamespace(value="completed"),
        steps_remaining=4,
        next_question=None,
        steps=(SimpleNamespace(causal_hypotheses=(), limitations=()),),
    )
    assert publish_reflection_completed(tmp_path / "missing.sock", cascade) is False
