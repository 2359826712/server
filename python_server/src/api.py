from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .models import BaseInfo, QueryReq
from .logic import logic_service
from .database import init_db
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc.errors())},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error processing request: {exc}")
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)},
    )

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/createNewGame")
async def create_new_game(base: BaseInfo):
    try:
        logic_service.new_game(base.GameName)
        return {"message": "create new game table success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/insert")
async def insert(base: BaseInfo):
    try:
        logic_service.insert(base)
        return {"message": "insert success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/update")
async def update(base: BaseInfo):
    try:
        logic_service.update(base)
        return {"message": "update success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/query")
async def query(req: QueryReq):
    try:
        if req.OnlineDuration == 0:
            raise HTTPException(status_code=400, detail="在线时长不能为0")
        
        data = logic_service.query(req)
        return {"message": "query success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/clearTalkChannel")
async def clear_talk_channel(req: QueryReq):
    # Note: Go version uses QueryReq structure but only reads GameName and TalkChannel
    try:
        logic_service.clear_talk_time(req.GameName, req.TalkChannel)
        return {"message": "clear talk time channel success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
