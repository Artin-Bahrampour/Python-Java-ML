"""Domain exceptions used by the analyzer."""


class LineageError(Exception):
    """Base class for expected analyzer errors."""


class ModelLoadError(LineageError):
    """Raised when model files cannot be safely loaded."""


class ModelParseError(LineageError):
    """Raised when a model is not one valid SQL query."""


class DuplicateModelError(LineageError):
    """Raised when two SQL files resolve to the same model name."""


class UnknownModelError(LineageError):
    """Raised when an impact request references an unknown model."""
