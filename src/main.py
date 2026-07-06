import argparse

from src.actions import finalize_run, write_output
from src.exceptions import ActionError
from src.gate import QualityGateService
from src.schema import ActionConfig
from src.token import TokenService

DEFAULT_TIMEOUT_SECONDS = 800


def build_config() -> ActionConfig:
    """Get action config"""

    parser = argparse.ArgumentParser(description="Quality gate runner")
    parser.add_argument("--oauth-client-id", required=True)
    parser.add_argument("--oauth-client-secret", required=True)
    parser.add_argument("--auth-service-host", required=True)
    parser.add_argument("--runtime-service-host", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()
    return ActionConfig.model_validate(vars(args))


if __name__ == "__main__":
    config = build_config()
    token_service = TokenService(config=config)
    gate_service = QualityGateService(config=config, token_service=token_service)

    try:
        run_id: int = gate_service.create_run()
        write_output("run-id", str(run_id))
        final_status = gate_service.wait_for_completion(run_id=run_id)
        finalize_run(final_status)
    except Exception as e:
        raise ActionError from e
