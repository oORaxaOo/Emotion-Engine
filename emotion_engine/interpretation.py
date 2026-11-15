"""Strict, provider-neutral contract for proposed event interpretations.

The parser validates model proposals but cannot establish that an interpretation is
psychologically true. It never writes to memory or calls a model.
"""
from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .errors import RecordValidationError
from .models import Appraisal, ClaimStatus, EmotionLabel, EvidenceOrigin

INTERPRETATION_SCHEMA_VERSION = "0.1"
MAX_PAYLOAD_CHARS = 30_000
MAX_EVIDENCE_REFS = 8
MAX_HYPOTHESES = 5
MAX_LIST_ITEMS = 10

_APPRAISAL_DIMENSIONS = (
    "relevance",
    "expectedness",
    "goal_congruence",
    "coping_potential",
    "normative_significance",
)


@dataclass(frozen=True, slots=True)
class AppraisalNote:
    """One model-proposed appraisal value with traceable source references."""

    dimension: str
    value: float
    rationale: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TextHypothesis:
    """A tentative meaning or alternative explanation, linked to input evidence."""

    statement: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmotionHypothesis:
    """A model-inferred emotion label that is always explicitly hypothetical."""

    emotion: EmotionLabel
    rationale: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InterpretationProposal:
    """Validated, ephemeral interpretation output; not a stored memory."""

    source_event_id: str
    schema_version: str
    event_summary: str
    summary_evidence_refs: tuple[str, ...]
    appraisal: Appraisal
    appraisal_notes: tuple[AppraisalNote, ...]
    meaning_hypotheses: tuple[TextHypothesis, ...]
    emotion_hypotheses: tuple[EmotionHypothesis, ...]
    alternative_explanations: tuple[TextHypothesis, ...]
    unknowns: tuple[str, ...]
    clarifying_questions: tuple[str, ...]


def _fail(message: str) -> None:
    raise RecordValidationError(message)


