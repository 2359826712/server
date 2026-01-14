
# GPU-Accelerated OCR Server

High-performance OCR server using FastAPI and PaddleOCR, designed for GPU acceleration.

## Features

- **FastAPI Architecture**: Modern, high-performance web framework.
- **GPU Acceleration**: Utilizes PaddleOCR with CUDA support.
- **Async Processing**: Non-blocking request handling.
- **Compatibility**: Supports legacy `orc_api.py` client.
- **Health Check**: `/health` endpoint.
- **Concurrency Control**: Built-in semaphore, default supports 100+ concurrent requests.

## Requirements

- Python 3.8+
- CUDA-enabled GPU (optional, falls back to CPU)
- `paddlepaddle-gpu` (for GPU support) or `paddlepaddle` (CPU only)
- `paddleocr`

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (Note: Ensure you have the correct version of `paddlepaddle-gpu` for your CUDA version)

2. Run the server:
   ```bash
   python -m app.main
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
   ```

## API Documentation

### POST /ocr
Performs OCR on an image.

**Request Body:**
```json
{
  "image_base64": "base64_encoded_image_string",
  "target_text": "optional_text_to_filter",
  "max_side": 720,
  "use_angle_cls": false
}
```

**Response:**
```json
{
  "code": 0,
  "data": [
    {
      "box": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
      "text": "detected text",
      "score": 0.99
    }
  ],
  "msg": "success"
}
```

### GET /health
Returns server status.

## Deployment Guide

### Docker
1. Build image:
   ```dockerfile
   FROM python:3.9
   RUN pip install paddlepaddle-gpu paddleocr fastapi uvicorn
   COPY . /app
   WORKDIR /app
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
   # 改为：
   # CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

### Performance Tuning
- **Concurrency**: Controlled via `MAX_CONCURRENT_REQUESTS` in [config.py](file:///c:/Users/Administrator/Desktop/ocr_server/app/core/config.py). Set to 128 for ≥100并发。
- **GPU**: Ensure `paddlepaddle-gpu` matches CUDA drivers. Service sets device via `paddle.device.set_device("gpu")` automatically。
- **Latency**: Keep `max_side`合理（如≤720），减少预处理开销；部署时使用本机内网以降低网络往返时间。
- **Workers**: 对GPU负载，建议`--workers 1`；如存在大量纯IO请求可提升至2，但注意GPU串行瓶颈。
- **Warmup**: 首次加载模型较慢，建议服务启动后执行一次小图请求进行预热。

## Testing
Run tests with pytest:
```bash
pytest
```

For CI tests (without real GPU model load), tests set `UNIT_TEST=1` to bypass heavy initialization:
- See [test_api.py](file:///c:/Users/Administrator/Desktop/ocr_server/tests/test_api.py) where environment is set before creating the client.
