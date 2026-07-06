FROM python:3.12-slim

ENV POETRY_VERSION=2.2.1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
    && poetry install --only main --no-root

COPY src/ ./src/

ENTRYPOINT ["python", "-m", "src.main"]
