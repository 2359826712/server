FROM paddlepaddle/paddle:2.5.0

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISABLE_MODEL_SOURCE_CHECK=True

WORKDIR /app

COPY ocr_server_other /app/ocr_server_other
COPY ocr_api.py /app/ocr_api.py

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir flask paddleocr \
    && python -m pip install --no-cache-dir opencv-python-headless

EXPOSE 5000

ENV OCR_BIND_HOST=0.0.0.0
ENV OCR_PORT=5000

CMD ["python", "-u", "ocr_server_other/server.py"]

