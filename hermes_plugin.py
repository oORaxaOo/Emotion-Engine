"""Native Hermes plugin adapter for the standalone Emotion Engine."""
from __future__ import annotations
import json, logging, threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4
try:
    from .emotion_engine import ActionOutcome, AgentActionRecord, ReflectionCascade, ReflectionEvidence, ReflectionEvidenceSource, SelfObservationEngine
    from .emotion_engine.kie_events import publish_reflection_completed, publish_reflection_failed
except ImportError:
    # Allows the same adapter to be unit-tested as a top-level module.
    from emotion_engine import ActionOutcome, AgentActionRecord, ReflectionCascade, ReflectionEvidence, ReflectionEvidenceSource, SelfObservationEngine
    from emotion_engine.kie_events import publish_reflection_completed, publish_reflection_failed

logger = logging.getLogger(__name__)
PLUGIN_ID = "emotion-engine"
TASK_NAME = "emotion_reflection"
MAX_SESSIONS, MAX_ACTIONS, MAX_CASCADES = 24, 32, 8
MAX_TEXT, MAX_TOKENS, TIMEOUT = 1600, 1000, 45

@dataclass
class _Session:
    actions: OrderedDict[str, AgentActionRecord] = field(default_factory=OrderedDict)
    cascades: OrderedDict[str, ReflectionCascade] = field(default_factory=OrderedDict)

class _VolatileState:
    """Bounded, per-session process memory. Nothing is written to disk."""
    def __init__(self):
        self.lock = threading.RLock()
        self.sessions: OrderedDict[str, _Session] = OrderedDict()

    def get(self, session_id: str) -> _Session:
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("Hermes session context is required")
        with self.lock:
            session = self.sessions.get(session_id)
            if session is None:
                session = _Session()
                self.sessions[session_id] = session
            self.sessions.move_to_end(session_id)
            while len(self.sessions) > MAX_SESSIONS:
                self.sessions.popitem(last=False)
            return session

    def capture(self, session_id: str, response: str) -> None:
        if not isinstance(response, str) or not response.strip():
            return
        summary = response.strip()
        if len(summary) > 2000:
            summary = summary[:1982] + " [truncated]"
        record = AgentActionRecord(component="hermes_llm", action="assistant_response",
                                   summary=summary, outcome=ActionOutcome.UNKNOWN)
        with self.lock:
            session = self.get(session_id)
            session.actions[record.action_id] = record
            while len(session.actions) > MAX_ACTIONS:
                session.actions.popitem(last=False)

    def add_cascade(self, session_id: str, cascade: ReflectionCascade) -> str:
        cascade_id = uuid4().hex
        with self.lock:
            session = self.get(session_id)
            session.cascades[cascade_id] = cascade
            while len(session.cascades) > MAX_CASCADES:
                session.cascades.popitem(last=False)
        return cascade_id

def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)

def _error(message: str) -> str:
    return _json({"ok": False, "error": message})

def _session_id(kwargs: dict[str, Any]) -> str:
    value = kwargs.get("session_id")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Hermes session context is required")
    return value

def _parse_evidence(raw: Any, *, maximum: int) -> tuple[ReflectionEvidence, ...]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= maximum:
        raise ValueError(f"evidence must contain 1 to {maximum} items")
    result = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"evidence_id", "source", "content"}:
            raise ValueError("evidence items require evidence_id, source, and content only")
        content = item["content"]
        if not isinstance(content, str) or len(content) > MAX_TEXT:
            raise ValueError("evidence content exceeds 1,600 characters")
        result.append(ReflectionEvidence(evidence_id=item["evidence_id"],
                                         source=ReflectionEvidenceSource(item["source"]),
                                         content=content))
    return tuple(result)

