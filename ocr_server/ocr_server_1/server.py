# 这是一个运行在 64位 Python 下的 OCR 服务
# 必须使用 64位 Python 解释器运行此脚本！
# pip install flask paddlepaddle paddleocr

from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import os
import logging
import base64
import io
import numpy as np
import cv2
import traceback

os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
try:
    import paddlex.utils.deps as _px_deps
    _px_deps.require_extra = lambda *args, **kwargs: None
    _px_deps.require_deps = lambda *args, **kwargs: None
except Exception:
    pass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

print("正在初始化 PaddleOCR，请稍候...")
# 初始化 OCR，只需要加载一次
# use_angle_cls=True 自动识别方向, lang="ch" 中文
# ocr_version='PP-OCRv4' 强制使用 v4 模型，避免调用 paddlex
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
    lang="ch",
    ocr_version="PP-OCRv4",
) 
print("PaddleOCR 初始化完成！")

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "msg": "Pong!"})

@app.route('/ocr', methods=['POST'])
def ocr_process():
    data = None
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None
    img = None
    img_path = None
    if data:
        b64 = data.get('image_base64')
        if b64:
            try:
                if ',' in b64:
                    b64 = b64.split(',', 1)[1]
                buf = base64.b64decode(b64)
                arr = np.frombuffer(buf, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            except Exception as e:
                return jsonify({"code": -1, "msg": f"Decode base64 failed: {e}"}), 400
        else:
            img_path = data.get('image_path')
    if img is None and 'image' in request.files:
        try:
            buf = request.files['image'].read()
            arr = np.frombuffer(buf, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({"code": -1, "msg": f"Decode file failed: {e}"}), 400
    if img is None and img_path:
        if not os.path.exists(img_path):
            return jsonify({"code": -1, "msg": f"File not found: {img_path}"}), 404
    if img is None and not img_path:
        return jsonify({"code": -1, "msg": "No image provided"}), 400
    
    # 获取可选参数
    region = data.get('region') if data else None # [x, y, w, h]
    target_text = data.get('target_text') if data else None
    use_angle_cls = data.get('use_angle_cls', False) if data else False
    
    try:
        # 如果需要裁剪，必须先加载图片
        if region:
            if img is None:
                # 从路径加载
                img = cv2.imread(img_path)
                if img is None:
                    return jsonify({"code": -1, "msg": f"Failed to load image from {img_path}"}), 400
            
            # 执行裁剪
            x, y, w, h = map(int, region)
            # 确保不越界 (可选，numpy 切片会自动处理，但逻辑上要正确)
            h_img, w_img = img.shape[:2]
            x = max(0, x)
            y = max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)
            
            if w > 0 and h > 0:
                img = img[y:y+h, x:x+w]
            else:
                 return jsonify({"code": -1, "msg": "Invalid region"}), 400
                 
        target = img if img is not None else img_path
        
        # 运行 OCR
        # cls=False 速度快，cls=True 支持方向检测
        # 注意：某些版本的 PaddleOCR.ocr() 不接受关键字参数 cls，需要位置参数或特定处理
        # 这里尝试直接传，如果报错则不传 cls 参数 (默认使用 init 时的配置)
        try:
             result = ocr.ocr(target, cls=use_angle_cls)
        except TypeError:
             # 如果不支持 cls 关键字参数，则只传 target
             # 这种情况下方向分类取决于初始化时的 use_angle_cls=True/False
             result = ocr.ocr(target)
        
        parsed_result = []
        # 解析结果
        if result and result[0]:
            # 兼容 PaddleX pipeline 输出格式 (dict)
            if isinstance(result[0], dict):
                res = result[0]
                boxes = res.get('dt_polys', [])
                texts = res.get('rec_texts', [])
                scores = res.get('rec_scores', [])
                
                for box, text, score in zip(boxes, texts, scores):
                    # 如果指定了目标文本，进行过滤
                    if target_text and target_text not in text:
                        continue
                    
                    # 转换 numpy array 为 list
                    if hasattr(box, 'tolist'):
                        box = box.tolist()
                        
                    parsed_result.append({
                        "text": text,
                        "confidence": float(score),
                        "box": box
                    })
            
            # 兼容传统 PaddleOCR 输出格式 (list of lists)
            elif isinstance(result[0], list):
                 for line in result[0]:
                    text = line[1][0]
                    confidence = float(line[1][1])
                    box = line[0]
                    
                    # 如果指定了目标文本，进行过滤
                    if target_text and target_text not in text:
                        continue
                    
                    parsed_result.append({
                        "text": text,
                        "confidence": confidence,
                        "box": box
                    })
        
        logging.info(f"Recognized {len(parsed_result)} lines")
        return jsonify({"code": 0, "data": parsed_result})
    except Exception as e:
        logging.error(f"OCR failed: {e}")
        logging.error(traceback.format_exc())
        return jsonify({"code": -1, "msg": str(e)}), 500

if __name__ == '__main__':
    print("启动 OCR 服务端口 5000...")
    # host='127.0.0.1' 限制只允许本地访问，更安全
    app.run(host='127.0.0.1', port=5000)
