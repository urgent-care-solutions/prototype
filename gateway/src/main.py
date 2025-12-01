import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from strawberry.fastapi import GraphQLRouter

from src.config import settings
from src.core.nats_client import nats_client
from src.core.security import get_context
from src.graphql.schema import schema

# Setup Logging
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[logging.StreamHandler()],
)
_log = logging.getLogger(settings.LOGGER)


# Lifespan context to manage NATS connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    _log.info(f"Starting {settings.SERVICE_NAME}...")

    # Connect NATS Client
    try:
        await nats_client.connect()
    except Exception as e:
        _log.error(f"Failed to connect to NATS: {e}")
        # We might want to exit here depending on strictness

    yield

    # Clean up
    await nats_client.close()
    _log.info(f"{settings.SERVICE_NAME} stopped.")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# Setup GraphQL Route
graphql_app = GraphQLRouter(schema, context_getter=get_context)

app.include_router(graphql_app, prefix="/graphql")


@app.get("/healthz")
async def health_check(response: Response):
    is_connected = await nats_client.broker.ping(timeout=1.0)
    if is_connected:
        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "nats": "connected",
        }

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "unhealthy",
        "service": settings.SERVICE_NAME,
        "nats": "disconnected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
