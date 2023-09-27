import asyncio
import sys
import time
from pathlib import Path

dir_path = Path(__file__).parent.parent
sys.path.append(f'{dir_path}')

from hikari_core import Hikari_Model, callback_hikari, get_ClanInfo, init_hikari, set_hikari_config  # noqa: E402


async def start():
    global start_time
    start_time = time.time()
    set_hikari_config(use_broswer='chromium', http2=False, proxy='http://localhost:7890', token='test:yuyuko_test', yuyuko_type='CHANNEL')
    hikari_data = await init_hikari('QQ', '2257844796', 'me ship 里希特', '693433753', Ignore_List=[get_ClanInfo])
    if hikari_data.Status == 'success':
        await output_with_check_type(hikari_data)
    elif hikari_data.Status == 'wait':
        await output_with_check_type(hikari_data)
        hikari_data.Input.Select_Index = 2
        hikari_data = await callback_hikari(hikari_data)
        await output_with_check_type(hikari_data)
    elif hikari_data.Status in ['error', 'failed']:
        print(hikari_data.Output.Data)


async def output_with_check_type(hikari_data: Hikari_Model):
    print(hikari_data.Output.Data_Type)
    if isinstance(hikari_data.Output.Data, bytes):
        with open('test.png', 'wb') as f:
            f.write(hikari_data.Output.Data)
            print(f'渲染完成,用时{time.time()-start_time}')
    elif isinstance(hikari_data.Output.Data, str):
        print(hikari_data.Output.Data)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
