import base64
import io
import os

import pyautogui
import requests

try:
    import mss

    _has_mss = True
except Exception:
    _has_mss = False


class Arc_api:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._http = requests.Session()
            self.ocr_server_url = (os.environ.get("OCR_SERVER_URL") or "http://127.0.0.1:8000").rstrip("/")
            self._initialized = True

    def ocr_text(self, x1, y1, x2, y2, target_text="", timeout=5, max_side=720, use_angle_cls=False, ocr_server_url=None):
        try:
            w = x2 - x1
            h = y2 - y1
            if w <= 0 or h <= 0:
                return None

            if _has_mss:
                with mss.mss() as sct:
                    monitor = {"left": x1, "top": y1, "width": w, "height": h}
                    shot = sct.grab(monitor)
                    import numpy as _np
                    import cv2 as _cv2

                    frame = _np.array(shot)[:, :, :3]
                    frame = _cv2.cvtColor(frame, _cv2.COLOR_BGRA2BGR)
                    ok, buf = _cv2.imencode(".jpg", frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])
                    if not ok:
                        return None
                    img_str = base64.b64encode(buf.tobytes()).decode()
            else:
                img = pyautogui.screenshot(region=(x1, y1, w, h))
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

            base_url = (ocr_server_url or self.ocr_server_url or "http://127.0.0.1:8000").rstrip("/")
            url = f"{base_url}/ocr/predict"
            payload = {
                "image_base64": img_str,
                "target_text": target_text,
                "max_side": max_side,
                "use_angle_cls": use_angle_cls,
            }

            response = self._http.post(url, json=payload, timeout=timeout)
            if response.status_code != 200:
                return None

            res_json = response.json()
            if res_json.get("code") == 0:
                return res_json.get("data")
            return None
        except requests.exceptions.ConnectionError:
            return None
        except Exception:
            return None

