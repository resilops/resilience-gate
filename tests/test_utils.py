import unittest

from src.exceptions import ActionError
from src.utils import build_url, default_headers


class UtilsTests(unittest.TestCase):
    def test_build_url_joins_host_and_path(self) -> None:
        self.assertEqual(
            build_url("https://runtime.example.com/", "/api/v1/test"),
            "https://runtime.example.com/api/v1/test",
        )

    def test_build_url_rejects_missing_scheme(self) -> None:
        with self.assertRaises(ActionError):
            build_url("runtime.example.com", "/api/v1/test")

    def test_default_headers_returns_expected_values(self) -> None:
        self.assertEqual(
            default_headers(),
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "resilience-quality-gate-action/1.0.0",
            },
        )
