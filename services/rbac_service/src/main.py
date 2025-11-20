import asyncio
import logging

from rich.logging import RichHandler

from src.broker import app


async def main() -> None:
    FORMAT = "%(message)s"
    logging.baseConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
