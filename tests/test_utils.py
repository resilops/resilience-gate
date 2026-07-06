import pytest

from src.exceptions import ActionError
from src.utils import build_url, default_headers


def test_build_url_joins_host_and_path() -> None:
    assert (
        build_url("https://runtime.example.com/", "/api/v1/test")
        == "https://runtime.example.com/api/v1/test"
    )


def test_build_url_rejects_missing_scheme() -> None:
    with pytest.raises(ActionError):
        build_url("runtime.example.com", "/api/v1/test")


def test_default_headers_returns_expected_values() -> None:
    assert default_headers() == {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "resilience-quality-gate-action/1.0.0",
    }
