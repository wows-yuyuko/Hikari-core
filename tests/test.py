import asyncio

from hikari_core import init_hikari


async def start():
    hikari_data = await init_hikari("QQ", "1119809439", "asia 123456 recent 30")

if __name__ == '__main__':
    asyncio.run(start())
