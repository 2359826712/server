import os
import sys
import base64
import logging
import multiprocessing
import queue
import threading
import traceback
import time
import uuid
from collections import OrderedDict
import cv2
import numpy as np

sys.dont_write_bytecode = True

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("PADDLEOCR_HOME", os.path.join(_BASE_DIR, "paddleocr_home"))

# 配置日志 (如果被主程序再次配置也无妨)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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


def check_and_download_models():
    """
    Initialize PaddleOCR once in the main process to ensure models are downloaded
    and cached, preventing race conditions in worker processes.
    """
    logging.info("Checking and downloading OCR models in main process...")
    try:
        try:
            from paddleocr.paddleocr import PaddleOCR
        except ImportError:
            from paddleocr import PaddleOCR
            
        # Use same params as worker
        PaddleOCR(
            device="cpu",
            text_det_box_thresh=0.5,
            text_det_unclip_ratio=1.6,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            lang="ch",
            ocr_version="PP-OCRv4",
            enable_mkldnn=False,
            cpu_threads=1,
            show_log=False 
        )
        logging.info("OCR models check complete.")
    except Exception as e:
        logging.error(f"Error during model check: {e}")
        # traceback.print_exc()

def _worker_main(task_queue, result_queue, worker_index):
    init_error = None
    os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
    os.environ.setdefault("PADDLEOCR_HOME", os.path.join(_BASE_DIR, "paddleocr_home"))

    try:
        from paddleocr.paddleocr import PaddleOCR
    except ImportError:
        from paddleocr import PaddleOCR
    
    logging.info(f"PaddleOCR imported from {PaddleOCR.__module__}")

    # GPU / CPU 配置 (强制 CPU)
    use_gpu = False
    
    # CPU 加速配置
    enable_mkldnn = True # 开启 mkldnn 加速 (CPU模式下通常能显著提升速度)
    # 如果 worker 数量少 (例如 1 个)，则可以给更多线程 (例如 10)。
    # 如果 worker 数量多，则线程数要少。
    # 这里默认设为 10，配合默认 worker=1 使用。
    cpu_threads = int(os.environ.get("OCR_CPU_THREADS", "10"))
    
    device = "cpu"
    
    ocr = None
    try:
        logging.info(f"Worker {os.getpid()} starting PaddleOCR init with GPU={use_gpu}, threads={cpu_threads}, mkldnn={enable_mkldnn}...")
        ocr = PaddleOCR(
            device="cpu",
            text_det_box_thresh=0.5,
            text_det_unclip_ratio=1.6,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            lang="ch",
            ocr_version="PP-OCRv4",
            enable_mkldnn=enable_mkldnn,
            cpu_threads=cpu_threads,
            show_log=False
        )
    except Exception as e:
        import traceback
        logging.error(f"Failed to initialize PaddleOCR on device={device}: {e}")
        logging.error(traceback.format_exc())
        init_error = f"CPU init failed: {str(e)}"
        ocr = None

    if ocr:
        logging.info(f"Worker {os.getpid()} PaddleOCR init done. ocr={ocr}")
        try:
            logging.info(f"ocr.text_detector={getattr(ocr, 'text_detector', 'N/A')}")
            logging.info(f"ocr.text_recognizer={getattr(ocr, 'text_recognizer', 'N/A')}")
            
            # --- Warmup ---
            logging.info("Warming up OCR model...")
            warmup_start = time.time()
            dummy_img = np.zeros((300, 300, 3), dtype=np.uint8)
            cv2.putText(dummy_img, "Warmup", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            try:
                ocr.ocr(dummy_img, cls=False, det=True, rec=True)
                logging.info(f"Warmup done in {time.time() - warmup_start:.2f}s")
            except Exception as e:
                logging.error(f"Warmup failed: {e}")
                # Don't fail completely on warmup, but log it
                pass
            # --------------
        except Exception as e:
            logging.error(f"Error checking ocr attributes or warmup: {e}")
            init_error = f"Warmup failed: {str(e)}"
            ocr = None

    ocr_cache = OrderedDict()
    ocr_cache_max = 32

    while True:
        task = task_queue.get()
        if task is None:
            break

        req_id = task.get("id")
        payload = task.get("payload") or {}

        if init_error:
             result_queue.put({"id": req_id, "code": -1, "status": 500, "msg": f"Worker Init Error: {init_error}"})
             continue
        
        if ocr is None:
             result_queue.put({"id": req_id, "code": -1, "status": 500, "msg": "Worker Init Error: OCR instance is None"})
             continue

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
            rec_batch_num = int(payload.get("rec_batch_num") or os.environ.get("OCR_REC_BATCH_NUM", "6"))
            
            try:
                # PaddleOCR.ocr() method signature:
                # def ocr(self, img, det=True, rec=True, cls=True, bin=False, inv=False, alpha_color=(255, 255, 255))
                # It does not accept det_limit_side_len or rec_batch_num as arguments to .ocr() directly in newer versions
                # These are usually passed in __init__ or handled internally.
                # However, older versions or some forks might. 
                # Let's check if we can pass them or if we should rely on init params.
                # Since we passed them in init (if they were available there), let's stick to standard args here.
                # Actually, PaddleOCR class stores these in self.args.
                # We can try to temporarily set them if needed, but it's safer to just call ocr(img, ...)
                
                # If we really need to change them per request, we might need to modify self.args, but that's risky for concurrency (though we are single threaded here)
                
                # Let's try standard call first.
                result = ocr.ocr(img, cls=use_angle_cls, det=True, rec=True)
            except Exception as e:
                import traceback
                logging.error(f"ocr.ocr failed: {e}")
                logging.error(traceback.format_exc())
                raise e

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
