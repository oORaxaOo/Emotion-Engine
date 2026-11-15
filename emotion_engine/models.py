"""Validated, immutable records used by the Emotion Engine data layer.

Numeric affect/appraisal values are computational annotations. They are not
measurements of subjective experience.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TypeAlias
from uuid import uuid4

from .errors import RecordValidationError

JsonScalar: TypeAlias = str | int | float | bool | None


class EvidenceOrigin(str, Enum):
    USER_REPORTED = "user_reported"
    SYSTEM_OBSERVED = "system_observed"
    MODEL_INFERRED = "model_inferred"
    HUMAN_CONFIRMED = "human_confirmed"


class ClaimStatus(str, Enum):
    REPORTED = "reported"
    HYPOTHESIS = "hypothesis"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


class ConsentStatus(str, Enum):
    EPHEMERAL = "ephemeral"
    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"


class ActionOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _text(name: str, value: str, *, maximum: int = 2000) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RecordValidationError(f"{name} must be a non-empty string")
    if len(value) > maximum:
        raise RecordValidationError(f"{name} exceeds {maximum} characters")


def _aware_datetime(name: str, value: datetime) -> None:
    if not isinstance(value, datetime):
        raise RecordValidationError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise RecordValidationError(f"{name} must include a timezone")


def _number(
    name: str,
    value: float | None,
    *,
    minimum: float,
    maximum: float,
) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RecordValidationError(f"{name} must be a number or None")
    if not math.isfinite(float(value)):
        raise RecordValidationError(f"{name} must be finite")
    if not minimum <= float(value) <= maximum:
        raise RecordValidationError(
            f"{name} must be between {minimum} and {maximum}"
        )


def _string_tuple(name: str, values: tuple[str, ...], *, maximum: int = 400) -> None:
    if not isinstance(values, (tuple, list)):
        raise RecordValidationError(f"{name} must be a list or tuple of strings")
    for value in values:
        _text(name, value, maximum=maximum)


@dataclass(frozen=True, slots=True)
class AffectCoordinates:
    """Optional circumplex-inspired coordinates, not human emotion measurements."""

    valence: float | None = None
    arousal: float | None = None

    def __post_init__(self) -> None:
        _number("valence", self.valence, minimum=-1.0, maximum=1.0)
        _number("arousal", self.arousal, minimum=0.0, maximum=1.0)


@dataclass(frozen=True, slots=True)
class Appraisal:
    """Optional event-appraisal annotations with documented normalised scales."""

    relevance: float | None = None
    expectedness: float | None = None
    goal_congruence: float | None = None
    coping_potential: float | None = None
    normative_significance: float | None = None

    def __post_init__(self) -> None:
        _number("relevance", self.relevance, minimum=0.0, maximum=1.0)
        _number("expectedness", self.expectedness, minimum=0.0, maximum=1.0)
        _number("goal_congruence", self.goal_congruence, minimum=-1.0, maximum=1.0)
        _number("coping_potential", self.coping_potential, minimum=0.0, maximum=1.0)
        _number(
            "normative_significance",
            self.normative_significance,
            minimum=0.0,
            maximum=1.0,
        )


@dataclass(frozen=True, slots=True)
class EmotionLabel:
    """A human-readable label with explicit origin and epistemic status."""

    label: str
    origin: EvidenceOrigin
    status: ClaimStatus = ClaimStatus.HYPOTHESIS

    def __post_init__(self) -> None:
        _text("emotion label", self.label, maximum=80)
        if not isinstance(self.origin, EvidenceOrigin):
            raise RecordValidationError("origin must be an EvidenceOrigin")
        if not isinstance(self.status, ClaimStatus):
            raise RecordValidationError("status must be a ClaimStatus")
        if (
            self.origin is EvidenceOrigin.MODEL_INFERRED
            and self.status in {ClaimStatus.REPORTED, ClaimStatus.CONFIRMED}
        ):
            raise RecordValidationError(
                "a model inference cannot be marked as directly reported or confirmed"
            )


@dataclass(frozen=True, slots=True)
class UserEventRecord:
    """A user-related emotional event; persistence requires granted consent."""

    summary: str
    source_origin: EvidenceOrigin
    consent_status: ConsentStatus = ConsentStatus.PENDING
    record_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=utc_now)
    recorded_at: datetime = field(default_factory=utc_now)
    appraisal: Appraisal | None = None
    affect: AffectCoordinates | None = None
    emotion_labels: tuple[EmotionLabel, ...] = ()
    uncertainties: tuple[str, ...] = ()
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _text("summary", self.summary, maximum=4000)
        _text("record_id", self.record_id, maximum=128)
        _text("schema_version", self.schema_version, maximum=32)
        _aware_datetime("occurred_at", self.occurred_at)
        _aware_datetime("recorded_at", self.recorded_at)

        if not isinstance(self.source_origin, EvidenceOrigin):
            raise RecordValidationError("source_origin must be an EvidenceOrigin")
        if not isinstance(self.consent_status, ConsentStatus):
            raise RecordValidationError("consent_status must be a ConsentStatus")
        if self.appraisal is not None and not isinstance(self.appraisal, Appraisal):
            raise RecordValidationError("appraisal must be an Appraisal or None")
        if self.affect is not None and not isinstance(self.affect, AffectCoordinates):
            raise RecordValidationError("affect must be AffectCoordinates or None")

        if not isinstance(self.emotion_labels, (tuple, list)):
            raise RecordValidationError("emotion_labels must be a list or tuple")
        labels = tuple(self.emotion_labels)
        if any(not isinstance(item, EmotionLabel) for item in labels):
            raise RecordValidationError("emotion_labels may contain only EmotionLabel records")
        object.__setattr__(self, "emotion_labels", labels)

        if not isinstance(self.uncertainties, (tuple, list)):
            raise RecordValidationError("uncertainties must be a list or tuple")
        uncertainty_items = tuple(self.uncertainties)
        _string_tuple("uncertainty", uncertainty_items, maximum=500)
        object.__setattr__(self, "uncertainties", uncertainty_items)


@dataclass(frozen=True, slots=True)
class AgentActionRecord:
    """A technical record of a Lilith component action, not an emotion report."""

    component: str
    action: str
    summary: str
    outcome: ActionOutcome = ActionOutcome.UNKNOWN
    action_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=utc_now)
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text("component", self.component, maximum=80)
        _text("action", self.action, maximum=120)
        _text("summary", self.summary, maximum=2000)
        _text("action_id", self.action_id, maximum=128)
        _aware_datetime("occurred_at", self.occurred_at)
        if not isinstance(self.outcome, ActionOutcome):
            raise RecordValidationError("outcome must be an ActionOutcome")
        if not isinstance(self.evidence_refs, (tuple, list)):
            raise RecordValidationError("evidence_refs must be a list or tuple")
        refs = tuple(self.evidence_refs)
        _string_tuple("evidence reference", refs, maximum=500)
        object.__setattr__(self, "evidence_refs", refs)


def _json_scalar(name: str, value: JsonScalar) -> None:
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise RecordValidationError(f"{name} must be a JSON scalar")
    if isinstance(value, float) and not math.isfinite(value):
        raise RecordValidationError(f"{name} must be finite")


@dataclass(frozen=True, slots=True)
class StateTransitionRecord:
    """A bounded, auditable change to an explicit computational state variable."""

    state_key: str
    previous_value: JsonScalar
    new_value: JsonScalar
    reason: str
    transition_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=utc_now)
    cause_action_id: str | None = None

    def __post_init__(self) -> None:
        _text("state_key", self.state_key, maximum=120)
        _text("reason", self.reason, maximum=1000)
        _text("transition_id", self.transition_id, maximum=128)
        _aware_datetime("occurred_at", self.occurred_at)
        _json_scalar("previous_value", self.previous_value)
        _json_scalar("new_value", self.new_value)
        if self.cause_action_id is not None:
            _text("cause_action_id", self.cause_action_id, maximum=128)
