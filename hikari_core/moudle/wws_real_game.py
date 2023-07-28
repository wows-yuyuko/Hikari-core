import os
import re
import traceback
from asyncio.exceptions import TimeoutError

import json_tools
import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..config import hikari_config
from ..HttpClient_Pool import (
    get_client_default,
    get_client_wg,
    get_client_yuyuko,
    recreate_client_default,
    recreate_client_wg,
    recreate_client_yuyuko,
)
from ..model import Hikari_Model

api_list = {
    'asia': 'https://api.worldofwarships.asia/wows/ships/stats/',
    'eu': 'https://api.worldofwarships.eu/wows/ships/stats/',
    'na': 'https://api.worldofwarships.com/wows/ships/stats/',
    'cn': 'https://vortex.wowsgame.cn/api/accounts/',
}
seach_ship_url = 'https://api.wows.shinoaki.com/public/wows/encyclopedia/ship/info'


async def get_latest_info(server, account_id):
    try:
        if server != 'cn':
            client_wg = await get_client_wg()
            params = {
                'application_id': '907d9c6bfc0d896a2c156e57194a97cf',
                'account_id': account_id,
                'extra': 'rank_solo',
            }
            resp = await client_wg.get(api_list[server], params=params)
            result = orjson.loads(resp.content)
        else:
            client_default = await get_client_default()
            url = f'{api_list[server]}{account_id}/ships/pvp/'
            resp = await client_default.get(url)
            result = orjson.loads(resp.content)
        return result
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
    except PoolTimeout:
        await recreate_client_default()
        await recreate_client_wg()
    except Exception:
        logger.error(traceback.format_exc())


def get_last_info(account_id):
    try:
        listen_data_path = f'{hikari_config.game_path}/account_data'
        if not os.path.exists(listen_data_path):
            os.mkdir(listen_data_path)
        with open(f'{listen_data_path}/{account_id}.json', 'rb') as f:
            last_info = orjson.loads(f.read())
        return last_info
    except Exception:
        print(traceback.format_exc())


def write_latest_info(account_id, data):
    try:
        listen_data_path = f'{hikari_config.game_path}/account_data'
        if not os.path.exists(listen_data_path):
            os.mkdir(listen_data_path)
        with open(f'{listen_data_path}/{account_id}.json', 'w', encoding='utf-8') as f:
            f.write(orjson.dumps(data).decode())
    except Exception:
        print(traceback.format_exc())


def jsonDiff(a, b):
    result = json_tools.diff(a, b)
    return result


def get_config():
    listen_data_path = f'{hikari_config.game_path}/account_data'
    if not os.path.exists(listen_data_path):
        os.mkdir(listen_data_path)
    listen_config_path = f'{hikari_config.game_path}/listen_config.json'
    if not os.path.exists(listen_config_path):
        with open(listen_config_path, 'w') as f:
            f.write(orjson.dumps({}).decode())
    with open(listen_config_path, 'rb') as f:
        config = orjson.loads(f.read())
    return config


async def get_diff_ship(hikari: Hikari_Model):  # noqa: PLR0915
    try:
        listen_data_path = f'{hikari_config.game_path}/account_data'
        config = get_config()
        account_id_list, account_list, send_list = [], [], []
        # 获取监控列表，去重
        for _group_id, group_config in config.items():
            for each in group_config:
                if each['account_id'] not in account_id_list:
                    account_id_list.append(each['account_id'])
                    account_list.append(each.copy())
        print(account_list)
        for account in account_list:
            # 不存在记录本轮先创建
            if not os.path.exists(f"{listen_data_path}/{account['account_id']}.json"):
                latest_data = await get_latest_info(account['server'], account['account_id'])
                if not latest_data['status'] == 'ok':
                    continue
                write_latest_info(account['account_id'], latest_data)
                continue
            # 存在历史记录，拉取最新战绩判断是否有差异
            latest_data = await get_latest_info(account['server'], account['account_id'])
            if not latest_data['status'] == 'ok':
                continue
            last_data = get_last_info(account['account_id'])
            write_latest_info(account['account_id'], latest_data)
            diff = jsonDiff(last_data, latest_data)
            if diff:
                compare_list = []
                for each in diff:
                    if 'replace' in each:
                        value = each['value'] - each['prev']
                        info = {'path': each['replace'], 'value': value}
                        compare_list.append(info.copy())
                    if 'add' in each:
                        value = each['value']
                        info = {'path': each['add'], 'value': value}
                        compare_list.append(info.copy())
                print(orjson.dumps(compare_list))

                battles, win, loss, damage, shipId = 0, 0, 0, 0, 0
                ship_name_cn = ''
                for each in compare_list:
                    if '/pvp/wins' in each['path']:
                        win += each['value']
                    if '/pvp/losses' in each['path']:
                        loss += each['value']
                    if 'pvp/damage_dealt' in each['path']:
                        damage += each['value']
                    if account['server'] != 'cn':
                        match = re.search(f"^/data/{account['account_id']}/(.*?)/pvp/battles$", each['path'])
                    else:
                        match = re.search(f"^/data/{account['account_id']}/statistics/(.*?)/pvp/battles_count$", each['path'])
                    if match:
                        battles += each['value']
                        if account['server'] != 'cn':
                            index = int(match.group(1))
                            shipId = int(latest_data['data'][str(account['account_id'])][index]['ship_id'])
                        else:
                            shipId = int(match.group(1))
                        params = {'shipId': shipId}
                        client_yuyuko = await get_client_yuyuko()
                        resp = await client_yuyuko.get(seach_ship_url, params=params)
                        result = orjson.loads(resp.content)
                        if result['code'] == 200:
                            ship_name_cn = ship_name_cn + result['data']['nameCn'] + ','

                # 构建消息
                for _group_id, group_config in config.items():
                    for each in group_config:
                        nick_name = each['nick_name']
                        if account['account_id'] == each['account_id']:
                            if battles == 1:
                                msg = f'喜报：\n{nick_name}刚刚输了一场对局\n使用{ship_name_cn}伤害{damage}'
                                if win:
                                    msg = f'悲报：\n{nick_name}刚刚赢了一场对局\n使用{ship_name_cn}伤害{damage}'
                            elif battles >= 2:
                                msg = f'{nick_name}刚刚完成了{battles}场对局\n胜{win}负{loss}平{battles-win-loss}\n使用{ship_name_cn}\n总伤害{damage}'
                            else:
                                continue
                            send_param = {'group_id': _group_id, 'msg': msg, 'type': 'text'}
                            send_list.append(send_param.copy())
        if not send_list:
            return hikari.failed('没有新的监控战绩')
        return hikari.success(send_list)
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_yuyuko()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def get_listen_list(hikari: Hikari_Model):
    try:
        config = get_config()
        group_id = hikari.UserInfo.GroupId
        msg = '本群监控列表\n'
        if str(group_id) in config:
            for each in config[str(group_id)]:
                msg += f"账号:{each['account_id']},备注:{each['nick_name']}\n"
        else:
            msg = '测试功能，请联系机器人搭建者添加监控'
        return hikari.success(msg)
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')