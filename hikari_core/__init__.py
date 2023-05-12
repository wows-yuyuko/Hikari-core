import asyncio
import time
import traceback

import httpx
import orjson
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from data_source import template_path
from loguru import logger
from model import Hikari, Input, Output, Ship, UserInfo


async def startup():
    try:
        tasks = []
        url = "https://benx1n.oss-cn-beijing.aliyuncs.com/template_Hikari_Latest/template.json"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=20)
            result = orjson.loads(resp.content)
            for each in result:
                for name, url in each.items():
                    tasks.append(asyncio.ensure_future(
                        startup_download(url, name)))
        await asyncio.gather(*tasks)
    except Exception:
        logger.error(traceback.format_exc())
        return


async def startup_download(url, name):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=20)
        with open(template_path / name, "wb+") as file:
            file.write(resp.content)


def startup1():
    try:
        url = "https://benx1n.oss-cn-beijing.aliyuncs.com/template_Hikari_Latest/template.json"
        with httpx.Client() as client:
            resp = client.get(url, timeout=20)
            result = orjson.loads(resp.content)
            for each in result:
                for name, url in each.items():
                    resp = client.get(url, timeout=20)
                    with open(template_path / name, "wb+") as file:
                        file.write(resp.content)
        print(f"success {time.time()}")
    except Exception:
        logger.error(traceback.format_exc())
        return


async def init_hikari(platform: str, PlatformId: str, command_text: str) -> Hikari:
    userinfo_data = UserInfo(Platform=platform, PlatformId=PlatformId)
    ship_data = Ship()
    input_data = Input(Command_Text=command_text, ShipInfo=ship_data)
    output_data = Output()
    Hikari_data = Hikari(UserInfo=userinfo_data,
                         Input=input_data, Output=output_data)
    return Hikari_data


if __name__ == '__main__':
    asyncio.run(startup())
    scheduler = AsyncIOScheduler()
    scheduler.add_job(startup, 'interval', seconds=10)
    scheduler.start()
    asyncio.get_event_loop().run_forever()
