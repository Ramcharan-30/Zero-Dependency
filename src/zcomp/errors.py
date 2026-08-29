class ZCompError(Exception):
    """Base class for all Zero-Compress errors."""
    pass

class ArchiveValidationError(ZCompError):
    """Raised when an archive fails validation."""
    pass
