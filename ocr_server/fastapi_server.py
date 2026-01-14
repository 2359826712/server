import os
import sys
import time
import logging
import base64
import traceback
import multiprocessing
from typing import Optional, List, Dict, Any, Union

# --- 自动注入 NVIDIA DLL 路径 (修复 cudnn64_9.dll 找不到的问题) ---
# (已删除 GPU 相关注入代码)
# -----------------------------------------------------------

from fastapi import FastAPI, UploadFile, File, Body, HTTPException, Request
from pydantic import BaseModel
import uvicorn
import json
import asyncio

# 禁用字节码生成
sys.dont_write_bytecode = True

# 设置环境变量，复用 server.py 的逻辑
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("PADDLEOCR_HOME", os.path.join(_BASE_DIR, "paddleocr_home"))

# 导入 ocr_engine.py 中的 OcrProcessPool
# 注意：确保 ocr_engine.py 在同一目录下
try:
    from ocr_engine import OcrProcessPool
except ImportError:
    # 如果直接运行此脚本，可能需要将当前目录加入 sys.path
    sys.path.append(_BASE_DIR)
    from ocr_engine import OcrProcessPool

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    # startup
    multiprocessing.freeze_support()
    use_gpu = False
    cpu_num = os.cpu_count() or 2
    
    if "OCR_WORKERS" in os.environ:
        worker_count = int(os.environ["OCR_WORKERS"])
    else:
        # 性能优先策略 (Low Latency Mode)：
        # 为了大幅降低单次请求的延迟 (Latency)，默认只启动 1 个 Worker。
        # PaddleOCR 在 CPU 模式下，单进程多线程 (MKLDNN) 的推理速度远快于多进程单线程。
        # 默认使用 1 个 Worker，并分配较多的 CPU 线程。
        worker_count = 1
    
    if "OCR_CPU_THREADS" not in os.environ:
        # 自动计算每个 Worker 的最佳线程数
        # 尽可能利用所有物理核心来加速单次推理
        # 预留 1-2 个核给系统和其他进程
        threads_per_worker = max(4, cpu_num - 2)
        os.environ["OCR_CPU_THREADS"] = str(threads_per_worker)
        logging.info(f"Auto-configured OCR_CPU_THREADS={threads_per_worker} (Total CPUs={cpu_num}) for Speed")

    logging.info(f"Initializing OCR Process Pool with {worker_count} workers...")
    
    # Pre-initialize models to avoid race conditions
    try:
        from ocr_engine import check_and_download_models
        check_and_download_models()
    except Exception as e:
        logging.error(f"Failed to pre-initialize models: {e}")

    pool = OcrProcessPool(worker_count=worker_count)
    yield
    # shutdown
    if pool:
        logging.info("Shutting down OCR Process Pool...")
        pool.close()

app = FastAPI(title="OCR Server (FastAPI)", lifespan=lifespan)
pool: Optional[OcrProcessPool] = None

class OCRRequest(BaseModel):
    image_base64: Optional[str] = None
    image_path: Optional[str] = None
    target_text: Optional[str] = None
    max_side: Optional[int] = None
    use_angle_cls: Optional[bool] = False
    region: Optional[List[int]] = None # [x, y, w, h]

@app.get("/ping")
async def ping():
    return {"status": "ok", "backend": "fastapi"}

@app.post("/ocr/predict")
async def ocr_predict(request: Request):
    """
    OCR 预测接口
    支持 JSON Body 传入 image_base64 或 image_path
    也支持 multipart/form-data 传入 image 文件
    """
    global pool
    if pool is None:
        raise HTTPException(status_code=500, detail="OCR pool not initialized")

    t0 = time.perf_counter()
    
    payload = {}
    content_type = request.headers.get("content-type", "")
    
    try:
        if "application/json" in content_type:
            payload = await request.json()
        elif "multipart/form-data" in content_type:
            form = await request.form()
            # 尝试解析 request_data 字段 (JSON 字符串)
            if "request_data" in form:
                try:
                    payload = json.loads(form["request_data"])
                except:
                    pass
            
            # 合并其他普通字段 (如 use_angle_cls 等)
            for key, value in form.items():
                if key not in payload and not isinstance(value, UploadFile):
                    # 简单的类型转换尝试
                    if value == "true": payload[key] = True
                    elif value == "false": payload[key] = False
                    else: payload[key] = value
            
            # 处理文件上传
            image = form.get("image")
            if isinstance(image, UploadFile):
                content = await image.read()
                payload["image_base64"] = base64.b64encode(content).decode("ascii")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Request parsing error: {str(e)}")
    
    if not payload.get("image_base64") and not payload.get("image_path"):
         raise HTTPException(status_code=400, detail="No image provided (image_base64, image_path, or file upload required)")

    try:
        timeout = float(os.environ.get("OCR_SERVER_TASK_TIMEOUT", "120"))
        
        # 这里的 pool.submit 是阻塞调用（虽然内部用了 Queue），在 FastAPI 中最好放到线程池中运行以免阻塞事件循环
        # 但 OcrProcessPool.submit 内部使用了 queue.get(timeout=...), 这会阻塞当前线程。
        # FastAPI 的 async def 运行在事件循环中，如果直接调用阻塞函数会阻塞整个循环。
        # 因此，我们需要使用 run_in_executor 或者直接定义 def 路由（FastAPI 会自动在线程池运行 def 路由）。
        # 这里为了简单且高效，我们将路由定义改为 async，并手动 wrap 一下，或者直接改回 def。
        # 鉴于 submit 内部逻辑主要是等待 Queue，使用 def 路由是最简单的方案。
        pass
    except Exception as e:
        logging.error(f"Error preparing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Run OCR in thread pool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    client_host = request.client.host if request.client else "unknown"
    return await loop.run_in_executor(None, _run_ocr, payload, t0, client_host)

def _run_ocr(payload, t0, client_host):
    try:
        timeout = float(os.environ.get("OCR_SERVER_TASK_TIMEOUT", "120"))
        res = pool.submit(payload, timeout=timeout)
        
        if not isinstance(res, dict):
             raise HTTPException(status_code=500, detail="Invalid worker response")

        cost_ms = (time.perf_counter() - t0) * 1000.0
        
        log_msg = f"[{client_host}] OCR processed successfully, cost={cost_ms:.1f}ms"
        logging.info(log_msg)
        print(log_msg, flush=True) # Ensure it appears in console
        
        if res.get("code") == 0:
            return {"code": 0, "data": res.get("data")}
        
        status = int(res.get("status", 500))
        err_msg = f"[{client_host}] OCR failed status={status} cost_ms={cost_ms:.1f}"
        logging.info(err_msg)
        print(err_msg, flush=True)
        
        # 保持与 Flask 接口返回格式一致
        return {"code": -1, "msg": res.get("msg")} # 状态码由 FastAPI 处理，这里返回 JSON
        
    except Exception as e:
        logging.error(f"[{client_host}] OCR failed: {e}")
        logging.error(traceback.format_exc())
        return {"code": -1, "msg": str(e)}


def main():
    host = os.environ.get("OCR_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("OCR_SERVER_PORT", "8000"))
    
    # 检查端口是否被占用 (简单的检查，uvicorn 也会检查)
    
    logging.info(f"Starting FastAPI OCR Server on {host}:{port}")
    # 强制使用 h11 协议解析器，避免 httptools (C扩展) 在打包后出现兼容性问题
    uvicorn.run(app, host=host, port=port, log_level="info", http="h11")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
