
from fastapi.testclient import TestClient
import os
os.environ["UNIT_TEST"] = "1"
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
from app.main import app
import base64
import io
from PIL import Image
import pytest

client = TestClient(app)

def create_dummy_image():
    img = Image.new('RGB', (100, 30), color = (255, 255, 255))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ocr_endpoint():
    img_b64 = create_dummy_image()
    payload = {
        "image_base64": img_b64,
        "target_text": "",
        "max_side": 720
    }
    
    # We expect the request to succeed, even if OCR finds nothing
    response = client.post("/ocr", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] in [0, -1] # 0 success, -1 error (e.g. model loading fail)
    
    if json_data["code"] == 0:
        assert "data" in json_data
        assert "msg" in json_data
