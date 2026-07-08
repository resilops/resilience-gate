from src.constants import USER_AGENT
from src.exceptions import ActionError


def build_url(host: str, path: str) -> str:
    """Join a validated host with a path while preserving the URL scheme."""

    normalized_host = host.rstrip("/")
    if not normalized_host.startswith("https://"):
        raise ActionError(f"Host must start with https://: {host}")
    return f"{normalized_host}/{path.lstrip('/')}"


def default_headers() -> dict[str, str]:
    """Return the default JSON headers for API requests."""

    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
