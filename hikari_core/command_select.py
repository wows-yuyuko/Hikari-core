from dataclasses import dataclass
from typing import List, Protocol, Tuple, runtime_checkable

from .game.ban_search import get_BanInfo
from .game.box_check import check_christmas_box
from .game.help import async_update_template, check_version, get_help

# from .game.ocr import get_Random_Ocr_Pic
from .game.roll import roll_ship
from .game.sx import get_sx_info
from .moudle.publicAPI import get_ship_name
from .moudle.wws_bind import change_BindInfo, delete_BindInfo, get_BindInfo, set_BindInfo, set_special_BindInfo
from .moudle.wws_clan import get_ClanInfo
from .moudle.wws_info import get_AccountInfo
from .moudle.wws_real_game import add_listen_list, delete_listen_list, get_diff_ship, get_listen_list, reset_config
from .moudle.wws_recent import get_RecentInfo
from .moudle.wws_recents import get_RecentsInfo

# from .moudle.wws_record import get_record
from .moudle.wws_ship_info import get_ShipInfo
from .moudle.wws_ship_recent import get_ShipRecent
from .moudle.wws_shiprank import get_ShipRank


@runtime_checkable
class Func(Protocol):
    async def __call__(self, **kwargs):
        ...


@dataclass
class command:
    keywords: Tuple[str, ...]
    func: Func
    default_func: Func = None


first_command_list = [  # 同指令中越长的匹配词越靠前
    command(('切换绑定', '更换绑定', '更改绑定'), change_BindInfo),
    command(('查询绑定', '绑定查询', '绑定列表', '查绑定'), get_BindInfo),
    command(('删除绑定',), delete_BindInfo),
    command(('特殊绑定',), set_special_BindInfo),
    command(('ship.rank', 'rank'), get_ShipRank),
    command(('bind', '绑定', 'set'), set_BindInfo),
    command(('recents', '单场近期'), None, get_RecentsInfo),
    command(('recent', '近期'), None, get_RecentInfo),
    command(('ship', '单船'), None, get_ShipInfo),
    # command(("record", "历史记录"), None, get_record),
    command(('clan', '军团', '公会', '工会'), get_ClanInfo),
    # command(("随机表情包",), get_Random_Ocr_Pic),
    command(('roll', '随机'), roll_ship),
    command(('sx', '扫雪'), get_sx_info),
    command(('ban', '封号记录'), get_BanInfo),
    command(('box', 'sd', '圣诞船池'), check_christmas_box),
    command(('搜船名', '查船名', '船名'), get_ship_name),
    command(('help', '帮助'), get_help),
    command(('check_version', '检查更新'), check_version),
    command(('更新样式',), async_update_template),
    command(('查询监控', '监控列表', '查询监听', '监听列表'), get_listen_list),
    command(('测试监控',), get_diff_ship),
    command(('添加监控',), add_listen_list),
    command(('删除监控',), delete_listen_list),
    command(('重置监控',), reset_config),
]

second_command_list = [
    command(('recent', '近期'), get_ShipRecent),
    command(('ship', '单船'), get_ShipRecent),
    # command(("clan", "军团", "公会", "工会"), get_record),
    # command(("record", "历史记录"), get_record),
]


async def findFunction_and_replaceKeywords(match_list, command_List, default_func) -> Tuple[command, List]:
    for com in command_List:
        for kw in com.keywords:
            for i, match_kw in enumerate(match_list):
                if match_kw.find(kw) + 1:
                    match_list[i] = str(match_kw).replace(kw, '')
                    if not match_list[i]:  # 为空时才删除，防止未加空格没有被split切割
                        match_list.remove('')
                    return com, match_list
    return command(None, default_func, None), match_list


async def select_command(search_list) -> Tuple[Func, List]:
    command, search_list = await findFunction_and_replaceKeywords(search_list, first_command_list, get_AccountInfo)
    if command.func is None:
        command, search_list = await findFunction_and_replaceKeywords(search_list, second_command_list, command.default_func)
    return command.func, search_list
