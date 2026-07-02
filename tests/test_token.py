import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from src.schema import AccessTokenModel, ActionConfig
from src.token import TokenService


def build_config(**overrides: object) -> ActionConfig:
    data = {
        "oauth_client_id": "client-id",
        "oauth_client_secret": "client-secret",
        "auth_service_host": "https://auth.example.com",
        "runtime_service_host": "https://runtime.example.com",
        "timeout_seconds": 60,
        "request_timeout_seconds": 25,
        "poll_interval_seconds": 11,
    }
    data.update(overrides)
    return ActionConfig.model_validate(data)


class TokenServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = build_config()

    def test_token_url_uses_auth_host(self) -> None:
        service = TokenService(config=self.config)
        self.assertEqual(service.token_url, "https://auth.example.com/api/v1/m2m/token")

    @mock.patch("src.token.requests.post")
    def test_fetch_token_posts_expected_payload(self, post_mock: mock.Mock) -> None:
        response = mock.Mock()
        response.json.return_value = {
            "access_token": "abc",
            "expires_in": 60,
            "token_type": "Bearer",
            "scope": "scope-a scope-b",
        }
        post_mock.return_value = response
        service = TokenService(config=self.config, scopes=("scope-a", "scope-b"))

        token = service._fetch_token()

        self.assertEqual(token.access_token, "abc")
        post_mock.assert_called_once_with(
            "https://auth.example.com/api/v1/m2m/token",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "resilience-quality-gate-action/1.0.0",
            },
            json={
                "client_id": "client-id",
                "client_secret": "client-secret",
                "grant_type": "client_credentials",
                "scope": "scope-a scope-b",
            },
            timeout=25,
        )
        response.raise_for_status.assert_called_once_with()

    def test_refresh_token_returns_cached_token_when_valid(self) -> None:
        service = TokenService(config=self.config)
        service.token = AccessTokenModel(
            access_token="cached",
            expires_in=60,
            token_type="Bearer",
            created_at=datetime.now(timezone.utc),
        )

        with mock.patch.object(service, "_fetch_token") as fetch_mock:
            token = service.refresh_token()

        self.assertEqual(token.access_token, "cached")
        fetch_mock.assert_not_called()

    def test_refresh_token_fetches_new_token_when_missing(self) -> None:
        service = TokenService(config=self.config)
        fresh = AccessTokenModel(
            access_token="fresh",
            expires_in=60,
            token_type="Bearer",
            created_at=datetime.now(timezone.utc),
        )

        with mock.patch.object(service, "_fetch_token", return_value=fresh) as fetch_mock:
            token = service.refresh_token()

        self.assertIs(token, fresh)
        fetch_mock.assert_called_once_with()

    def test_refresh_token_fetches_new_token_when_expired(self) -> None:
        service = TokenService(config=self.config)
        service.token = AccessTokenModel(
            access_token="stale",
            expires_in=10,
            token_type="Bearer",
            created_at=datetime.now(timezone.utc) - timedelta(seconds=15),
        )
        fresh = AccessTokenModel(
            access_token="fresh",
            expires_in=60,
            token_type="Bearer",
            created_at=datetime.now(timezone.utc),
        )

        with mock.patch.object(service, "_fetch_token", return_value=fresh) as fetch_mock:
            token = service.refresh_token()

        self.assertIs(token, fresh)
        fetch_mock.assert_called_once_with()

