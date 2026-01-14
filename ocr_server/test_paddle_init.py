import os
import logging
import sys

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test():
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        logging.error("Failed to import PaddleOCR")
        return

    logging.info("Starting PaddleOCR init...")
    try:
        ocr = PaddleOCR(
            device="cpu",
            text_det_box_thresh=0.5,
            text_det_unclip_ratio=1.6,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="ch",
            ocr_version="PP-OCRv4",
            enable_mkldnn=False,
            cpu_threads=1
        )
        logging.info("PaddleOCR init done.")
    except Exception as e:
        logging.error(f"Init failed: {e}")
        return

    logging.info("Starting Warmup...")
    try:
        # Create a dummy image if test_image.png doesn't exist
        img_path = "test_image.png"
        if not os.path.exists(img_path):
            import cv2
            import numpy as np
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(img_path, img)
            
        ocr.ocr(img_path, cls=False, det=True, rec=True)
        logging.info("Warmup done.")
    except Exception as e:
        logging.error(f"Warmup failed: {e}")

if __name__ == "__main__":
    test()
