import time
from typing import List, Optional, Protocol, Union, runtime_checkable

from pydantic import BaseModel, Field


@runtime_checkable
class Func(Protocol):
    async def __call__(self, **kwargs):
        ...


class UserInfo_Model(BaseModel):
    Platform: str = 'QQ'
    PlatformId: str = '1119809439'
    GroupId: str = None


class Ship_Model(BaseModel):
    Ship_Nation: Optional[str]
    Ship_Tier: Optional[int]
    Ship_Type: Optional[str]
    Ship_Name_Cn: Optional[str]
    Ship_Name_English: Optional[str]
    ship_Name_Numbers: Optional[str]
    Ship_Id: Optional[int]


class Input_Model(BaseModel):
    Command_Text: Optional[str] = ''  # 输入的指令,请提前去除wws
    Command_List: Optional[List]
    Search_Type: Optional[int] = 3  # 1:me  2:@  3:server+name or default
    Platform: Optional[str]
    PlatformId: Optional[str]
    Server: Optional[str]
    AccountName: Optional[str]
    AccountId: Optional[int]
    ClanName: Optional[str]
    Recent_Day: Optional[int] = 0
    Recent_Date: Optional[str] = time.strftime('%Y-%m-%d', time.localtime())
    Select_Index: Optional[int]
    Select_Data: Optional[List]
    ShipInfo: Ship_Model = Ship_Model()


class Output_Model(BaseModel):
    Yuyuko_Code: Optional[int]
    Data_Type: str = Field('str', description='返回的类型')
    Data: Union[str, int, bytes] = Field('初始化', description='返回的数据')
    Template: Optional[str]
    Width: Optional[int]
    Height: Optional[int]


class Hikari_Model(BaseModel):
    Status: str = 'init'  # init:初始化 success:请求成功  failed:请求成功但API有错误或空返回  error:异常及本地错误
    UserInfo: UserInfo_Model = UserInfo_Model()
    Function: Func = None
    Input: Input_Model = Input_Model()
    Output: Output_Model = Output_Model()

    class Config:
        arbitrary_types_allowed = True

    def error(self, error_data):
        self.Status = 'error'
        self.Output.Data = error_data
        self.Output.Data_Type = str(type(error_data))
        return self

    def success(self, success_data):
        self.Status = 'success'
        self.Output.Data = success_data
        self.Output.Data_Type = str(type(success_data))
        return self

    def failed(self, failed_data):
        self.Status = 'failed'
        self.Output.Data = failed_data
        self.Output.Data_Type = str(type(failed_data))
        return self

    def wait(self, select_data: List):
        self.Status = 'wait'
        self.Input.Select_Data = select_data
        self.Output.Data = select_data
        self.Output.Data_Type = str(type(self.Output.Data))
        return self

    def set_template_info(self, template_name: str, width: int, height: int):
        """配置模板解析参数

        Args:
            template_name (str): 模板名
            width (int): 宽度
            height (int): 高度

        Returns:
            Hikari_Model
        """
        self.Output.Template = template_name
        self.Output.Width = width
        self.Output.Height = height
        return self
