import requests
import time
import base64
import cv2
import numpy as np
import os

def create_dummy_image(path):
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Hello World", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
    cv2.imwrite(path, img)

def test_ocr():
    url = "http://127.0.0.1:8000/ocr"
    img_path = "test_image.png"
    
    if not os.path.exists(img_path):
        create_dummy_image(img_path)

    with open(img_path, "rb") as f:
        img_bytes = f.read()
    
    b64_img = base64.b64encode(img_bytes).decode('utf-8')
    
    payload = {
        "image_base64": b64_img,
        # "use_angle_cls": True
    }
    
    try:
        start_time = time.time()
        resp = requests.post(url, json=payload)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        print(f"Time taken: {time.time() - start_time:.4f}s")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_ocr()
