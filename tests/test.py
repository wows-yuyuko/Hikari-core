import asyncio
import sys
import time
from pathlib import Path

dir_path = Path(__file__).parent.parent
sys.path.append(f'{dir_path}')

from hikari_core import Hikari_Model, callback_hikari, init_hikari, set_hikari_config  # noqa: E402

platform = 'QQ'
platform_id = '2622749113'
group_id = '967546463'


async def start():
    global start_time
    start_time = time.time()
    set_hikari_config(use_broswer='chromium', http2=False, proxy='http://localhost:7890', token='test:yuyuko_test', yuyuko_type='QQ_CHANNEL')
    await command("公会战记录 cn 团子大家族 25", False)
    await command("公会战记录 cn 团子大家族 25 1", False)
    await command("公会战记录 me 25", False)
    await command("公会战记录 me 25 1", False)
    # await command("asia _nahida", True)
    # await command("wws查询绑定 me", True)
    # await command("me ship 大和", True)
    # await command("wws me sx", True)
    # await command("wws me sd", True)
    # await command("clan asia YU_RI", True)
    # await command("战舰排行榜 cn 大和", True)
    # await command("封号记录 国服 西行寺雨季", True)
    # await command("公会战排行榜 20", True)
    # # 以下指令不抛出异常，特殊情况特殊测试
    # await command("me ship 无比 recent 2024-05-30", False)
    # await command("wws me recent 3", False)
    # await command("wws me recents 10", False)


async def command(command_text: str, is_err: bool):
    hikari_data = await init_hikari(platform, platform_id, command_text, group_id)
    if hikari_data.Status == 'success':
        await output_with_check_type(hikari_data, command_text)
    elif hikari_data.Status == 'wait':
        await output_with_check_type(hikari_data, command_text)
        hikari_data.Input.Select_Index = 2
        hikari_data = await callback_hikari(hikari_data)
        await output_with_check_type(hikari_data, command_text)
    elif hikari_data.Status in ['error', 'failed']:
        if is_err:
            raise IOError(hikari_data.Output.Data)
        else:
            print("\033[31m" + hikari_data.Output.Data + "\033[0m")


async def output_with_check_type(hikari_data: Hikari_Model, command: str):
    print(hikari_data.Output.Data_Type)
    if isinstance(hikari_data.Output.Data, bytes):
        with open(command.replace(' ', '-') + '.png', 'wb') as f:
            f.write(hikari_data.Output.Data)
            print(f'渲染完成,用时{time.time() - start_time}')
    elif isinstance(hikari_data.Output.Data, str):
        print(hikari_data.Output.Data)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
