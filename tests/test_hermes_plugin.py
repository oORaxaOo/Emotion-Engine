"""Hermes plugin contract tests using the public plugin context shape."""

import json
import subprocess
import sys
import tempfile
import unittest
import sys
import types
from unittest.mock import Mock, patch
from pathlib import Path

import hermes_plugin


def reflection_output(*, next_question=None, answer=None, answer_refs=None, evidence_id="assistant-response"):
    return json.dumps({
        "schema_version": "0.1",
        "assessment": "undetermined",
        "finding": "The response text is available, but its factual basis is not established.",
        "finding_evidence_refs": [evidence_id],
        "self_challenge": "The response may be incomplete or incorrect; no independent source is present.",
        "self_challenge_evidence_refs": [evidence_id],
        "inquiry_answer": answer,
        "inquiry_answer_evidence_refs": answer_refs or [],
        "causal_hypotheses": [],
        "limitations": ["The model output does not reveal hidden computation or intent."],
        "next_question": next_question,
        "next_question_reason": "Independent evidence is needed." if next_question else None,
        "next_question_evidence_refs": [evidence_id] if next_question else [],
        "evidence_to_collect": ["The tool result or source record."] if next_question else [],
    })


class FakeLLM:
    def __init__(self, outputs=None):
        self.outputs = list(outputs or [reflection_output(next_question="Which independent source verifies this response?")])
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return type("Result", (), {"text": self.outputs.pop(0)})()


class FakeContext:
    def __init__(self, outputs=None, settings=None):
        self.llm = FakeLLM(outputs)
        self.settings = settings or {}

    def get_config(self, key, default=None):
        return self.settings.get(key, default)
        self.tools = {}
        self.hooks = {}
        self.auxiliary = []

    def register_auxiliary_task(self, name, **kwargs):
        self.auxiliary.append((name, kwargs))

    def register_tool(self, *, name, toolset, schema, handler, **kwargs):
        self.tools[name] = {"toolset": toolset, "schema": schema, "handler": handler}

    def register_hook(self, name, handler, **kwargs):
        self.hooks[name] = handler


