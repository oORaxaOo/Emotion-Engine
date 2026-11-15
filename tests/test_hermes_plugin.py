"""Hermes plugin contract tests using the public plugin context shape."""

import json
import unittest

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
    def __init__(self, outputs=None):
        self.llm = FakeLLM(outputs)
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
