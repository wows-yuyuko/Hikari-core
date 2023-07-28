import time
import traceback

import jinja2
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from pydantic import ValidationError

from .analyze import analyze_command
from .config import hikari_config, set_hikari_config  # noqa:F401
from .data_source import set_render_params, template_path
from .game.help import update_template
from .Html_Render import html_to_pic
from .model import Hikari_Model, Input_Model, UserInfo_Model

env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path), enable_async=True)
env.globals.update(
    time=time,
    abs=abs,
    enumerate=enumerate,
    int=int,
)


async def init_hikari(
    platform: str,
    PlatformId: str,
    command_text: str = None,
    GroupId: str = None,
) -> Hikari_Model:
    """Hikari初始化

    Args:
        platform (str): 平台类型
        PlatformId (str): 平台ID
        command_text (str): 传入指令，不带wws

    Returns:
        Hikari_Model: 可通过Hikari.Status和Hikari.Output.Data内数据判断是否输出
    """
    try:
        userinfo = UserInfo_Model(Platform=platform, PlatformId=PlatformId, GroupId=GroupId)
        input = Input_Model(Command_Text=command_text)
        hikari = Hikari_Model(UserInfo=userinfo, Input=input)
        hikari = await analyze_command(hikari)
        if not hikari.Status == 'init' or not hikari.Function:
            return hikari
        hikari: Hikari_Model = await hikari.Function(hikari)
        return await output_hikari(hikari)
    except ValidationError:
        logger.error(traceback.format_exc())
        return Hikari_Model().error('参数校验错误，请联系开发者确认入参是否符合Model')
    except Exception:
        logger.error(traceback.format_exc())
        return Hikari_Model().error('Hikari-core顶层错误，请检查log')


async def callback_hikari(hikari: Hikari_Model) -> Hikari_Model:
    """回调wait状态的Hikari

    Args:
        hikari (Hikari_Model):前置或自行构造的Hikari_Model，可通过from hikari_core import Hikari_Model引入

    Returns:
        Hikari_Model: 可通过Hikari.Status和Hikari.Output.Data内数据判断是否输出
    """
    try:
        if not hikari.Status == 'wait':
            return hikari.error('当前请求状态错误，请确认是否为wait')
        if not hikari.Function:
            return hikari.error('缺少请求方法')
        hikari: Hikari_Model = await hikari.Function(hikari)
        return await output_hikari(hikari)

    except Exception:
        logger.error(traceback.format_exc())
        return Hikari_Model().error('Hikari-core顶层错误，请检查log')


async def output_hikari(hikari: Hikari_Model) -> Hikari_Model:
    """输出Hikari

    Args:
        hikari (Hikari_Model):前置或自行构造的Hikari_Model，可通过from hikari_core import Hikari_Model引入

    Returns:
        Hikari_Model: 可通过Hikari.Status和Hikari.Output.Data内数据判断是否输出
    """
    try:
        if (
            hikari.Status in ['success', 'wait']
            and hikari_config.auto_rendering
            and hikari.Output.Template
            and (isinstance(hikari.Output.Data, dict) or isinstance(hikari.Output.Data, list))  # noqa: PLR1701
        ):
            template = env.get_template(hikari.Output.Template)
            if hikari.Status == 'success':
                template_data = await set_render_params(hikari.Output.Data)
            elif hikari.Status == 'wait':
                template_data = await set_render_params(hikari.Input.Select_Data)
            content = await template.render_async(template_data)
            hikari.Output.Data = content
            hikari.Output.Data_Type = type(hikari.Output.Data)

            if hikari_config.auto_image:
                hikari.Output.Data = await html_to_pic(
                    content,
                    wait=0,
                    viewport={'width': hikari.Output.Width, 'height': hikari.Output.Height},
                    use_browser=hikari_config.use_broswer,
                )
                hikari.Output.Data_Type = type(hikari.Output.Data)
        return hikari
    except Exception:
        logger.error(traceback.format_exc())
        return Hikari_Model().error('Hikari-core顶层错误，请检查log')


update_template()
scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
scheduler.add_job(update_template, 'cron', hour='4,12')
scheduler.start()

# logger.add(
#    'hikari-core-logs/error.log',
#    rotation='00:00',
#    retention='1 week',
#    diagnose=False,
#    level='ERROR',
#    encoding='utf-8',
# )
# logger.add(
#    'hikari-core-logs/info.log',
#    rotation='00:00',
#    retention='1 week',
#    diagnose=False,
#    level='INFO',
#    encoding='utf-8',
# )
# logger.add(
#    'hikari-core-logs/warning.log',
#    rotation='00:00',
#    retention='1 week',
#    diagnose=False,
#    level='WARNING',
#    encoding='utf-8',
# )
