import os
import re
import shutil
import traceback
from asyncio.exceptions import TimeoutError

import json_tools
import orjson
from httpx import ConnectTimeout, PoolTimeout, TimeoutException
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
from .publicAPI import get_AccountIdByName

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
        if not result:
            raise Exception
        return result
    except PoolTimeout:
        logger.error('连接池错误，尝试重新创建')
        await recreate_client_default()
        await recreate_client_wg()
        return None
    except TimeoutException:
        logger.error(f'获取{account_id}实时战绩超时，可能是网络原因')
        return None
    except Exception:
        logger.error(traceback.format_exc())
        return None


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


def write_config(config):
    listen_data_path = f'{hikari_config.game_path}/account_data'
    if not os.path.exists(listen_data_path):
        os.mkdir(listen_data_path)
    listen_config_path = f'{hikari_config.game_path}/listen_config.json'
    if not os.path.exists(listen_config_path):
        with open(listen_config_path, 'w') as f:
            f.write(orjson.dumps({}).decode())
    with open(listen_config_path, 'w', encoding='utf-8') as f:
        f.write(orjson.dumps(config).decode())
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
        logger.info('开始获取监控信息')
        for account in account_list:
            # 不存在记录本轮先创建
            if not os.path.exists(f"{listen_data_path}/{account['account_id']}.json"):
                latest_data = await get_latest_info(account['server'], account['account_id'])
                if not latest_data or not latest_data['status'] == 'ok':
                    continue
                write_latest_info(account['account_id'], latest_data)
                continue
            # 存在历史记录，拉取最新战绩判断是否有差异
            latest_data = await get_latest_info(account['server'], account['account_id'])
            if not latest_data or not latest_data['status'] == 'ok':
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
                logger.info(orjson.dumps(compare_list))

                battles, win, loss, damage, shipId, match_count = 0, 0, 0, 0, 0, 0
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
                        match_count += 1
                        if match_count > 5:
                            break
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
                if match_count > 5:
                    break
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
        flag = 1
        if str(group_id) in config:
            for each in config[str(group_id)]:
                msg += f"{flag}：账号:{each['account_id']},备注:{each['nick_name']}\n"
                flag += 1
        else:
            msg = '当前群监控列表为空，请联系机器人搭建者添加监控'
        return hikari.success(msg)
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def add_listen_list(hikari: Hikari_Model):
    try:
        if hikari.Status == 'init':
            if hikari.Input.Search_Type == 3:
                hikari.Input.AccountId = await get_AccountIdByName(hikari.Input.Server, hikari.Input.AccountName)
                if not isinstance(hikari.Input.AccountId, int):
                    return hikari.error(f'{hikari.Input.AccountId}')
        else:
            return hikari.error('当前请求状态错误')
        add_param = {'server': hikari.Input.Server, 'account_id': hikari.Input.AccountId, 'nick_name': hikari.Input.Command_List[1]}
        config = get_config()
        group_id = hikari.UserInfo.GroupId
        if not group_id:
            return hikari.error('不支持私聊')
        if group_id in config:
            group_list = config[group_id]
        else:
            group_list = []
        group_list.append(add_param)
        config[group_id] = group_list
        write_config(config)
        return hikari.success('添加成功')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def delete_listen_list(hikari: Hikari_Model):
    try:
        config = get_config()
        group_id = hikari.UserInfo.GroupId
        if not group_id:
            return hikari.error('不支持私聊')
        if group_id in config:
            group_list: list = config[group_id]
        else:
            return hikari.error('当前群没有监控列表')
        if hikari.Input.Select_Index > len(group_list):
            return hikari.error('请确认序号是否小于监控列表')

        group_list.pop(hikari.Input.Select_Index - 1)
        config[group_id] = group_list
        if len(config[group_id]) == 0:
            config.pop(group_id)
        write_config(config)
        return hikari.success('删除成功')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')


async def reset_config(hikari: Hikari_Model):
    try:
        listen_data_path = f'{hikari_config.game_path}/account_data'
        shutil.rmtree(listen_data_path, ignore_errors=True)
        os.mkdir(listen_data_path)
        listen_config_path = f'{hikari_config.game_path}/listen_config.json'
        os.remove(listen_config_path)
        with open(listen_config_path, 'w') as f:
            f.write(orjson.dumps({}).decode())
        return hikari.success('重置监控配置成功')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.success('重置监控配置失败')
