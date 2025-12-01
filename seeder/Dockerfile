FROM ghcr.io/astral-sh/uv:alpine3.22

WORKDIR /app

COPY . /app

RUN uv venv && \
    source .venv/bin/activate && \
    uv pip install \
    faker \
    passlib \
    bcrypt \
    sqlalchemy \
    aiosqlite \
    pydantic \
    pydantic-settings

ENV PYTHONPATH=/app

CMD ["uv", "run", "seeder/seed.py"]
