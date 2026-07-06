from unittest import mock

from src import main
from src.schema import ActionConfig


def test_build_config_parses_required_arguments() -> None:
    argv = [
        "main.py",
        "--oauth-client-id",
        "client-id",
        "--oauth-client-secret",
        "client-secret",
        "--auth-service-host",
        "https://auth.example.com",
        "--runtime-service-host",
        "https://runtime.example.com",
        "--timeout-seconds",
        "900",
    ]

    with mock.patch("sys.argv", argv):
        config = main.build_config()

    assert isinstance(config, ActionConfig)
    assert config.oauth_client_id == "client-id"
    assert config.oauth_client_secret.get_secret_value() == "client-secret"
    assert config.auth_service_host == "https://auth.example.com"
    assert config.runtime_service_host == "https://runtime.example.com"
    assert config.timeout_seconds == 900


def test_build_config_uses_module_default_timeout() -> None:
    argv = [
        "main.py",
        "--oauth-client-id",
        "client-id",
        "--oauth-client-secret",
        "client-secret",
        "--auth-service-host",
        "https://auth.example.com",
        "--runtime-service-host",
        "https://runtime.example.com",
    ]

    with mock.patch("sys.argv", argv):
        config = main.build_config()

    assert config.timeout_seconds == main.DEFAULT_TIMEOUT_SECONDS
