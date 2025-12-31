from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BaseInfo(BaseModel):
    ID: Optional[int] = None
    game_name: str
    account: Optional[str] = None
    b_zone: Optional[str] = None
    s_zone: Optional[str] = None
    rating: Optional[int] = None

class Account(BaseInfo):
    created_at: Optional[datetime] = None
    online_time: Optional[datetime] = None
    last_talk_time1: Optional[datetime] = None
    last_talk_time2: Optional[datetime] = None
    last_talk_time3: Optional[datetime] = None
    last_talk_time4: Optional[datetime] = None
    last_talk_time5: Optional[datetime] = None
    last_talk_time6: Optional[datetime] = None

class QueryReq(BaseInfo):
    online_duration: int # Go: uint
    talk_channel: Optional[int] = None # Go: uint
    cnt: Optional[int] = None # Go: uint

class MessageResponse(BaseModel):
    message: str
    data: Optional[list] = None
