import traceback
from asyncio.exceptions import TimeoutError

import orjson
from bs4 import BeautifulSoup
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..data_source import set_ShipRank_Numbers
from ..HttpClient_Pool import recreate_client_yuyuko
from ..model import Hikari_Model
from .publicAPI import get_AccountIdByName, get_ship_byName


async def get_ShipRank(hikari: Hikari_Model):
    try:
        if hikari.Status == 'init':
            shipList = await get_ship_byName(hikari.Input.ShipInfo.Ship_Name)
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

        if not param_server == 'cn':
            content = await search_ShipRank_Yuyuko(select_shipId, param_server, shipInfo)
            if content:  # 存在缓存，直接出图
                return await html_to_pic(content, wait=0, viewport={'width': 1300, 'height': 100})
            else:  # 无缓存，去Number爬
                content, numbers_data = await search_ShipRank_Numbers(number_url, param_server, select_shipId, shipInfo)
                if content:
                    await post_ShipRank(numbers_data)  # 上报Yuyuko
                    return await html_to_pic(content, wait=0, viewport={'width': 1300, 'height': 100})
                else:
                    return 'wuwuu好像出了点问题，可能是网络问题，过一会儿还是不行的话请联系麻麻~'
        else:
            content = await search_cn_rank(select_shipId, param_server, 1, shipInfo)
            if content:
                return await html_to_pic(content, wait=0, viewport={'width': 1300, 'height': 100})
            else:
                return 'wuwuu好像出了点问题，可能是网络问题，过一会儿还是不行的话请联系麻麻~'
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_yuyuko()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def search_ShipRank_Yuyuko(shipId, server, shipInfo):
    try:
        content = None
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/v2/upload/ship/rank'
        params = {'server': server, 'shipId': int(shipId)}
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            template = env.get_template('ship-rank.html')
            result_data = {'data': result['data'], 'shipInfo': shipInfo}
            content = await template.render_async(result_data)
            return content
        else:
            return None
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return None
    except Exception:
        logger.error(traceback.format_exc())
        return None


async def search_ShipRank_Numbers(url, server, shipId, shipInfo):
    try:
        content = None
        resp = await client_default.get(url, timeout=None)
        soup = BeautifulSoup(resp.content, 'html.parser')
        data = soup.select('tr[class="cells-middle"]')
        infoList = await set_ShipRank_Numbers(data, server, shipId)
        if infoList:
            result_data = {'data': infoList, 'shipInfo': shipInfo}
            template = env.get_template('ship-rank.html')
            content = await template.render_async(result_data)
            return content, infoList
        else:
            return None, None
    except Exception:
        logger.error(traceback.format_exc())
        return None, None


async def post_ShipRank(data):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/v2/upload/ship/rank'
        resp = await client_yuyuko.post(url, json=data, timeout=None)
        result = orjson.loads(resp.content)
        logger.success(result)
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
    except Exception:
        logger.error(traceback.format_exc())


async def search_cn_rank(shipId, server, page, shipInfo):
    try:
        content = None  # 查询是否有缓存
        url = 'https://api.wows.shinoaki.com/wows/rank/ship/server'
        params = {'server': server, 'shipId': int(shipId), 'page': int(page)}
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            template = env.get_template('ship-rank.html')
            result_data = {'data': result['data'], 'shipInfo': shipInfo}
            content = await template.render_async(result_data)
            return content
        else:
            return None
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return None
    except Exception:
        logger.error(traceback.format_exc())
        return None
