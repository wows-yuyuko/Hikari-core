import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..HttpClient_Pool import get_client_yuyuko, recreate_client_yuyuko
from ..model import Hikari_Model
from .publicAPI import get_AccountIdByName

# from nonebot_plugin_htmlrender import html_to_pic


async def get_RecentsInfo(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status == 'init':
            if hikari.Input.Search_Type == 3:
                hikari.Input.AccountId = await get_AccountIdByName(hikari.Input.Server, hikari.Input.AccountName)
                if not isinstance(hikari.Input.AccountId, int):
                    return hikari.error(f'{hikari.Input.AccountId}')
        else:
            return hikari.error('当前请求状态错误')
        url = 'https://recent.wows.shinoaki.com:8890/api/wows/recents/day/info'
        if hikari.Input.Search_Type == 3:
            params = {
                'server': hikari.Input.Server,
                'accountId': hikari.Input.AccountId,
                'dateTime': hikari.Input.Recent_Date,
                'day': hikari.Input.Recent_Day,
                'shipId': 0,
            }
        else:
            params = {
                'server': hikari.Input.Platform,
                'accountId': hikari.Input.PlatformId,
                'dateTime': hikari.Input.Recent_Date,
                'day': hikari.Input.Recent_Day,
                'shipId': 0,
            }
        print(params)
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        hikari.Output.Yuyuko_Code = result['code']
        if result['code'] == 200:
            hikari = hikari.set_template_info('wws-info-recents.html', 1200, 100)
            return hikari.success(result['data'])
        elif result['code'] == 403:
            return hikari.failed(f"{result['message']}")
        elif result['code'] == 404 or result['code'] == 405:
            return hikari.failed(f"{result['message']}\n您可以发送wws help查看recents相关说明")
        elif result['code'] == 500:
            return hikari.failed(f"{result['message']}\n这是服务器问题，请联系雨季麻麻")
        else:
            return hikari.failed(f"{result['message']}")
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_yuyuko()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')
