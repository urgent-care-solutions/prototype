import argparse
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

# Configuration
PYTHON_VERSION = "3.14"
DOCKER_IMAGE = "ghcr.io/astral-sh/uv:alpine3.22"

# Paths
ROOT_DIR = Path.cwd()
SERVICES_DIR = ROOT_DIR / "services"
SHARED_LIB_PATH = ROOT_DIR / "shared"


def run_cmd(cmd: list, cwd: Path):
    """Runs a shell command in a specific directory."""
    try:
        print(f"   Running: {' '.join(cmd)}...")
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"❌  Error executing: {' '.join(cmd)}")
        print(e.stderr.decode())
        sys.exit(1)


def write_file(path: Path, content: str):
    """Writes content to a file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip(), encoding="utf-8")
    print(f"📄  Created: {path.relative_to(ROOT_DIR)}")


def generate_service(service_name: str):
    # Normalize name (appointment-service -> appointment_service)
    folder_name = service_name.replace("-", "_")
    # Clean name for Docker/Env (appointment_service -> appointment)
    short_name = folder_name.replace("_service", "")

    service_path = SERVICES_DIR / folder_name

    if service_path.exists():
        print(f"❌ Error: Directory {service_path} already exists.")
        sys.exit(1)

    print(f"\n🚀 Scaffolding new service: {folder_name}")
    print(f"   Location: {service_path}")

    # 1. Initialize uv project
    service_path.mkdir(parents=True)
    run_cmd(
        ["uv", "init", "--python", PYTHON_VERSION], cwd=service_path
    )

    # 2. Add Dependencies
    print("📦 Installing dependencies...")
    # Core deps
    run_cmd(
        [
            "uv",
            "add",
            "faststream[nats]",
            "pydantic-settings",
            "sqlalchemy",
            "aiosqlite",
            "rich",
            "toml",
        ],
        cwd=service_path,
    )

    # Dev deps
    run_cmd(
        ["uv", "add", "--dev", "alembic", "ruff", "pytest"],
        cwd=service_path,
    )

    # Link Shared Library
    # Note: relative path from services/my_service to shared/
    run_cmd(
        ["uv", "add", "--editable", "../../shared"], cwd=service_path
    )

    # 3. Create File Structure

    # config.py
    env_prefix = f"PHI__{short_name.upper()}__"
    config_content = f"""
    from pathlib import Path
    import toml
    from pydantic_settings import BaseSettings, SettingsConfigDict

    THIS_DIR = Path(__file__).parent

    class Settings(BaseSettings):
        SERVICE_NAME: str
        SERVICE_DESCRIPTION: str = "Microservice for {short_name}"
        VERSION: str
        NATS_CONNECTION_STR: str = "nats://localhost:4222"
        DATABASE_URL: str = "sqlite+aiosqlite:///./database/{short_name}.db"
        LOGGER: str = "rich"

        model_config = SettingsConfigDict(
            env_file=THIS_DIR.parent / ".env",
            env_prefix="{env_prefix}",
            env_file_encoding="utf8",
        )

    with Path(THIS_DIR.parent / "pyproject.toml").open("r") as f:
        pp_data = toml.load(f)

    settings = Settings(
        SERVICE_NAME=pp_data["project"]["name"],
        VERSION=pp_data["project"]["version"],
    )
    """
    write_file(service_path / "src/config.py", config_content)

    # database.py
    db_content = """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from src.config import settings

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def get_session() -> AsyncSession:
        async with AsyncSessionLocal() as session:
            yield session
    """
    write_file(service_path / "src/database.py", db_content)

    # main.py
    main_content = """
    import asyncio
    import logging
    from contextlib import asynccontextmanager
    from faststream import FastStream
    from faststream.nats import NatsBroker
    from src.config import settings
    from src.database import engine

    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger(settings.LOGGER)

    broker = NatsBroker(settings.NATS_CONNECTION_STR)

    @asynccontextmanager
    async def lifespan(app):
        _log.info(f"Starting {settings.SERVICE_NAME}...")
        await broker.connect()
        yield
        await broker.close()
        await engine.dispose()
        _log.info(f"{settings.SERVICE_NAME} stopped.")

    app = FastStream(
        broker,
        title=settings.SERVICE_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    if __name__ == "__main__":
        asyncio.run(app.run())
    """
    write_file(service_path / "src/main.py", main_content)

    # Dockerfile
    dockerfile_content = f"""
    FROM {DOCKER_IMAGE}

    WORKDIR /app
    COPY . .
    
    # Ensure database dir exists
    RUN mkdir -p database

    RUN uv sync --no-dev && \\
        addgroup -g 1001 -S app && \\
        adduser -u 1001 -S app -G app && \\
        chown -R app:app /app

    USER app
    CMD [ "uv", "run", "src/main.py" ]
    """
    write_file(service_path / "Dockerfile", dockerfile_content)

    # .env
    env_content = f"""
    {env_prefix}SERVICE_NAME={folder_name.replace("_", "-")}
    {env_prefix}NATS_CONNECTION_STR=nats://nats:4222
    """
    write_file(service_path / ".env", env_content)

    # Cleanup
    (service_path / "hello.py").unlink(missing_ok=True)

    # Create DB/Migrations folder structure
    (service_path / "database/migrations").mkdir(
        parents=True, exist_ok=True
    )

    # Generate Alembic Configs (Optional but helpful)
    # generate_alembic_config(service_path, short_name)

    print_next_steps(folder_name, short_name)


def generate_alembic_config(service_path: Path, short_name: str):
    # alembic.ini
    alembic_ini = f"""
    [alembic]
    script_location = %(here)s/database/migrations
    prepend_sys_path = .
    sqlalchemy.url = sqlite:///database/{short_name}.db

    [loggers]
    keys = root,sqlalchemy,alembic
    [handlers]
    keys = console
    [formatters]
    keys = generic
    [logger_root]
    level = WARN
    handlers = console
    [logger_sqlalchemy]
    level = WARN
    handlers =
    qualname = sqlalchemy.engine
    [logger_alembic]
    level = INFO
    handlers =
    qualname = alembic
    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = NOTSET
    formatter = generic
    [formatter_generic]
    format = %(levelname)-5.5s [%(name)s] %(message)s
    datefmt = %H:%M:%S
    """
    write_file(service_path / "alembic.ini", alembic_ini)

    # env.py
    env_py = """
    import sys
    from logging.config import fileConfig
    from pathlib import Path
    from alembic import context
    from sqlalchemy import pool
    from sqlalchemy.ext.asyncio import async_engine_from_config

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    # Import your Base model here in the future
    # from src.models import Base
    from sqlalchemy.orm import declarative_base
    Base = declarative_base() # Placeholder until models are created

    from src.config import settings

    config = context.config
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    target_metadata = Base.metadata

    def run_migrations_offline() -> None:
        url = config.get_main_option("sqlalchemy.url")
        context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations() -> None:
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online() -> None:
        asyncio.run(run_async_migrations())

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
    """
    write_file(service_path / "database/migrations/env.py", env_py)


def print_next_steps(folder_name: str, short_name: str):
    docker_snippet = f"""
  {short_name}:
    build: ./services/{folder_name}
    container_name: {folder_name.replace("_", "-")}
    networks:
      - phi
    depends_on:
      - nats
    volumes:
      - ./services/{folder_name}/database:/app/database
"""

    print(f"\n✅ {folder_name} created successfully!")
    print("\n--- NEXT STEPS ---")
    print(
        "1. Add the following to your 'docker-compose.yaml' under 'services:':"
    )
    print(docker_snippet)
    print(f"2. cd services/{folder_name}")
    print("3. Create your models in 'src/models.py'")
    print(
        "4. Update 'database/migrations/env.py' to import your real Base model."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scaffold a new microservice using uv."
    )
    parser.add_argument(
        "name", help="Name of the service (e.g., appointment_service)"
    )

    args = parser.parse_args()

    if not SHARED_LIB_PATH.exists():
        print(
            "❌ Error: 'shared' directory not found. Are you in the project root?"
        )
        sys.exit(1)

    generate_service(args.name)
