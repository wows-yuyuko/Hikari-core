import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..config import hikari_config
from ..HttpClient_Pool import get_client_yuyuko, recreate_client_yuyuko
from ..model import Hikari_Model


async def get_CwRank(hikari: Hikari_Model) -> Hikari_Model:
    """查询军团战排行榜"""
    try:
        if hikari.Status == 'init':
            if not hikari.Input.Server:
                hikari.Input.Server = 'global'
        else:
            return hikari.error('当前请求状态错误')

        url = f'{hikari_config.yuyuko_url}/public/wows/clan/rank/cw'
        params = {
            'season': hikari.Input.CwSeasonId,
            'server': hikari.Input.Server,
            'page': 1,
            'size': 100,
        }
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        hikari.Output.Yuyuko_Code = result['code']
        if result['code'] == 200 and result['data']:
            hikari.set_template_info('cw-rank.html', 1300, 100)
            result_data = {'data': result['data'], 'server': hikari.Input.Server, 'season': hikari.Input.CwSeasonId}
            return hikari.success(result_data)
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
