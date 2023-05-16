import html
import re
import traceback
from datetime import datetime

from loguru import logger

from .command_select import select_command
from .data_source import servers
from .model import Hikari_Model
from .moudle.wws_info import get_AccountInfo
from .moudle.wws_recent import get_RecentInfo
from .moudle.wws_ship_info import get_ShipInfo
from .utils import match_keywords


async def analyze_command(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status == "init":  # 状态为init时才解析
            if not hikari.Input.Command_Text:
                return hikari.error("请发送wws help查看帮助")
            hikari.Input.Command_Text = html.unescape(str(hikari.Input.Command_Text)).strip()
            hikari = await extract_with_special_name(hikari)
            hikari.Function, hikari.Input.Command_List = await select_command(hikari.Input.Command_List)
            hikari = await extract_with_me_or_at(hikari)
            hikari = await extract_with_function(hikari)
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("解析指令时发生错误，请确认输入参数无误")


async def extract_with_special_name(hikari: Hikari_Model) -> Hikari_Model:
    try:
        match = re.search(r"(\(|（)(.*?)(\)|）)", hikari.Input.Command_Text)  # 是否存在（），存在则需提取出来
        if match:
            hikari.Input.AccountName = match.group(2)
            hikari.Input.Command_List = hikari.Input.Command_Text.replace(match.group(0), "").split()
        else:
            hikari.Input.Command_List = hikari.Input.Command_Text.split()
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("解析指令时发生错误，请确认输入参数无误")


async def extract_with_me_or_at(hikari: Hikari_Model) -> Hikari_Model:
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


async def extract_with_function(hikari: Hikari_Model) -> Hikari_Model:
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
                    else:
                        return hikari.error("服务器名输入错误")
                else:
                    return hikari.error("您似乎准备用游戏昵称查询水表，请检查参数中是否包含服务器和游戏昵称，以空格分隔，顺序不限")

        elif hikari.Function in [get_ShipInfo]:
            if hikari.Input.Search_Type == 3:
                if len(hikari.Input.Command_List) == 3:
                    hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                    if hikari.Input.Server:
                        hikari.Input.AccountName = str(hikari.Input.Command_List[0])
                        hikari.Input.ShipInfo.Ship_Name = str(hikari.Input.Command_List[1])
                    else:
                        return hikari.error("服务器参数输入错误")
                else:
                    return hikari.error("您似乎准备用服务器+昵称查询单船总体战绩，请检查参数是否缺少或溢出，以空格分隔，顺序不限")
            else:
                if len(hikari.Input.Command_List) == 1:
                    hikari.Input.ShipInfo.Ship_Name = str(hikari.Input.Command_List[0])
                else:
                    return hikari.error("您似乎准备用me或@查询单船总体战绩，请检查参数是否缺少或溢出，以空格分隔，顺序不限")
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("解析指令时发生错误，请确认输入参数无误")
