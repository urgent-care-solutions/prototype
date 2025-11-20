FROM ghcr.io/astral-sh/uv:alpine3.22

WORKDIR /app

COPY . .

RUN uv sync --no-dev && \
    addgroup -g 1001 -S app && \
    adduser -u 1001 -S app -G app && \
    chown -R app:app /app

USER app

EXPOSE 50051

CMD [ "uv", "run", "main.py" ]
