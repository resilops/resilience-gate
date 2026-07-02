import unittest
from unittest import mock

from src import main
from src.schema import ActionConfig


class MainTests(unittest.TestCase):
    def test_build_config_parses_required_arguments(self) -> None:
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

        self.assertIsInstance(config, ActionConfig)
        self.assertEqual(config.oauth_client_id, "client-id")
        self.assertEqual(config.oauth_client_secret.get_secret_value(), "client-secret")
        self.assertEqual(config.auth_service_host, "https://auth.example.com")
        self.assertEqual(config.runtime_service_host, "https://runtime.example.com")
        self.assertEqual(config.timeout_seconds, 900)

    def test_build_config_uses_module_default_timeout(self) -> None:
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

        self.assertEqual(config.timeout_seconds, main.DEFAULT_TIMEOUT_SECONDS)
