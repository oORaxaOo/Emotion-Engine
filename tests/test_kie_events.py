import json
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from emotion_engine.kie_events import publish_reflection_completed


class _CaptureServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


class KIEEventPublisherTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name)
        self.socket_path = self.root / "kie.sock"

    def _capture(self, callback):
        received = []

        class Handler(socketserver.StreamRequestHandler):
            def handle(inner_self):
                received.append(json.loads(inner_self.rfile.readline(65537)))
                inner_self.wfile.write(b'{"ok":true}\n')
                inner_self.wfile.flush()

        server = _CaptureServer(str(self.socket_path), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertTrue(callback(self.socket_path))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        return received[0]

    def test_publisher_sends_only_reflection_lifecycle_metadata(self):
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
        message = self._capture(lambda path: publish_reflection_completed(path, cascade))

        self.assertEqual(message["engine_id"], "emotion")
        self.assertEqual(message["event_type"], "emotion.reflection_completed")
        self.assertEqual(message["payload"], {
            "status": "completed",
            "step_count": 2,
            "steps_remaining": 2,
            "hypothesis_count": 1,
            "limitations_count": 2,
            "follow_up_pending": False,
        })
        self.assertNotIn("private hypothesis", json.dumps(message))
        self.assertNotIn("private limitation", json.dumps(message))

    def test_publisher_is_disabled_without_socket_path(self):
        cascade = SimpleNamespace(
            status=SimpleNamespace(value="completed"),
            steps_remaining=0,
            next_question=None,
            steps=(),
        )
        self.assertFalse(publish_reflection_completed(None, cascade))

    def test_publisher_fails_open_when_kie_is_unavailable(self):
        cascade = SimpleNamespace(
            status=SimpleNamespace(value="completed"),
            steps_remaining=0,
            next_question=None,
            steps=(),
        )
        self.assertFalse(publish_reflection_completed(self.root / "missing.sock", cascade))

    def test_publisher_rejects_inconsistent_step_budget(self):
        cascade = SimpleNamespace(
            status=SimpleNamespace(value="completed"),
            steps_remaining=4,
            next_question=None,
            steps=(SimpleNamespace(causal_hypotheses=(), limitations=()),),
        )
        self.assertFalse(publish_reflection_completed(self.root / "missing.sock", cascade))


if __name__ == "__main__":
    unittest.main()
