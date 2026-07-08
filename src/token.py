import requests

from src.constants import USER_AGENT
from src.schema import AccessTokenModel, ActionConfig
from src.utils import build_url


class TokenService:
    """Fetch and cache machine-to-machine tokens for API requests."""

    TOKEN_PATH = "/api/v1/m2m/token"
    DEFAULT_OAUTH_SCOPES: tuple[str, ...] = (
        "res:oauth:scope:cicd:quality_gate:run:create",
        "res:oauth:scope:cicd:quality_gate:run:status",
    )

    def __init__(
        self,
        config: ActionConfig,
        scopes: tuple[str, ...] | None = None,
    ) -> None:
        self.config = config
        self.scopes = scopes or self.DEFAULT_OAUTH_SCOPES
        self.token: AccessTokenModel | None = None

    @property
    def token_url(self) -> str:
        """Return the full token endpoint URL."""
        return build_url(self.config.auth_service_host, self.TOKEN_PATH)

    def refresh_token(self) -> AccessTokenModel:
        """Return a valid cached token, refreshing it when needed."""
        if self.token is None or self.token.is_expired:
            self.token = self._fetch_token()
        return self.token

    def _fetch_token(self) -> AccessTokenModel:
        """Request a new OAuth access token from the auth service."""
        response = requests.post(
            self.token_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
            auth=(
                self.config.oauth_client_id,
                self.config.oauth_client_secret.get_secret_value(),
            ),
            data={
                "grant_type": "client_credentials",
                "scope": " ".join(self.scopes),
            },
            timeout=self.config.request_timeout_seconds,
        )
        response.raise_for_status()
        return AccessTokenModel.model_validate(response.json())
