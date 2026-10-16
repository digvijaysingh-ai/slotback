# Slotback demo container (Hugging Face Space, Docker SDK, free CPU).
# Postgres runs embedded in the container (pgserver); the showcase day is rebuilt
# deterministically on every boot, so restarts lose nothing that matters.
FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.12.23 \
 && useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH \
    PGDATA_DIR=/tmp/pg PORT=7860 UV_COMPILE_BYTECODE=1
WORKDIR /home/user/app

COPY --chown=user pyproject.toml uv.lock README.md ./
COPY --chown=user packages ./packages
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=user slotback ./slotback
COPY --chown=user db ./db
COPY --chown=user evidence ./evidence
COPY --chown=user metrics ./metrics
COPY --chown=user evals/results/latest.json ./evals/results/latest.json
RUN uv sync --frozen --no-dev

EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import os, urllib.request; urllib.request.urlopen(f\"http://localhost:{os.environ.get('PORT', '7860')}/health\")"
CMD [".venv/bin/python", "-m", "slotback.serve"]
