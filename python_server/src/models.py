from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class BaseInfo(BaseModel):
    ID: Optional[int] = Field(None, alias="ID")
    GameName: str = Field(..., alias="game_name")
    Account: Optional[str] = Field(None, alias="account")
    BZone: Optional[str] = Field(None, alias="b_zone")
    SZone: Optional[str] = Field(None, alias="s_zone")
    Rating: Optional[int] = Field(None, alias="rating")

    @validator('GameName')
    def validate_game_name(cls, v):
        if not v:
            raise ValueError("游戏名不能为空")
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError("游戏名必须是字母数字或下划线且以字母开头")
        return v

class QueryReq(BaseInfo):
    OnlineDuration: int = Field(0, alias="online_duration")
    TalkChannel: int = Field(0, alias="talk_channel")
    Cnt: int = Field(0, alias="cnt")
