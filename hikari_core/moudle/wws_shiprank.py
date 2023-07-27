import traceback
from asyncio.exceptions import TimeoutError

import orjson
from bs4 import BeautifulSoup
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..data_source import number_url_homes, set_ShipRank_Numbers
from ..HttpClient_Pool import get_client_default, get_client_yuyuko, recreate_client_default, recreate_client_yuyuko
from ..model import Hikari_Model
from .publicAPI import get_ship_byName


async def get_ShipRank(hikari: Hikari_Model):
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

        if not hikari.Input.Server == 'cn':
            hikari = await search_ShipRank_Yuyuko(hikari)
            # 无缓存，去Number爬
            if not hikari.Status == 'success':
                hikari, numbers_data = await search_ShipRank_Numbers(hikari)
                # 上报缓存
                if hikari.Status == 'success':
                    await post_ShipRank(numbers_data)  # 上报Yuyuko
            return hikari
        else:
            return await search_cn_rank(hikari)
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_yuyuko()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def search_ShipRank_Yuyuko(hikari: Hikari_Model):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/v2/upload/ship/rank'
        params = {'server': hikari.Input.Server, 'shipId': int(hikari.Input.ShipInfo.Ship_Id)}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            hikari.set_template_info('ship-rank.html', 1300, 100)
            result_data = {'data': result['data'], 'shipInfo': hikari.Input.ShipInfo.dict()}
            return hikari.success(result_data)
        else:
            return hikari
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_yuyuko()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def search_ShipRank_Numbers(hikari: Hikari_Model):
    try:
        client_default = await get_client_default()
        number_url = f'{number_url_homes[hikari.Input.Server]}/ship/{hikari.Input.ShipInfo.Ship_Id},{hikari.Input.ShipInfo.ship_Name_Numbers}'
        resp = await client_default.get(number_url, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        data = soup.select('tr[class="cells-middle"]')
        infoList = await set_ShipRank_Numbers(data, hikari.Input.Server, hikari.Input.ShipInfo.Ship_Id)
        if infoList:
            hikari.set_template_info('ship-rank.html', 1300, 100)
            result_data = {'data': infoList, 'shipInfo': hikari.Input.ShipInfo.dict()}
            return hikari.success(result_data), infoList
        else:
            return hikari.error('wuwuu好像出了点问题，可能是网络问题，过一会儿还是不行的话请联系麻麻~'), None
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~'), None
    except PoolTimeout:
        await recreate_client_default()
        return hikari.error('连接池异常，请尝试重新查询~'), None
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决'), None


async def post_ShipRank(data):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/v2/upload/ship/rank'
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.post(url, json=data, timeout=10)
        result = orjson.loads(resp.content)
        logger.success(result)
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
    except PoolTimeout:
        await recreate_client_yuyuko()
    except Exception:
        logger.error(traceback.format_exc())


async def search_cn_rank(hikari: Hikari_Model):
    try:
        url = 'https://api.wows.shinoaki.com/wows/rank/ship/server'
        params = {'server': hikari.Input.Server, 'shipId': int(hikari.Input.ShipInfo.Ship_Id), 'page': 1}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            hikari.set_template_info('ship-rank.html', 1300, 100)
            result_data = {'data': result['data'], 'shipInfo': hikari.Input.ShipInfo.dict()}
            return hikari.success(result_data)
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
