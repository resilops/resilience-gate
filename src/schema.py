from enum import Enum
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, SecretStr


class QualityGateRunStatusEnum(str, Enum):
    """Quality gate run status identifiers."""

    queued = "queued"
    executing = "executing"
    success = "success"
    failed = "failed"


class QualityGateRunDecisionEnum(str, Enum):
    """Quality gate run decision identifiers for CI/CD consumers."""

    pending = "pending"
    passed = "passed"
    failed = "failed"


class ReliabilityStatusEnum(str, Enum):
    """Quality gate run status identifiers."""

    success = "success"
    failed = "failed"
    unknown = "unknown"


class ActionConfig(BaseModel):
    """Validated runtime configuration for the action."""

    oauth_client_id: str
    oauth_client_secret: SecretStr
    auth_service_host: str
    runtime_service_host: str

    timeout_seconds: int = Field(default=600, gt=0, lt=1200)
    request_timeout_seconds: int = Field(default=30, gt=0, lt=300)
    poll_interval_seconds: int = Field(default=10, gt=10, lt=100)


class AccessTokenModel(BaseModel):
    """Machine-to-machine access token response."""

    access_token: str = Field(..., description="Short-lived access token")
    expires_in: int = Field(..., description="Expiration time in seconds")
    token_type: str = Field(..., description="Token type")
    scope: str | None = Field(default=None, description="Requested scopes")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Time when the token was obtained",
    )

    @property
    def expires_at(self) -> datetime:
        """Return the effective expiry time with a small safety buffer."""

        return self.created_at + timedelta(seconds=max(self.expires_in - 5, 0))

    @property
    def is_expired(self) -> bool:
        """Return whether the cached token should be refreshed."""

        return datetime.now(timezone.utc) >= self.expires_at


class QualityGateRunCICDStatus(BaseModel):
    """Compact CI/CD polling response for a quality gate run."""

    run_id: int = Field(..., description="Quality gate run ID")
    quality_gate_id: int = Field(..., description="Quality gate ID")
    quality_gate_name: str = Field(..., description="Quality gate name")
    status: QualityGateRunStatusEnum = Field(..., description="Quality gate run status")
    reliability_status: ReliabilityStatusEnum = Field(..., description="Quality gate run reliability status")
    decision: QualityGateRunDecisionEnum = Field(
        ..., description="Quality gate run CI/CD decision",
    )
    is_terminal: bool = Field(
        ..., description="Whether the quality gate run has reached a terminal state",
    )
    started_at: datetime = Field(..., description="Quality gate run start timestamp")
    finished_at: datetime | None = Field(
        default=None, description="Quality gate run finish timestamp",
    )
