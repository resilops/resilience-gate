
class ActionError(Exception):
    """Raised when the GitHub Action cannot complete successfully."""

class ActionTimeoutError(ActionError):
    """Raised when the GitHub Action timed out."""
