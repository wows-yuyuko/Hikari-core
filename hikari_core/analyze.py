import html
import random
import re
import time
import traceback
from datetime import datetime

from loguru import logger

from .command_select import select_command
from .data_source import levels, nations, servers, shiptypes
from .game.ban_search import get_BanInfo
from .game.box_check import check_christmas_box
from .game.roll import roll_ship
from .game.sx import get_sx_info
from .model import Hikari_Model
from .moudle.publicAPI import get_ship_name
from .moudle.wws_bind import change_BindInfo, delete_BindInfo, get_BindInfo, set_BindInfo, set_special_BindInfo
from .moudle.wws_clan import get_ClanInfo
from .moudle.wws_info import get_AccountInfo
from .moudle.wws_real_game import add_listen_list, delete_listen_list
from .moudle.wws_recent import get_RecentInfo
from .moudle.wws_recents import get_RecentsInfo
from .moudle.wws_ship_info import get_ShipInfo
from .moudle.wws_ship_recent import get_ShipRecent
from .moudle.wws_shiprank import get_ShipRank
from .utils import match_keywords


async def analyze_command(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status == 'init':  # 状态为init时才解析
            if not hikari.Input.Command_Text:
                return hikari.error('请发送wws help查看帮助')
            if random.randint(1, 1000) == 1:
                return hikari.error('一天到晚惦记你那b水表，就nm离谱')
            hikari.Input.Command_Text = html.unescape(str(hikari.Input.Command_Text)).strip()
            hikari = await extract_with_special_name(hikari)
            hikari.Function, hikari.Input.Command_List = await select_command(hikari.Input.Command_List)
            if hikari.Input.AccountName:
                hikari.Input.Command_List.insert(0, hikari.Input.AccountName)
            hikari = await extract_with_me_or_at(hikari)
            hikari = await extract_with_function(hikari)
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('解析指令时发生错误，请确认输入参数无误')


async def extract_with_special_name(hikari: Hikari_Model) -> Hikari_Model:
    try:
        match = re.search(r'(\(|（)(.*?)(\)|）)', hikari.Input.Command_Text)  # 是否存在（），存在则需提取出来
        if match:
            hikari.Input.AccountName = match.group(2)
            hikari.Input.Command_List = hikari.Input.Command_Text.replace(match.group(0), '').split()
        else:
            hikari.Input.Command_List = hikari.Input.Command_Text.split()
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('解析指令时发生错误，请确认输入参数无误')


async def extract_with_me_or_at(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.UserInfo.Platform in ['QQ', 'QQ_CHANNEL']:
            for i in hikari.Input.Command_List:
                if str(i).lower() == 'me':
                    hikari.Input.Search_Type = 1
                    hikari.Input.Platform = hikari.UserInfo.Platform
                    hikari.Input.PlatformId = hikari.UserInfo.PlatformId
                    hikari.Input.Command_List.remove(i)
                    break
                if hikari.UserInfo.Platform == 'QQ':
                    match = re.search(r'CQ:at,qq=(\d+)', i)
                elif hikari.UserInfo.Platform == 'QQ_CHANNEL':
                    match = re.search(r'<@!(\d+)', i)
                if match:
                    hikari.Input.Search_Type = 2
                    hikari.Input.Platform = hikari.UserInfo.Platform
                    hikari.Input.PlatformId = str(match.group(1))
                    hikari.Input.Command_List.remove(i)
                    break
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('解析指令时发生错误，请确认输入参数无误')


async def extract_with_function(hikari: Hikari_Model) -> Hikari_Model:  # noqa: PLR0915
    try:
        if hikari.Function in [get_AccountInfo, get_RecentInfo, get_RecentsInfo, get_ShipInfo, get_ShipRecent]:
            hikari.Input.Recent_Date = time.strftime('%Y-%m-%d', time.localtime())
            if hikari.Function == get_RecentInfo and datetime.now().hour < 7:
                hikari.Input.Recent_Day = 1
            # 判断day,date
            delete_list = []
            for i in hikari.Input.Command_List:
                if str(i).isdigit() and len(i) <= 3:
                    hikari.Input.Recent_Day = int(i)
                    delete_list.append(i)
                try:
                    time.strptime(str(i), '%Y-%m-%d')
                    hikari.Input.Recent_Date = str(i)
                    delete_list.append(i)
                    hikari.Input.Recent_Day = 0  # 存在date时day强制为0
                except ValueError:
                    continue
            # 移除day,date
            for each in delete_list:
                hikari.Input.Command_List.remove(each)
            if hikari.Function in [get_AccountInfo, get_RecentInfo, get_RecentsInfo]:
                if hikari.Input.Search_Type == 3:
                    if len(hikari.Input.Command_List) == 2:
                        hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                        if hikari.Input.Server:
                            hikari.Input.AccountName = str(hikari.Input.Command_List[0])
                        else:
                            return hikari.error('服务器名输入错误')
                    else:
                        return hikari.error('您似乎准备用游戏昵称查询水表，请检查参数中是否包含服务器和游戏昵称，以空格分隔，顺序不限')
            elif hikari.Function in [get_ShipInfo, get_ShipRecent]:
                if hikari.Input.Search_Type == 3:
                    if len(hikari.Input.Command_List) == 3:
                        hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                        if hikari.Input.Server:
                            hikari.Input.AccountName = str(hikari.Input.Command_List[0])
                            hikari.Input.ShipInfo.Ship_Name_Cn = str(hikari.Input.Command_List[1])
                        else:
                            return hikari.error('服务器参数输入错误')
                    else:
                        return hikari.error('您似乎准备用服务器+昵称查询单船战绩，请检查参数是否缺少或溢出，以空格分隔，顺序不限')
                elif len(hikari.Input.Command_List) == 1:
                    hikari.Input.ShipInfo.Ship_Name_Cn = str(hikari.Input.Command_List[0])
                else:
                    return hikari.error('您似乎准备用me或@查询单船战绩，请检查参数是否缺少或溢出，以空格分隔，顺序不限')
        elif hikari.Function in [get_BindInfo, set_BindInfo, set_special_BindInfo, change_BindInfo, delete_BindInfo]:
            if hikari.Function == get_BindInfo and hikari.Input.Search_Type not in [1, 2]:
                return hikari.error('参数似乎出了问题呢，请使用me或@群友')
            elif hikari.Function in [set_BindInfo, set_special_BindInfo]:
                if hikari.Input.Search_Type != 3 and len(hikari.Input.Command_List) != 2:
                    return hikari.error('参数似乎输错了呢，请确保后面跟随服务器+游戏昵称')
                else:
                    # 解析双参数内的AccountName和Server
                    hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                    if hikari.Input.Server:
                        # 普通绑定时剩余的参数为AccountName
                        if hikari.Function == set_BindInfo:
                            hikari.Input.AccountName = str(hikari.Input.Command_List[0])
                        # 特殊绑定时剩余的参数为AccountId
                        elif hikari.Function == set_special_BindInfo and hikari.Input.Command_List[0].isdigit():
                            hikari.Input.AccountId = int(hikari.Input.Command_List[0])
                        else:
                            return hikari.error('请在网页版复制正确的特殊绑定指令，地址：https://wows.mgaia.top')
                        # 绑定强制为当前平台账号
                        hikari.Input.Platform = hikari.UserInfo.Platform
                        hikari.Input.PlatformId = hikari.UserInfo.PlatformId
                    else:
                        return hikari.error('服务器名输入错误')
            elif hikari.Function in [change_BindInfo, delete_BindInfo]:
                if len(hikari.Input.Command_List) not in [0, 1]:
                    return hikari.error('请检查是否仅输入了要切换的序号，也可为空进入选择列表')
                # 检查是否带序号
                delete_list = []
                if len(hikari.Input.Command_List) == 1:
                    for i in hikari.Input.Command_List:
                        if str(i).isdigit() and len(i) <= 3:
                            hikari.Input.Select_Index = int(i)
                            delete_list.append(i)
                    for each in delete_list:
                        hikari.Input.Command_List.remove(each)
                # 切换删除绑定强制为当前平台账号
                hikari.Input.Platform = hikari.UserInfo.Platform
                hikari.Input.PlatformId = hikari.UserInfo.PlatformId
        elif hikari.Function in [get_BanInfo, get_sx_info, check_christmas_box]:
            if hikari.Input.Search_Type == 3:
                if len(hikari.Input.Command_List) == 2:
                    hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                    if hikari.Input.Server:
                        hikari.Input.AccountName = str(hikari.Input.Command_List[0])
                    elif hikari.Function == get_BanInfo and hikari.Input.Server != 'cn':
                        return hikari.error('服务器名输入错误,目前仅支持国服查询')
                else:
                    return hikari.error('您似乎准备用游戏昵称查询，请检查参数中是否包含服务器和游戏昵称，以空格分隔，顺序不限')
        elif hikari.Function in [get_ship_name, roll_ship]:
            hikari.Input.ShipInfo.Ship_Nation, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, nations)
            if not hikari.Input.ShipInfo.Ship_Nation and hikari.Function == get_ship_name:
                return hikari.error('请检查国家名是否正确')

            hikari.Input.ShipInfo.Ship_Type, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, shiptypes)
            if not hikari.Input.ShipInfo.Ship_Type and hikari.Function == get_ship_name:
                return hikari.error('请检查船只类别是否正确')

            hikari.Input.ShipInfo.Ship_Tier, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, levels)
            if not hikari.Input.ShipInfo.Ship_Tier and hikari.Function == get_ship_name:
                return hikari.error('请检查船只等级是否正确')
        elif hikari.Function in [get_ShipRank]:
            if len(hikari.Input.Command_List) == 2:
                hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                if hikari.Input.Server:
                    hikari.Input.ShipInfo.Ship_Name_Cn = str(hikari.Input.Command_List[0])
                else:
                    return hikari.error('服务器名输入错误')
            else:
                return hikari.error('请检查参数中是否包含服务器和船名，以空格分隔，顺序不限')
        elif hikari.Function in [add_listen_list]:
            if len(hikari.Input.Command_List) == 3:
                hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                if hikari.Input.Server:
                    hikari.Input.AccountName = str(hikari.Input.Command_List[0])
                else:
                    return hikari.error('服务器名输入错误')
            else:
                return hikari.error('请检查参数中是否包含服务器、游戏昵称、备注昵称，以空格分隔，顺序不限')
        elif hikari.Function in [delete_listen_list]:
            if len(hikari.Input.Command_List) == 1:
                if str(hikari.Input.Command_List[0]).isdigit() and len(hikari.Input.Command_List[0]) < 3:
                    hikari.Input.Select_Index = int(hikari.Input.Command_List[0])
                else:
                    return hikari.error('请确认输入序号是否正确')
            else:
                return hikari.error('请检查是否仅输入了要删除的监控序号')
        elif hikari.Function in [get_ClanInfo]:
            if hikari.Input.Search_Type == 3:
                if len(hikari.Input.Command_List) == 2:
                    hikari.Input.Server, hikari.Input.Command_List = await match_keywords(hikari.Input.Command_List, servers)
                    if hikari.Input.Server:
                        hikari.Input.ClanName = str(hikari.Input.Command_List[0])
                    else:
                        return hikari.error('服务器名输入错误')
                else:
                    return hikari.error('您似乎准备用公会TAG查询水表，请检查参数中是否包含服务器和公会TAG，以空格分隔，顺序不限')
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('解析指令时发生错误，请确认输入参数无误')
