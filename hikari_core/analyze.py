import html
import re
import traceback
from datetime import datetime
from typing import List, Tuple

from loguru import logger

from .command_select import Func, select_command
from .model import Hikari, Input, Output, Ship, UserInfo
from .moudle.wws_recent import get_RecentInfo
from .moudle.wws_info import get_AccountInfo
from .utils import match_keywords
from .data_source import servers


async def analyze_command(hikari: Hikari) -> Hikari:
    try:
        if hikari.Status == 'init':  # 状态为init时才解析
            if not hikari.Input.Command_Text:
                return hikari.error("请发送wws help查看帮助")
            hikari.Input.Command_Text = html.unescape(
                str(hikari.Input.Command_Text)).strip()
            hikari = await extract_with_special_name(hikari)
            hikari.Function, hikari.Input.Command_List = await select_command(hikari.Input.Command_List)
            hikari = await extract_with_me_or_at(hikari)
            hikari = await extract_with_function(hikari)
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("解析指令时发生错误，请确认输入参数无误")


async def extract_with_special_name(hikari: Hikari) -> Hikari:
    try:
        match = re.search(r"(\(|（)(.*?)(\)|）)",
                          hikari.Input.Command_Text)  # 是否存在（），存在则需提取出来
        if match:
            hikari.Input.AccountName = match.group(2)
            hikari.Input.Command_List = hikari.Input.Command_Text.replace(
                match.group(0), "").split()
        else:
            hikari.Input.Command_List = hikari.Input.Command_Text.split()
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("解析指令时发生错误，请确认输入参数无误")


async def extract_with_me_or_at(hikari: Hikari) -> Hikari:
    try:
        for i in hikari.Input.Command_List:
            if str(i).lower() == "me":
                hikari.Input.Search_Type = 1
                hikari.Input.Platform = hikari.UserInfo.Platform
                hikari.Input.PlatformId = hikari.UserInfo.PlatformId
                hikari.Input.Command_List.remove(i)
                break
            match = re.search(r"CQ:at,qq=(\d+)", i)
            if match:
                hikari.Input.Search_Type = 2
                hikari.Input.Platform = hikari.UserInfo.Platform
                hikari.Input.Platform = str(match.group(1))
                hikari.Input.Command_List.remove(i)
                break
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("解析指令时发生错误，请确认输入参数无误")


async def extract_with_function(hikari: Hikari) -> Hikari:
    try:
        if hikari.Function in [get_AccountInfo, get_RecentInfo]:
            if datetime.now().hour < 7:
                hikari.Input.Recent_Day = 1
            for i in hikari.Input.Command_List:
                if str(i).isdigit() and len(i) <= 3:
                    hikari.Input.Recent_Day = int(i)
                    hikari.Input.Command_List.remove(i)
            if hikari.Input.Search_Type == 3:
                if len(hikari.Input.Command_List) == 2:
                    hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                    if hikari.Input.Server:
                        hikari.Input.AccountName = str(hikari.Input.Command_List[0])
                        hikari.Input.Command_List.remove(hikari.Input.Command_List[0])
                    else:
                        return hikari.error("服务器参数输入错误")
                else:
                    return hikari.error("您似乎准备用游戏昵称查询水表，请检查参数中是否包含服务器和游戏昵称，以空格区分")
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("解析指令时发生错误，请确认输入参数无误")
