import os
import time

from loguru import logger

from .analyze import analyze_command
from .data_source import template_path
from .model import Hikari, Input, Output, Ship, UserInfo
from .utils import startup


async def init_hikari(
    platform: str,
    PlatformId: str,
    command_text: str = None,
    proxy: str = None,
    auto_rendering: bool = True,
    auto_image: bool = True
) -> Hikari:
    userinfo_data = UserInfo(Platform=platform, PlatformId=PlatformId)
    ship_data = Ship()
    input_data = Input(Command_Text=command_text, ShipInfo=ship_data)
    output_data = Output()
    hikari_data = Hikari(UserInfo=userinfo_data,
                         Input=input_data, Output=output_data)
    hikari_data = await analyze_command(hikari_data)
    logger.info(hikari_data.dict())
    return hikari_data


mtime = os.path.getmtime(template_path/"wws-info.html")
if time.time()-mtime > 86400:
    startup()
logger.add(
    "hikari-core-logs/error.log",
    rotation="00:00",
    retention="1 week",
    diagnose=False,
    level="ERROR",
    encoding="utf-8",
)
logger.add(
    "hikari-core-logs/info.log",
    rotation="00:00",
    retention="1 week",
    diagnose=False,
    level="INFO",
    encoding="utf-8",
)
logger.add(
    "hikari-core-logs/warning.log",
    rotation="00:00",
    retention="1 week",
    diagnose=False,
    level="WARNING",
    encoding="utf-8",
)
