import time
import requests

from src.exceptions import ActionTimeoutError
from src.schema import ActionConfig, QualityGateRunCICDStatus
from src.token import TokenService
from src.utils import build_url, default_headers


class QualityGateService:
    """Create quality gate runs and poll them until they reach a terminal state."""

    CREATE_PATH = "/api/v1/cicd/quality-gates/runs"
    STATUS_PATH_TEMPLATE = "/api/v1/cicd/quality-gates/runs/{run_id}/status"

    def __init__(
        self, config: ActionConfig, token_service: TokenService,
    ) -> None:
        """Initialize the quality gate service with shared config and auth access."""

        self.config = config
        self.token_service = token_service

    def _request(self, method: str, url: str, json: dict | None = None) -> dict:
        """Perform an authenticated JSON request against the runtime service."""

        access_token = self.token_service.refresh_token().access_token
        headers = {
            **default_headers(), "Authorization": f"Bearer {access_token}",
        }
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_run(self) -> int:
        """Create a quality gate run and return its run ID."""

        url = build_url(self.config.runtime_service_host, self.CREATE_PATH)
        response = self._request("POST", url, json={})
        return response["id"]

    def fetch_status(self, run_id: int) -> QualityGateRunCICDStatus:
        """Fetch and normalize the current quality gate run status."""

        path = self.STATUS_PATH_TEMPLATE.format(run_id=run_id)
        url = build_url(self.config.runtime_service_host, path)
        response = self._request("GET", url)
        return QualityGateRunCICDStatus.model_validate(response)

    def wait_for_completion(self, run_id: int) -> QualityGateRunCICDStatus:
        """Poll the status endpoint until completion or effective timeout."""

        deadline = time.monotonic() + self.config.timeout_seconds
        while True:
            status = self.fetch_status(run_id)
            if status.is_terminal:
                return status

            if time.monotonic() >= deadline:
                raise ActionTimeoutError(
                    "Timed out after "
                    f"{self.config.timeout_seconds} seconds waiting for "
                    f"quality gate run {run_id}.",
                )

            time.sleep(self.config.poll_interval_seconds)
