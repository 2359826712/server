# 这是一个运行在 64位 Python 下的 OCR 服务
# 必须使用 64位 Python 解释器运行此脚本！
# pip install flask paddlepaddle paddleocr

from flask import Flask, request, jsonify
import os
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_new_executor"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
from paddleocr import PaddleOCR, TextRecognition
import paddle
import logging
import base64
import io
import numpy as np
import cv2
import traceback
import time
import threading


class HardwareConfig:
    """
    封装硬件与运行模式配置的简单数据结构。
    """

    def __init__(self, device: str, use_mkldnn: bool, num_threads: int | None):
        self.device = device
        self.use_mkldnn = use_mkldnn
        self.num_threads = num_threads


class ModelConfig:
    """
    封装检测/识别模型选择的简单数据结构。
    """

    def __init__(self, ocr_version: str, rec_model_name: str):
        self.ocr_version = ocr_version
        self.rec_model_name = rec_model_name


def detect_hardware_and_config() -> HardwareConfig:
    """
    根据 Paddle 能力与环境变量选择运行设备和并行参数。
    """
    mode = os.environ.get("OCR_RUNTIME_MODE", "auto").lower()
    default_threads = os.environ.get("OCR_CPU_THREADS")

    if mode == "gpu":
        if paddle.is_compiled_with_cuda():
            return HardwareConfig(device="gpu", use_mkldnn=False, num_threads=None)
        return HardwareConfig(device="cpu", use_mkldnn=True, num_threads=int(default_threads) if default_threads else None)

    if mode == "cpu":
        return HardwareConfig(device="cpu", use_mkldnn=True, num_threads=int(default_threads) if default_threads else None)

    if paddle.is_compiled_with_cuda():
        return HardwareConfig(device="gpu", use_mkldnn=False, num_threads=None)
    return HardwareConfig(device="cpu", use_mkldnn=True, num_threads=int(default_threads) if default_threads else None)


def load_model_config() -> ModelConfig:
    """
    从环境变量加载模型选择配置。
    """
    ocr_version = os.environ.get("OCR_VERSION", "PP-OCRv3")
    rec_model_name = os.environ.get("OCR_REC_MODEL_NAME", "PP-OCRv3_mobile_rec")
    return ModelConfig(ocr_version=ocr_version, rec_model_name=rec_model_name)


def setup_runtime(hardware: HardwareConfig) -> None:
    """
    按配置初始化 Paddle 运行环境。
    """
    if hardware.device == "gpu":
        try:
            paddle.set_device("gpu")
        except Exception:
            paddle.set_device("cpu")
    else:
        paddle.set_device("cpu")

    try:
        paddle.set_flags({
            "FLAGS_new_executor": 0,
        })
    except Exception:
        pass

    if hardware.device == "cpu" and hardware.num_threads:
        try:
            paddle.set_num_threads(hardware.num_threads)
        except Exception:
            pass


def build_ocr_engines(model_cfg: ModelConfig, hardware: HardwareConfig) -> tuple[PaddleOCR, TextRecognition]:
    """
    根据配置构建检测+识别管线与纯识别模型。
    """
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
        lang="ch",
        ocr_version=model_cfg.ocr_version,
        enable_mkldnn=hardware.use_mkldnn,
    )
    rec_model = TextRecognition(model_name=model_cfg.rec_model_name)
    return ocr, rec_model


try:
    import paddlex.utils.deps as _px_deps
    _px_deps.require_extra = lambda *args, **kwargs: None
    _px_deps.require_deps = lambda *args, **kwargs: None
except Exception:
    pass


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)


print("正在初始化 PaddleOCR，请稍候...")
hardware_cfg = detect_hardware_and_config()
model_cfg = load_model_config()
setup_runtime(hardware_cfg)
ocr, rec_model = build_ocr_engines(model_cfg, hardware_cfg)
print("PaddleOCR 初始化完成！")


API_KEY = os.environ.get("OCR_API_KEY")
REQUEST_METRICS = {
    "total": 0,
    "success": 0,
    "error": 0,
    "total_duration_ms": 0,
}
METRICS_LOCK = threading.Lock()