def _render(cascade_id: str, cascade: ReflectionCascade) -> dict[str, Any]:
    steps = []
    for step in cascade.steps:
        steps.append({
            "step_number": step.step_number, "assessment": step.assessment.value,
            "finding": step.finding, "finding_evidence_refs": list(step.finding_evidence_refs),
            "self_challenge": step.self_challenge,
            "self_challenge_evidence_refs": list(step.self_challenge_evidence_refs),
            "inquiry_answer": step.inquiry_answer,
            "inquiry_answer_evidence_refs": list(step.inquiry_answer_evidence_refs),
            "causal_hypotheses": [{"statement": h.statement, "evidence_refs": list(h.evidence_refs)}
                                  for h in step.causal_hypotheses],
            "limitations": list(step.limitations), "next_question": step.next_question,
            "next_question_reason": step.next_question_reason,
            "evidence_to_collect": list(step.evidence_to_collect),
        })
    return {"ok": True, "cascade_id": cascade_id, "status": cascade.status.value,
            "step_count": len(cascade.steps), "steps_remaining": cascade.steps_remaining,
            "next_question": cascade.next_question, "steps": steps,
            "notice": "Model-generated audit proposals, not verified causes or evidence of subjective experience."}

def register(ctx: Any) -> None:
    state = _VolatileState()
    try:
        kie_event_socket = ctx.get_config("kie_event_socket", None)
    except Exception:
        kie_event_socket = None
    def publish_completion(cascade: ReflectionCascade) -> None:
        # An awaiting-evidence checkpoint is not a completed reflection.
        if cascade.status.value not in {"completed", "budget_exhausted"}:
            return
        try:
            publish_reflection_completed(kie_event_socket, cascade)
        except Exception as exc:
            logger.warning("Emotion KIE completion event unavailable (%s)", type(exc).__name__)

    def publish_failure() -> None:
        try:
            publish_reflection_failed(kie_event_socket)
        except Exception as exc:
            logger.warning("Emotion KIE failure event unavailable (%s)", type(exc).__name__)

    ctx.register_auxiliary_task(TASK_NAME, display_name="Emotion Engine",
        description="Bounded self-observation of recent assistant responses using explicit evidence.")

    def on_post_llm_call(*, session_id: str = "", assistant_response: str = "", **kwargs: Any) -> None:
        # Deliberately ignore user_message and conversation_history.
        del kwargs
        try:
            state.capture(session_id, assistant_response)
        except Exception as exc:
            logger.warning("Emotion Engine response capture failed (%s)", type(exc).__name__)

    def list_actions(args: dict[str, Any], **kwargs: Any) -> str:
        try:
            session_id = _session_id(kwargs)
            limit = args.get("limit", 8)
            if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 16:
                return _error("limit must be an integer from 1 to 16")
            with state.lock:
                actions = list(state.get(session_id).actions.values())[-limit:][::-1]
                return _json({"ok": True, "storage": "volatile process memory only",
                    "actions": [{"action_id": a.action_id, "component": a.component,
                        "action": a.action, "summary": a.summary, "outcome": a.outcome.value,
                        "occurred_at": a.occurred_at.isoformat()} for a in actions]})
        except Exception:
            return _error("could not list recent actions; active session context is required")

    def make_engine():
        def generate(*, prompt: str, max_output_tokens: int, timeout_seconds: float) -> str:
            result = ctx.llm.complete(messages=[{"role": "user", "content": prompt}],
                temperature=0.0, max_tokens=min(max_output_tokens, MAX_TOKENS),
                timeout=min(timeout_seconds, TIMEOUT),
                purpose="emotion-engine.self-observation", task=TASK_NAME)
            return result.text
        return SelfObservationEngine(generate, max_steps=4, max_output_tokens=MAX_TOKENS,
                                     timeout_seconds=TIMEOUT)

    def reflect(args: dict[str, Any], **kwargs: Any) -> str:
        try:
            session_id = _session_id(kwargs)
            action_id = args.get("action_id")
            if not isinstance(action_id, str) or not action_id.strip():
                return _error("action_id is required")
            with state.lock:
                action = state.get(session_id).actions.get(action_id)
            if action is None:
                return _error("action not found in this active Hermes session")
            extra = args.get("evidence", [])
            if extra is None:
                extra = []
            if not isinstance(extra, list) or len(extra) > 11:
                return _error("at most 11 additional evidence fragments are allowed")
            own_output = ReflectionEvidence(evidence_id="assistant-response",
                source=ReflectionEvidenceSource.MODEL_OUTPUT, content=action.summary[:MAX_TEXT])
            evidence = (own_output,) + _parse_evidence(extra, maximum=11) if extra else (own_output,)
            cascade = make_engine().start(action, evidence)
            cascade_id = state.add_cascade(session_id, cascade)
            publish_completion(cascade)
            return _json(_render(cascade_id, cascade))
        except Exception as exc:
            logger.warning("Emotion Engine reflection failed (%s)", type(exc).__name__)
            publish_failure()
            return _error("reflection failed; no result was retained")

    def continue_reflection(args: dict[str, Any], **kwargs: Any) -> str:
        try:
            session_id = _session_id(kwargs)
            cascade_id = args.get("cascade_id")
            if not isinstance(cascade_id, str) or not cascade_id.strip():
                return _error("cascade_id is required")
            with state.lock:
                cascade = state.get(session_id).cascades.get(cascade_id)
            if cascade is None:
                return _error("cascade not found in this active Hermes session")
            updated = make_engine().continue_cascade(cascade, _parse_evidence(args.get("evidence"), maximum=12))
            with state.lock:
                session = state.get(session_id)
                if cascade_id not in session.cascades:
                    return _error("cascade expired before the result could be saved")
                session.cascades[cascade_id] = updated
                session.cascades.move_to_end(cascade_id)
            publish_completion(updated)
            return _json(_render(cascade_id, updated))
        except Exception as exc:
            logger.warning("Emotion Engine continuation failed (%s)", type(exc).__name__)
            publish_failure()
            return _error("continuation failed; previous valid cascade was retained")

    def clear_session(args: dict[str, Any], **kwargs: Any) -> str:
        del args
        try:
            with state.lock:
                session = state.get(_session_id(kwargs))
                action_count, cascade_count = len(session.actions), len(session.cascades)
                session.actions.clear()
                session.cascades.clear()
            return _json({"ok": True, "cleared_actions": action_count,
                "cleared_cascades": cascade_count, "storage": "volatile process memory only"})
        except Exception:
            return _error("could not clear this session")

    evidence_item = {"type": "object", "properties": {
        "evidence_id": {"type": "string"},
        "source": {"type": "string", "enum": [x.value for x in ReflectionEvidenceSource]},
        "content": {"type": "string", "maxLength": MAX_TEXT}},
        "required": ["evidence_id", "source", "content"], "additionalProperties": False}

    ctx.register_tool(name="emotion_list_recent_actions", toolset=PLUGIN_ID,
        schema={"name": "emotion_list_recent_actions",
            "description": "List recent assistant responses captured in this active Hermes session. Use this to select a response for self-review. Only assistant response text is temporarily held in process memory.",
            "parameters": {"type": "object", "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 16}},
                "required": [], "additionalProperties": False}},
        handler=list_actions)
    ctx.register_tool(name="emotion_reflect", toolset=PLUGIN_ID,
        schema={"name": "emotion_reflect",
            "description": "Audit one recent assistant response. First call emotion_list_recent_actions to obtain action_id. Add independent tool results, source records, or policy traces as evidence. Performs exactly one bounded model call and may produce one evidence-seeking question. Cannot inspect hidden reasoning.",
            "parameters": {"type": "object", "properties": {
                "action_id": {"type": "string"},
                "evidence": {"type": "array", "maxItems": 11, "items": evidence_item}},
                "required": ["action_id"], "additionalProperties": False}},
        handler=reflect)
    ctx.register_tool(name="emotion_continue_reflection", toolset=PLUGIN_ID,
        schema={"name": "emotion_continue_reflection",
            "description": "Advance a reflection cascade by exactly one step using genuinely new evidence for its previous question. No automatic recursion occurs.",
            "parameters": {"type": "object", "properties": {
                "cascade_id": {"type": "string"},
                "evidence": {"type": "array", "minItems": 1, "maxItems": 12, "items": evidence_item}},
                "required": ["cascade_id", "evidence"], "additionalProperties": False}},
        handler=continue_reflection)
    ctx.register_tool(name="emotion_clear_session", toolset=PLUGIN_ID,
        schema={"name": "emotion_clear_session",
            "description": "Clear temporarily captured assistant responses and reflection cascades for this active Hermes session.",
            "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}},
        handler=clear_session)
    ctx.register_hook("post_llm_call", on_post_llm_call)

__all__ = ["register"]
