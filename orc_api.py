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

    def __init__(self, server_url=None):
        self._http = requests.Session()
        if server_url:
            self.server_url = server_url
        else:
            self.server_url = "http://127.0.0.1:5000/ocr"

    def ocr_text(self, x1, y1, x2, y2, target_text="", timeout=5, max_side=480, use_angle_cls=False):
        """
        截图并调用本地 OCR 服务进行识别 (不保存图片文件)
        """
        try:
            w = x2 - x1
            h = y2 - y1
            if w <= 0 or h <= 0:
                print("无效的截图区域")
                return None
            
            # 强制使用 pyautogui 截图，规避 mss 可能导致的崩溃
            if _has_mss:
            # if False: 
                with mss.mss() as sct:
                    monitor = {"left": x1, "top": y1, "width": w, "height": h}
                    shot = sct.grab(monitor)
                    import numpy as _np
                    import cv2 as _cv2
                    # BGRA -> BGR
                    frame = _np.array(shot)[:, :, :3]
                    frame = _cv2.cvtColor(frame, _cv2.COLOR_BGRA2BGR)
                    # 编码为 JPEG，降低开销
                    ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])
                    if not ok:
                        raise Exception("mss 编码失败")
                    img_str = base64.b64encode(buf.tobytes()).decode()
            else:
                # print(f"截图区域: {x1},{y1} {w}x{h}")
                img = pyautogui.screenshot(region=(x1, y1, w, h))
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
            
            url = self.server_url
            payload = {
                "image_base64": img_str,
                "target_text": target_text,
                "max_side": max_side,
                "use_angle_cls": use_angle_cls,
            }

            try:
                response = self._http.post(url, json=payload, timeout=timeout)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get("code") == 0:
                        return res_json.get("data")
                    else:
                        print(f"OCR 识别失败: {res_json.get('msg')}")
                        return None
                else:
                    print(f"OCR 服务请求失败: {response.status_code}")
                    return None
            except requests.exceptions.ConnectionError:
                 print(f"OCR 服务未启动或无法连接 ({self.server_url})")
                 return None
                
        except Exception as e:
            print(f"OCR 调用异常: {e}")
            return None

    def ocr_recognize(self, x1, y1, x2, y2, target_text="", timeout=5, max_side=480, use_angle_cls=False):
        data = self.ocr_text(x1, y1, x2, y2, target_text=target_text, timeout=timeout, max_side=max_side, use_angle_cls=use_angle_cls)
        if not data:
            return None
        def _rect_from_box(box):
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            return x_min, y_min, x_max - x_min, y_max - y_min
        out = []
        for item in data:
            box = item.get("box")
            text = item.get("text")
            conf = item.get("confidence")
            cx = sum(p[0] for p in box) / 4.0 + x1
            cy = sum(p[1] for p in box) / 4.0 + y1
            rx, ry, rw, rh = _rect_from_box(box)
            rx += x1
            ry += y1
            out.append({
                "text": text,
                "confidence": conf,
                "box": box,
                "center": [int(cx), int(cy)],
                "rect": [int(rx), int(ry), int(rw), int(rh)]
            })
        return out
