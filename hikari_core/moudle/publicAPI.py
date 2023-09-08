import asyncio
import gzip
import traceback
from asyncio.exceptions import TimeoutError
from base64 import b64encode
from typing import List

import orjson
from bs4 import BeautifulSoup
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..data_source import number_url_homes
from ..HttpClient_Pool import (
    get_client_default,
    get_client_wg,
    get_client_yuyuko,
    recreate_client_default,
    recreate_client_wg,
    recreate_client_yuyuko,
)
from ..model import Hikari_Model, Ship_Model


async def get_nation_list():
    try:
        msg = ''
        url = 'https://v3-api.wows.shinoaki.com:8443/public/wows/encyclopedia/nation/list'
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, timeout=10)
        result = orjson.loads(resp.content)
        for nation in result['data']:
            msg: str = msg + f"{nation['cn']}：{nation['nation']}\n"
        return msg
    except PoolTimeout:
        await recreate_client_yuyuko()
        return
    except Exception:
        logger.error(traceback.format_exc())


async def get_ship_name(hikari: Hikari_Model):
    msg = ''
    try:
        params = {
            'country': hikari.Input.ShipInfo.Ship_Nation,
            'level': hikari.Input.ShipInfo.Ship_Tier,
            'shipName': '',
            'shipType': hikari.Input.ShipInfo.Ship_Type,
            'groupType': 'default',
        }
        url = 'https://v3-api.wows.shinoaki.com:8443/public/wows/encyclopedia/ship/search'
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['data']:
            for ship in result['data']:
                msg += f"{ship['nameCn']}：{ship['nameEnglish']}\n"
            return hikari.success(msg)
        else:
            return hikari.failed('没有符合的船只')
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_yuyuko()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def get_ship_byName(shipname: str) -> List:
    try:
        shipname_select_index = None
        result = shipname.split('.')
        if len(result) == 2 and result[1].isdigit():
            shipname = result[0]
            shipname_select_index = int(result[1])
        url = 'https://v3-api.wows.shinoaki.com:8443/public/wows/encyclopedia/ship/search'
        params = {'country': '', 'level': '', 'shipName': shipname, 'shipType': '', 'groupType': 'default'}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        List, select_List = [], []
        if result['code'] == 200 and result['data']:
            for each in result['data']:
                List.append(
                    Ship_Model(
                        Ship_Nation=each['country'],
                        Ship_Tier=each['level'],
                        Ship_Type=each['shipType'],
                        Ship_Name_Cn=each['nameCn'],
                        Ship_Name_English=each['nameEnglish'],
                        ship_Name_Numbers=each['nameEnglish'],
                        Ship_Id=each['shipId'],
                    )
                )
            if shipname_select_index and shipname_select_index <= len(List):
                select_List.append(List[shipname_select_index - 1])
                return select_List
            else:
                return List
        else:
            return None
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
    except PoolTimeout:
        await recreate_client_yuyuko()
        return
    except Exception:
        logger.error(traceback.format_exc())
        return None


async def get_all_shipList():
    try:
        url = 'https://v3-api.wows.shinoaki.com:8443/public/wows/encyclopedia/ship/search'
        params = {'country': '', 'level': '', 'shipName': '', 'shipType': '', 'groupType': 'default'}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            return result['data']
        else:
            return None
    except PoolTimeout:
        await recreate_client_yuyuko()
        return
    except Exception:
        return None


