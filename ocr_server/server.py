import os
import sys

sys.dont_write_bytecode = True

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("PADDLEOCR_HOME", os.path.join(_BASE_DIR, "paddleocr_home"))

import base64
import logging
import multiprocessing
import queue
import threading
import traceback
import time
import uuid
from collections import OrderedDict

from flask import Flask, jsonify, request

import cv2
import numpy as np

# Removed top-level paddlex patch to prevent initialization issues
# The patching is now handled inside _worker_main

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)


@app.get("/ping")
def ping():
    return jsonify({"status": "ok"})


def _decode_image_from_payload(payload):
    img = None
    img_path = None

    if payload:
        b64 = payload.get("image_base64")
        if b64:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            buf = base64.b64decode(b64)
            arr = np.frombuffer(buf, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        else:
            img_path = payload.get("image_path")

    if img is None and img_path:
        if not os.path.exists(img_path):
            raise FileNotFoundError(img_path)

    return img, img_path


def _maybe_crop_and_resize(img, payload):
    if img is None:
        return None

    region = payload.get("region") if payload else None
    if region:
        x, y, w, h = map(int, region)
        h_img, w_img = img.shape[:2]
        x = max(0, x)
        y = max(0, y)
        w = min(w, w_img - x)
        h = min(h, h_img - y)
        if w <= 0 or h <= 0:
            raise ValueError("Invalid region")
        img = img[y : y + h, x : x + w]

    max_side = payload.get("max_side") if payload else None
    if max_side:
        ms = int(max_side)
        if ms > 0:
            h_img, w_img = img.shape[:2]
            s = max(h_img, w_img)
            if s > ms:
                scale = ms / float(s)
                new_w = max(1, int(w_img * scale))
                new_h = max(1, int(h_img * scale))
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return img


def _parse_ocr_result(result, target_text):
    parsed_result = []
    if not result or not result[0]:
        return parsed_result

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
            parsed_result.append({"text": text, "confidence": float(score), "box": box})
        return parsed_result

    if isinstance(result[0], list):
        for line in result[0]:
            text = line[1][0]
            confidence = float(line[1][1])
            box = line[0]
            if target_text and target_text not in text:
                continue
            parsed_result.append({"text": text, "confidence": confidence, "box": box})
        return parsed_result

    return parsed_result


def _worker_main(task_queue, result_queue, worker_index):
    os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
    os.environ.setdefault("PADDLEOCR_HOME", os.path.join(_BASE_DIR, "paddleocr_home"))

    import sys
    from types import ModuleType

    # MOCK PADDLEX REMOVED to allow real initialization
    # if 'paddlex' not in sys.modules:
    #     pdx = ModuleType('paddlex')
    #     ... (all mocked code commented out)
    
    try:
        from paddleocr.paddleocr import PaddleOCR
    except ImportError:
        from paddleocr import PaddleOCR
    
    logging.info(f"PaddleOCR imported from {PaddleOCR.__module__}")

    # GPU / CPU 配置
    use_gpu = os.environ.get("OCR_USE_GPU", "False").lower() == "true"
    
    # CPU 加速配置 (仅当不使用 GPU 时生效)
    enable_mkldnn = os.environ.get("OCR_ENABLE_MKLDNN", "True").lower() == "true"
    cpu_threads = int(os.environ.get("OCR_CPU_THREADS", "10"))
    
    device = "gpu" if use_gpu else "cpu"
    
    ocr = None
    try:
        ocr = PaddleOCR(
            device=device,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            lang="ch",
            ocr_version="PP-OCRv4",
            enable_mkldnn=enable_mkldnn,
            cpu_threads=cpu_threads
        )
    except Exception as e:
        import traceback
        logging.error(f"Failed to initialize PaddleOCR: {e}")
        logging.error(traceback.format_exc())
        # Keep running to allow logging to flush, but maybe exit?
        # If we exit here, the process dies and pool might restart it indefinitely.
        # Let's wait a bit to ensure log is written.
        time.sleep(1)
        # We can't really recover, so re-raise or exit.
        raise e

    logging.info(f"Worker {os.getpid()} PaddleOCR init done. ocr={ocr}")
    try:
        logging.info(f"ocr.text_detector={getattr(ocr, 'text_detector', 'N/A')}")
        logging.info(f"ocr.text_recognizer={getattr(ocr, 'text_recognizer', 'N/A')}")
    except Exception as e:
        logging.error(f"Error checking ocr attributes: {e}")

    ocr_cache = OrderedDict()
    ocr_cache_max = 32

    while True:
        task = task_queue.get()
        if task is None:
            break

        req_id = task.get("id")
        payload = task.get("payload") or {}

        try:
            target_text = payload.get("target_text")
            use_angle_cls = bool(payload.get("use_angle_cls", False))

            img, img_path = _decode_image_from_payload(payload)
            if img is None and img_path:
                img = cv2.imread(img_path)
            if img is None:
                result_queue.put({"id": req_id, "code": -1, "status": 400, "msg": "No image provided"})
                continue

            img = _maybe_crop_and_resize(img, payload)

            cache_key = None
            try:
                raw = img.tobytes()
                cache_key = (
                    str(hash(raw)) + "|" + str(target_text) + "|" + ("1" if use_angle_cls else "0")
                )
                if cache_key in ocr_cache:
                    result_queue.put({"id": req_id, "code": 0, "data": ocr_cache[cache_key]})
                    continue
            except Exception:
                cache_key = None
            
            limit_side_len = int(payload.get("limit_side_len") or os.environ.get("OCR_LIMIT_SIDE_LEN", "960"))
            
            try:
                # 动态参数支持
                # 如果传入 det_limit_side_len 则使用传入值
                # 如果没有，则使用默认值
                # 注意：ocr.predict 并不直接接收 limit_side_len，
                # 但可以通过 ocr.text_detector_module.limit_side_len 来临时修改(不推荐并发下修改)
                # 或者调用时传递 (如果 PaddleOCR 封装支持的话，v2.6+ 支持 det_limit_side_len)
                
                # 检查是否支持 det_limit_side_len
                # PaddleOCR.predict(img, cls=True, det=True, rec=True, type_list=None, **kwargs)
                # kwargs 会传递给 detector
                
                result = ocr.ocr(img, cls=use_angle_cls, det=True, rec=True, det_limit_side_len=limit_side_len)
            except Exception:
                # 降级尝试，兼容旧版本
                 try:
                    result = ocr.predict(img, cls=use_angle_cls)
                 except TypeError:
                    result = ocr.predict(img)

            parsed_result = _parse_ocr_result(result, target_text)

            if cache_key is not None:
                ocr_cache[cache_key] = parsed_result
                if len(ocr_cache) > ocr_cache_max:
                    ocr_cache.popitem(last=False)

            result_queue.put({"id": req_id, "code": 0, "data": parsed_result})
        except FileNotFoundError as e:
            result_queue.put({"id": req_id, "code": -1, "status": 404, "msg": f"File not found: {e}"})
        except Exception as e:
            result_queue.put(
                {
                    "id": req_id,
                    "code": -1,
                    "status": 500,
                    "msg": str(e),
                }
            )


class OcrProcessPool:
    def __init__(self, worker_count):
        self._ctx = multiprocessing.get_context("spawn")
        self._task_queue = self._ctx.Queue(maxsize=max(4, worker_count * 4))
        self._result_queue = self._ctx.Queue()
        self._pending = {}
        self._pending_lock = threading.Lock()
        self._stopped = threading.Event()

        self._workers = []
        for i in range(worker_count):
            p = self._ctx.Process(target=_worker_main, args=(self._task_queue, self._result_queue, i))
            p.daemon = True
            p.start()
            self._workers.append(p)

        self._collector = threading.Thread(target=self._collect_results, daemon=True)
        self._collector.start()

    def _collect_results(self):
        while not self._stopped.is_set():
            try:
                item = self._result_queue.get(timeout=0.2)
            except Exception:
                continue
            if not item:
                continue
            req_id = item.get("id")
            if not req_id:
                continue
            with self._pending_lock:
                q = self._pending.get(req_id)
            if q is not None:
                try:
                    q.put_nowait(item)
                except Exception:
                    pass

    def submit(self, payload, timeout):
        req_id = uuid.uuid4().hex
        reply_q = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[req_id] = reply_q
        try:
            self._task_queue.put({"id": req_id, "payload": payload}, timeout=timeout)
            return reply_q.get(timeout=timeout)
        finally:
            with self._pending_lock:
                self._pending.pop(req_id, None)

    def close(self, join_timeout=5):
        self._stopped.set()
        for _ in self._workers:
            try:
                self._task_queue.put_nowait(None)
            except Exception:
                pass
        for p in self._workers:
            try:
                p.join(timeout=join_timeout)
            except Exception:
                pass


@app.post("/ocr/predict")
def ocr_predict():
    t0 = time.perf_counter()
    try:
        payload = None
        try:
            payload = request.get_json(silent=True)
        except Exception:
            payload = None
        payload = payload or {}

        if "image_base64" not in payload and "image" in request.files:
            buf = request.files["image"].read()
            payload["image_base64"] = base64.b64encode(buf).decode("ascii")

        pool = app.config.get("OCR_POOL")
        if pool is None:
            return jsonify({"code": -1, "msg": "OCR pool not initialized"}), 500

        timeout = float(os.environ.get("OCR_SERVER_TASK_TIMEOUT", "120"))
        res = pool.submit(payload, timeout=timeout)
        if not isinstance(res, dict):
            return jsonify({"code": -1, "msg": "Invalid worker response"}), 500

        if res.get("code") == 0:
            logging.info("ocr_predict ok cost_ms=%.1f", (time.perf_counter() - t0) * 1000.0)
            return jsonify({"code": 0, "data": res.get("data")})
        status = int(res.get("status", 500))
        logging.info("ocr_predict fail status=%s cost_ms=%.1f", status, (time.perf_counter() - t0) * 1000.0)
        return jsonify({"code": -1, "msg": res.get("msg")}), status
    except Exception as e:
        logging.error(f"OCR failed: {e}")
        logging.error(traceback.format_exc())
        return jsonify({"code": -1, "msg": str(e)}), 500


def main():
    multiprocessing.freeze_support()
    host = os.environ.get("OCR_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("OCR_SERVER_PORT", "8000"))
    use_gpu = os.environ.get("OCR_USE_GPU", "False").lower() == "true"
    if "OCR_WORKERS" in os.environ:
        worker_count = int(os.environ["OCR_WORKERS"])
    else:
        worker_count = 1 if use_gpu else int(str(max(1, (os.cpu_count() or 2) // 2)))
    logging.info("Starting OCR server host=%s port=%s workers=%s", host, port, worker_count)
    pool = OcrProcessPool(worker_count=worker_count)
    app.config["OCR_POOL"] = pool
    try:
        app.run(host=host, port=port, threaded=True)
    finally:
        try:
            pool.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
