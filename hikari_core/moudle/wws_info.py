import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout
from loguru import logger

from ..HttpClient_Pool import client_yuyuko
from ..model import Hikari
from .publicAPI import check_yuyuko_cache, get_AccountIdByName


async def get_AccountInfo(hikari: Hikari) -> Hikari:
    try:
        if hikari.Status == "init":
            if hikari.Input.Search_Type == 3:
                hikari.Input.AccountId = await get_AccountIdByName(hikari.Input.Server, hikari.Input.AccountName)
                if not isinstance(hikari.Input.AccountId, int):
                    return hikari.error(f"{hikari.Input.AccountId}")
        else:
            return hikari.error("当前请求状态错误")
        is_cache = await check_yuyuko_cache(hikari.Input.Server, hikari.Input.AccountId)
        if is_cache:
            logger.success("上报数据成功")
        else:
            logger.success("跳过上报数据，直接请求")
        url = "https://api.wows.shinoaki.com/public/wows/account/user/info"
        if hikari.Input.Search_Type == 3:
            params = {"server": hikari.Input.Server,
                      "accountId": hikari.Input.AccountId}
        else:
            params = {"server": hikari.Input.Platform,
                      "accountId": hikari.Input.PlatformId}
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        logger.success(
            f"本次请求总耗时{resp.elapsed.total_seconds()*1000}，服务器计算耗时:{result['queryTime']}")
        if result["code"] == 200 and result["data"]:
            hikari.Output.Template = "wws-info.html"
            hikari.Output.Width = 920
            hikari.Output.Height = 1000
            return hikari.success(result["data"])
        elif result["code"] == 403:
            return hikari.success(f"{result['message']}\n请先绑定账号")
        elif result["code"] == 500:
            return hikari.success(f"{result['message']}\n这是服务器问题，请联系雨季麻麻")
        else:
            return hikari.success(f"{result['message']}")
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.erroe("请求超时了，请过会儿再尝试哦~")
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error("wuwuwu出了点问题，请联系麻麻解决")
