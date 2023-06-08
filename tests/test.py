import asyncio
import sys
import time
from pathlib import Path

dir_path = Path(__file__).parent.parent
sys.path.append(f"{dir_path}")

from hikari_core import callback_hikari, hikari_config, init_hikari, set_hikari_config


async def start():
    start_time = time.time()
    set_hikari_config(use_broswer="chromium", http2=False, proxy="http://localhost:7890", token="")
    hikari_data = await init_hikari("QQ", "2622749113", "asia Remove_Carrier_Vessels recent 3")
    if hikari_data.Status == "success":
        with open('test.png', 'wb') as f:
            f.write(hikari_data.Output.Data)
            print(f"渲染完成，用时{time.time()-start_time}")
    elif hikari_data.Status == "wait":
        hikari_data.Input.Select_Index = 1
        hikari_data = await callback_hikari(hikari_data)
        if hikari_data.Status == "success":
            if hikari_config.auto_rendering and hikari_config.auto_image:
                with open('test.png', 'wb') as f:
                    f.write(hikari_data.Output.Data)
                    print(f"渲染完成，用时{time.time()-start_time}")
    if hikari_data.Status in ["error", "failed"]:
        print(hikari_data.Output.Data)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
