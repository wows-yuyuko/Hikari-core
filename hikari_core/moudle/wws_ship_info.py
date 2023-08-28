import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..HttpClient_Pool import get_client_yuyuko, recreate_client_yuyuko
from ..model import Hikari_Model
from .publicAPI import check_yuyuko_cache, get_AccountIdByName, get_MyShipRank_yuyuko, get_ship_byName


async def get_ShipInfo(hikari: Hikari_Model) -> Hikari_Model:  # noqa: PLR0915
    try:
        if hikari.Status == 'init':
            shipList = await get_ship_byName(hikari.Input.ShipInfo.Ship_Name_Cn)
            if shipList:
                if len(shipList) < 2:
                    hikari.Input.ShipInfo = shipList[0]
                else:
                    hikari.Input.Select_Data = shipList
                    hikari.set_template_info('select-ship.html', 360, 100)
                    return hikari.wait(shipList)
            else:
                return hikari.failed('找不到船，请确认船名是否正确，可以使用【wws 查船名】查询船只中英文')
        elif hikari.Status == 'wait':
            if hikari.Input.Select_Data and hikari.Input.Select_Index and hikari.Input.Select_Index <= len(hikari.Input.Select_Data):
                hikari.Input.ShipInfo = hikari.Input.Select_Data[hikari.Input.Select_Index - 1]
            else:
                return hikari.error('请选择有效的序号')
        else:
            return hikari.error('当前请求状态错误')

        if hikari.Input.Search_Type == 3:
            hikari.Input.AccountId = await get_AccountIdByName(hikari.Input.Server, hikari.Input.AccountName)
            if not isinstance(hikari.Input.AccountId, int):
                return hikari.error(f'{hikari.Input.AccountId}')

        if hikari.Input.Search_Type == 3:
            is_cache = await check_yuyuko_cache(hikari.Input.Server, hikari.Input.AccountId)
        else:
            is_cache = await check_yuyuko_cache(hikari.Input.Platform, hikari.Input.PlatformId)
        if is_cache:
            logger.success('上报数据成功')
        else:
            logger.success('跳过上报数据，直接请求')

        url = 'https://v3-api.wows.shinoaki.com:8443/public/wows/account/ship/info'
        if hikari.Input.Search_Type == 3:
            params = {'server': hikari.Input.Server, 'accountId': hikari.Input.AccountId, 'shipId': hikari.Input.ShipInfo.Ship_Id}
        else:
            params = {'server': hikari.Input.Platform, 'accountId': hikari.Input.PlatformId, 'shipId': hikari.Input.ShipInfo.Ship_Id}

        ranking = await get_MyShipRank_yuyuko(params)
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        hikari.Output.Yuyuko_Code = result['code']

        if result['code'] == 200 and result['data']:
            if result['data']['typeInfo']['PVP']['battle'] or result['data']['typeInfo']['RANK_SOLO']['battle']:
                hikari.set_template_info('wws-ship.html', 800, 100)
                result['data']['shipRank'] = ranking
                return hikari.success(result['data'])
            else:
                return hikari.failed('查询不到战绩数据')
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
