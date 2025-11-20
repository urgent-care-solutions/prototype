import asyncio

from src.broker import app


async def main() -> None:
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
