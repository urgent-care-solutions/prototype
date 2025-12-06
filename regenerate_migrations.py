import subprocess
import logging
from pathlib import Path
from collections.abc import Generator

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s"
)
THIS_DIR = Path(__file__).parent
SERVICES_DIR = THIS_DIR / "services"
EXCLUDE_SERVICES = ["auth_service"]


def _get_service_directories() -> Generator[Path, None, None]:
    if not SERVICES_DIR.exists():
        logging.warning(f"Services directory not found: {SERVICES_DIR}")
        return

    for service in SERVICES_DIR.iterdir():
        if service.is_dir():
            yield service


def boot_pgsql_from_docker_compose() -> None:
    logging.info("Booting PostgreSQL container...")
    cmd = ["docker", "compose", "up", "-d", "pgsql"]
    subprocess.run(cmd, check=True)


def delete_old_migrations() -> None:
    logging.info("Cleaning up old migrations...")

    for service in _get_service_directories():
        versions_dir = service / "database" / "migrations" / "versions"

        if not versions_dir.exists():
            continue

        logging.info(f"Scanning {versions_dir}")
        for item in versions_dir.iterdir():
            if item.is_file() and item.name != "__init__.py":
                logging.info(f"Removing {item.name}")
                item.unlink()


def generate_migrations() -> None:
    cmd = [
        "uv",
        "run",
        "alembic",
        "revision",
        "-m",
        "Initial postgres migration",
        "--autogenerate",
    ]

    for service in _get_service_directories():
        if service.name not in EXCLUDE_SERVICES:
            logging.info(f"Generating migrations for {service.name}")
            subprocess.run(cmd, cwd=service, check=True)


def regenerate_migrations() -> None:
    try:
        boot_pgsql_from_docker_compose()
        delete_old_migrations()
        generate_migrations()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def main() -> None:
    regenerate_migrations()


if __name__ == "__main__":
    main()
