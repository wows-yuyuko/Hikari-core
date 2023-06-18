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
        url = 'https://v3-api.wows.shinoaki.com/public/user/platform/bind/list'
        params = {'platformType': hikari.Input.Platform, 'platformId': hikari.Input.PlatformId}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['message'] == 'success':
            if result['data']:
                hikari = hikari.set_template_info('bind-list.html', 900, 440)
                return hikari.success(result['data'])
            else:
                return '该用户似乎还没绑定窝窝屎账号'
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return f"{result['message']}"
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
            if hikari.Input.Search_Type == 3:
                hikari.Input.AccountId = await get_AccountIdByName(hikari.Input.Server, hikari.Input.AccountName)
                if not isinstance(hikari.Input.AccountId, int):
                    return hikari.error(f'{hikari.Input.AccountId}')
        else:
            return hikari.error('当前请求状态错误')
        url = 'https://api.wows.shinoaki.com/api/wows/bind/account/platform/bind/put'
        params = {'platformType': hikari.Input.Platform, 'platformId': hikari.Input.PlatformId, 'accountId': hikari.Input.AccountId}
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['message'] == 'success':
            return '绑定成功'
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return f"{result['message']}"
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
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['message'] == 'success':
            return '绑定成功'
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return f"{result['message']}"
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

        # if isinstance(info, List) and len(info) == 1 and str(info[0]).isdigit():
        #    url = 'https://api.wows.shinoaki.com/public/wows/bind/account/platform/bind/list'
        #    params = {
        #        'platformType': server_type,
        #        'platformId': ev.user_id,
        #    }
        # else:
        #    return '参数似乎出了问题呢，请跟随要切换的序号'
        # resp = await client_yuyuko.get(url, params=params, timeout=None)
        # result = orjson.loads(resp.content)
        # if result['code'] == 200 and result['message'] == 'success':
        #    if result['data'] and len(result['data']) >= int(info[0]):
        #        account_name = result['data'][int(info[0]) - 1]['userName']
        #        param_server = result['data'][int(info[0]) - 1]['serverType']
        #        param_accountid = result['data'][int(info[0]) - 1]['accountId']
        #        url = 'https://api.wows.shinoaki.com/api/wows/bind/account/platform/bind/put'
        #        params = {
        #            'platformType': server_type,
        #            'platformId': str(ev.user_id),
        #            'accountId': param_accountid,
        #        }
        #    else:
        #        return '没有对应序号的绑定记录'
        # elif result['code'] == 500:
        #    return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        # else:
        #    return f"{result['message']}"
        # resp = await client_yuyuko.get(url, params=params, timeout=None)
        # result = orjson.loads(resp.content)
        # if result['code'] == 200 and result['message'] == 'success':
        #    return f'切换绑定成功,当前绑定账号{param_server}：{account_name}'
        # elif result['code'] == 403:
        #    return f"{result['message']}\n请先绑定账号"
        # elif result['code'] == 500:
        #    return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        # else:
        #    return f"{result['message']}"
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return '请求超时了，请过会儿再尝试哦~'
    except Exception:
        logger.error(traceback.format_exc())
        return 'wuwuwu出了点问题，请联系麻麻解决'


async def delete_BindInfo(hikari: Hikari_Model) -> Hikari_Model:
    try:
        return
        # if isinstance(info, List) and len(info) == 1 and str(info[0]).isdigit():
        #    url = 'https://api.wows.shinoaki.com/public/wows/bind/account/platform/bind/list'
        #    params = {
        #        'platformType': server_type,
        #        'platformId': ev.user_id,
        #    }
        # else:
        #    return '参数似乎出了问题呢，请跟随要切换的序号'
        # resp = await client_yuyuko.get(url, params=params, timeout=None)
        # result = orjson.loads(resp.content)
        # if result['code'] == 200 and result['message'] == 'success':
        #    if result['data'] and len(result['data']) >= int(info[0]):
        #        account_name = result['data'][int(info[0]) - 1]['userName']
        #        param_server = result['data'][int(info[0]) - 1]['serverType']
        #        param_accountid = result['data'][int(info[0]) - 1]['accountId']
        #        url = 'https://api.wows.shinoaki.com/api/wows/bind/account/platform/bind/remove'
        #        params = {
        #            'platformType': server_type,
        #            'platformId': str(ev.user_id),
        #            'accountId': param_accountid,
        #        }
        #    else:
        #        return '没有对应序号的绑定记录'
        # elif result['code'] == 500:
        #    return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        # else:
        #    return f"{result['message']}"
        # resp = await client_yuyuko.get(url, params=params, timeout=None)
        # result = orjson.loads(resp.content)
        # if result['code'] == 200 and result['message'] == 'success':
        #    return f'删除绑定成功,删除的账号为{param_server}：{account_name}'
        # elif result['code'] == 500:
        #    return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        # else:
        #    return f"{result['message']}"
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return '请求超时了，请过会儿再尝试哦~'
    except Exception:
        logger.error(traceback.format_exc())
        return 'wuwuwu出了点问题，请联系麻麻解决'


async def get_DefaultBindInfo(platformType, platformId):
    try:
        url = 'https://api.wows.shinoaki.com/public/wows/bind/account/platform/bind/list'
        params = {
            'platformType': platformType,
            'platformId': platformId,
        }
        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=None)
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
