"""Domain-specific exceptions used by the parser and CLI."""


class OACGError(Exception):
    """Base class for expected application errors."""


class SpecLoadError(OACGError):
    """Raised when a specification cannot be read or parsed safely."""


class SpecValidationError(OACGError):
    """Raised when a parsed document is not a supported OpenAPI document."""
