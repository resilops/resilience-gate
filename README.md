# Resilience Quality Gate

[![Tests](https://github.com/resilops/resilience-gate/actions/workflows/test.yaml/badge.svg)](https://github.com/resilops/resilience-gate/actions/workflows/test.yaml)
[![codecov](https://codecov.io/gh/resilops/resilience-gate/graph/badge.svg)](https://codecov.io/gh/resilops/resilience-gate)
[![Release](https://img.shields.io/github/v/release/resilops/resilience-gate)](https://github.com/resilops/resilience-gate/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/resilops/resilience-gate/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://github.com/resilops/resilience-gate/blob/main/pyproject.toml)

Run a Resilience quality gate in GitHub Actions and block delivery unless the
runtime returns `decision=passed`.

This action:

- authenticates with your Resilience auth service using an OAuth client
- creates a Quality Gate Run
- polls the run until it completes or times out
- writes a readable report to the GitHub Actions step summary
- fails the step unless the final decision is `passed`

## Usage

```yaml
name: Quality Gate

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  resilience-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Run resilience quality gate
        id: resilience
        uses: resilops/resilience-gate@v1
        with:
          oauth-client-id: ${{ secrets.RESILIENCE_OAUTH_CLIENT_ID }}
          oauth-client-secret: ${{ secrets.RESILIENCE_OAUTH_CLIENT_SECRET }}
          auth-service-host: https://auth.example.com
          runtime-service-host: https://runtime.example.com
          timeout-seconds: "900"

      - name: Use action outputs
        run: |
          echo "Run ID: ${{ steps.resilience.outputs.run-id }}"
          echo "Runtime status: ${{ steps.resilience.outputs.final-status }}"
```

## Inputs

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `oauth-client-id` | Yes | - | OAuth client ID for machine-to-machine authentication. |
| `oauth-client-secret` | Yes | - | OAuth client secret for machine-to-machine authentication. |
| `auth-service-host` | Yes | - | Base URL of the Resilience auth service. Must use `https://`. |
| `runtime-service-host` | Yes | - | Base URL of the Resilience runtime service. Must use `https://`. |
| `timeout-seconds` | No | `600` | Maximum time to wait for the quality gate to finish. |

## Outputs

| Name | Description |
| --- | --- |
| `run-id` | Quality gate run identifier. |
| `final-status` | Final runtime execution status. |
| `status-response` | Final `QualityGateRunCICDStatus` payload as compact JSON. |
| `status-report` | Markdown report written to the step summary and exposed as an output. |

## Behavior

The action trusts the runtime as the source of truth.

- while the runtime response is non-terminal, the action keeps polling
- when the runtime finishes, the action succeeds only if `decision=passed`
- any other final decision causes the step to fail

On completion, the action also:

- writes a report to `GITHUB_STEP_SUMMARY`
- emits a GitHub Actions annotation with the final decision

## What You See in GitHub Actions

The step summary includes:

- decision
- execution status
- reliability status
- quality gate name and run ID
- start and finish timestamps
- the raw final runtime payload

This makes it easy to diagnose why a gate passed or failed without digging
through raw logs.

## Versioning

For public usage, publish a stable major tag such as `v1` and reference the
action as:

```yaml
uses: resilops/resilience-gate@v1
```

## Local Testing

```bash
poetry install
poetry run pytest
```
