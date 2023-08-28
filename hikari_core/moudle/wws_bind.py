import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..HttpClient_Pool import get_client_yuyuko, recreate_client_yuyuko
from ..model import Hikari_Model
from .publicAPI import get_AccountIdByName


async def get_BindInfo(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status != 'init':
            return hikari.error('当前请求状态错误')
        url = 'https://v3-api.wows.shinoaki.com:8443/api/user/platform/bind/list'
        params = {'platformType': hikari.Input.Platform, 'platformId': hikari.Input.PlatformId}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['message'] == 'success':
            if result['data']:
                hikari = hikari.set_template_info('bind-list.html', 900, 440)
                return hikari.success(result['data'])
            else:
                return hikari.failed('该用户似乎还没绑定窝窝屎账号')
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


async def set_BindInfo(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status == 'init':
            if hikari.Input.Search_Type == 3 and not hikari.Input.AccountId:
                hikari.Input.AccountId = await get_AccountIdByName(hikari.Input.Server, hikari.Input.AccountName)
                if not isinstance(hikari.Input.AccountId, int):
                    return hikari.error(f'{hikari.Input.AccountId}')
        else:
            return hikari.error('当前请求状态错误')
        url = 'https://api.wows.shinoaki.com/api/wows/bind/account/platform/bind/put'
        params = {'platformType': hikari.Input.Platform, 'platformId': hikari.Input.PlatformId, 'accountId': hikari.Input.AccountId}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['message'] == 'success':
            return hikari.success('绑定成功')
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


# 防止混淆纯数字名与AID，单独添加特殊绑定指令
async def set_special_BindInfo(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status != 'init':
            return hikari.error('当前请求状态错误')
        url = 'https://api.wows.shinoaki.com/api/wows/bind/account/platform/bind/put'
        params = {'platformType': hikari.Input.Platform, 'platformId': hikari.Input.PlatformId, 'accountId': hikari.Input.AccountId}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['message'] == 'success':
            return hikari.success('绑定成功')
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


async def change_BindInfo(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status not in ['init', 'wait']:
            return hikari.error('当前请求状态错误')
        # 初次调用时无参数，返回输出选择列表
        if hikari.Status == 'init' and not hikari.Input.Select_Index:
            hikari = await get_BindInfo(hikari)
            # 成功获取绑定列表时置为wait，否则按原状态返回
            if hikari.Status == 'success':
                hikari.Status = 'wait'
                hikari.Input.Select_Data = hikari.Output.Data
            return hikari
        # 初次调用时或回调时有参数
        elif hikari.Input.Select_Index:
            # 初次调用时有选择序号，查询一次绑定列表
            if not hikari.Input.Select_Data:
                hikari.Status = 'init'
                hikari = await get_BindInfo(hikari)
                if not hikari.Status == 'success':
                    return hikari
                hikari.Input.Select_Data = hikari.Output.Data
            if hikari.Input.Select_Index > len(hikari.Input.Select_Data):
                return hikari.error('请选择正确的序号')
            hikari.Input.AccountId = hikari.Input.Select_Data[hikari.Input.Select_Index - 1]['accountId']
            hikari.Status = 'init'
            # 切换绑定
            hikari = await set_BindInfo(hikari)
            if hikari.Status == 'success':
                return hikari.success(
                    f"切换绑定成功,当前绑定账号{hikari.Input.Select_Data[hikari.Input.Select_Index - 1]['server']}：{hikari.Input.Select_Data[hikari.Input.Select_Index - 1]['userName']}"
                )
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return '请求超时了，请过会儿再尝试哦~'
    except Exception:
        logger.error(traceback.format_exc())
        return 'wuwuwu出了点问题，请联系麻麻解决'


async def delete_BindInfo(hikari: Hikari_Model) -> Hikari_Model:
    try:
        if hikari.Status not in ['init', 'wait']:
            return hikari.error('当前请求状态错误')
        # 初次调用时无参数，返回输出选择列表
        if hikari.Status == 'init' and not hikari.Input.Select_Index:
            hikari = await get_BindInfo(hikari)
            # 成功获取绑定列表时置为wait，否则按原状态返回
            if hikari.Status == 'success':
                hikari.Status = 'wait'
                hikari.Input.Select_Data = hikari.Output.Data
            return hikari
        # 初次调用时或回调时有参数
        elif hikari.Input.Select_Index:
            # 初次调用时有选择序号，查询一次绑定列表
            if not hikari.Input.Select_Data:
                hikari.Status = 'init'
                hikari = await get_BindInfo(hikari)
                if not hikari.Status == 'success':
                    return hikari
                hikari.Input.Select_Data = hikari.Output.Data
            if hikari.Input.Select_Index > len(hikari.Input.Select_Data):
                return hikari.error('请选择正确的序号')
            hikari.Input.AccountId = hikari.Input.Select_Data[hikari.Input.Select_Index - 1]['accountId']
            url = 'https://api.wows.shinoaki.com/api/wows/bind/account/platform/bind/remove'
            params = {'platformType': hikari.Input.Platform, 'platformId': hikari.Input.PlatformId, 'accountId': hikari.Input.AccountId}
            client_yuyuko = await get_client_yuyuko()
            resp = await client_yuyuko.get(url, params=params, timeout=10)
            result = orjson.loads(resp.content)
            if result['code'] == 200 and result['message'] == 'success':
                return hikari.success(
                    f"删除绑定成功，删除的账号为{hikari.Input.Select_Data[hikari.Input.Select_Index - 1]['server']}：{hikari.Input.Select_Data[hikari.Input.Select_Index - 1]['userName']}"
                )
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


async def get_DefaultBindInfo(platformType, platformId):
    try:
        url = 'https://api.wows.shinoaki.com/public/wows/bind/account/platform/bind/list'
        params = {
            'platformType': platformType,
            'platformId': platformId,
        }
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['message'] == 'success':
            if result['data']:
                for each in result['data']:
                    if each['defaultId']:
                        return each
            else:
                return None
    except Exception:
        logger.error(traceback.format_exc())
        return None
