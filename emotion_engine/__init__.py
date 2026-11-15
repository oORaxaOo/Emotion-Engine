"""Emotion Engine: local-first affect modelling and bounded self-observation."""

from .appraisal import AppraisalAssessment, AppraisalInput, assess_appraisal
from .errors import (
    ConsentRequiredError,
    EmotionEngineError,
    RecordNotFoundError,
    RecordValidationError,
)
from .interpretation import (
    AppraisalNote,
    EmotionHypothesis,
    InterpretationProposal,
    TextHypothesis,
    parse_interpretation,
    parse_interpretation_json,
)
from .knowledge import CATALOGUE_VERSION, Concept, get_concept, list_concepts
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
    "AppraisalAssessment",
    "AppraisalInput",
    "AppraisalNote",
    "CATALOGUE_VERSION",
    "ClaimStatus",
    "Concept",
    "ConsentRequiredError",
    "ConsentStatus",
    "EmotionEngineError",
    "EmotionHypothesis",
    "EmotionLabel",
    "EvidenceOrigin",
    "InterpretationProposal",
    "RecordNotFoundError",
    "RecordValidationError",
    "SQLiteEmotionStore",
    "StateTransitionRecord",
    "TextHypothesis",
    "UserEventRecord",
    "assess_appraisal",
    "get_concept",
    "list_concepts",
    "parse_interpretation",
    "parse_interpretation_json",
]
