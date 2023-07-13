import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..data_source import __version__
from ..HttpClient_Pool import get_client_default, recreate_client_default
from ..model import Hikari_Model


async def get_help(hikari: Hikari_Model):
    try:
        url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/version.json'
        client_default = await get_client_default()
        resp = await client_default.get(url, timeout=10)
        result = orjson.loads(resp.content)
        latest_version = result['latest_version']
        url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/wws_help.txt'
        resp = await client_default.get(url, timeout=10)
        result = resp.text
        result = f"""帮助列表                                                当前版本{__version__}  最新版本{latest_version}\n{result}"""
        data = {'text': result}
        hikari = hikari.set_template_info('text.html', 800, 10)
        return hikari.success(data)
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_default()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def check_version(hikari: Hikari_Model):
    try:
        url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/version.json'
        client_default = await get_client_default()
        resp = await client_default.get(url, timeout=10)
        result = orjson.loads(resp.content)
        match, msg = False, '发现新版本'
        for each in result['data']:
            if each['version'] > __version__:
                match = True
                msg += f"\n{each['date']} v{each['version']}\n"
                for i in each['description']:
                    msg += f'{i}\n'
        if match:
            return hikari.success(msg)
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_default()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')