async def get_AccountIdByName(server: str, name: str) -> str:
    try:
        url = f'https://v3-api.wows.shinoaki.com:8443/public/wows/account/search/{server}/user'
        params = {'userName': name, 'one': True}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.post(url, json=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            return int(result['data'][0]['accountId'])
        else:
            return result['message']
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return '请求超时了，请过一会儿重试哦~'
    except PoolTimeout:
        await recreate_client_yuyuko()
        return
    except Exception:
        logger.error(traceback.format_exc())
        return '好像出了点问题呢，可能是网络问题，如果重试几次还不行的话，请联系麻麻解决'


async def get_ClanIdByName(server: str, tag: str):
    try:
        url = f'https://v3-api.wows.shinoaki.com:8443/public/wows/clan/search/{server}'
        params = {
            'tag': tag,
        }
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            return result['data']
        else:
            return None
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return None
    except PoolTimeout:
        await recreate_client_yuyuko()
        return
    except Exception:
        logger.error(traceback.format_exc())
        return None


async def check_yuyuko_cache(server, id):
    try:
        yuyuko_cache_url = 'https://v3-api.wows.shinoaki.com:8443/api/wows/cache/check'
        params = {'accountId': id, 'server': server}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.post(yuyuko_cache_url, json=params, timeout=5)
        result = orjson.loads(resp.content)
        cache_data = {}
        if result['code'] == 201:
            if 'DEV' in result['data']:
                await get_wg_info(cache_data, 'DEV', result['data']['DEV'])
            elif 'PVP' in result['data']:
                tasks = []
                for key in result['data']:
                    tasks.append(asyncio.ensure_future(get_wg_info(cache_data, key, result['data'][key])))
                await asyncio.gather(*tasks)
            if not cache_data:
                return False
            data_base64 = b64encode(gzip.compress(orjson.dumps(cache_data))).decode()
            params['data'] = data_base64
            resp = await client_yuyuko.post(yuyuko_cache_url, json=params, timeout=5)
            result = orjson.loads(resp.content)
            logger.success(result)
            if result['code'] == 200:
                return True
            else:
                return False
        return False
    except PoolTimeout:
        await recreate_client_yuyuko()
        return False
    except Exception:
        logger.error('缓存上报失败')
        return False


async def get_wg_info(params, key, url):
    try:
        client_wg = await get_client_wg()
        resp = await client_wg.get(url, timeout=5, follow_redirects=True)
        wg_result = orjson.loads(resp.content)
        if resp.status_code == 200 and wg_result['status'] == 'ok':
            params[key] = resp.text
    except PoolTimeout:
        await recreate_client_wg()
        return
    except Exception:
        logger.error(f'wg请求异常,请配置代理后尝试,上报url：{url}')
        return


async def get_MyShipRank_yuyuko(params) -> int:
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/upload/user/ship/rank'
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            if result['data']['ranking']:
                return result['data']['ranking']
            elif not result['data']['ranking'] and not result['data']['serverId'] == 'cn':
                ranking = await get_MyShipRank_Numbers(result['data']['httpUrl'], result['data']['serverId'])
                if ranking:
                    await post_MyShipRank_yuyuko(
                        result['data']['accountId'],
                        ranking,
                        result['data']['serverId'],
                        result['data']['shipId'],
                    )
                return ranking
            else:
                return None
        else:
            return None
    except PoolTimeout:
        await recreate_client_yuyuko()
        return
    except Exception:
        logger.error(traceback.format_exc())
        return None


async def get_MyShipRank_Numbers(url, server) -> int:
    try:
        data = None
        client_default = await get_client_default()
        resp = await client_default.get(url, timeout=10)
        if resp.content:
            result = orjson.loads(resp.content)
            page_url = str(result['url']).replace('\\', '')
            nickname = str(result['nickname'])
            my_rank_url = f'{number_url_homes[server]}{page_url}'
            resp = await client_default.get(my_rank_url, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            data = soup.select_one(f'tr[data-nickname="{nickname}"]').select_one('td').string
        if data and data.isdigit():
            return data
        else:
            return None
    except PoolTimeout:
        await recreate_client_default()
        return
    except Exception:
        logger.error(traceback.format_exc())
        return None


async def post_MyShipRank_yuyuko(accountId, ranking, serverId, shipId):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/upload/user/ship/rank'
        post_data = {
            'accountId': int(accountId),
            'ranking': int(ranking),
            'serverId': serverId,
            'shipId': int(shipId),
        }
        client_yuyuko = await get_client_yuyuko()
        await client_yuyuko.post(url, json=post_data, timeout=10)
        return
    except PoolTimeout:
        await recreate_client_yuyuko()
        return
    except Exception:
        logger.error(traceback.format_exc())
        return
