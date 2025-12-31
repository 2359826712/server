from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.game import BaseInfo, QueryReq, MessageResponse
from app.services import game_service
from app.utils.validator import is_valid_game_name

router = APIRouter()

@router.post("/createNewGame", response_model=MessageResponse)
def create_new_game(game: BaseInfo, db: Session = Depends(get_db)):
    if not is_valid_game_name(game.game_name):
         raise HTTPException(status_code=400, detail="游戏名必须是字母数字或下划线且以字母开头")
    try:
        game_service.create_table(db, game.game_name)
        return {"message": "create new game table success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/insert", response_model=MessageResponse)
def insert_game(game: BaseInfo, db: Session = Depends(get_db)):
    if not is_valid_game_name(game.game_name):
         raise HTTPException(status_code=400, detail="游戏名必须是字母数字或下划线且以字母开头")
    try:
        game_service.insert_game(db, game)
        return {"message": "insert success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update", response_model=MessageResponse)
def update_game(game: BaseInfo, db: Session = Depends(get_db)):
    if not is_valid_game_name(game.game_name):
         raise HTTPException(status_code=400, detail="游戏名必须是字母数字或下划线且以字母开头")
    try:
        game_service.update_game(db, game)
        return {"message": "update success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/query", response_model=MessageResponse)
def query_game(query: QueryReq, db: Session = Depends(get_db)):
    if not is_valid_game_name(query.game_name):
         raise HTTPException(status_code=400, detail="游戏名必须是字母数字或下划线且以字母开头")
    if query.online_duration == 0:
        raise HTTPException(status_code=400, detail="在线时长不能为0")
    try:
        result = game_service.query_game(db, query)
        return {"message": "query success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/clearTalkChannel", response_model=MessageResponse)
def clear_talk_channel(query: QueryReq, db: Session = Depends(get_db)):
    # Note: Go uses QueryReq for input but only uses GameName and TalkChannel
    if not is_valid_game_name(query.game_name):
         raise HTTPException(status_code=400, detail="游戏名必须是字母数字或下划线且以字母开头")
    try:
        if query.talk_channel is None:
             raise HTTPException(status_code=400, detail="talk_channel is required")
             
        game_service.clear_talk_time(db, query.game_name, query.talk_channel)
        return {"message": "clear talk time channel success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
