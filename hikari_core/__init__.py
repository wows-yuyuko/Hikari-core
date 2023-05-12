import asyncio
import os
import time
import traceback

import httpx
import orjson
from loguru import logger

from .data_source import template_path
from .model import Hikari, Input, Output, Ship, UserInfo
from .analyze import analyze_command


def startup():
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
    Hikari_data = analyze_command(Hikari_data)
    return Hikari_data


mtime = os.path.getmtime(template_path/"wws-info.html")
if time.time()-mtime > 86400:
    startup()
