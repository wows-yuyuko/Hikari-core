import asyncio
import sys
from pathlib import Path

dir_path = Path(__file__).parent.parent
sys.path.append(f"{dir_path}")

from hikari_core import hikari_config, init_hikari, set_hikari_config


async def start():
    set_hikari_config(use_broswer="chromium", http2=False, proxy="http://localhost:7890")
    hikari_data = await init_hikari("QQ", "1119809439", "me")
    if hikari_config.auto_rendering and hikari_config.auto_image:
        with open('test.png', 'wb') as f:
            f.write(hikari_data.Output.Data)
    await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(start())
