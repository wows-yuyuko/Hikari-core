from datetime import date
from typing import List, Optional, Protocol, Union, runtime_checkable

from pydantic import BaseModel, Field


@runtime_checkable
class Func(Protocol):
    async def __call__(self, **kwargs):
        ...

class UserInfo(BaseModel):
    Platform: str
    PlatformId: str


class Ship(BaseModel):
    Ship_Nation: Optional[str]
    Ship_Tier: Optional[int]
    Ship_Type: Optional[str]
    Ship_Name: Optional[str]
    Ship_Id: Optional[int]


class Input(BaseModel):
    Command_Text: Optional[str]  # 输入的指令,请提前去除wws
    Command_List: Optional[List]
    Search_Type: Optional[int] = 3  # 1:me  2:@  3:server+name or default
    Platform: Optional[str]
    PlatformId: Optional[str]
    Server: Optional[str]
    AccountName: Optional[str]
    AccountId: Optional[int]
    ClanName: Optional[str]
    Recent_Day: Optional[int] = 0
    Recent_Date: Optional[date]
    Select_Index: Optional[int]
    Select_Data: Optional[List]
    ShipInfo: Optional[Ship]


class Output(BaseModel):
    Yuyuko_Code: Optional[int]
    Data_Type: str = Field("str", description="返回的类型")
    Data: Union[str, int, bytes] = Field("初始化", description="返回的数据")
    Template: Optional[str]
    Width: Optional[int]
    Height: Optional[int]


class Hikari(BaseModel):
    Status: str = "init"
    UserInfo: UserInfo
    Function: Func = None
    Input: Optional[Input]
    Output: Optional[Output]

    class Config:
        arbitrary_types_allowed = True

    def error(self, error_data):
        self.Status = "error"
        self.Output.Data = error_data
        self.Output.Data_Type = str(type(error_data))
        return self

    def success(self, success_data):
        self.Status = "success"
        self.Output.Data = success_data
        self.Output.Data_Type = str(type(success_data))
        return self

    def wait(self, select_data: List):
        self.Status = "wait"
        self.Input.Select_Data = select_data
        self.Output.Data = "等待选择"
        self.Output.Data_Type = str(type(self.Output.Data))
        return self


