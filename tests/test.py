import asyncio

from hikari_core import init_hikari, set_config
from hikari_core.Html_Render.browser import get_browser


async def start():
    # browser = await get_browser(use_browser="chronium")
    # await set_config(auto_rendering=False, use_browser="chronium")
    hikari_data = await init_hikari("QQ", "1119809439", "me")
    return
if __name__ == '__main__':
    asyncio.run(start())
