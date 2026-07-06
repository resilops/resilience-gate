import json
import os
from datetime import datetime, timezone

from src.exceptions import ActionError
from src.schema import QualityGateRunCICDStatus, QualityGateRunDecisionEnum


def format_timestamp(value: datetime | None) -> str:
    """Format timestamps consistently for logs and markdown output."""

    if value is None:
        return "-"
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def build_status_report(status: QualityGateRunCICDStatus) -> str:
    """Return a markdown report for the final quality gate status."""

    lines = [
        "## Resilience Quality Gate",
        "",
        f"- Decision: `{status.decision.value}`",
        f"- Execution status: `{status.status.value}`",
        f"- Reliability status: `{status.reliability_status.value}`",
        f"- Terminal: `{str(status.is_terminal).lower()}`",
        f"- Quality gate: `{status.quality_gate_name}` (ID `{status.quality_gate_id}`)",
        f"- Run ID: `{status.run_id}`",
        f"- Started at: `{format_timestamp(status.started_at)}`",
        f"- Finished at: `{format_timestamp(status.finished_at)}`",
        "",
        "### Raw response",
        "",
        "```json",
        json.dumps(status.model_dump(mode="json"), indent=2),
        "```",
    ]
    return "\n".join(lines)


def _append_text(path: str | None, content: str) -> None:
    """Append text to a GitHub Actions environment file when available."""

    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(content)


def write_output(name: str, value: str) -> None:
    """Write a named output for the current GitHub Actions step."""

    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return

    delimiter = f"__RESILIENCE_{name.upper()}__"
    _append_text(output_path, f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def write_step_summary(markdown: str) -> None:
    """Append markdown to the GitHub Actions step summary when available."""

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    _append_text(summary_path, f"{markdown}\n")


def emit_annotation(status: QualityGateRunCICDStatus) -> None:
    """Emit a GitHub Actions log annotation for the final gate result."""

    message = (
        f"Quality gate '{status.quality_gate_name}' run {status.run_id}: "
        f"decision={status.decision.value}, "
        f"status={status.status.value}, "
        f"reliability_status={status.reliability_status.value}"
    )
    if status.decision == QualityGateRunDecisionEnum.failed:
        print(f"::error title=Resilience Quality Gate::{message}")
        return
    if status.decision == QualityGateRunDecisionEnum.passed:
        print(f"::notice title=Resilience Quality Gate::{message}")
        return
    print(f"::warning title=Resilience Quality Gate::{message}")


def finalize_run(status: QualityGateRunCICDStatus) -> None:
    """Write outputs, summary, and fail the action when the gate blocks delivery."""

    serialized_status = json.dumps(status.model_dump(mode="json"), separators=(",", ":"))
    report = build_status_report(status)

    write_output("run-id", str(status.run_id))
    write_output("final-status", status.status.value)
    write_output("status-response", serialized_status)
    write_output("status-report", report)
    write_step_summary(report)
    emit_annotation(status)

    if status.decision != QualityGateRunDecisionEnum.passed:
        raise ActionError(
            "Quality gate did not pass with "
            f"decision={status.decision.value}, "
            f"status={status.status.value}, "
            f"reliability_status={status.reliability_status.value}.",
        )