def _object(value: Any, name: str, allowed: set[str], required: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{name} must be an object")
    keys = set(value.keys())
    if any(not isinstance(key, str) for key in keys):
        _fail(f"{name} keys must be strings")
    extra = keys - allowed
    missing = required - keys
    if extra:
        _fail(f"{name} contains unsupported fields: {', '.join(sorted(extra))}")
    if missing:
        _fail(f"{name} is missing required fields: {', '.join(sorted(missing))}")
    return value


def _text(value: Any, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{name} must be a non-empty string")
    if len(value) > maximum:
        _fail(f"{name} exceeds {maximum} characters")
    return value.strip()


def _string_list(value: Any, name: str, *, maximum_items: int, maximum_chars: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        _fail(f"{name} must be an array")
    if len(value) > maximum_items:
        _fail(f"{name} may contain at most {maximum_items} items")
    result = tuple(_text(item, name, maximum_chars) for item in value)
    if len(result) != len(set(result)):
        _fail(f"{name} must not contain duplicates")
    return result


def _evidence_refs(value: Any, name: str, allowed: frozenset[str]) -> tuple[str, ...]:
    refs = _string_list(
        value,
        name,
        maximum_items=MAX_EVIDENCE_REFS,
        maximum_chars=100,
    )
    if not refs:
        _fail(f"{name} must cite at least one supplied evidence identifier")
    unknown = set(refs) - allowed
    if unknown:
        _fail(f"{name} contains unknown evidence identifiers: {', '.join(sorted(unknown))}")
    return refs


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        _fail(f"{name} must be a finite number")
    return number


def _parse_text_hypotheses(
    value: Any,
    name: str,
    allowed: frozenset[str],
) -> tuple[TextHypothesis, ...]:
    if not isinstance(value, list):
        _fail(f"{name} must be an array")
    if len(value) > MAX_HYPOTHESES:
        _fail(f"{name} may contain at most {MAX_HYPOTHESES} items")
    parsed = []
    for index, item in enumerate(value):
        obj = _object(
            item,
            f"{name}[{index}]",
            {"statement", "evidence_refs"},
            {"statement", "evidence_refs"},
        )
        parsed.append(TextHypothesis(
            statement=_text(obj["statement"], f"{name}[{index}].statement", 1200),
            evidence_refs=_evidence_refs(
                obj["evidence_refs"], f"{name}[{index}].evidence_refs", allowed
            ),
        ))
    return tuple(parsed)


def _parse_emotions(value: Any, allowed: frozenset[str]) -> tuple[EmotionHypothesis, ...]:
    if not isinstance(value, list):
        _fail("emotion_hypotheses must be an array")
    if len(value) > MAX_HYPOTHESES:
        _fail(f"emotion_hypotheses may contain at most {MAX_HYPOTHESES} items")
    parsed = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        obj = _object(
            item,
            f"emotion_hypotheses[{index}]",
            {"label", "rationale", "evidence_refs"},
            {"label", "rationale", "evidence_refs"},
        )
        label = _text(obj["label"], f"emotion_hypotheses[{index}].label", 80)
        if label.casefold() in seen:
            _fail("emotion_hypotheses must not repeat labels")
        seen.add(label.casefold())
        parsed.append(EmotionHypothesis(
            emotion=EmotionLabel(
                label=label,
                origin=EvidenceOrigin.MODEL_INFERRED,
                status=ClaimStatus.HYPOTHESIS,
            ),
            rationale=_text(obj["rationale"], f"emotion_hypotheses[{index}].rationale", 1000),
            evidence_refs=_evidence_refs(
                obj["evidence_refs"], f"emotion_hypotheses[{index}].evidence_refs", allowed
            ),
        ))
    return tuple(parsed)


def _parse_appraisal(
    value: Any,
    allowed: frozenset[str],
) -> tuple[Appraisal, tuple[AppraisalNote, ...]]:
    if not isinstance(value, Mapping):
        _fail("appraisal must be an object")
    keys = set(value.keys())
    if any(not isinstance(key, str) for key in keys):
        _fail("appraisal keys must be strings")
    extra = keys - set(_APPRAISAL_DIMENSIONS)
    if extra:
        _fail(f"appraisal contains unsupported dimensions: {', '.join(sorted(extra))}")

    values: dict[str, float | None] = {key: None for key in _APPRAISAL_DIMENSIONS}
    notes: list[AppraisalNote] = []
    for dimension, raw_note in value.items():
        note = _object(
            raw_note,
            f"appraisal.{dimension}",
            {"value", "rationale", "evidence_refs"},
            {"value", "rationale", "evidence_refs"},
        )
        numeric_value = _number(note["value"], f"appraisal.{dimension}.value")
        values[dimension] = numeric_value
        notes.append(AppraisalNote(
            dimension=dimension,
            value=numeric_value,
            rationale=_text(note["rationale"], f"appraisal.{dimension}.rationale", 1000),
            evidence_refs=_evidence_refs(
                note["evidence_refs"], f"appraisal.{dimension}.evidence_refs", allowed
            ),
        ))

    return Appraisal(**values), tuple(notes)


def parse_interpretation(
    payload: Mapping[str, Any],
    *,
    source_event_id: str,
    allowed_evidence_ids: Iterable[str],
) -> InterpretationProposal:
    """Validate an LLM-proposed interpretation against a bounded input envelope.

    Evidence IDs must come from the event supplied to the model. This verifies
    reference integrity, not whether the model interpreted the cited evidence
    correctly. The returned object is ephemeral and is not persisted.
    """
    event_id = _text(source_event_id, "source_event_id", 128)
    if isinstance(allowed_evidence_ids, (str, bytes)):
        _fail("allowed_evidence_ids must be an iterable of identifiers, not text")
    try:
        allowed_items = tuple(allowed_evidence_ids)
    except TypeError as exc:
        raise RecordValidationError("allowed_evidence_ids must be iterable") from exc
    if (
        not allowed_items
        or len(allowed_items) > 100
        or any(
            not isinstance(item, str)
            or not item.strip()
            or item != item.strip()
            for item in allowed_items
        )
        or len(set(allowed_items)) != len(allowed_items)
    ):
        _fail("allowed_evidence_ids must contain 1–100 unique, trimmed, non-empty identifiers")
    allowed = frozenset(allowed_items)

    obj = _object(
        payload,
        "interpretation",
        {
            "schema_version",
            "event_summary",
            "summary_evidence_refs",
            "appraisal",
            "meaning_hypotheses",
            "emotion_hypotheses",
            "alternative_explanations",
            "unknowns",
            "clarifying_questions",
        },
        {
            "schema_version",
            "event_summary",
            "summary_evidence_refs",
            "appraisal",
            "meaning_hypotheses",
            "emotion_hypotheses",
            "alternative_explanations",
            "unknowns",
            "clarifying_questions",
        },
    )
    version = _text(obj["schema_version"], "schema_version", 20)
    if version != INTERPRETATION_SCHEMA_VERSION:
        _fail(f"unsupported interpretation schema_version: {version}")

    appraisal, appraisal_notes = _parse_appraisal(obj["appraisal"], allowed)
    return InterpretationProposal(
        source_event_id=event_id,
        schema_version=version,
        event_summary=_text(obj["event_summary"], "event_summary", 1600),
        summary_evidence_refs=_evidence_refs(
            obj["summary_evidence_refs"], "summary_evidence_refs", allowed
        ),
        appraisal=appraisal,
        appraisal_notes=appraisal_notes,
        meaning_hypotheses=_parse_text_hypotheses(
            obj["meaning_hypotheses"], "meaning_hypotheses", allowed
        ),
        emotion_hypotheses=_parse_emotions(obj["emotion_hypotheses"], allowed),
        alternative_explanations=_parse_text_hypotheses(
            obj["alternative_explanations"], "alternative_explanations", allowed
        ),
        unknowns=_string_list(
            obj["unknowns"], "unknowns", maximum_items=MAX_LIST_ITEMS, maximum_chars=500
        ),
        clarifying_questions=_string_list(
            obj["clarifying_questions"],
            "clarifying_questions",
            maximum_items=MAX_HYPOTHESES,
            maximum_chars=500,
        ),
    )


def parse_interpretation_json(
    raw_json: str,
    *,
    source_event_id: str,
    allowed_evidence_ids: Iterable[str],
) -> InterpretationProposal:
    """Parse bounded JSON text and reject duplicate object keys."""
    if not isinstance(raw_json, str) or not raw_json.strip():
        _fail("raw_json must be a non-empty string")
    if len(raw_json) > MAX_PAYLOAD_CHARS:
        _fail(f"raw_json exceeds {MAX_PAYLOAD_CHARS} characters")

    def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    try:
        payload = json.loads(raw_json, object_pairs_hook=no_duplicate_keys)
    except RecordValidationError:
        raise
    except (json.JSONDecodeError, TypeError, RecursionError) as exc:
        raise RecordValidationError("raw_json is not valid JSON") from exc

    return parse_interpretation(
        payload,
        source_event_id=source_event_id,
        allowed_evidence_ids=allowed_evidence_ids,
    )