class HermesPluginTests(unittest.TestCase):
    def setUp(self):
        self.ctx = FakeContext()
        hermes_plugin.register(self.ctx)
        self.hook = self.ctx.hooks["post_llm_call"]

    def call(self, tool, args=None, session="session-A"):
        return json.loads(self.ctx.tools[tool]["handler"](args or {}, session_id=session))

    def test_plugin_entrypoint_loads_as_a_package_without_repo_on_sys_path(self):
        root = Path(__file__).resolve().parents[1]
        code = (
            "import importlib.util, sys; "
            "root=sys.argv[1]; "
            "spec=importlib.util.spec_from_file_location("
            "'isolated_emotion_plugin', root + '/__init__.py', "
            "submodule_search_locations=[root]); "
            "module=importlib.util.module_from_spec(spec); "
            "sys.modules[spec.name]=module; "
            "spec.loader.exec_module(module); "
            "assert callable(module.register)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code, str(root)],
            cwd=tempfile.gettempdir(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
    def test_registers_tools_hook_and_own_auxiliary_route(self):
        self.assertIn("emotion_list_recent_actions", self.ctx.tools)
        self.assertIn("emotion_reflect", self.ctx.tools)
        self.assertIn("emotion_continue_reflection", self.ctx.tools)
        self.assertIn("emotion_clear_session", self.ctx.tools)
        self.assertIn("post_llm_call", self.ctx.hooks)
        self.assertEqual(self.ctx.auxiliary[0][0], "emotion_reflection")

    def test_hook_captures_only_assistant_output_and_is_session_scoped(self):
        self.hook(
            session_id="session-A",
            assistant_response="A recorded assistant answer.",
            user_message="PRIVATE USER MESSAGE",
            conversation_history=[{"content": "PRIVATE HISTORY"}],
            model="local-model",
            platform="cli",
        )
        listed = self.call("emotion_list_recent_actions")
        self.assertEqual(len(listed["actions"]), 1)
        self.assertIn("A recorded assistant answer.", listed["actions"][0]["summary"])
        self.assertNotIn("PRIVATE USER MESSAGE", json.dumps(listed))
        other = self.call("emotion_list_recent_actions", session="session-B")
        self.assertEqual(other["actions"], [])

    def test_reflection_publishes_only_bounded_metadata_to_kie(self):
        publisher = Mock()
        fake_kie = types.ModuleType("kie")
        fake_kie.__path__ = []
        fake_publisher_module = types.ModuleType("kie.publisher")
        fake_publisher_module.publish_emotion_reflection = publisher
        with patch.dict(sys.modules, {"kie": fake_kie, "kie.publisher": fake_publisher_module}):
            ctx = FakeContext(
                [reflection_output(next_question="PRIVATE NEXT QUESTION")],
                {"kie_database": "/tmp/kie-emotion-test.sqlite3"},
            )
            hermes_plugin.register(ctx)
            hook = ctx.hooks["post_llm_call"]
            hook(session_id="session-A", assistant_response="PRIVATE ASSISTANT RESPONSE")
            action_id = json.loads(ctx.tools["emotion_list_recent_actions"]["handler"](
                {"limit": 8}, session_id="session-A"
            ))["actions"][0]["action_id"]
            result = json.loads(ctx.tools["emotion_reflect"]["handler"](
                {"action_id": action_id}, session_id="session-A"
            ))

        self.assertTrue(result["ok"])
        publisher.assert_called_once()
        args, kwargs = publisher.call_args
        self.assertEqual(args[0], "/tmp/kie-emotion-test.sqlite3")
        self.assertEqual(kwargs["status"], "awaiting_evidence")
        self.assertEqual(kwargs["step_count"], 1)
        self.assertEqual(kwargs["assessments"], ("undetermined",))
        self.assertTrue(kwargs["next_question_available"])
        serialized = repr(kwargs)
        self.assertNotIn("PRIVATE NEXT QUESTION", serialized)
        self.assertNotIn("PRIVATE ASSISTANT RESPONSE", serialized)
        self.assertNotIn("finding", serialized)
        self.assertNotIn("evidence", serialized)

    def test_kie_publication_failure_does_not_break_reflection(self):
        publisher = Mock(side_effect=OSError("database unavailable"))
        fake_kie = types.ModuleType("kie")
        fake_kie.__path__ = []
        fake_publisher_module = types.ModuleType("kie.publisher")
        fake_publisher_module.publish_emotion_reflection = publisher
        with patch.dict(sys.modules, {"kie": fake_kie, "kie.publisher": fake_publisher_module}):
            ctx = FakeContext(
                [reflection_output(next_question="An independent source?")],
                {"kie_database": "/tmp/kie-emotion-test.sqlite3"},
            )
            hermes_plugin.register(ctx)
            ctx.hooks["post_llm_call"](session_id="session-A", assistant_response="A response.")
            actions = json.loads(ctx.tools["emotion_list_recent_actions"]["handler"](
                {"limit": 8}, session_id="session-A"
            ))
            result = json.loads(ctx.tools["emotion_reflect"]["handler"](
                {"action_id": actions["actions"][0]["action_id"]}, session_id="session-A"
            ))
        self.assertTrue(result["ok"])
        publisher.assert_called_once()

    def test_relative_kie_path_disables_publication(self):
        ctx = FakeContext(settings={"kie_database": "relative/kie.sqlite3"})
        hermes_plugin.register(ctx)
        self.assertNotIn("_kie_publisher", ctx.__dict__)

    def test_reflection_uses_captured_response_and_calls_hermes_once(self):
        self.hook(session_id="session-A", assistant_response="I answered 42.")
        action_id = self.call("emotion_list_recent_actions")["actions"][0]["action_id"]
        result = self.call("emotion_reflect", {"action_id": action_id})
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "awaiting_evidence")
        self.assertEqual(len(self.ctx.llm.calls), 1)
        prompt = self.ctx.llm.calls[0]["messages"][0]["content"]
        self.assertIn("I answered 42.", prompt)
        self.assertEqual(self.ctx.llm.calls[0]["task"], "emotion_reflection")
        self.assertEqual(self.ctx.llm.calls[0]["max_tokens"], 1000)

    def test_reflection_cascade_continues_only_with_new_evidence(self):
        self.ctx.llm.outputs = [
            reflection_output(next_question="Which source was selected?"),
            reflection_output(
                next_question=None,
                answer="The supplied source log records cache entry 4.",
                answer_refs=["trace-2"],
                evidence_id="trace-2",
            ),
        ]
        self.hook(session_id="session-A", assistant_response="The answer was 42.")
        action_id = self.call("emotion_list_recent_actions")["actions"][0]["action_id"]
        first = self.call("emotion_reflect", {"action_id": action_id})
        continued = self.call("emotion_continue_reflection", {
            "cascade_id": first["cascade_id"],
            "evidence": [{
                "evidence_id": "trace-2",
                "source": "system_log",
                "content": "Source selection log: cache entry 4 was selected.",
            }],
        })
        self.assertTrue(continued["ok"])
        self.assertEqual(continued["status"], "completed")
        self.assertEqual(continued["step_count"], 2)
        self.assertEqual(len(self.ctx.llm.calls), 2)

    def test_cascade_cannot_be_used_from_another_session(self):
        self.hook(session_id="session-A", assistant_response="A response.")
        action_id = self.call("emotion_list_recent_actions")["actions"][0]["action_id"]
        first = self.call("emotion_reflect", {"action_id": action_id})
        other = self.call("emotion_continue_reflection", {
            "cascade_id": first["cascade_id"],
            "evidence": [{
                "evidence_id": "trace-2",
                "source": "system_log",
                "content": "A new external system trace.",
            }],
        }, session="session-B")
        self.assertFalse(other["ok"])
        self.assertEqual(len(self.ctx.llm.calls), 1)

    def test_tools_fail_closed_without_session_context(self):
        raw = self.ctx.tools["emotion_list_recent_actions"]["handler"]({})
        self.assertFalse(json.loads(raw)["ok"])

    def test_clear_session_removes_volatile_actions_and_cascades(self):
        self.hook(session_id="session-A", assistant_response="A response.")
        result = self.call("emotion_clear_session")
        self.assertTrue(result["ok"])
        self.assertEqual(self.call("emotion_list_recent_actions")["actions"], [])

    def test_hook_ignores_empty_or_missing_response(self):
        self.hook(session_id="session-A", assistant_response="")
        self.hook(session_id="", assistant_response="Not attributable.")
        self.assertEqual(self.call("emotion_list_recent_actions")["actions"], [])


if __name__ == "__main__":
    unittest.main()
