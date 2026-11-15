"""Project-specific exceptions."""


class EmotionEngineError(Exception):
    """Base exception for Emotion Engine."""


class RecordValidationError(EmotionEngineError, ValueError):
    """Raised when a record is incomplete or violates its schema."""


class ConsentRequiredError(EmotionEngineError, PermissionError):
    """Raised when user emotional data is saved without explicit consent."""


class RecordNotFoundError(EmotionEngineError, LookupError):
    """Raised when an update targets a record that does not exist."""


class ModelInvocationError(EmotionEngineError):
    """Raised when the injected model transport fails."""


class ModelOutputError(EmotionEngineError):
    """Raised when model output is empty, oversized, or fails validation."""


class EncryptionKeyRequiredError(EmotionEngineError, PermissionError):
    """Raised when encrypted user memories are accessed without their key."""


class EncryptionError(EmotionEngineError):
    """Raised when encrypted user memory is malformed or cannot be authenticated."""