def update_metrics(success: bool, duration_ms: int | None = None) -> None:
    with METRICS_LOCK:
        REQUEST_METRICS["total"] += 1
        if success:
            REQUEST_METRICS["success"] += 1
        else:
            REQUEST_METRICS["error"] += 1
        if duration_ms is not None:
            REQUEST_METRICS["total_duration_ms"] += max(0, int(duration_ms))


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
        total = data.get("total", 0)
        total_duration = data.get("total_duration_ms", 0)
        avg_duration = int(total_duration / total) if total > 0 else 0
        data["avg_duration_ms"] = avg_duration
        data["device"] = getattr(hardware_cfg, "device", "unknown")
    return jsonify(data)


class OcrEngine:
    """
    封装检测(det)和识别(rec-only)两种模式的算法逻辑。
    """

    def __init__(self, ocr_pipeline: PaddleOCR, rec_model: TextRecognition):
        self._ocr = ocr_pipeline
        self._rec_model = rec_model

    def run(
        self,
        img: np.ndarray,
        *,
        det: bool,
        use_angle_cls: bool,
        target_text: str | None = None,
    ) -> list[dict]:
        """
        执行一次 OCR 任务，返回统一的结果列表：
        [{"text": str, "confidence": float, "box": [[x,y] * 4]}, ...]
        """
        if det:
            det_result = self._ocr.ocr(img, use_textline_orientation=use_angle_cls)
            parsed_det = self._parse_det_result(det_result, target_text)
            if parsed_det:
                return parsed_det
            rec_result = self._rec_model.predict(img)
            return self._parse_rec_only_result(img, rec_result, target_text)
        rec_result = self._rec_model.predict(img)
        return self._parse_rec_only_result(img, rec_result, target_text)

    def _parse_det_result(self, result, target_text: str | None) -> list[dict]:
        parsed_result: list[dict] = []
        if not result or not result[0]:
            return parsed_result
        res_data = result[0]
        if isinstance(res_data, dict):
            boxes = res_data.get("dt_polys", [])
            texts = res_data.get("rec_texts", [])
            scores = res_data.get("rec_scores", [])
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
        elif isinstance(res_data, list):
            for line in res_data:
                if len(line) < 2:
                    continue
                box = line[0]
                text = line[1][0]
                confidence = float(line[1][1])
                if target_text and target_text not in text:
                    continue
                parsed_result.append(
                    {
                        "text": text,
                        "confidence": confidence,
                        "box": box,
                    }
                )
        return parsed_result

    def _parse_rec_only_result(self, img: np.ndarray, result, target_text: str | None) -> list[dict]:
        parsed_result: list[dict] = []
        h_img, w_img = img.shape[:2]
        if not isinstance(result, list):
            return parsed_result
        for item in result:
            if not isinstance(item, dict):
                continue
            text = item.get("rec_text", "")
            score = float(item.get("rec_score", 0.0))
            if target_text and target_text not in text:
                continue
            box = [[0, 0], [w_img, 0], [w_img, h_img], [0, h_img]]
            parsed_result.append(
                {
                    "text": text,
                    "confidence": score,
                    "box": box,
                }
            )
        return parsed_result


ocr_engine = OcrEngine(ocr, rec_model)


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
    det = data.get("det", True) if data else True
    max_side = data.get("max_side", 0) if data else 0

    print(f"DEBUG_SERVER: det={det}, use_angle_cls={use_angle_cls}", flush=True)

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

        if img is None:
            update_metrics(False)
            return jsonify({"code": -1, "msg": "Image load failed"}), 400

        parsed_result = ocr_engine.run(
            img,
            det=det,
            use_angle_cls=use_angle_cls,
            target_text=target_text,
        )
        full_text = [item["text"] for item in parsed_result]

        duration_ms = int((time.perf_counter() - start_ts) * 1000)
        update_metrics(True, duration_ms=duration_ms)
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
        update_metrics(True, duration_ms=duration_ms)
        logging.error(f"OCR failed: {e}")
        logging.error(traceback.format_exc())
        return jsonify({"code": 0, "data": [], "summary": {"full_text": "", "duration_ms": duration_ms}})
    except Exception as e:
        duration_ms = int((time.perf_counter() - start_ts) * 1000)
        update_metrics(False, duration_ms=duration_ms)
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
