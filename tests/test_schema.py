from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from pydantic import ValidationError

from src.schema import AccessTokenModel, ActionConfig


def test_action_config_validates_timeout_bounds() -> None:
    with pytest.raises(ValidationError):
        ActionConfig.model_validate(
            {
                "oauth_client_id": "client-id",
                "oauth_client_secret": "client-secret",
                "auth_service_host": "https://auth.example.com",
                "runtime_service_host": "https://runtime.example.com",
                "timeout_seconds": 0,
            }
        )


def test_access_token_expires_at_uses_safety_buffer() -> None:
    created_at = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)
    token = AccessTokenModel(
        access_token="token",
        expires_in=60,
        token_type="Bearer",
        created_at=created_at,
    )

    assert token.expires_at == created_at + timedelta(seconds=55)


def test_access_token_is_expired_true_after_expiry() -> None:
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
        assert token.is_expired is True


def test_access_token_is_expired_false_before_expiry() -> None:
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
        assert token.is_expired is False
