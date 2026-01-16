import cv2
import numpy as np
import paddle
from paddleocr import PaddleOCR, TextRecognition

# Set flags like server.py
try:
    paddle.set_flags({
        "FLAGS_new_executor": 0,
    })
except Exception:
    pass

# Create a dummy image (white background, black text-ish)
img = np.full((50, 200, 3), 255, dtype=np.uint8)
cv2.putText(img, "Hello", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

# Init OCR exactly like server.py
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
    lang="ch",
    ocr_version="PP-OCRv3",
    enable_mkldnn=True,
)

print("Pipeline dir:", dir(ocr.paddlex_pipeline))
# Try to access submodules
# print("Pipeline submodules:", ocr.paddlex_pipeline.submodules) # Guessing attribute name

