import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from src.actions import _append_text  # noqa
from src.actions import (
    build_status_report,
    emit_annotation,
    finalize_run,
    format_timestamp,
    write_output,
    write_step_summary,
)
from src.exceptions import ActionError
from src.schema import (
    QualityGateRunCICDStatus,
    QualityGateRunDecisionEnum,
    QualityGateRunStatusEnum,
    ReliabilityStatusEnum,
)


def build_status(*, decision: QualityGateRunDecisionEnum) -> QualityGateRunCICDStatus:
    return QualityGateRunCICDStatus(
        run_id=42,
        quality_gate_id=7,
        quality_gate_name="production-check",
        status=QualityGateRunStatusEnum.success,
        reliability_status=ReliabilityStatusEnum.success,
        decision=decision,
        is_terminal=True,
        started_at=datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 7, 2, 10, 5, tzinfo=timezone.utc),
    )


def test_format_timestamp_returns_dash_for_none() -> None:
    assert format_timestamp(None) == "-"


def test_format_timestamp_normalizes_to_utc() -> None:
    local_time = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=2)))
    assert format_timestamp(local_time) == "2026-07-02T10:00:00Z"


def test_append_text_ignores_missing_path() -> None:
    _append_text(None, "ignored")


def test_build_status_report_contains_expected_fields() -> None:
    status = build_status(decision=QualityGateRunDecisionEnum.passed)

    report = build_status_report(status)

    assert "## Resilience Quality Gate" in report
    assert "Decision: `passed`" in report
    assert "Execution status: `success`" in report
    assert "Reliability status: `success`" in report
    assert "Quality gate: `production-check`" in report
    assert "Run ID: `42`" in report
    assert "Started at: `2026-07-02T10:00:00Z`" in report
    assert "Finished at: `2026-07-02T10:05:00Z`" in report
    assert "Duration: `300s`" in report
    assert "Raw response" not in report
    assert '"run_id": 42' not in report


def test_write_output_noops_without_github_output() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        write_output("name", "value")


def test_write_step_summary_noops_without_summary_path() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        write_step_summary("summary")


def test_write_output_and_summary_append_content() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        output_path = os.path.join(tempdir, "github_output.txt")
        summary_path = os.path.join(tempdir, "github_summary.md")
        with mock.patch.dict(
            os.environ,
            {
                "GITHUB_OUTPUT": output_path,
                "GITHUB_STEP_SUMMARY": summary_path,
            },
            clear=False,
        ):
            write_output("run-id", "42")
            write_step_summary("hello")

        with open(output_path, encoding="utf-8") as handle:
            output_text = handle.read()
        with open(summary_path, encoding="utf-8") as handle:
            summary_text = handle.read()

    assert "run-id<<__RESILIENCE_RUN-ID__" in output_text
    assert "42" in output_text
    assert summary_text == "hello\n"


@mock.patch("builtins.print")
def test_emit_annotation_prints_notice_for_passed(print_mock: mock.Mock) -> None:
    emit_annotation(build_status(decision=QualityGateRunDecisionEnum.passed))
    printed = print_mock.call_args[0][0]
    assert "::notice title=Resilience Quality Gate::" in printed


@mock.patch("builtins.print")
def test_emit_annotation_prints_warning_for_pending(print_mock: mock.Mock) -> None:
    emit_annotation(build_status(decision=QualityGateRunDecisionEnum.pending))
    printed = print_mock.call_args[0][0]
    assert "::warning title=Resilience Quality Gate::" in printed


@mock.patch("builtins.print")
def test_emit_annotation_prints_error_for_failed(print_mock: mock.Mock) -> None:
    emit_annotation(build_status(decision=QualityGateRunDecisionEnum.failed))
    printed = print_mock.call_args[0][0]
    assert "::error title=Resilience Quality Gate::" in printed


def test_finalize_run_writes_outputs_and_summary() -> None:
    status = build_status(decision=QualityGateRunDecisionEnum.passed)
    with tempfile.TemporaryDirectory() as tempdir:
        output_path = os.path.join(tempdir, "github_output.txt")
        summary_path = os.path.join(tempdir, "github_summary.md")
        with mock.patch.dict(
            os.environ,
            {
                "GITHUB_OUTPUT": output_path,
                "GITHUB_STEP_SUMMARY": summary_path,
            },
            clear=False,
        ):
            finalize_run(status)

        with open(output_path, encoding="utf-8") as handle:
            output_text = handle.read()
        with open(summary_path, encoding="utf-8") as handle:
            summary_text = handle.read()

    assert "run-id<<__RESILIENCE_RUN-ID__" in output_text
    assert "final-status<<__RESILIENCE_FINAL-STATUS__" in output_text
    assert (
        json.dumps(status.model_dump(mode="json"), separators=(",", ":")) in output_text
    )
    assert "## Resilience Quality Gate" in summary_text


def test_finalize_run_raises_when_decision_failed() -> None:
    status = build_status(decision=QualityGateRunDecisionEnum.failed)

    with pytest.raises(ActionError):
        finalize_run(status)


def test_finalize_run_raises_when_decision_pending() -> None:
    status = build_status(decision=QualityGateRunDecisionEnum.pending)

    with pytest.raises(ActionError):
        finalize_run(status)
