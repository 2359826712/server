# 这是一个运行在 64位 Python 下的 OCR 服务
# 必须使用 64位 Python 解释器运行此脚本！
# pip install flask paddlepaddle paddleocr

from flask import Flask, request, jsonify
import os
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_new_executor"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
from paddleocr import PaddleOCR
import paddle
import logging
import base64
import io
import numpy as np
import cv2
import traceback
import time
import threading


try:
    import paddlex.utils.deps as _px_deps
    _px_deps.require_extra = lambda *args, **kwargs: None
    _px_deps.require_deps = lambda *args, **kwargs: None
except Exception:
    pass


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)


print("正在初始化 PaddleOCR，请稍候...")
try:
    paddle.set_flags({
        "FLAGS_new_executor": 0,
    })
except Exception:
    pass
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
    lang="ch",
    ocr_version="PP-OCRv3",
    enable_mkldnn=True,
)
print("PaddleOCR 初始化完成！")


API_KEY = os.environ.get("OCR_API_KEY")
REQUEST_METRICS = {
    "total": 0,
    "success": 0,
    "error": 0,
}
METRICS_LOCK = threading.Lock()


def update_metrics(success: bool) -> None:
    with METRICS_LOCK:
        REQUEST_METRICS["total"] += 1
        if success:
            REQUEST_METRICS["success"] += 1
        else:
            REQUEST_METRICS["error"] += 1


def require_api_key() -> bool:
    if not API_KEY:
        return True
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        return False
    return True


def resize_image(img: np.ndarray, max_side: int) -> np.ndarray:
    if max_side <= 0:
        return img
    h, w = img.shape[:2]
    long_side = max(h, w)
    if long_side <= max_side:
        return img
    scale = max_side / float(long_side)
    nw = int(w * scale)
    nh = int(h * scale)
    if nw <= 0 or nh <= 0:
        return img
    return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "msg": "Pong!"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


@app.route("/metrics", methods=["GET"])
def metrics():
    with METRICS_LOCK:
        data = dict(REQUEST_METRICS)
    return jsonify(data)


@app.route("/ocr", methods=["POST"])
def ocr_process():
    start_ts = time.perf_counter()
    if not require_api_key():
        update_metrics(False)
        return jsonify({"code": -1, "msg": "Unauthorized"}), 401
    data = None
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None
    img = None
    img_path = None
    if data:
        b64 = data.get('image_base64')
        if b64:
            try:
                if ',' in b64:
                    b64 = b64.split(',', 1)[1]
                buf = base64.b64decode(b64)
                arr = np.frombuffer(buf, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            except Exception as e:
                return jsonify({"code": -1, "msg": f"Decode base64 failed: {e}"}), 400
        else:
            img_path = data.get('image_path')
    if img is None and 'image' in request.files:
        try:
            buf = request.files['image'].read()
            arr = np.frombuffer(buf, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({"code": -1, "msg": f"Decode file failed: {e}"}), 400
    if img is None and img_path:
        if not os.path.exists(img_path):
            return jsonify({"code": -1, "msg": f"File not found: {img_path}"}), 404
    if img is None and not img_path:
        update_metrics(False)
        return jsonify({"code": -1, "msg": "No image provided"}), 400

    region = data.get("region") if data else None
    target_text = data.get("target_text") if data else None
    use_angle_cls = data.get("use_angle_cls", False) if data else False
    max_side = data.get("max_side", 0) if data else 0

    try:
        if region:
            if img is None:
                img = cv2.imread(img_path)
                if img is None:
                    update_metrics(False)
                    return jsonify({"code": -1, "msg": f"Failed to load image from {img_path}"}), 400

            x, y, w, h = map(int, region)
            h_img, w_img = img.shape[:2]
            x = max(0, x)
            y = max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)

            if w > 0 and h > 0:
                img = img[y:y + h, x:x + w]
            else:
                update_metrics(False)
                return jsonify({"code": -1, "msg": "Invalid region"}), 400

        if img is not None and max_side:
            img = resize_image(img, int(max_side))

        target = img if img is not None else img_path
# 进行OCR识别
        try:
            # use_angle_cls maps to use_textline_orientation in PaddleOCR v3+
            result = ocr.ocr(target, use_angle_cls=use_angle_cls)
        except TypeError as e:
            print(f"Warning: OCR call failed with specific params, retrying with defaults. Error: {e}")
            result = ocr.ocr(target)

        parsed_result = []
        full_text = []
        if result and result[0]:
            if isinstance(result[0], dict):
                res = result[0]
                boxes = res.get("dt_polys", [])
                texts = res.get("rec_texts", [])
                scores = res.get("rec_scores", [])

                for box, text, score in zip(boxes, texts, scores):
                    if target_text and target_text not in text:
                        continue
                    if hasattr(box, "tolist"):
                        box = box.tolist()
                    parsed_result.append(
                        {
                            "text": text,
                            "confidence": float(score),
                            "box": box,
                        }
                    )
                    full_text.append(text)
            elif isinstance(result[0], list):
                for line in result[0]:
                    text = line[1][0]
                    confidence = float(line[1][1])
                    box = line[0]
                    if target_text and target_text not in text:
                        continue
                    parsed_result.append(
                        {
                            "text": text,
                            "confidence": confidence,
                            "box": box,
                        }
                    )
                    full_text.append(text)

        duration_ms = int((time.perf_counter() - start_ts) * 1000)
        update_metrics(True)
        logging.info(f"Recognized {len(parsed_result)} lines in {duration_ms} ms")
        print(f"DEBUG_SERVER: Processing time {duration_ms} ms", flush=True)
        return jsonify(
            {
                "code": 0,
                "data": parsed_result,
                "summary": {
                    "full_text": "".join(full_text),
                    "duration_ms": duration_ms,
                },
            }
        )
    except NotImplementedError as e:
        duration_ms = int((time.perf_counter() - start_ts) * 1000)
        update_metrics(True)
        logging.error(f"OCR failed: {e}")
        logging.error(traceback.format_exc())
        return jsonify({"code": 0, "data": [], "summary": {"full_text": "", "duration_ms": duration_ms}})
    except Exception as e:
        duration_ms = int((time.perf_counter() - start_ts) * 1000)
        update_metrics(False)
        logging.error(f"OCR failed: {e}")
        logging.error(traceback.format_exc())
        return jsonify({"code": -1, "msg": str(e), "duration_ms": duration_ms}), 500

if __name__ == '__main__':
    host = os.environ.get("OCR_BIND_HOST", "0.0.0.0")
    port = int(os.environ.get("OCR_PORT", "5000"))
    cert = os.environ.get("OCR_SSL_CERT")
    key = os.environ.get("OCR_SSL_KEY")
    ssl_context = None
    if cert and key and os.path.exists(cert) and os.path.exists(key):
        ssl_context = (cert, key)
    print(f"启动 OCR 服务端口 {port}...")
    app.run(host=host, port=port, ssl_context=ssl_context)
