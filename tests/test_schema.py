import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from pydantic import ValidationError

from src.schema import AccessTokenModel, ActionConfig


class SchemaTests(unittest.TestCase):
    def test_action_config_validates_timeout_bounds(self) -> None:
        with self.assertRaises(ValidationError):
            ActionConfig.model_validate(
                {
                    "oauth_client_id": "client-id",
                    "oauth_client_secret": "client-secret",
                    "auth_service_host": "https://auth.example.com",
                    "runtime_service_host": "https://runtime.example.com",
                    "timeout_seconds": 0,
                }
            )

    def test_access_token_expires_at_uses_safety_buffer(self) -> None:
        created_at = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)
        token = AccessTokenModel(
            access_token="token",
            expires_in=60,
            token_type="Bearer",
            created_at=created_at,
        )

        self.assertEqual(token.expires_at, created_at + timedelta(seconds=55))

    def test_access_token_is_expired_true_after_expiry(self) -> None:
        created_at = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)
        token = AccessTokenModel(
            access_token="token",
            expires_in=10,
            token_type="Bearer",
            created_at=created_at,
        )

        frozen_now = created_at + timedelta(seconds=6)
        with mock.patch("src.schema.datetime") as datetime_mock:
            datetime_mock.now.return_value = frozen_now
            self.assertTrue(token.is_expired)

    def test_access_token_is_expired_false_before_expiry(self) -> None:
        created_at = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)
        token = AccessTokenModel(
            access_token="token",
            expires_in=30,
            token_type="Bearer",
            created_at=created_at,
        )

        frozen_now = created_at + timedelta(seconds=10)
        with mock.patch("src.schema.datetime") as datetime_mock:
            datetime_mock.now.return_value = frozen_now
            self.assertFalse(token.is_expired)

