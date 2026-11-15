"""Emotion Engine: local-first affect modelling and bounded self-observation."""

from .errors import (
    ConsentRequiredError,
    EmotionEngineError,
    RecordNotFoundError,
    RecordValidationError,
)
from .models import (
    ActionOutcome,
    AffectCoordinates,
    Appraisal,
    ClaimStatus,
    ConsentStatus,
    EmotionLabel,
    EvidenceOrigin,
    AgentActionRecord,
    StateTransitionRecord,
    UserEventRecord,
)
from .store import SQLiteEmotionStore

__all__ = [
    "ActionOutcome",
    "AffectCoordinates",
    "AgentActionRecord",
    "Appraisal",
    "ClaimStatus",
    "ConsentRequiredError",
    "ConsentStatus",
    "EmotionEngineError",
    "EmotionLabel",
    "EvidenceOrigin",
    "RecordNotFoundError",
    "RecordValidationError",
    "SQLiteEmotionStore",
    "StateTransitionRecord",
    "UserEventRecord",
]
