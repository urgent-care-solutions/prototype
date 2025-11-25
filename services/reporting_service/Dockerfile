FROM ghcr.io/astral-sh/uv:alpine3.22

WORKDIR /app
COPY . .

# Ensure database dir exists
RUN mkdir -p database

RUN uv sync --no-dev && \
    addgroup -g 1001 -S app && \
    adduser -u 1001 -S app -G app && \
    chown -R app:app /app

USER app
CMD [ "uv", "run", "src/main.py" ]