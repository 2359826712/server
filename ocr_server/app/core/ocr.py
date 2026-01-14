
import base64
import cv2
import numpy as np
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from paddleocr import PaddleOCR
from app.core.config import settings
import paddle

# Patch for PaddlePaddle 2.6+
try:
    if hasattr(paddle, 'base') and hasattr(paddle.base, 'libpaddle') and hasattr(paddle.base.libpaddle, 'AnalysisConfig'):
        if not hasattr(paddle.base.libpaddle.AnalysisConfig, 'set_optimization_level'):
            paddle.base.libpaddle.AnalysisConfig.set_optimization_level = lambda self, x: None
except Exception:
    pass

logger = logging.getLogger(__name__)

class OCREngine:
    _instance = None
    
    def __init__(self):
        logger.info("Initializing OCR Engine...")
        os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
        os.environ.setdefault("PADDLEPDX_NO_NETWORK", "True")
        self.use_gpu = settings.USE_GPU
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self._disabled = os.environ.get("UNIT_TEST") == "1"
        if self._disabled:
            logger.info("OCR Engine disabled (UNIT_TEST=1).")
            return
        
        # GPU Check
        if self.use_gpu:
            try:
                if not paddle.device.is_compiled_with_cuda():
                    logger.warning("PaddlePaddle is not compiled with CUDA. Falling back to CPU.")
                    self.use_gpu = False
                else:
                    paddle.device.set_device("gpu")
                    logger.info(f"Using GPU: {paddle.device.get_device()}")
            except Exception as e:
                logger.warning(f"Error checking GPU: {e}. Falling back to CPU.")
                self.use_gpu = False

        if not self.use_gpu:
             paddle.device.set_device("cpu")

        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=settings.OCR_LANG,
            use_gpu=self.use_gpu,
            show_log=False,
        )
        # Thread pool for processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        logger.info("OCR Engine Initialized.")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _decode_image(self, b64_string: str):
        if "," in b64_string:
            b64_string = b64_string.split(",", 1)[1]
        try:
            buf = base64.b64decode(b64_string)
            arr = np.frombuffer(buf, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Image decode error: {e}")
            raise ValueError("Invalid image data")

    def _process_sync(self, img, target_text, max_side):
        if img is None:
            return []
            
        h, w = img.shape[:2]
        if max_side and max(h, w) > max_side:
            scale = max_side / float(max(h, w))
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h))
            
        result = self.ocr.ocr(img, cls=True)
        
        parsed_data = []
        if result and result[0]:
            for line in result[0]:
                box = line[0]
                txt = line[1][0]
                score = line[1][1]
                
                if target_text and target_text not in txt:
                    continue
                    
                parsed_data.append({
                    "box": box,
                    "text": txt,
                    "score": float(score)
                })
        return parsed_data

    async def predict(self, b64_image: str, target_text: str = None, max_side: int = 720):
        loop = asyncio.get_event_loop()
        async with self.semaphore:
            try:
                if self._disabled:
                    return []
                img = await loop.run_in_executor(self.executor, self._decode_image, b64_image)
                result = await loop.run_in_executor(self.executor, self._process_sync, img, target_text, max_side)
                return result
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                raise e
