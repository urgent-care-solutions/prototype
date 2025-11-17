from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.db.database import init_db, close_db
from app.api.v1.endpoints import users, roles, clinics, health, organizations

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Clinic Config Service...")
    await init_db()
    logger.info("Clinic Config Service started successfully")
    yield
    logger.info("Shutting down Clinic Config Service...")
    await close_db()
    logger.info("Clinic Config Service shut down successfully")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(
    organizations.router, prefix=settings.API_V1_STR, tags=["organizations"]
)
app.include_router(roles.router, prefix=settings.API_V1_STR, tags=["roles"])
app.include_router(users.router, prefix=settings.API_V1_STR, tags=["users"])
app.include_router(clinics.router, prefix=settings.API_V1_STR, tags=["clinics"])


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
