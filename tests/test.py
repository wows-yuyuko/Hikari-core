import asyncio

from hikari_core import init_hikari


async def start():
    hikari_data = await init_hikari("QQ", "1119809439", "wws me")
    print(hikari_data)

if __name__ == '__main__':
    asyncio.run(start())
