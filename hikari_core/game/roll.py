import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..HttpClient_Pool import get_client_yuyuko, recreate_client_yuyuko
from ..model import Hikari_Model


async def roll_ship(hikari: Hikari_Model):
    try:
        if not hikari.Input.ShipInfo.Ship_Nation:
            hikari.Input.ShipInfo.Ship_Nation = ''
        if not hikari.Input.ShipInfo.Ship_Tier:
            hikari.Input.ShipInfo.Ship_Tier = ''
        if not hikari.Input.ShipInfo.Ship_Type:
            hikari.Input.ShipInfo.Ship_Type = ''
        params = {
            'accountId': hikari.UserInfo.PlatformId,
            'server': hikari.UserInfo.Platform,
            'county': hikari.Input.ShipInfo.Ship_Nation,
            'level': hikari.Input.ShipInfo.Ship_Tier,
            'shipName': '',
            'shipType': hikari.Input.ShipInfo.Ship_Type,
        }
        url = 'https://api.wows.shinoaki.com/public/wows/roll/ship/roll'
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.post(url, json=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            return hikari.success(f"本次roll到了{result['data']['shipNameCn']}")
        elif result['code'] == 403:
            return hikari.failed(f"{result['message']}\n请先绑定账号")
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
