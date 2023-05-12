from datetime import date
from typing import List, Optional, Union

from command_select import Func
from pydantic import BaseModel, Field


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
    Command_Text: Optional[str]  # 输入的指令,可带wws
    Search_Type: Optional[int]  # 1:me  2:@  3:server+name
    Server: Optional[str]
    AccountName: Optional[str]
    AccountId: Optional[int]
    ClanName: Optional[str]
    Recent_Day: int = Field(1, gt=0, description="recent向前查找天数")
    Recent_Date: Optional[date]
    Select_Index: Optional[int]
    Select_Data: Optional[List]
    ShipInfo: Optional[Ship]


class Output(BaseModel):
    Yuyuko_Code: Optional[int]
    Data_Type: str = Field("str", description="返回的类型")
    Data: Union[str, int, bytes] = Field("初始化", description="返回的数据")


class Hikari(BaseModel):
    Status: str = "init"
    UserInfo: UserInfo
    Function: Func = None
    Input: Optional[Input]
    Output: Optional[Output]

    class Config:
        arbitrary_types_allowed = True


userinfo = UserInfo(Platform="QQ", PlatformId="1119809439")
ship = Ship()
input = Input(ShipInfo=ship)
output = Output()
Hikari1 = Hikari(UserInfo=userinfo, Ship=ship, Input=input, Output=output)
Hikari1.UserInfo = {"TEM": "QQ"}
Hikari1.Input.Recent_Day = 3
print(Hikari1.dict())
