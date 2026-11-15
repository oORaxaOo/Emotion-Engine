"""Emotion Engine: local-first affect modelling and bounded self-observation."""

from .appraisal import AppraisalAssessment, AppraisalInput, assess_appraisal
from .errors import (
    ConsentRequiredError,
    EmotionEngineError,
    EncryptionError,
    EncryptionKeyRequiredError,
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
from .memory import MemoryLifecycle, RetentionPolicy
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
from .store import SQLiteEmotionStore, generate_encryption_key

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
    "EncryptionError",
    "EncryptionKeyRequiredError",
    "EmotionHypothesis",
    "EmotionLabel",
    "EvidenceFragment",
    "EvidenceOrigin",
    "EventAnalysisInput",
    "InterpretationProposal",
    "InterpretationRun",
    "ModelInvocationError",
    "MemoryLifecycle",
    "ModelOutputError",
    "RecordNotFoundError",
    "RecordValidationError",
    "RetentionPolicy",
    "SQLiteEmotionStore",
    "StateTransitionRecord",
    "TextGenerator",
    "TextHypothesis",
    "UserEventRecord",
    "assess_appraisal",
    "generate_encryption_key",
    "get_concept",
    "list_concepts",
    "parse_interpretation",
    "parse_interpretation_json",
]
