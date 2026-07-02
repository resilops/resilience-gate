import unittest
from datetime import datetime, timezone
from unittest import mock

from src.exceptions import ActionError
from src.gate import QualityGateService
from src.schema import (
    ActionConfig,
    QualityGateRunDecisionEnum,
    QualityGateRunStatusEnum,
    SLOStatusEnum,
)


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


def build_status_payload(*, is_terminal: bool) -> dict:
    return {
        "run_id": 42,
        "quality_gate_id": 7,
        "quality_gate_name": "prod-gate",
        "status": QualityGateRunStatusEnum.success.value
        if is_terminal
        else QualityGateRunStatusEnum.executing.value,
        "slo_status": SLOStatusEnum.success.value,
        "decision": QualityGateRunDecisionEnum.passed.value
        if is_terminal
        else QualityGateRunDecisionEnum.pending.value,
        "is_terminal": is_terminal,
        "started_at": datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc).isoformat(),
        "finished_at": datetime(2026, 7, 2, 10, 5, tzinfo=timezone.utc).isoformat()
        if is_terminal
        else None,
    }


class QualityGateServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = build_config()
        self.token_service = mock.Mock()
        self.token_service.refresh_token.return_value.access_token = "test-token"
        self.service = QualityGateService(
            config=self.config,
            token_service=self.token_service,
        )

    @mock.patch("src.gate.requests.request")
    def test_request_adds_auth_headers_and_returns_json(self, request_mock: mock.Mock) -> None:
        response = mock.Mock()
        response.json.return_value = {"id": 11}
        request_mock.return_value = response

        result = self.service._request("POST", "https://runtime.example.com/path", json={})

        self.assertEqual(result, {"id": 11})
        request_mock.assert_called_once_with(
            method="POST",
            url="https://runtime.example.com/path",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "resilience-quality-gate-action/1.0.0",
                "Authorization": "Bearer test-token",
            },
            json={},
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()

    def test_create_run_uses_cicd_create_endpoint(self) -> None:
        with mock.patch.object(self.service, "_request", return_value={"id": 99}) as request_mock:
            run_id = self.service.create_run()

        self.assertEqual(run_id, 99)
        request_mock.assert_called_once_with(
            "POST",
            "https://runtime.example.com/api/v1/cicd/quality-gates/runs",
            json={},
        )

    def test_fetch_status_validates_runtime_payload(self) -> None:
        payload = build_status_payload(is_terminal=True)
        with mock.patch.object(self.service, "_request", return_value=payload) as request_mock:
            status = self.service.fetch_status(run_id=42)

        self.assertEqual(status.run_id, 42)
        self.assertTrue(status.is_terminal)
        request_mock.assert_called_once_with(
            "GET",
            "https://runtime.example.com/api/v1/cicd/quality-gates/runs/42/status",
        )

    def test_wait_for_completion_returns_immediately_for_terminal_status(self) -> None:
        terminal = mock.Mock(is_terminal=True)

        with mock.patch.object(self.service, "fetch_status", return_value=terminal) as fetch_mock:
            with mock.patch("src.gate.time.sleep") as sleep_mock:
                result = self.service.wait_for_completion(run_id=42)

        self.assertIs(result, terminal)
        fetch_mock.assert_called_once_with(42)
        sleep_mock.assert_not_called()

    def test_wait_for_completion_polls_until_terminal(self) -> None:
        first = mock.Mock(is_terminal=False)
        second = mock.Mock(is_terminal=True)

        with mock.patch.object(self.service, "fetch_status", side_effect=[first, second]) as fetch_mock:
            with mock.patch("src.gate.time.monotonic", side_effect=[100.0, 105.0]):
                with mock.patch("src.gate.time.sleep") as sleep_mock:
                    result = self.service.wait_for_completion(run_id=42)

        self.assertIs(result, second)
        self.assertEqual(fetch_mock.call_count, 2)
        sleep_mock.assert_called_once_with(self.config.poll_interval_seconds)

    def test_wait_for_completion_raises_on_timeout(self) -> None:
        non_terminal = mock.Mock(is_terminal=False)

        with mock.patch.object(self.service, "fetch_status", return_value=non_terminal):
            with mock.patch("src.gate.time.monotonic", side_effect=[100.0, 161.0]):
                with self.assertRaises(ActionError) as context:
                    self.service.wait_for_completion(run_id=42)

        self.assertIn("Timed out after 60 seconds waiting for quality gate run 42.", str(context.exception))
