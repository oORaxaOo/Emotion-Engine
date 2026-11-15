"""Project-specific exceptions."""


class EmotionEngineError(Exception):
    """Base exception for Emotion Engine."""


class RecordValidationError(EmotionEngineError, ValueError):
    """Raised when a record is incomplete or violates its schema."""


class ConsentRequiredError(EmotionEngineError, PermissionError):
    """Raised when user emotional data is saved without explicit consent."""


class RecordNotFoundError(EmotionEngineError, LookupError):
    """Raised when an update targets a record that does not exist."""
