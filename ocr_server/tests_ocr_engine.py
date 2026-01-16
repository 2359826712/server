import time
import numpy as np
import cv2

from ocr_server_other.server import ocr_engine


def _build_dummy_image() -> np.ndarray:
    img = np.full((50, 200, 3), 255, dtype=np.uint8)
    cv2.putText(img, "Hello", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    return img


def test_ocr_engine_det_mode():
    img = _build_dummy_image()
    result = ocr_engine.run(img, det=True, use_angle_cls=False, target_text=None)
    assert isinstance(result, list)
    if result:
        item = result[0]
        assert "text" in item and "confidence" in item and "box" in item


def test_ocr_engine_rec_only_mode():
    img = _build_dummy_image()
    result = ocr_engine.run(img, det=False, use_angle_cls=False, target_text=None)
    assert isinstance(result, list)
    if result:
        item = result[0]
        assert "text" in item and "confidence" in item and "box" in item


def bench_ocr_engine():
    img = _build_dummy_image()
    for det in (True, False):
        t0 = time.time()
        for _ in range(5):
            _ = ocr_engine.run(img, det=det, use_angle_cls=False, target_text=None)
        elapsed = time.time() - t0
        print(f"BENCH det={det}: {elapsed/5.0:.4f} s per run")


if __name__ == "__main__":
    test_ocr_engine_det_mode()
    test_ocr_engine_rec_only_mode()
    bench_ocr_engine()

