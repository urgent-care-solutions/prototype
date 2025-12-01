FROM ghcr.io/astral-sh/uv:alpine3.22

WORKDIR /app

COPY shared /app/shared
COPY services/rbac_service /app/services/rbac_service

WORKDIR /app/services/rbac_service

RUN uv sync --frozen --no-dev && \
    addgroup -g 1001 -S app && \
    adduser -u 1001 -S app -G app && \
    chown -R app:app /app

USER app

CMD [ "uv", "run", "faststream", "run", "src::main:app", "--host", "0.0.0.0", "--port", "8080" ]
