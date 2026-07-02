# Resilience Quality Gate GitHub Action

This repository contains a public Docker-based GitHub Action that:

1. Exchanges an OAuth client ID and client secret for a machine-to-machine access token.
2. Creates a quality gate run against the runtime service.
3. Polls the quality gate run status until it reaches a terminal state or times out.

## Inputs

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `oauth-client-id` | Yes | - | OAuth client ID for the token request. |
| `oauth-client-secret` | Yes | - | OAuth client secret for the token request. |
| `auth-service-host` | Yes | - | Base URL of the auth service. Must include `http://` or `https://`. |
| `runtime-service-host` | Yes | - | Base URL of the runtime service. Must include `http://` or `https://`. |
| `timeout-seconds` | No | `600` | Maximum total wait time before the action fails. |

## Outputs

| Name | Description |
| --- | --- |
| `run-id` | Quality gate run ID from the create endpoint response. |
| `final-status` | Final normalized status reported by the status endpoint. |
| `status-response` | Final raw status response serialized as compact JSON. |
| `status-report` | Final markdown report with decision, SLO status, timestamps, and raw response details. |

## Endpoint Contract

The action calls these endpoints:

- `POST /api/v1/m2m/token`
- `POST /api/v1/cicd/quality-gates/runs`
- `GET /api/v1/cicd/quality-gates/runs/{run_id}/status`

The quality gate create request is sent with an empty JSON object body: `{}`.

The token request body is:

```json
{
  "client_id": "<oauth-client-id>",
  "client_secret": "<oauth-client-secret>",
  "grant_type": "client_credentials"
}
```

The action expects the token response to contain `access_token`.
The quality gate create response must include `id`.
The status response must match the runtime CI/CD schema returned by
`GET /api/v1/cicd/quality-gates/runs/{run_id}/status`.

When the run completes, the action:

- writes `run-id`, `final-status`, `status-response`, and `status-report` to `GITHUB_OUTPUT`
- appends a markdown summary to `GITHUB_STEP_SUMMARY`
- emits a GitHub Actions `notice`, `warning`, or `error` annotation based on the final decision
- fails the step when the final decision is `failed`

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
        uses: your-org/resilience-action@v1
        with:
          oauth-client-id: ${{ secrets.RESILIENCE_OAUTH_CLIENT_ID }}
          oauth-client-secret: ${{ secrets.RESILIENCE_OAUTH_CLIENT_SECRET }}
          auth-service-host: https://auth.example.com
          runtime-service-host: https://runtime.example.com
          timeout-seconds: "900"

      - name: Print run metadata
        run: |
          echo "Run ID: ${{ steps.resilience.outputs.run-id }}"
          echo "Final status: ${{ steps.resilience.outputs.final-status }}"
```

## Publishing

1. Push this repository to GitHub.
2. Tag a release, for example `v1.0.0`.
3. Create a major version tag that you can move forward, for example `v1`.
4. Reference the action from workflows as `owner/repo@v1`.

## Development

Run unit tests locally:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
```
