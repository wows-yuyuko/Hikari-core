import traceback
from asyncio.exceptions import TimeoutError

import httpx
import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..data_source import __version__, template_path
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
        msg += '实验性更新指令：wws 更新Hikari，请在能登录上服务器的情况下执行该命令'
        if match:
            return hikari.success(msg)
        else:
            return hikari.success('Hikari:当前已经是最新版本了')
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_default()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


def update_template():
    try:
        # tasks = []
        url = 'https://hikari-resource.oss-cn-shanghai.aliyuncs.com/hikari_core_template/template.json'
        with httpx.Client() as client:
            resp = client.get(url, timeout=20)
            result = orjson.loads(resp.content)
            for each in result:
                for name, url in each.items():
                    resp = client.get(url, timeout=5)
                    with open(template_path / name, 'wb+') as file:
                        file.write(resp.content)
            logger.info('更新模板成功')
            # for each in result:
            #    for name, url in each.items():
            #        tasks.append(asyncio.ensure_future(download_template(url, name)))
        # await asyncio.gather(*tasks)
    except Exception:
        logger.error(traceback.format_exc())


async def async_update_template(hikari: Hikari_Model = Hikari_Model()):  # noqa: B008
    try:
        # tasks = []
        url = 'https://hikari-resource.oss-cn-shanghai.aliyuncs.com/hikari_core_template/template.json'
        with httpx.Client() as client:
            resp = client.get(url, timeout=20)
            result = orjson.loads(resp.content)
            for each in result:
                for name, url in each.items():
                    resp = client.get(url, timeout=5)
                    with open(template_path / name, 'wb+') as file:
                        file.write(resp.content)
            logger.info('更新模板成功')
            return hikari.success('更新模板成功')
            # for each in result:
            #    for name, url in each.items():
            #        tasks.append(asyncio.ensure_future(download_template(url, name)))
        # await asyncio.gather(*tasks)
    except Exception:
        logger.error(traceback.format_exc())
