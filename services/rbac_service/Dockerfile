FROM ghcr.io/astral-sh/uv:alpine3.22

WORKDIR /app

COPY . .

RUN uv sync --no-dev && \
    addgroup -g 1001 -S app && \
    adduser -u 1001 -S app -G app && \
    chown -R app:app /app

USER app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD [ "uv", "run", "healthz.py" ]

CMD [ "uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001" ]
