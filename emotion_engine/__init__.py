"""Emotion Engine: local-first affect modelling and bounded self-observation."""

from .appraisal import AppraisalAssessment, AppraisalInput, assess_appraisal
from .errors import (
    ConsentRequiredError,
    EmotionEngineError,
    ModelInvocationError,
    ModelOutputError,
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
from .model_adapter import (
    BoundedModelAdapter,
    EventAnalysisInput,
    EvidenceFragment,
    InterpretationRun,
    TextGenerator,
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
    "AppraisalAssessment",
    "AppraisalInput",
    "AppraisalNote",
    "BoundedModelAdapter",
    "CATALOGUE_VERSION",
    "ClaimStatus",
    "Concept",
    "ConsentRequiredError",
    "ConsentStatus",
    "EmotionEngineError",
    "EmotionHypothesis",
    "EmotionLabel",
    "EvidenceFragment",
    "EvidenceOrigin",
    "EventAnalysisInput",
    "InterpretationProposal",
    "InterpretationRun",
    "ModelInvocationError",
    "ModelOutputError",
    "RecordNotFoundError",
    "RecordValidationError",
    "SQLiteEmotionStore",
    "StateTransitionRecord",
    "TextGenerator",
    "TextHypothesis",
    "UserEventRecord",
    "assess_appraisal",
    "get_concept",
    "list_concepts",
    "parse_interpretation",
    "parse_interpretation_json",
]
