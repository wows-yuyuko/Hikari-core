import asyncio

from hikari_core import init_hikari, set_config


async def start():
    await set_config(use_browser="chromium")
    hikari_data = await init_hikari("QQ", "1119809439", "")
    return
if __name__ == '__main__':
    asyncio.run(start())
