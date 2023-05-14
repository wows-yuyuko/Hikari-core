import asyncio

from hikari_core import init_hikari, set_hikari_config


async def start():
    # browser = await get_browser(use_browser="chronium")
    # await set_config(auto_rendering=False, use_browser="chronium")
    set_hikari_config(use_broswer="firefox", http2=False, proxy="http://localhost:7890")
    hikari_data = await init_hikari("QQ", "1119809439", "me")
    return
if __name__ == '__main__':
    asyncio.run(start())
